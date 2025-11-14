#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
n8n Nodes Explorer - Streamlit App
Search and explore all n8n node types
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="n8n Nodes Explorer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stDataFrame {
        width: 100%;
    }
    .node-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        background-color: #f9f9f9;
    }
    .node-type {
        font-family: monospace;
        color: #0066cc;
        font-weight: bold;
    }
    .node-category {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
        font-weight: bold;
        margin-right: 0.5rem;
    }
    .cat-app { background-color: #e3f2fd; color: #1976d2; }
    .cat-trigger { background-color: #fff3e0; color: #f57c00; }
    .cat-core { background-color: #e8f5e9; color: #388e3c; }
    .cat-langchain { background-color: #f3e5f5; color: #7b1fa2; }
    .cat-community { background-color: #fce4ec; color: #c2185b; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_database_connection():
    """Cached database connection"""
    return sqlite3.connect('data/n8n_docs.db', check_same_thread=False)

@st.cache_data(ttl=60)
def load_all_nodes():
    """Load all nodes from database"""
    conn = get_database_connection()

    # Official nodes from API
    query_api = """
        SELECT
            node_type,
            display_name,
            description,
            category,
            version,
            'API' as source
        FROM node_types_api
    """

    # GitHub nodes
    query_github = """
        SELECT
            node_type,
            display_name,
            description,
            'GitHub' as category,
            version,
            'GitHub' as source
        FROM node_types_github
    """

    # Community nodes
    query_community = """
        SELECT
            package_name as node_type,
            package_name as display_name,
            description,
            'Community' as category,
            version,
            'npm' as source
        FROM community_nodes
    """

    df_api = pd.read_sql_query(query_api, conn)
    df_github = pd.read_sql_query(query_github, conn)
    df_community = pd.read_sql_query(query_community, conn)

    # Combine all (exclude n8n API workflow nodes)
    df = pd.concat([df_api, df_github, df_community], ignore_index=True)

    # Remove duplicates (prefer API over GitHub)
    df = df.drop_duplicates(subset=['node_type'], keep='first')

    # Categorize
    df['category'] = df.apply(categorize_node, axis=1)

    return df

def categorize_node(row):
    """Categorize node based on node_type"""
    node_type = row['node_type']

    if pd.isna(node_type):
        return 'Unknown'

    # Community nodes
    if node_type.startswith('@') and 'n8n-nodes' in node_type:
        return 'Community'

    # LangChain nodes
    if 'langchain' in node_type.lower():
        return 'LangChain'

    # Official n8n-nodes-base
    if node_type.startswith('n8n-nodes-base.'):
        node_name = node_type.replace('n8n-nodes-base.', '').lower()

        # Trigger nodes
        if 'trigger' in node_name:
            return 'Trigger'

        # Core/Utility nodes
        core_keywords = [
            'webhook', 'cron', 'schedule', 'manual', 'code', 'set', 'if', 'switch',
            'merge', 'split', 'function', 'crypto', 'datetime', 'filter', 'sort',
            'limit', 'aggregate', 'compress', 'convert', 'edit', 'html', 'xml',
            'jwt', 'wait', 'noop', 'error', 'debug', 'sticky'
        ]

        if any(keyword in node_name for keyword in core_keywords):
            return 'Core'

        # App nodes
        return 'App'

    return row.get('category', 'Unknown')

def get_category_stats(df):
    """Get statistics by category"""
    return df['category'].value_counts().to_dict()

def calculate_relevance_score(row, search_terms):
    """Calculate relevance score for intelligent search"""
    score = 0
    node_type = str(row['node_type']).lower()
    display_name = str(row['display_name']).lower()
    description = str(row['description']).lower() if pd.notna(row['description']) else ''

    for term in search_terms:
        term = term.lower()

        # Exact match in display name (highest priority)
        if term == display_name:
            score += 100
        elif term in display_name:
            score += 50

        # Exact match in node_type
        if term == node_type:
            score += 80
        elif term in node_type:
            score += 30

        # Match in description
        if term in description:
            score += 10

        # Word boundary matches (whole word)
        import re
        if re.search(rf'\b{re.escape(term)}\b', display_name):
            score += 20
        if re.search(rf'\b{re.escape(term)}\b', node_type):
            score += 15

    return score

def expand_search_terms(search_term):
    """Expand search term with synonyms and related terms"""
    # Common synonyms and related terms for n8n nodes
    synonyms = {
        'email': ['mail', 'gmail', 'outlook', 'smtp', 'imap'],
        'mail': ['email', 'gmail', 'outlook', 'smtp'],
        'calendar': ['schedule', 'event', 'appointment', 'google calendar'],
        'database': ['db', 'sql', 'postgres', 'mysql', 'mongodb'],
        'db': ['database', 'sql', 'postgres', 'mysql'],
        'sheet': ['spreadsheet', 'excel', 'google sheets', 'airtable'],
        'spreadsheet': ['sheet', 'excel', 'google sheets'],
        'storage': ['drive', 'dropbox', 'box', 's3', 'cloud'],
        'cloud': ['storage', 'drive', 'aws', 'azure', 'gcp'],
        'chat': ['slack', 'teams', 'discord', 'telegram', 'whatsapp', 'messenger'],
        'message': ['chat', 'sms', 'whatsapp', 'telegram'],
        'crm': ['salesforce', 'hubspot', 'pipedrive', 'zoho'],
        'payment': ['stripe', 'paypal', 'paddle'],
        'automation': ['workflow', 'trigger', 'cron', 'schedule'],
        'ai': ['openai', 'anthropic', 'langchain', 'gpt', 'claude', 'gemini'],
        'llm': ['ai', 'openai', 'anthropic', 'langchain', 'gpt'],
        'social': ['twitter', 'facebook', 'linkedin', 'instagram'],
        'document': ['doc', 'pdf', 'google docs', 'notion'],
        'form': ['typeform', 'google forms', 'jotform'],
        'video': ['youtube', 'vimeo'],
        'sms': ['twilio', 'message', 'text'],
        'webhook': ['http', 'api', 'trigger'],
        'api': ['http', 'rest', 'webhook'],
        'code': ['javascript', 'python', 'function'],
        'microsoft': ['outlook', 'teams', 'onedrive', 'excel', 'sharepoint'],
        'google': ['gmail', 'sheets', 'drive', 'calendar', 'docs'],
        'aws': ['s3', 'lambda', 'dynamodb', 'sns', 'sqs'],
    }

    terms = [search_term.lower()]

    # Add synonyms
    if search_term.lower() in synonyms:
        terms.extend(synonyms[search_term.lower()])

    # Check if search term is part of any synonym
    for key, values in synonyms.items():
        if search_term.lower() in values:
            terms.append(key)
            terms.extend(values)

    # Remove duplicates while preserving order
    seen = set()
    expanded = []
    for term in terms:
        if term not in seen:
            seen.add(term)
            expanded.append(term)

    return expanded

def search_nodes(df, search_term, selected_categories, sort_by):
    """Intelligent filter and search nodes with relevance ranking"""
    # Filter by category
    if selected_categories and 'All' not in selected_categories:
        df = df[df['category'].isin(selected_categories)]

    # Intelligent search
    if search_term:
        # Expand search terms with synonyms
        search_terms = expand_search_terms(search_term)

        # Create a mask for matching rows
        mask = pd.Series([False] * len(df), index=df.index)

        for term in search_terms:
            term_lower = term.lower()
            mask |= (
                df['node_type'].str.lower().str.contains(term_lower, na=False, regex=False) |
                df['display_name'].str.lower().str.contains(term_lower, na=False, regex=False) |
                df['description'].str.lower().str.contains(term_lower, na=False, regex=False)
            )

        df = df[mask].copy()

        # Calculate relevance scores
        if len(df) > 0:
            df['_relevance'] = df.apply(lambda row: calculate_relevance_score(row, search_terms), axis=1)

            # Sort by relevance if we have search results
            if sort_by == 'Relevance' or search_term:
                df = df.sort_values('_relevance', ascending=False)

    # Sort (if not already sorted by relevance)
    if not search_term or sort_by != 'Relevance':
        if sort_by == 'Name (A-Z)':
            df = df.sort_values('display_name')
        elif sort_by == 'Name (Z-A)':
            df = df.sort_values('display_name', ascending=False)
        elif sort_by == 'Node Type (A-Z)':
            df = df.sort_values('node_type')
        elif sort_by == 'Category':
            df = df.sort_values(['category', 'display_name'])

    # Remove temporary relevance column if it exists
    if '_relevance' in df.columns:
        df = df.drop(columns=['_relevance'])

    return df

def get_category_color(category):
    """Get CSS class for category badge"""
    category_map = {
        'App': 'cat-app',
        'Trigger': 'cat-trigger',
        'Core': 'cat-core',
        'LangChain': 'cat-langchain',
        'Community': 'cat-community'
    }
    return category_map.get(category, 'cat-app')

def main():
    # Header
    st.title("🔍 n8n Nodes Explorer")
    st.markdown("Search all available n8n node types (Official, Community & Custom)")

    # Load data
    with st.spinner('Loading node data...'):
        df = load_all_nodes()

    # Sidebar - Filters
    st.sidebar.header("🎯 Filters & Options")

    # Category filter
    categories = ['All'] + sorted(df['category'].unique().tolist())
    selected_categories = st.sidebar.multiselect(
        "Categories",
        options=categories,
        default=['All']
    )

    # Sort options
    sort_options = ['Relevance', 'Name (A-Z)', 'Name (Z-A)', 'Node Type (A-Z)', 'Category']
    sort_by = st.sidebar.selectbox("Sort by", sort_options)

    # View mode
    view_mode = st.sidebar.radio(
        "View",
        options=['Cards', 'Table', 'Compact List'],
        index=1  # Default to Table view
    )

    # Statistics in sidebar
    st.sidebar.markdown("---")
    st.sidebar.header("📊 Statistics")
    stats = get_category_stats(df)

    total_nodes = len(df)
    st.sidebar.metric("Total Nodes", f"{total_nodes:,}")

    for category, count in sorted(stats.items()):
        st.sidebar.metric(category, f"{count:,}")

    # Main content - Search
    st.markdown("---")
    search_col1, search_col2 = st.columns([3, 1])

    with search_col1:
        # Initialize search term in session state if not present
        if 'search_term' not in st.session_state:
            st.session_state['search_term'] = ''

        search_term = st.text_input(
            "🔎 Intelligent Search",
            value=st.session_state['search_term'],
            placeholder="e.g. 'email', 'database', 'ai', 'payment'...",
            help="""
            **Intelligent Search with Synonyms:**
            - 'email' → finds Gmail, Outlook, SMTP, etc.
            - 'database' → finds Postgres, MySQL, MongoDB, etc.
            - 'ai' → finds OpenAI, Anthropic, LangChain, etc.
            - 'chat' → finds Slack, Teams, Discord, etc.
            - 'cloud' → finds AWS, Azure, Google Cloud, etc.
            """,
            key='search_input'
        )
        # Update session state when text input changes
        st.session_state['search_term'] = search_term

    with search_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state['search_term'] = ''
            st.rerun()

    # Quick search buttons
    st.markdown("**Quick Search:**")
    quick_col1, quick_col2, quick_col3, quick_col4, quick_col5, quick_col6 = st.columns(6)

    quick_searches = {
        '📧 Email': 'email',
        '💬 Chat': 'chat',
        '🤖 AI': 'ai',
        '💾 Database': 'database',
        '☁️ Cloud': 'cloud',
        '💳 Payment': 'payment'
    }

    cols = [quick_col1, quick_col2, quick_col3, quick_col4, quick_col5, quick_col6]
    for col, (label, term) in zip(cols, quick_searches.items()):
        with col:
            if st.button(label, use_container_width=True):
                st.session_state['search_term'] = term
                st.rerun()

    # Filter and search
    filtered_df = search_nodes(df, search_term, selected_categories, sort_by)

    # Show expanded search terms if searching
    if search_term:
        expanded_terms = expand_search_terms(search_term)
        if len(expanded_terms) > 1:
            with st.expander(f"🧠 Intelligent Search: '{search_term}' → {len(expanded_terms)} terms", expanded=False):
                st.info(f"Search expanded to: **{', '.join(expanded_terms[:10])}**" +
                       (f" +{len(expanded_terms)-10} more" if len(expanded_terms) > 10 else ""))

    # Results count
    st.markdown(f"**{len(filtered_df):,}** nodes found")

    # Display results based on view mode
    st.markdown("---")

    if len(filtered_df) == 0:
        st.info("No nodes found. Try a different search.")

    elif view_mode == 'Cards':
        # Card view
        for idx, row in filtered_df.iterrows():
            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    # Category badge
                    category_class = get_category_color(row['category'])
                    st.markdown(
                        f'<span class="node-category {category_class}">{row["category"]}</span>',
                        unsafe_allow_html=True
                    )

                    # Display name
                    st.markdown(f"### {row['display_name']}")

                    # Node type (technical name)
                    st.markdown(f'<code class="node-type">{row["node_type"]}</code>', unsafe_allow_html=True)

                    # Description
                    if pd.notna(row['description']) and row['description']:
                        st.markdown(f"*{row['description'][:200]}{'...' if len(str(row['description'])) > 200 else ''}*")

                with col2:
                    if pd.notna(row['version']):
                        st.markdown(f"**Version:** {row['version']}")
                    st.markdown(f"**Source:** {row['source']}")

                st.markdown("---")

    elif view_mode == 'Table':
        # Table view
        display_df = filtered_df[['display_name', 'node_type', 'category', 'version', 'description']].copy()
        display_df.columns = ['Name', 'Node Type', 'Category', 'Version', 'Description']

        # Truncate description
        display_df['Description'] = display_df['Description'].apply(
            lambda x: str(x)[:100] + '...' if pd.notna(x) and len(str(x)) > 100 else x
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=600
        )

    elif view_mode == 'Compact List':
        # Compact list view
        for idx, row in filtered_df.iterrows():
            category_class = get_category_color(row['category'])

            st.markdown(
                f'''
                <div style="padding: 0.5rem 0; border-bottom: 1px solid #eee;">
                    <span class="node-category {category_class}">{row["category"]}</span>
                    <strong>{row["display_name"]}</strong>
                    <br>
                    <code style="font-size: 0.8rem; color: #666;">{row["node_type"]}</code>
                </div>
                ''',
                unsafe_allow_html=True
            )

    # Footer
    st.markdown("---")
    st.markdown(
        f"""
        <div style="text-align: center; color: #666; font-size: 0.9rem;">
            💾 Database: n8n_docs.db |
            📊 {total_nodes:,} Total Nodes |
            🔄 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == '__main__':
    main()

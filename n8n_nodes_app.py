#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
n8n Nodes Explorer - Streamlit App
Search and explore all n8n node types
"""

import streamlit as st
import sqlite3
import pandas as pd
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

def load_node_context_for_ai(limit=100):
    """
    Load node information for AI context
    Returns nodes with their operations, parameters, and credentials
    """
    conn = get_database_connection()
    cursor = conn.cursor()

    # Get nodes with their details
    cursor.execute('''
        SELECT DISTINCT
            n.node_type,
            n.display_name,
            n.description,
            n.category
        FROM node_types_api n
        WHERE n.category IN ('App', 'Trigger', 'Core')
        ORDER BY n.display_name
        LIMIT ?
    ''', (limit,))

    nodes_data = []
    for node_type, display_name, description, category in cursor.fetchall():
        node_info = {
            'node_type': node_type,
            'display_name': display_name,
            'description': description,
            'category': category
        }
        nodes_data.append(node_info)

    return nodes_data

def generate_workflow_with_openai(prompt, api_key, nodes_context):
    """
    Generate n8n workflow using OpenAI API
    """
    try:
        import openai

        # Set API key (compatible with openai 0.28)
        openai.api_key = api_key

        # Build system message with node context
        system_message = f"""You are an expert n8n workflow automation engineer.
You help users create n8n workflows in JSON format.

Available n8n nodes (selection):
{json.dumps(nodes_context[:20], indent=2)}

CRITICAL RULES:
1. ALWAYS return valid n8n workflow JSON - NEVER ask questions or provide explanations
2. If the user's request is vague, make reasonable assumptions and create a working workflow
3. Use exact node types from the list above
4. Include proper node connections between all nodes
5. Set realistic parameters with sensible defaults
6. Use expressions like {{{{ $json.fieldname }}}} for dynamic values
7. Follow n8n workflow schema exactly

Example workflow structure:
{{
  "name": "Workflow Name",
  "nodes": [
    {{
      "parameters": {{}},
      "name": "Node Name",
      "type": "n8n-nodes-base.nodetype",
      "typeVersion": 1,
      "position": [250, 300],
      "id": "unique-id-1"
    }},
    {{
      "parameters": {{}},
      "name": "Next Node",
      "type": "n8n-nodes-base.nexttype",
      "typeVersion": 1,
      "position": [500, 300],
      "id": "unique-id-2"
    }}
  ],
  "connections": {{
    "Node Name": {{
      "main": [[{{"node": "Next Node", "type": "main", "index": 0}}]]
    }}
  }}
}}

MANDATORY: Return ONLY the JSON workflow, absolutely NO explanations, questions, or additional text."""

        # Call OpenAI API (compatible with openai 0.28)
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Create an n8n workflow for: {prompt}"}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        # Extract workflow JSON
        workflow_json = response.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if workflow_json.startswith('```'):
            parts = workflow_json.split('```')
            if len(parts) >= 2:
                workflow_json = parts[1]
                if workflow_json.startswith('json'):
                    workflow_json = workflow_json[4:]
                workflow_json = workflow_json.strip()

        # Parse to validate
        workflow = json.loads(workflow_json)

        return workflow, None

    except ImportError:
        return None, "OpenAI package not installed. Run: pip install openai==0.28"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON generated: {e}\n\nRaw response: {workflow_json[:500] if 'workflow_json' in locals() else 'N/A'}"
    except Exception as e:
        return None, f"Error: {str(e)}"

def validate_workflow(workflow):
    """
    Validate n8n workflow structure
    """
    errors = []
    warnings = []

    # Check required fields
    if 'nodes' not in workflow:
        errors.append("Missing 'nodes' field")
    if 'connections' not in workflow:
        warnings.append("Missing 'connections' field - nodes won't be connected")

    # Validate nodes
    if 'nodes' in workflow:
        for i, node in enumerate(workflow['nodes']):
            if 'type' not in node:
                errors.append(f"Node {i}: Missing 'type' field")
            if 'name' not in node:
                errors.append(f"Node {i}: Missing 'name' field")
            if 'position' not in node:
                warnings.append(f"Node {i}: Missing 'position' field")

    return errors, warnings

def export_workflow(workflow):
    """
    Export workflow as JSON string
    """
    return json.dumps(workflow, indent=2, ensure_ascii=False)

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
    st.title("🔍 n8n Nodes Explorer & AI Workflow Generator")

    # Main tabs
    tab1, tab2 = st.tabs(["🔍 Node Explorer", "🤖 AI Workflow Generator"])

    # Load data
    with st.spinner('Loading node data...'):
        df = load_all_nodes()

    # ===== TAB 1: NODE EXPLORER =====
    with tab1:
        st.markdown("Search all available n8n node types (Official, Community & Custom)")

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
        st.sidebar.metric(label="Total Nodes", value=f"{total_nodes:,}")

        for category, count in sorted(stats.items()):
            if category:  # Only show metrics with non-empty category names
                st.sidebar.metric(label=category, value=f"{count:,}")

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

            # Fix version column to be string type
            display_df['Version'] = display_df['Version'].astype(str).replace('nan', '')

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

    # ===== TAB 2: AI WORKFLOW GENERATOR =====
    with tab2:
        st.markdown("Generate n8n workflows from natural language using AI")

        # Check for API key
        api_key = os.getenv('OPENAI_API_KEY', '')

        if not api_key:
            st.error("⚠️ OpenAI API Key not found in environment variables")
            st.info("Please add OPENAI_API_KEY to your .env file")
            st.code("OPENAI_API_KEY=sk-your-key-here", language="bash")
            return

        st.success("✅ OpenAI API Key loaded from .env")

        # Load node context for AI
        with st.spinner('Loading node database for AI...'):
            nodes_context = load_node_context_for_ai(limit=100)

        st.info(f"📚 Loaded {len(nodes_context)} nodes for AI context")

        # Example prompts
        st.markdown("### 💡 Example Prompts")
        examples_col1, examples_col2, examples_col3 = st.columns(3)

        with examples_col1:
            if st.button("📧 Email on Webhook", use_container_width=True, key='ex1'):
                st.session_state['ai_prompt'] = "Create a workflow that receives a webhook and sends an email with the data"

        with examples_col2:
            if st.button("🗄️ Database to Spreadsheet", use_container_width=True, key='ex2'):
                st.session_state['ai_prompt'] = "Get data from PostgreSQL and save it to Google Sheets"

        with examples_col3:
            if st.button("🤖 AI Content Generator", use_container_width=True, key='ex3'):
                st.session_state['ai_prompt'] = "Receive a topic via webhook, use OpenAI to generate content, and post to Slack"

        # Prompt input
        st.markdown("### ✍️ Describe Your Workflow")
        ai_prompt = st.text_area(
            "What should the workflow do?",
            value=st.session_state.get('ai_prompt', ''),
            placeholder="Example: Create a workflow that monitors Gmail for new emails, extracts attachments, and uploads them to Google Drive",
            height=100,
            key='ai_prompt_input'
        )

        if 'ai_prompt_input' in st.session_state and st.session_state['ai_prompt_input']:
            st.session_state['ai_prompt'] = st.session_state['ai_prompt_input']

        # Generate button
        col1, col2 = st.columns([3, 1])

        with col1:
            generate_button = st.button("🚀 Generate Workflow with AI", type="primary", use_container_width=True)

        with col2:
            if st.button("🗑️ Clear", use_container_width=True, key='clear_ai'):
                st.session_state['ai_prompt'] = ''
                st.session_state['ai_workflow'] = None
                st.rerun()

        # Generate workflow
        if generate_button:
            if not ai_prompt:
                st.error("⚠️ Please describe what the workflow should do")
            else:
                with st.spinner('🤖 Generating workflow with AI...'):
                    workflow, error = generate_workflow_with_openai(ai_prompt, api_key, nodes_context)

                    if error:
                        st.error(f"❌ {error}")
                    else:
                        st.session_state['ai_workflow'] = workflow
                        st.success("✅ Workflow generated successfully!")

        # Display workflow
        if 'ai_workflow' in st.session_state and st.session_state['ai_workflow']:
            workflow = st.session_state['ai_workflow']

            st.markdown("---")
            st.markdown("### 📋 Generated Workflow")

            # Validate
            errors, warnings = validate_workflow(workflow)

            if errors:
                st.error("❌ Validation Errors:")
                for error in errors:
                    st.write(f"- {error}")

            if warnings:
                st.warning("⚠️ Warnings:")
                for warning in warnings:
                    st.write(f"- {warning}")

            # Workflow info
            info_col1, info_col2, info_col3 = st.columns(3)

            with info_col1:
                st.metric("Nodes", len(workflow.get('nodes', [])))

            with info_col2:
                st.metric("Connections", len(workflow.get('connections', {})))

            with info_col3:
                workflow_name = workflow.get('name', 'Unnamed Workflow')
                st.metric("Workflow Name", workflow_name)

            # Tabs for different views
            workflow_tab1, workflow_tab2, workflow_tab3 = st.tabs(["📊 Visual Overview", "📝 JSON", "⬇️ Export"])

            with workflow_tab1:
                st.markdown("#### Nodes in Workflow")
                for i, node in enumerate(workflow.get('nodes', []), 1):
                    with st.expander(f"{i}. {node.get('name', 'Unnamed')} ({node.get('type', 'unknown')})"):
                        st.json(node)

                st.markdown("#### Connections")
                if workflow.get('connections'):
                    st.json(workflow['connections'])
                else:
                    st.info("No connections defined")

            with workflow_tab2:
                st.markdown("#### Complete Workflow JSON")
                workflow_json = json.dumps(workflow, indent=2, ensure_ascii=False)
                st.code(workflow_json, language='json')

            with workflow_tab3:
                st.markdown("#### Export Workflow")

                # Filename input
                filename = st.text_input(
                    "Filename",
                    value=workflow.get('name', 'workflow').replace(' ', '_') + '.json',
                    key='workflow_filename'
                )

                # Export button
                workflow_json_export = export_workflow(workflow)

                st.download_button(
                    label="📥 Download as JSON",
                    data=workflow_json_export,
                    file_name=filename,
                    mime="application/json",
                    use_container_width=True
                )

                st.markdown("---")
                st.markdown("#### How to Import in n8n")
                st.markdown("""
                1. Open your n8n instance
                2. Click on **Workflows** → **Import from File**
                3. Upload the downloaded JSON file
                4. Configure credentials if needed
                5. Activate and test the workflow
                """)

if __name__ == '__main__':
    main()

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
    page_title="n8n Nodes Explorer & AI Generator",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Dark Theme CSS
st.markdown("""
<style>
    /* Main container styling */
    .main > div {
        padding-top: 1.5rem;
    }

    /* Header styling - keeping visible text on dark backgrounds */
    h1, h2, h3 {
        font-weight: 600;
    }

    /* Tab styling - Dark theme */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: rgba(30, 41, 59, 0.3);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 2rem;
        background-color: rgba(51, 65, 85, 0.5);
        border-radius: 8px;
        border: 2px solid rgba(100, 116, 139, 0.3);
        font-weight: 600;
        font-size: 1.1rem;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        border-color: #3b82f6;
    }

    /* Card styling - Dark theme */
    .info-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }

    .stats-card {
        background: rgba(30, 41, 59, 0.5);
        padding: 1.25rem;
        border-radius: 10px;
        border: 1px solid rgba(100, 116, 139, 0.3);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
    }

    .node-card {
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid rgba(100, 116, 139, 0.3);
        margin-bottom: 1rem;
        background: rgba(30, 41, 59, 0.4);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    }

    .node-card:hover {
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        transform: translateY(-2px);
        border-color: rgba(59, 130, 246, 0.5);
    }

    /* Node type and category badges */
    .node-type {
        font-family: 'Courier New', monospace;
        color: #60a5fa;
        font-weight: 700;
        font-size: 0.95rem;
        background-color: rgba(59, 130, 246, 0.15);
        padding: 0.3rem 0.6rem;
        border-radius: 6px;
        display: inline-block;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }

    .node-category {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Category colors - vibrant gradients for dark mode */
    .cat-app {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        box-shadow: 0 2px 6px rgba(59, 130, 246, 0.4);
    }
    .cat-trigger {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        box-shadow: 0 2px 6px rgba(245, 158, 11, 0.4);
    }
    .cat-core {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        box-shadow: 0 2px 6px rgba(16, 185, 129, 0.4);
    }
    .cat-langchain {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
        color: white;
        box-shadow: 0 2px 6px rgba(139, 92, 246, 0.4);
    }
    .cat-community {
        background: linear-gradient(135deg, #ec4899 0%, #db2777 100%);
        color: white;
        box-shadow: 0 2px 6px rgba(236, 72, 153, 0.4);
    }

    /* Button styling - Dark theme */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        border: 2px solid rgba(100, 116, 139, 0.3);
        transition: all 0.3s ease;
        backdrop-filter: blur(5px);
    }

    .stButton > button:hover {
        border-color: #3b82f6;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.3);
    }

    /* Input styling - Dark theme */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 2px solid rgba(100, 116, 139, 0.3);
        background-color: rgba(30, 41, 59, 0.5);
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
    }

    /* Dataframe styling */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }

    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }

    /* Workflow preview - keep dark for code display */
    .workflow-preview {
        background-color: #1e293b;
        padding: 1.5rem;
        border-radius: 10px;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        color: #e2e8f0;
        max-height: 600px;
        overflow-y: auto;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(100, 116, 139, 0.3);
    }

    /* AI section styling */
    .ai-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.5);
    }

    .feature-box {
        background: rgba(30, 41, 59, 0.5);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #3b82f6;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
    }

    /* Ensure good contrast for code blocks */
    code {
        background-color: rgba(30, 41, 59, 0.6);
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        border: 1px solid rgba(100, 116, 139, 0.3);
    }
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

    # Fix version column - convert all to string to avoid Arrow serialization issues
    if 'version' in df.columns:
        df['version'] = df['version'].fillna('').astype(str).replace('nan', '').replace('None', '')

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
    Compatible with both openai 0.28 and 1.0+
    """
    try:
        import openai

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

        # Check OpenAI version and use appropriate API
        try:
            # Try new API (openai >= 1.0.0)
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Create an n8n workflow for: {prompt}"}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            workflow_json = response.choices[0].message.content.strip()
        except (ImportError, AttributeError):
            # Fallback to old API (openai 0.28)
            openai.api_key = api_key
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Create an n8n workflow for: {prompt}"}
                ],
                temperature=0.7,
                max_tokens=2000
            )
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
        return None, "OpenAI package not installed. Run: pip install openai"
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
    # Professional Header with gradient background
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 2rem; border-radius: 15px; margin-bottom: 2rem;
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);'>
        <h1 style='color: white; margin: 0; font-size: 2.5rem; font-weight: 800;'>
            🚀 n8n Workflow Studio
        </h1>
        <p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1.2rem;'>
            Explore 500+ Nodes & Generate AI-Powered Workflows
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Main tabs with elegant icons
    tab1, tab2 = st.tabs(["🔍 Node Explorer", "🤖 AI Workflow Generator"])

    # Load data
    with st.spinner('🔄 Loading node database...'):
        df = load_all_nodes()

    # ===== TAB 1: NODE EXPLORER =====
    with tab1:
        # Info banner
        st.markdown("""
        <div class='stats-card'>
            <h3 style='margin: 0 0 0.5rem 0; color: #1e293b;'>📚 Complete Node Directory</h3>
            <p style='margin: 0; color: #64748b;'>
                Browse and search through official, community, and custom n8n nodes.
                Find the perfect integration for your automation workflows.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Sidebar - Compact organized sections
        st.sidebar.markdown("""
        <div style='text-align: center; padding: 0.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 8px; margin-bottom: 1rem;'>
            <h3 style='color: white; margin: 0; font-size: 1.1rem;'>⚙️ Controls</h3>
        </div>
        """, unsafe_allow_html=True)

        # Quick Stats at top - compact
        stats = get_category_stats(df)
        total_nodes = len(df)

        st.sidebar.markdown(f"""
        <div style='background: rgba(59, 130, 246, 0.1); padding: 0.75rem; border-radius: 6px;
                    border-left: 3px solid #3b82f6; margin-bottom: 1rem;'>
            <div style='font-size: 1.5rem; font-weight: 700; color: #3b82f6;'>{total_nodes:,}</div>
            <div style='font-size: 0.8rem; color: #94a3b8;'>Total Nodes Available</div>
        </div>
        """, unsafe_allow_html=True)

        # Filters Section - compact
        with st.sidebar.expander("🎯 Filters", expanded=True):
            categories = ['All'] + sorted(df['category'].unique().tolist())
            selected_categories = st.multiselect(
                "Categories",
                options=categories,
                default=['All'],
                label_visibility="collapsed"
            )

        # Display Options - compact
        with st.sidebar.expander("🎨 Display", expanded=True):
            sort_options = ['Relevance', 'Name (A-Z)', 'Name (Z-A)', 'Node Type (A-Z)', 'Category']
            sort_by = st.selectbox(
                "Sort",
                sort_options,
                label_visibility="collapsed"
            )

            view_mode = st.radio(
                "View",
                options=['Table', 'Cards', 'Compact'],
                index=0,
                horizontal=True,
                label_visibility="collapsed"
            )

        # Statistics - very compact
        with st.sidebar.expander("📊 Statistics"):
            for category, count in sorted(stats.items()):
                if category and category.strip():
                    st.markdown(f"""
                    <div style='display: flex; justify-content: space-between; padding: 0.25rem 0;'>
                        <span style='font-size: 0.85rem;'>{category}</span>
                        <span style='font-weight: 600; color: #3b82f6;'>{count:,}</span>
                    </div>
                    """, unsafe_allow_html=True)

        # Main content - Search Section
        st.markdown("### 🔍 Search Nodes")

        # Initialize search term in session state if not present
        if 'search_term' not in st.session_state:
            st.session_state['search_term'] = ''

        search_col1, search_col2 = st.columns([4, 1])

        with search_col1:
            search_term = st.text_input(
                "Search",
                value=st.session_state['search_term'],
                placeholder="Search by name, type, or description... (e.g., 'email', 'database', 'ai')",
                help="🧠 **Intelligent Search** - Automatically expands your search with related terms and synonyms",
                key='search_input',
                label_visibility="collapsed"
            )
            st.session_state['search_term'] = search_term

        with search_col2:
            if st.button("🔄 Clear Search", width='stretch', type="secondary"):
                st.session_state['search_term'] = ''
                st.rerun()

        # Quick search buttons in elegant card
        st.markdown("""
        <div class='stats-card' style='margin-top: 1rem;'>
            <p style='margin: 0 0 0.75rem 0; color: #64748b; font-weight: 600;'>⚡ Quick Search</p>
        </div>
        """, unsafe_allow_html=True)

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
                if st.button(label, width='stretch', key=f"quick_{term}"):
                    st.session_state['search_term'] = term
                    st.rerun()

        # Filter and search
        filtered_df = search_nodes(df, search_term, selected_categories, sort_by)

        # Show expanded search terms if searching
        if search_term:
            expanded_terms = expand_search_terms(search_term)
            if len(expanded_terms) > 1:
                with st.expander(f"🧠 Intelligent Search Expansion", expanded=False):
                    st.markdown(f"""
                    <div class='feature-box'>
                        <strong>'{search_term}'</strong> expanded to <strong>{len(expanded_terms)}</strong> related terms:<br>
                        <small>{', '.join(expanded_terms[:15])}{' +' + str(len(expanded_terms)-15) + ' more' if len(expanded_terms) > 15 else ''}</small>
                    </div>
                    """, unsafe_allow_html=True)

        # Results header with count
        st.markdown("---")
        result_col1, result_col2 = st.columns([3, 1])

        with result_col1:
            st.markdown(f"""
            <h3 style='margin: 0;'>
                📋 Results <span style='color: #3b82f6;'>({len(filtered_df):,} nodes)</span>
            </h3>
            """, unsafe_allow_html=True)

        with result_col2:
            if search_term or selected_categories != ['All']:
                if st.button("↻ Show All Nodes", width='stretch'):
                    st.session_state['search_term'] = ''
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

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
                width='stretch',
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
        # AI Header banner
        st.markdown("""
        <div class='ai-header'>
            <h2 style='margin: 0; font-size: 2rem; font-weight: 800;'>
                ✨ AI-Powered Workflow Generator
            </h2>
            <p style='margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.95;'>
                Describe your automation in plain language, and let AI create the workflow
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Check for API key
        api_key = os.getenv('OPENAI_API_KEY', '')

        if not api_key:
            st.markdown("""
            <div class='feature-box' style='border-left-color: #ef4444;'>
                <h4 style='color: #ef4444; margin-top: 0;'>⚠️ API Key Required</h4>
                <p>OpenAI API Key not found. Please add it to your <code>.env</code> file:</p>
                <code style='background: #f1f5f9; padding: 0.5rem; border-radius: 4px; display: block;'>
                    OPENAI_API_KEY=sk-your-key-here
                </code>
            </div>
            """, unsafe_allow_html=True)
            return

        # Load node context for AI
        with st.spinner('🔄 Loading AI context...'):
            nodes_context = load_node_context_for_ai(limit=100)

        # Features info
        col_feat1, col_feat2, col_feat3 = st.columns(3)

        with col_feat1:
            st.markdown("""
            <div class='stats-card' style='text-align: center;'>
                <div style='font-size: 2rem; margin-bottom: 0.5rem;'>🤖</div>
                <div style='font-weight: 600; color: #1e293b;'>GPT-4 Powered</div>
                <div style='color: #64748b; font-size: 0.9rem;'>Advanced AI Generation</div>
            </div>
            """, unsafe_allow_html=True)

        with col_feat2:
            st.markdown(f"""
            <div class='stats-card' style='text-align: center;'>
                <div style='font-size: 2rem; margin-bottom: 0.5rem;'>📚</div>
                <div style='font-weight: 600; color: #1e293b;'>{len(nodes_context)} Nodes</div>
                <div style='color: #64748b; font-size: 0.9rem;'>In AI Context</div>
            </div>
            """, unsafe_allow_html=True)

        with col_feat3:
            st.markdown("""
            <div class='stats-card' style='text-align: center;'>
                <div style='font-size: 2rem; margin-bottom: 0.5rem;'>⚡</div>
                <div style='font-weight: 600; color: #1e293b;'>Instant Export</div>
                <div style='color: #64748b; font-size: 0.9rem;'>Ready for n8n</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Example prompts
        st.markdown("### 💡 Quick Start Templates")
        examples_col1, examples_col2, examples_col3 = st.columns(3)

        with examples_col1:
            if st.button("📧 Email on Webhook", width='stretch', key='ex1'):
                st.session_state['ai_prompt'] = "Create a workflow that receives a webhook and sends an email with the data"
                st.rerun()

        with examples_col2:
            if st.button("🗄️ Database to Spreadsheet", width='stretch', key='ex2'):
                st.session_state['ai_prompt'] = "Get data from PostgreSQL and save it to Google Sheets"
                st.rerun()

        with examples_col3:
            if st.button("🤖 AI Content Generator", width='stretch', key='ex3'):
                st.session_state['ai_prompt'] = "Receive a topic via webhook, use OpenAI to generate content, and post to Slack"
                st.rerun()

        # Prompt input section
        st.markdown("---")
        st.markdown("### ✍️ Describe Your Workflow")
        st.markdown("<small style='color: #94a3b8;'>Explain what you want your workflow to do in plain language. Be as specific or general as you like.</small>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        ai_prompt = st.text_area(
            "Workflow Description",
            value=st.session_state.get('ai_prompt', ''),
            placeholder="Example: Create a workflow that monitors Gmail for new emails with attachments, extracts the attachments, and uploads them to a specific Google Drive folder. Send a Slack notification when complete.",
            height=120,
            key='ai_prompt_input',
            label_visibility="collapsed"
        )

        if 'ai_prompt_input' in st.session_state and st.session_state['ai_prompt_input']:
            st.session_state['ai_prompt'] = st.session_state['ai_prompt_input']

        st.markdown("<br>", unsafe_allow_html=True)

        # Generate button row
        gen_col1, gen_col2 = st.columns([3, 1])

        with gen_col1:
            generate_button = st.button(
                "🚀 Generate Workflow with AI",
                type="primary",
                width='stretch',
                help="Generate an n8n workflow based on your description"
            )

        with gen_col2:
            if st.button("🗑️ Clear All", width='stretch', key='clear_ai', type="secondary"):
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
                    width='stretch'
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

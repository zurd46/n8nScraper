#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-Powered n8n Workflow Generator
Uses OpenAI to generate n8n workflows from natural language descriptions
"""

import streamlit as st
import sqlite3
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="n8n Workflow Generator",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .workflow-preview {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        font-family: monospace;
        font-size: 0.9rem;
        max-height: 500px;
        overflow-y: auto;
    }
    .node-info {
        background-color: #e3f2fd;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_database_connection():
    """Cached database connection"""
    return sqlite3.connect('n8n_docs.db', check_same_thread=False)

def load_node_context(limit=50):
    """
    Load node information for AI context
    Returns top nodes with their operations, parameters, and credentials
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
            'category': category,
            'operations': [],
            'parameters': [],
            'credentials': []
        }

        # Get operations
        cursor.execute('''
            SELECT operation, description
            FROM node_operations
            WHERE node_type = ?
        ''', (node_type,))
        node_info['operations'] = [
            {'operation': op, 'description': desc}
            for op, desc in cursor.fetchall()
        ]

        # Get parameters (for first operation if available)
        cursor.execute('''
            SELECT parameter_name, display_name, parameter_type, required, description
            FROM node_parameters
            WHERE node_type = ?
            LIMIT 10
        ''', (node_type,))
        node_info['parameters'] = [
            {
                'name': param_name,
                'display_name': display_name,
                'type': param_type,
                'required': bool(required),
                'description': desc
            }
            for param_name, display_name, param_type, required, desc in cursor.fetchall()
        ]

        # Get credentials
        cursor.execute('''
            SELECT credential_type, display_name
            FROM node_credentials
            WHERE node_type = ?
        ''', (node_type,))
        node_info['credentials'] = [
            {'type': cred_type, 'display_name': display_name}
            for cred_type, display_name in cursor.fetchall()
        ]

        nodes_data.append(node_info)

    return nodes_data

def generate_workflow_with_openai(prompt, api_key, nodes_context):
    """
    Generate n8n workflow using OpenAI API
    """
    try:
        import openai

        # Set API key
        openai.api_key = api_key

        # Build system message with node context
        system_message = f"""You are an expert n8n workflow automation engineer.
You help users create n8n workflows in JSON format.

Available n8n nodes (selection):
{json.dumps(nodes_context[:20], indent=2)}

IMPORTANT RULES:
1. Return ONLY valid n8n workflow JSON
2. Use exact node types from the list above
3. Include proper node connections
4. Set realistic parameters
5. Use expressions like {{{{ $json.fieldname }}}} for dynamic values
6. Follow n8n workflow schema exactly

Example workflow structure:
{{
  "name": "Workflow Name",
  "nodes": [
    {{
      "parameters": {{}},
      "name": "Node Name",
      "type": "n8n-nodes-base.nodetype",
      "typeVersion": 1,
      "position": [250, 300]
    }}
  ],
  "connections": {{
    "Node Name": {{
      "main": [[{{"node": "Next Node", "type": "main", "index": 0}}]]
    }}
  }}
}}

Return ONLY the JSON, no explanations."""

        # Call OpenAI API
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
            workflow_json = workflow_json.split('```')[1]
            if workflow_json.startswith('json'):
                workflow_json = workflow_json[4:]
            workflow_json = workflow_json.strip()

        # Parse to validate
        workflow = json.loads(workflow_json)

        return workflow, None

    except ImportError:
        return None, "OpenAI package not installed. Run: pip install openai"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON generated: {e}\n\nResponse: {workflow_json}"
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

def export_workflow(workflow, filename):
    """
    Export workflow as JSON file
    """
    workflow_json = json.dumps(workflow, indent=2, ensure_ascii=False)
    return workflow_json

def main():
    st.title("🤖 AI n8n Workflow Generator")
    st.markdown("Generate n8n workflows from natural language using OpenAI")

    # Sidebar - Configuration
    st.sidebar.header("⚙️ Configuration")

    # OpenAI API Key - Load from env or manual input
    default_api_key = os.getenv('OPENAI_API_KEY', '')

    api_key = st.sidebar.text_input(
        "OpenAI API Key",
        value=default_api_key,
        type="password",
        help="Enter your OpenAI API key (starts with sk-...) or set OPENAI_API_KEY in .env file"
    )

    if default_api_key:
        st.sidebar.success("✅ API Key loaded from .env")

    # Model selection
    model = st.sidebar.selectbox(
        "Model",
        ["gpt-4", "gpt-3.5-turbo"],
        help="GPT-4 recommended for better workflow quality"
    )

    # Load node context
    with st.spinner('Loading node database...'):
        nodes_context = load_node_context(limit=100)

    st.sidebar.success(f"Loaded {len(nodes_context)} nodes")

    # Show available nodes
    with st.sidebar.expander("📚 Available Nodes (sample)"):
        for node in nodes_context[:10]:
            st.markdown(f"**{node['display_name']}** - {node['node_type']}")

    # Main content
    st.markdown("---")

    # Example prompts
    st.markdown("### 💡 Example Prompts")
    examples_col1, examples_col2, examples_col3 = st.columns(3)

    with examples_col1:
        if st.button("📧 Email on Webhook", use_container_width=True):
            st.session_state['prompt'] = "Create a workflow that receives a webhook and sends an email with the data"

    with examples_col2:
        if st.button("🗄️ Database to Spreadsheet", use_container_width=True):
            st.session_state['prompt'] = "Get data from PostgreSQL and save it to Google Sheets"

    with examples_col3:
        if st.button("🤖 AI Content Generator", use_container_width=True):
            st.session_state['prompt'] = "Receive a topic via webhook, use OpenAI to generate content, and post to Slack"

    # Prompt input
    st.markdown("### ✍️ Describe Your Workflow")
    prompt = st.text_area(
        "What should the workflow do?",
        value=st.session_state.get('prompt', ''),
        placeholder="Example: Create a workflow that monitors Gmail for new emails, extracts attachments, and uploads them to Google Drive",
        height=100,
        key='prompt_input'
    )

    if 'prompt_input' in st.session_state and st.session_state['prompt_input']:
        st.session_state['prompt'] = st.session_state['prompt_input']

    # Generate button
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        generate_button = st.button("🚀 Generate Workflow", type="primary", use_container_width=True)

    with col2:
        clear_button = st.button("🗑️ Clear", use_container_width=True)
        if clear_button:
            st.session_state['prompt'] = ''
            st.session_state['workflow'] = None
            st.rerun()

    # Generate workflow
    if generate_button:
        if not api_key:
            st.error("⚠️ Please enter your OpenAI API key in the sidebar")
        elif not prompt:
            st.error("⚠️ Please describe what the workflow should do")
        else:
            with st.spinner('🤖 Generating workflow with AI...'):
                workflow, error = generate_workflow_with_openai(prompt, api_key, nodes_context)

                if error:
                    st.markdown(f'<div class="error-box">❌ {error}</div>', unsafe_allow_html=True)
                else:
                    st.session_state['workflow'] = workflow
                    st.success("✅ Workflow generated successfully!")

    # Display workflow
    if 'workflow' in st.session_state and st.session_state['workflow']:
        workflow = st.session_state['workflow']

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
        tab1, tab2, tab3 = st.tabs(["📊 Visual Overview", "📝 JSON", "⬇️ Export"])

        with tab1:
            st.markdown("#### Nodes in Workflow")
            for i, node in enumerate(workflow.get('nodes', []), 1):
                with st.expander(f"{i}. {node.get('name', 'Unnamed')} ({node.get('type', 'unknown')})"):
                    st.json(node)

            st.markdown("#### Connections")
            if workflow.get('connections'):
                st.json(workflow['connections'])
            else:
                st.info("No connections defined")

        with tab2:
            st.markdown("#### Complete Workflow JSON")
            workflow_json = json.dumps(workflow, indent=2, ensure_ascii=False)
            st.code(workflow_json, language='json')

        with tab3:
            st.markdown("#### Export Workflow")

            # Filename input
            filename = st.text_input(
                "Filename",
                value=workflow.get('name', 'workflow').replace(' ', '_') + '.json'
            )

            # Export button
            workflow_json = export_workflow(workflow, filename)

            st.download_button(
                label="📥 Download as JSON",
                data=workflow_json,
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

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        🤖 Powered by OpenAI |
        💾 Database: n8n_docs.db |
        🔧 Generated with Claude Code
    </div>
    """, unsafe_allow_html=True)

if __name__ == '__main__':
    main()

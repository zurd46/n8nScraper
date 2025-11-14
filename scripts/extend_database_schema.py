#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extend database schema for AI workflow generation
Adds tables for: operations, parameters, credentials, io_schema, examples
"""

import sqlite3
from datetime import datetime

def extend_database_schema(db_path='../n8n_docs.db'):
    """
    Add new tables to existing database for AI workflow generation
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Extending database schema for AI workflow generation...")
    print("=" * 60)

    # 1. Node Operations (what can each node do?)
    print("\n[1/5] Creating table: node_operations")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS node_operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_type TEXT NOT NULL,
            resource TEXT,
            operation TEXT NOT NULL,
            description TEXT,
            display_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(node_type, resource, operation)
        )
    ''')
    print("  [OK] node_operations table created")

    # 2. Node Parameters (fields for each operation)
    print("\n[2/5] Creating table: node_parameters")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS node_parameters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_type TEXT NOT NULL,
            resource TEXT,
            operation TEXT,
            parameter_name TEXT NOT NULL,
            display_name TEXT,
            parameter_type TEXT,
            required BOOLEAN DEFAULT 0,
            default_value TEXT,
            description TEXT,
            placeholder TEXT,
            options TEXT,
            min_value REAL,
            max_value REAL,
            display_options TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(node_type, resource, operation, parameter_name)
        )
    ''')
    print("  [OK] node_parameters table created")

    # Add index for faster queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_node_parameters_lookup
        ON node_parameters(node_type, resource, operation)
    ''')

    # 3. Node Credentials
    print("\n[3/5] Creating table: node_credentials")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS node_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_type TEXT NOT NULL,
            credential_type TEXT NOT NULL,
            credential_name TEXT,
            required BOOLEAN DEFAULT 1,
            display_name TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(node_type, credential_type)
        )
    ''')
    print("  [OK] node_credentials table created")

    # 4. Node Input/Output Schema
    print("\n[4/5] Creating table: node_io_schema")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS node_io_schema (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_type TEXT NOT NULL,
            resource TEXT,
            operation TEXT,
            input_schema TEXT,
            output_schema TEXT,
            output_fields TEXT,
            example_input TEXT,
            example_output TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(node_type, resource, operation)
        )
    ''')
    print("  [OK] node_io_schema table created")

    # 5. Example Workflows
    print("\n[5/5] Creating table: example_workflows")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS example_workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            use_case TEXT,
            workflow_json TEXT NOT NULL,
            node_types_used TEXT,
            tags TEXT,
            complexity TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("  [OK] example_workflows table created")

    # Commit before creating indexes
    conn.commit()

    # Add index for workflow search
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_workflows_tags
        ON example_workflows(tags)
    ''')

    # 6. Create view for easy AI context retrieval
    print("\n[BONUS] Creating view: ai_node_context")
    cursor.execute('''
        CREATE VIEW IF NOT EXISTS ai_node_context AS
        SELECT
            n.node_type,
            n.display_name,
            n.description,
            n.category,
            GROUP_CONCAT(DISTINCT o.operation) as operations,
            GROUP_CONCAT(DISTINCT c.credential_type) as credentials,
            COUNT(DISTINCT p.parameter_name) as parameter_count
        FROM node_types_api n
        LEFT JOIN node_operations o ON n.node_type = o.node_type
        LEFT JOIN node_credentials c ON n.node_type = c.node_type
        LEFT JOIN node_parameters p ON n.node_type = p.node_type
        GROUP BY n.node_type
    ''')
    print("  [OK] ai_node_context view created")

    conn.commit()

    # Show table stats
    print("\n" + "=" * 60)
    print("Database Schema Extended Successfully!")
    print("=" * 60)

    print("\nNew Tables:")
    tables = [
        'node_operations',
        'node_parameters',
        'node_credentials',
        'node_io_schema',
        'example_workflows'
    ]

    for table in tables:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f"  - {table}: {count} rows")

    # Show existing node count
    cursor.execute('SELECT COUNT(*) FROM node_types_api')
    api_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM community_nodes')
    community_count = cursor.fetchone()[0]

    print(f"\nExisting Data:")
    print(f"  - Official nodes: {api_count}")
    print(f"  - Community nodes: {community_count}")
    print(f"  - Total: {api_count + community_count}")

    conn.close()

    print("\n" + "=" * 60)
    print("Next Steps:")
    print("  1. Run node parameter extractor to populate new tables")
    print("  2. Use scripts/extract_node_details.py to parse n8n repo")
    print("  3. Export AI context with scripts/export_for_ai.py")
    print("=" * 60)

def add_sample_data(db_path='../n8n_docs.db'):
    """
    Add sample data to demonstrate the schema
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\nAdding sample data...")

    # Sample: Gmail operations
    cursor.execute('''
        INSERT OR REPLACE INTO node_operations
        (node_type, resource, operation, description, display_name)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        'n8n-nodes-base.gmail',
        'message',
        'send',
        'Send an email',
        'Send Email'
    ))

    cursor.execute('''
        INSERT OR REPLACE INTO node_operations
        (node_type, resource, operation, description, display_name)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        'n8n-nodes-base.gmail',
        'message',
        'get',
        'Get a specific email',
        'Get Email'
    ))

    # Sample: Gmail parameters for 'send' operation
    params = [
        ('to', 'To', 'string', 1, None, 'Email recipients (comma-separated)', 'recipient@example.com'),
        ('subject', 'Subject', 'string', 1, None, 'Email subject line', 'My Subject'),
        ('message', 'Message', 'string', 1, None, 'Email body content (HTML or text)', 'Hello World'),
        ('attachments', 'Attachments', 'string', 0, None, 'Binary property containing attachments', 'data'),
        ('bcc', 'BCC', 'string', 0, None, 'Blind carbon copy recipients', None),
        ('cc', 'CC', 'string', 0, None, 'Carbon copy recipients', None),
    ]

    for param in params:
        cursor.execute('''
            INSERT OR REPLACE INTO node_parameters
            (node_type, resource, operation, parameter_name, display_name,
             parameter_type, required, default_value, description, placeholder)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('n8n-nodes-base.gmail', 'message', 'send') + param)

    # Sample: Gmail credentials
    cursor.execute('''
        INSERT OR REPLACE INTO node_credentials
        (node_type, credential_type, credential_name, required, display_name, description)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        'n8n-nodes-base.gmail',
        'gmailOAuth2',
        'gmail',
        1,
        'Gmail OAuth2 API',
        'OAuth2 credentials for Gmail API access'
    ))

    # Sample: HTTP Request node
    cursor.execute('''
        INSERT OR REPLACE INTO node_operations
        (node_type, resource, operation, description, display_name)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        'n8n-nodes-base.httpRequest',
        None,
        'request',
        'Make an HTTP request',
        'HTTP Request'
    ))

    # HTTP Request parameters
    http_params = [
        ('method', 'Method', 'options', 1, 'GET', 'HTTP method to use', None, '["GET","POST","PUT","DELETE","PATCH","HEAD","OPTIONS"]'),
        ('url', 'URL', 'string', 1, None, 'The URL to make the request to', 'https://api.example.com/endpoint', None),
        ('authentication', 'Authentication', 'options', 0, 'none', 'Authentication method', None, '["none","basicAuth","oAuth2","headerAuth"]'),
        ('sendBody', 'Send Body', 'boolean', 0, 'false', 'Whether to send a body with the request', None, None),
        ('bodyContentType', 'Body Content Type', 'options', 0, 'json', 'Format of the body', None, '["json","form-urlencoded","raw"]'),
        ('jsonParameters', 'JSON Parameters', 'boolean', 0, 'false', 'Add parameters as JSON', None, None),
        ('sendHeaders', 'Send Headers', 'boolean', 0, 'false', 'Add custom headers', None, None),
    ]

    for param in http_params:
        param_name, display_name, param_type, required, default, desc, placeholder, options = param
        cursor.execute('''
            INSERT OR REPLACE INTO node_parameters
            (node_type, resource, operation, parameter_name, display_name,
             parameter_type, required, default_value, description, placeholder, options)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('n8n-nodes-base.httpRequest', None, 'request', param_name, display_name,
              param_type, required, default, desc, placeholder, options))

    # Sample: Input/Output schema for HTTP Request
    cursor.execute('''
        INSERT OR REPLACE INTO node_io_schema
        (node_type, resource, operation, output_schema, output_fields)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        'n8n-nodes-base.httpRequest',
        None,
        'request',
        '{"body": "any", "headers": "object", "statusCode": "number", "statusMessage": "string"}',
        '["body", "headers", "statusCode", "statusMessage"]'
    ))

    # Sample: Example workflow
    example_workflow = {
        "nodes": [
            {
                "parameters": {
                    "path": "webhook-test",
                    "responseMode": "onReceived",
                    "options": {}
                },
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300]
            },
            {
                "parameters": {
                    "resource": "message",
                    "operation": "send",
                    "to": "={{ $json.email }}",
                    "subject": "New webhook received",
                    "message": "=Webhook data: {{ $json }}"
                },
                "name": "Gmail",
                "type": "n8n-nodes-base.gmail",
                "typeVersion": 2,
                "position": [450, 300],
                "credentials": {
                    "gmailOAuth2": {
                        "id": "1",
                        "name": "Gmail account"
                    }
                }
            }
        ],
        "connections": {
            "Webhook": {
                "main": [[{"node": "Gmail", "type": "main", "index": 0}]]
            }
        }
    }

    import json
    cursor.execute('''
        INSERT OR REPLACE INTO example_workflows
        (title, description, use_case, workflow_json, node_types_used, tags, complexity)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Webhook to Email',
        'Receive webhook data and send it via email',
        'notification, webhook, email',
        json.dumps(example_workflow, indent=2),
        'n8n-nodes-base.webhook,n8n-nodes-base.gmail',
        'webhook,email,notification,gmail',
        'beginner'
    ))

    conn.commit()
    conn.close()

    print("  [OK] Sample data added for Gmail and HTTP Request nodes")
    print("  [OK] Example workflow added")

def show_sample_query(db_path='../n8n_docs.db'):
    """
    Demonstrate how to query the new schema
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("Sample Query - Get all info for Gmail node:")
    print("=" * 60)

    # Get operations
    cursor.execute('''
        SELECT operation, description
        FROM node_operations
        WHERE node_type = 'n8n-nodes-base.gmail'
    ''')
    operations = cursor.fetchall()

    print("\nOperations:")
    for op, desc in operations:
        print(f"  - {op}: {desc}")

    # Get parameters for 'send' operation
    cursor.execute('''
        SELECT parameter_name, display_name, parameter_type, required, description
        FROM node_parameters
        WHERE node_type = 'n8n-nodes-base.gmail'
        AND operation = 'send'
        ORDER BY required DESC
    ''')
    params = cursor.fetchall()

    print("\nParameters for 'send' operation:")
    for param_name, display_name, param_type, required, desc in params:
        req_text = "[REQUIRED]" if required else "[optional]"
        print(f"  {req_text} {param_name} ({param_type}): {desc}")

    # Get credentials
    cursor.execute('''
        SELECT credential_type, display_name, description
        FROM node_credentials
        WHERE node_type = 'n8n-nodes-base.gmail'
    ''')
    creds = cursor.fetchall()

    print("\nCredentials:")
    for cred_type, display_name, desc in creds:
        print(f"  - {display_name} ({cred_type})")

    conn.close()

if __name__ == '__main__':
    # Extend schema
    extend_database_schema('../n8n_docs.db')

    # Add sample data
    add_sample_data('../n8n_docs.db')

    # Show example query
    show_sample_query('../n8n_docs.db')

    print("\n" + "=" * 60)
    print("Schema extension complete!")
    print("Database ready for AI workflow generation")
    print("=" * 60)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract detailed node information (parameters, operations, credentials)
This is needed to build AI-powered workflow generators
"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime

class NodeDetailsExtractor:
    def __init__(self, n8n_repo_path=None):
        """
        Initialize extractor

        Args:
            n8n_repo_path: Path to cloned n8n repository
                          If None, will use GitHub API (limited)
        """
        self.n8n_repo_path = n8n_repo_path
        self.conn = sqlite3.connect('../n8n_docs.db')
        self.create_tables()

    def create_tables(self):
        """Create tables for detailed node information"""
        cursor = self.conn.cursor()

        # Node operations (what the node can do)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS node_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_type TEXT NOT NULL,
                resource TEXT,
                operation TEXT NOT NULL,
                description TEXT,
                UNIQUE(node_type, resource, operation)
            )
        ''')

        # Node parameters (fields for each operation)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS node_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_type TEXT NOT NULL,
                resource TEXT,
                operation TEXT,
                parameter_name TEXT NOT NULL,
                parameter_type TEXT,
                required BOOLEAN,
                default_value TEXT,
                description TEXT,
                options TEXT,  -- JSON array of possible values
                UNIQUE(node_type, resource, operation, parameter_name)
            )
        ''')

        # Node credentials
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS node_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_type TEXT NOT NULL,
                credential_type TEXT NOT NULL,
                required BOOLEAN,
                UNIQUE(node_type, credential_type)
            )
        ''')

        # Example workflows
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS example_workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_type TEXT NOT NULL,
                workflow_json TEXT NOT NULL,
                description TEXT,
                use_case TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Node input/output schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS node_io_schema (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_type TEXT NOT NULL,
                resource TEXT,
                operation TEXT,
                input_schema TEXT,  -- JSON schema
                output_schema TEXT,  -- JSON schema
                output_fields TEXT,  -- JSON array of available fields
                UNIQUE(node_type, resource, operation)
            )
        ''')

        self.conn.commit()

    def extract_from_local_repo(self):
        """
        Extract node details from local n8n repository clone

        To use this:
        1. Clone n8n repo: git clone https://github.com/n8n-io/n8n.git
        2. Run: python extract_node_details.py --repo-path /path/to/n8n
        """
        if not self.n8n_repo_path:
            print("❌ No repository path provided")
            return

        nodes_path = Path(self.n8n_repo_path) / "packages" / "nodes-base" / "nodes"

        if not nodes_path.exists():
            print(f"❌ Nodes path not found: {nodes_path}")
            return

        print(f"🔍 Scanning nodes in {nodes_path}")

        # Find all .node.ts files
        node_files = list(nodes_path.glob("**/*.node.ts"))
        print(f"📄 Found {len(node_files)} node files")

        for node_file in node_files:
            self.extract_node_file(node_file)

    def extract_node_file(self, file_path):
        """Extract details from a single node file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract node class name
            # Look for: export class NodeName implements INodeType
            import re

            # Find node properties
            properties_match = re.search(r'properties:\s*INodeProperties\[\]\s*=\s*\[(.*?)\];', content, re.DOTALL)
            if properties_match:
                properties_str = properties_match.group(1)
                # This would need proper TypeScript parsing
                # For now, we'll use a simpler approach
                print(f"✓ Found properties in {file_path.name}")

            # Find credentials
            credentials_match = re.search(r'credentials:\s*ICredentialDataDecryptedObject\[\]\s*=\s*\[(.*?)\];', content, re.DOTALL)
            if credentials_match:
                print(f"✓ Found credentials in {file_path.name}")

        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")

    def extract_from_api_docs(self):
        """
        Alternative: Extract from n8n API documentation
        """
        print("📚 Extracting from n8n documentation...")
        print("⚠️  This is limited - better to use local repo or GitHub API")

        # Could scrape https://docs.n8n.io/integrations/builtin/app-nodes/
        # But node parameters are not always fully documented

    def generate_example_data(self):
        """
        Generate example data for common nodes
        This helps the AI understand typical patterns
        """
        cursor = self.conn.cursor()

        # Gmail example
        cursor.execute('''
            INSERT OR REPLACE INTO node_operations
            (node_type, resource, operation, description)
            VALUES (?, ?, ?, ?)
        ''', ('n8n-nodes-base.gmail', 'message', 'send', 'Send an email'))

        cursor.execute('''
            INSERT OR REPLACE INTO node_parameters
            (node_type, resource, operation, parameter_name, parameter_type, required, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('n8n-nodes-base.gmail', 'message', 'send', 'to', 'string', True, 'Email recipients'))

        cursor.execute('''
            INSERT OR REPLACE INTO node_parameters
            (node_type, resource, operation, parameter_name, parameter_type, required, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('n8n-nodes-base.gmail', 'message', 'send', 'subject', 'string', True, 'Email subject'))

        cursor.execute('''
            INSERT OR REPLACE INTO node_credentials
            (node_type, credential_type, required)
            VALUES (?, ?, ?)
        ''', ('n8n-nodes-base.gmail', 'gmailOAuth2', True))

        # HTTP Request example
        cursor.execute('''
            INSERT OR REPLACE INTO node_operations
            (node_type, resource, operation, description)
            VALUES (?, ?, ?, ?)
        ''', ('n8n-nodes-base.httpRequest', None, 'request', 'Make HTTP request'))

        cursor.execute('''
            INSERT OR REPLACE INTO node_parameters
            (node_type, resource, operation, parameter_name, parameter_type, required, description, options)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('n8n-nodes-base.httpRequest', None, 'request', 'method', 'options', True,
              'HTTP method', json.dumps(['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])))

        cursor.execute('''
            INSERT OR REPLACE INTO node_parameters
            (node_type, resource, operation, parameter_name, parameter_type, required, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('n8n-nodes-base.httpRequest', None, 'request', 'url', 'string', True, 'Request URL'))

        self.conn.commit()
        print("[OK] Generated example data for common nodes")

    def export_for_ai(self, output_file='node_details_for_ai.json'):
        """
        Export all node details in AI-friendly format
        """
        cursor = self.conn.cursor()

        # Get all nodes
        cursor.execute('SELECT DISTINCT node_type FROM node_types_api')
        nodes = cursor.fetchall()

        ai_data = []

        for (node_type,) in nodes[:10]:  # Limit to 10 for testing
            node_data = {
                'node_type': node_type,
                'operations': [],
                'credentials': [],
                'examples': []
            }

            # Get operations
            cursor.execute('''
                SELECT resource, operation, description
                FROM node_operations
                WHERE node_type = ?
            ''', (node_type,))

            for resource, operation, description in cursor.fetchall():
                op_data = {
                    'resource': resource,
                    'operation': operation,
                    'description': description,
                    'parameters': []
                }

                # Get parameters for this operation
                cursor.execute('''
                    SELECT parameter_name, parameter_type, required, description, options
                    FROM node_parameters
                    WHERE node_type = ? AND resource = ? AND operation = ?
                ''', (node_type, resource, operation))

                for param_name, param_type, required, desc, options in cursor.fetchall():
                    op_data['parameters'].append({
                        'name': param_name,
                        'type': param_type,
                        'required': bool(required),
                        'description': desc,
                        'options': json.loads(options) if options else None
                    })

                node_data['operations'].append(op_data)

            # Get credentials
            cursor.execute('''
                SELECT credential_type, required
                FROM node_credentials
                WHERE node_type = ?
            ''', (node_type,))

            for cred_type, required in cursor.fetchall():
                node_data['credentials'].append({
                    'type': cred_type,
                    'required': bool(required)
                })

            ai_data.append(node_data)

        # Export to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(ai_data, f, indent=2, ensure_ascii=False)

        print(f"[OK] Exported {len(ai_data)} nodes to {output_file}")
        print(f"[INFO] This file can be used as context for AI workflow generation")

def main():
    print("Node Details Extractor")
    print("=" * 60)

    extractor = NodeDetailsExtractor()

    # Generate example data for demonstration
    print("\nGenerating example data...")
    extractor.generate_example_data()

    # Export for AI
    print("\nExporting for AI...")
    extractor.export_for_ai('../output/node_details_for_ai.json')

    print("\n" + "=" * 60)
    print("Done!")
    print("\nTo get full node details:")
    print("   1. Clone n8n repo: git clone https://github.com/n8n-io/n8n.git")
    print("   2. Run with --repo-path flag")
    print("\nCurrent database has basic info - enough for simple workflows")
    print("For complex workflows, we need parameter details")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scrape n8n node documentation using Jina AI Reader
Extract parameters, operations, credentials for AI workflow generation
"""

import requests
import sqlite3
import json
import re
import time
from datetime import datetime

class JinaNodeDocsScraper:
    def __init__(self, db_path='../n8n_docs.db'):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.jina_reader_base = "https://r.jina.ai/"

    def get_nodes_to_scrape(self, limit=None):
        """Get list of nodes that need documentation"""
        query = '''
            SELECT node_type, display_name, category
            FROM node_types_api
            WHERE category IN ('App', 'Trigger', 'Core')
            ORDER BY display_name
        '''

        if limit:
            query += f' LIMIT {limit}'

        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_doc_url(self, node_type, display_name):
        """
        Generate docs URL for a node
        n8n docs pattern: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.{nodename}/
        """
        # Extract node name from node_type
        # e.g. n8n-nodes-base.gmail -> gmail
        if '.' in node_type:
            node_name = node_type.split('.')[-1].lower()
        else:
            node_name = display_name.lower().replace(' ', '-')

        # Build URL
        base_url = "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base"
        doc_url = f"{base_url}.{node_name}/"

        return doc_url

    def scrape_with_jina(self, url):
        """
        Scrape URL using Jina AI Reader
        Returns markdown content
        """
        try:
            jina_url = f"{self.jina_reader_base}{url}"

            print(f"  Fetching: {jina_url}")
            response = requests.get(jina_url, timeout=30)

            if response.status_code == 200:
                return response.text
            else:
                print(f"  [WARN] Status {response.status_code}")
                return None

        except Exception as e:
            print(f"  [ERROR] {e}")
            return None

    def extract_operations_from_markdown(self, markdown_content, node_type):
        """
        Extract operations from markdown documentation
        Look for sections like "## Operations", "### Send", etc.
        """
        operations = []

        # Pattern for operation sections
        # Example: ### Send an email
        operation_pattern = r'###\s+([A-Z][a-z]+.*?)(?:\n|$)'

        matches = re.findall(operation_pattern, markdown_content)

        for match in matches:
            operation_name = match.strip()
            # Clean up operation name
            operation_name = operation_name.replace('*', '').strip()

            operations.append({
                'operation': operation_name.lower().replace(' ', '_'),
                'display_name': operation_name,
                'description': operation_name
            })

        return operations

    def extract_parameters_from_markdown(self, markdown_content):
        """
        Extract parameters from markdown documentation
        Look for parameter descriptions
        """
        parameters = []

        # Pattern for parameter descriptions
        # Example: **To** - Email recipients
        param_pattern = r'\*\*([A-Za-z\s]+)\*\*\s*[-:]\s*(.*?)(?:\n|$)'

        matches = re.findall(param_pattern, markdown_content, re.MULTILINE)

        for param_name, description in matches:
            param_name = param_name.strip()
            description = description.strip()

            # Skip section headers
            if len(param_name) > 30:
                continue

            # Determine if required (heuristic)
            required = 'required' in description.lower() or 'must' in description.lower()

            parameters.append({
                'parameter_name': param_name.lower().replace(' ', '_'),
                'display_name': param_name,
                'description': description,
                'required': required,
                'parameter_type': 'string'  # Default, would need better detection
            })

        return parameters

    def extract_credentials_from_markdown(self, markdown_content, node_type, display_name):
        """
        Extract credentials information
        Look for OAuth, API Key, authentication mentions
        """
        credentials = []

        # Check for OAuth
        if 'oauth' in markdown_content.lower() or 'oauth2' in markdown_content.lower():
            cred_name = f"{display_name.lower().replace(' ', '')}OAuth2"
            credentials.append({
                'credential_type': cred_name,
                'credential_name': display_name.lower(),
                'display_name': f"{display_name} OAuth2",
                'required': True
            })

        # Check for API Key
        elif 'api key' in markdown_content.lower() or 'apikey' in markdown_content.lower():
            cred_name = f"{display_name.lower().replace(' ', '')}Api"
            credentials.append({
                'credential_type': cred_name,
                'credential_name': display_name.lower(),
                'display_name': f"{display_name} API",
                'required': True
            })

        return credentials

    def save_operations(self, node_type, operations):
        """Save operations to database"""
        for op in operations:
            try:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO node_operations
                    (node_type, resource, operation, description, display_name)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    node_type,
                    None,  # Resource detection would need more sophisticated parsing
                    op['operation'],
                    op['description'],
                    op['display_name']
                ))
            except Exception as e:
                print(f"    [ERROR] Saving operation: {e}")

        self.conn.commit()

    def save_parameters(self, node_type, operation, parameters):
        """Save parameters to database"""
        for param in parameters:
            try:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO node_parameters
                    (node_type, resource, operation, parameter_name, display_name,
                     parameter_type, required, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    node_type,
                    None,
                    operation,
                    param['parameter_name'],
                    param['display_name'],
                    param['parameter_type'],
                    param['required'],
                    param['description']
                ))
            except Exception as e:
                print(f"    [ERROR] Saving parameter: {e}")

        self.conn.commit()

    def save_credentials(self, node_type, credentials):
        """Save credentials to database"""
        for cred in credentials:
            try:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO node_credentials
                    (node_type, credential_type, credential_name, required, display_name)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    node_type,
                    cred['credential_type'],
                    cred['credential_name'],
                    cred['required'],
                    cred['display_name']
                ))
            except Exception as e:
                print(f"    [ERROR] Saving credential: {e}")

        self.conn.commit()

    def scrape_node(self, node_type, display_name, category):
        """Scrape documentation for a single node"""
        print(f"\n[{display_name}] ({node_type})")

        # Get documentation URL
        doc_url = self.get_doc_url(node_type, display_name)
        print(f"  URL: {doc_url}")

        # Scrape with Jina AI
        markdown_content = self.scrape_with_jina(doc_url)

        if not markdown_content:
            print(f"  [SKIP] No content retrieved")
            return False

        # Extract data
        operations = self.extract_operations_from_markdown(markdown_content, node_type)
        print(f"  Operations found: {len(operations)}")

        parameters = self.extract_parameters_from_markdown(markdown_content)
        print(f"  Parameters found: {len(parameters)}")

        credentials = self.extract_credentials_from_markdown(markdown_content, node_type, display_name)
        print(f"  Credentials found: {len(credentials)}")

        # Save to database
        if operations:
            self.save_operations(node_type, operations)

            # Save parameters for first operation (would need better operation detection)
            if parameters and operations:
                self.save_parameters(node_type, operations[0]['operation'], parameters)

        if credentials:
            self.save_credentials(node_type, credentials)

        print(f"  [OK] Data saved")
        return True

    def scrape_all(self, limit=10, delay=2):
        """
        Scrape documentation for all nodes

        Args:
            limit: Maximum number of nodes to scrape (None for all)
            delay: Delay between requests in seconds
        """
        nodes = self.get_nodes_to_scrape(limit)

        print("=" * 60)
        print(f"Scraping {len(nodes)} nodes with Jina AI")
        print("=" * 60)

        success_count = 0
        fail_count = 0

        for i, (node_type, display_name, category) in enumerate(nodes, 1):
            print(f"\n[{i}/{len(nodes)}]", end=" ")

            try:
                success = self.scrape_node(node_type, display_name, category)
                if success:
                    success_count += 1
                else:
                    fail_count += 1

            except Exception as e:
                print(f"  [ERROR] {e}")
                fail_count += 1

            # Rate limiting
            if i < len(nodes):
                time.sleep(delay)

        print("\n" + "=" * 60)
        print(f"Scraping complete!")
        print(f"  Success: {success_count}")
        print(f"  Failed: {fail_count}")
        print("=" * 60)

    def close(self):
        """Close database connection"""
        self.conn.close()

def main():
    print("n8n Node Documentation Scraper (Jina AI)")
    print("=" * 60)

    scraper = JinaNodeDocsScraper('../n8n_docs.db')

    # Scrape ALL nodes
    print("\nScraping ALL nodes from database...")
    print("This will take approximately 15-20 minutes\n")

    scraper.scrape_all(limit=None, delay=2)

    scraper.close()

    print("\n" + "=" * 60)
    print("Done! Check database for extracted data:")
    print("  - node_operations")
    print("  - node_parameters")
    print("  - node_credentials")
    print("=" * 60)

if __name__ == '__main__':
    main()

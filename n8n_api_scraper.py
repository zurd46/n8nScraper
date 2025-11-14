#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
n8n API Node-Type Scraper
Holt die exakten technischen Node-Namen direkt aus der n8n API
"""

import sys
import io
import requests

# Fix für Windows Console Encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import json
import sqlite3
from datetime import datetime

class N8nApiScraper:
    def __init__(self, api_url, api_key, db_name='n8n_docs.db'):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.db_name = db_name
        self.conn = None
        self.setup_database()

    def setup_database(self):
        """Verbindet mit der bestehenden Datenbank"""
        self.conn = sqlite3.connect(self.db_name)
        cursor = self.conn.cursor()

        # Tabelle für exakte Node-Types aus der n8n API
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS node_types_api (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_type TEXT UNIQUE NOT NULL,
                display_name TEXT,
                description TEXT,
                version INTEGER,
                icon TEXT,
                category TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()
        print(f"✓ Datenbank '{self.db_name}' verbunden")

    def get_node_types(self):
        """Holt alle Node-Types von der n8n API"""
        # Versuche verschiedene mögliche Endpoints
        endpoints = [
            '/api/v1/workflows',  # Um alle Workflows zu holen
            '/rest/workflows',     # Alternative
            '/types/nodes.json',   # Node types
        ]

        headers = {
            'X-N8N-API-KEY': self.api_key,
            'Accept': 'application/json'
        }

        # Teste jeden Endpoint
        for endpoint in endpoints:
            url = f"{self.api_url}{endpoint}"
            print(f"  Versuche: {url}")

            try:
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code == 200:
                    print(f"  ✓ Erfolg mit: {endpoint}")
                    return response.json()
                else:
                    print(f"  ✗ Status {response.status_code}: {endpoint}")
            except Exception as e:
                print(f"  ✗ Fehler: {e}")

        return None

    def get_node_types_from_workflows(self):
        """Extrahiert Node-Types aus existierenden Workflows"""
        url = f"{self.api_url}/api/v1/workflows"

        headers = {
            'X-N8N-API-KEY': self.api_key,
            'Accept': 'application/json'
        }

        try:
            print(f"📥 Fetching node types from: {url}")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            print(f"❌ API Fehler: {e}")
            return None

    def save_node_type(self, node_data):
        """Speichert einen Node-Type in der Datenbank"""
        cursor = self.conn.cursor()

        try:
            # Extrahiere relevante Felder
            node_type = node_data.get('node_type') or node_data.get('name')
            display_name = node_data.get('display_name') or node_data.get('displayName', node_type)
            description = node_data.get('description', '')
            version = node_data.get('version', 1)
            icon = node_data.get('icon', '')

            # Überprüfe ob node_type vorhanden ist
            if not node_type:
                return False

            # Kategorie aus codex extrahieren falls vorhanden
            category = node_data.get('category')
            if not category and 'codex' in node_data and 'categories' in node_data['codex']:
                categories = node_data['codex']['categories']
                if categories:
                    category = ', '.join(categories)

            cursor.execute('''
                INSERT OR REPLACE INTO node_types_api
                (node_type, display_name, description, version, icon, category, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                node_type,
                display_name,
                description,
                version,
                icon,
                category,
                datetime.now()
            ))

            self.conn.commit()
            return True

        except sqlite3.Error as e:
            print(f"  ❌ Datenbankfehler: {e}")
            return False

    def extract_node_types_from_workflows(self, workflows_data):
        """Extrahiert einzigartige Node-Types aus Workflows"""
        node_types_set = set()

        if 'data' in workflows_data:
            workflows = workflows_data['data']
        else:
            workflows = workflows_data if isinstance(workflows_data, list) else []

        for workflow in workflows:
            if 'nodes' in workflow:
                for node in workflow['nodes']:
                    if 'type' in node:
                        node_type = node['type']
                        node_name = node.get('name', '')

                        node_types_set.add((node_type, node_name))

        return list(node_types_set)

    def scrape_all_nodes(self):
        """Scraped alle Node-Types von der API (aus Workflows)"""
        print(f"\n🚀 Starte n8n API Node-Type Scraping...\n")

        # Hole alle Workflows
        url = f"{self.api_url}/api/v1/workflows"
        headers = {
            'X-N8N-API-KEY': self.api_key,
            'Accept': 'application/json'
        }

        try:
            print(f"📥 Fetching workflows from: {url}")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            workflows_data = response.json()
            node_types = self.extract_node_types_from_workflows(workflows_data)

            total = len(node_types)
            print(f"📊 Gefunden: {total} einzigartige Node-Types in Workflows\n")

            saved = 0
            for idx, (node_type, node_name) in enumerate(node_types, 1):
                print(f"[{idx}/{total}] {node_type}")

                node_info = {
                    'node_type': node_type,
                    'display_name': node_name,
                    'description': f'Extrahiert aus Workflows',
                    'version': '1',
                    'icon': '',
                    'category': ''
                }

                if self.save_node_type(node_info):
                    saved += 1

            print(f"\n✅ Scraping abgeschlossen!")
            print(f"📈 {saved}/{total} Node-Types gespeichert")

        except requests.exceptions.RequestException as e:
            print(f"❌ API Fehler: {e}")
            return

    def print_stats(self):
        """Zeigt Statistiken"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM node_types_api")
        total = cursor.fetchone()[0]

        print(f"\n📈 Statistiken:")
        print(f"   ✓ Node-Types gespeichert: {total}")

        # Zeige einige Beispiele
        cursor.execute("""
            SELECT node_type, display_name
            FROM node_types_api
            WHERE node_type LIKE '%outlook%' OR node_type LIKE '%http%'
            LIMIT 5
        """)

        examples = cursor.fetchall()
        if examples:
            print(f"\n📝 Beispiele:")
            for node_type, display_name in examples:
                print(f"   • {node_type} → {display_name}")

    def close(self):
        """Schließt die Datenbankverbindung"""
        if self.conn:
            self.conn.close()
            print(f"\n💾 Datenbank geschlossen")


def main():
    """Hauptfunktion"""
    # n8n API Konfiguration
    api_url = 'https://zurdai.ngrok.io'
    api_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3YTZjN2E0NC1mMGIzLTRmYjMtOGM0NS02NDM1MzcwZmFlZWMiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzYzMTI4MjA3fQ.avDQGD8t1ui96uCxsexNjyQvTEmN0VIjWuSDLK4kqhM'

    scraper = N8nApiScraper(api_url, api_key)

    try:
        scraper.scrape_all_nodes()
        scraper.print_stats()
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping durch Benutzer abgebrochen")
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()


if __name__ == '__main__':
    main()

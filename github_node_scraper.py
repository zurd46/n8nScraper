#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Node Type Scraper
Holt die exakten technischen Node-Namen direkt aus dem n8n GitHub Repository
"""

import sys
import io

# Fix für Windows Console Encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
import sqlite3
import time
from datetime import datetime

class GitHubNodeScraper:
    def __init__(self, db_name='n8n_docs.db'):
        self.db_name = db_name
        self.github_api = 'https://api.github.com'
        self.repo = 'n8n-io/n8n'
        self.nodes_path = 'packages/nodes-base/nodes'
        self.conn = None
        self.setup_database()

    def setup_database(self):
        """Verbindet mit der bestehenden Datenbank"""
        self.conn = sqlite3.connect(self.db_name)
        cursor = self.conn.cursor()

        # Neue Tabelle für exakte Node-Types aus GitHub
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS node_types_github (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_type TEXT UNIQUE NOT NULL,
                display_name TEXT,
                description TEXT,
                version TEXT,
                folder_path TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()
        print(f"✓ Datenbank '{self.db_name}' verbunden")

    def get_directory_contents(self, path):
        """Holt Verzeichnisinhalte von GitHub"""
        url = f"{self.github_api}/repos/{self.repo}/contents/{path}"
        headers = {'Accept': 'application/vnd.github.v3+json'}

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Fehler beim Abrufen von {path}: {e}")
            return []

    def get_file_content(self, path):
        """Holt Dateiinhalt von GitHub (Raw)"""
        url = f"https://raw.githubusercontent.com/{self.repo}/master/{path}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"❌ Fehler beim Abrufen von {path}: {e}")
            return None

    def extract_node_info(self, json_content, folder_path):
        """Extrahiert Node-Informationen aus der .node.json Datei"""
        try:
            data = json.loads(json_content)

            return {
                'node_type': data.get('node'),
                'display_name': data.get('displayName'),
                'description': data.get('description'),
                'version': str(data.get('version', 1)),
                'folder_path': folder_path
            }
        except json.JSONDecodeError as e:
            print(f"  ⚠️  JSON Parse Error: {e}")
            return None

    def save_node_type(self, node_info):
        """Speichert Node-Type in der Datenbank"""
        if not node_info or not node_info.get('node_type'):
            return False

        cursor = self.conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO node_types_github
                (node_type, display_name, description, version, folder_path, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                node_info['node_type'],
                node_info['display_name'],
                node_info['description'],
                node_info['version'],
                node_info['folder_path'],
                datetime.now()
            ))

            self.conn.commit()
            print(f"  ✓ {node_info['node_type']}")
            return True

        except sqlite3.Error as e:
            print(f"  ❌ Datenbankfehler: {e}")
            return False

    def crawl_node_folder(self, folder_path):
        """Crawlt einen Node-Ordner nach .node.json Dateien"""
        contents = self.get_directory_contents(folder_path)

        for item in contents:
            if item['type'] == 'file' and item['name'].endswith('.node.json'):
                # Hole die .node.json Datei
                print(f"  📥 {item['path']}")
                json_content = self.get_file_content(item['path'])

                if json_content:
                    node_info = self.extract_node_info(json_content, folder_path)
                    if node_info:
                        self.save_node_type(node_info)

                time.sleep(0.5)  # Rate limiting

    def crawl_all_nodes(self):
        """Crawlt alle Node-Ordner"""
        print(f"\n🚀 Starte GitHub Node-Type Crawling...\n")

        # Hole alle Ordner im nodes Verzeichnis
        contents = self.get_directory_contents(self.nodes_path)

        node_folders = [item for item in contents if item['type'] == 'dir']
        total = len(node_folders)

        print(f"📊 Gefunden: {total} Node-Ordner\n")

        for idx, folder in enumerate(node_folders, 1):
            print(f"[{idx}/{total}] {folder['name']}")
            self.crawl_node_folder(folder['path'])
            time.sleep(1)  # Rate limiting zwischen Ordnern

        print(f"\n✅ Crawling abgeschlossen!")
        self.print_stats()

    def print_stats(self):
        """Zeigt Statistiken"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM node_types_github")
        total = cursor.fetchone()[0]

        print(f"\n📈 Statistiken:")
        print(f"   ✓ Node-Types gespeichert: {total}")

    def close(self):
        """Schließt die Datenbankverbindung"""
        if self.conn:
            self.conn.close()
            print(f"\n💾 Datenbank geschlossen")


def main():
    """Hauptfunktion"""
    scraper = GitHubNodeScraper()

    try:
        scraper.crawl_all_nodes()
    except KeyboardInterrupt:
        print("\n\n⚠️  Crawling durch Benutzer abgebrochen")
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()


if __name__ == '__main__':
    main()

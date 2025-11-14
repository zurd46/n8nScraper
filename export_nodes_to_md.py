#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exportiert alle Node-Types aus der Datenbank in eine Markdown-Datei
"""

import sys
import io
import sqlite3
from datetime import datetime

# Fix für Windows Console Encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class NodeTypesExporter:
    def __init__(self, db_name='n8n_docs.db', output_file='n8n_node_types.md'):
        self.db_name = db_name
        self.output_file = output_file
        self.conn = None

    def connect_db(self):
        """Verbindet mit der Datenbank"""
        self.conn = sqlite3.connect(self.db_name)
        print(f"✓ Verbunden mit Datenbank: {self.db_name}")

    def get_all_node_types(self):
        """Holt alle Node-Types aus beiden Tabellen"""
        cursor = self.conn.cursor()

        # Hole Node-Types aus der API-Tabelle
        cursor.execute("""
            SELECT DISTINCT node_type, display_name, category
            FROM node_types_api
            ORDER BY node_type
        """)
        api_nodes = cursor.fetchall()

        # Hole Node-Types aus der GitHub-Tabelle
        cursor.execute("""
            SELECT DISTINCT node_type, display_name, description
            FROM node_types_github
            ORDER BY node_type
        """)
        github_nodes = cursor.fetchall()

        return api_nodes, github_nodes

    def categorize_nodes(self, nodes):
        """Kategorisiert Nodes nach Typ"""
        categories = {
            'Trigger Nodes': [],
            'Core Nodes': [],
            'App Nodes': [],
            'LangChain Nodes': [],
            'Community Nodes': [],
            'Custom Nodes': []
        }

        for node_type, display_name, extra in nodes:
            if node_type.startswith('n8n-nodes-base.'):
                node_name = node_type.replace('n8n-nodes-base.', '')

                # Trigger Nodes
                if 'trigger' in node_name.lower():
                    categories['Trigger Nodes'].append((node_type, display_name, extra))
                # Core/Utility Nodes
                elif any(keyword in node_name.lower() for keyword in [
                    'webhook', 'cron', 'schedule', 'manual', 'code', 'set', 'if', 'switch',
                    'merge', 'split', 'function', 'crypto', 'datetime', 'filter', 'sort',
                    'limit', 'aggregate', 'compress', 'convert', 'edit', 'html', 'xml',
                    'jwt', 'wait', 'noop', 'error', 'debug', 'sticky'
                ]):
                    categories['Core Nodes'].append((node_type, display_name, extra))
                # App/Service Integration Nodes
                else:
                    categories['App Nodes'].append((node_type, display_name, extra))
            elif node_type.startswith('@n8n/n8n-nodes-langchain.'):
                categories['LangChain Nodes'].append((node_type, display_name, extra))
            elif node_type.startswith('@'):
                categories['Community Nodes'].append((node_type, display_name, extra))
            elif node_type.startswith('CUSTOM.'):
                categories['Custom Nodes'].append((node_type, display_name, extra))
            else:
                categories['Core Nodes'].append((node_type, display_name, extra))

        return categories

    def generate_markdown(self):
        """Generiert die Markdown-Datei"""
        api_nodes, github_nodes = self.get_all_node_types()

        # Kombiniere und dedupliziere
        all_nodes = {}

        # Füge GitHub Nodes hinzu
        for node_type, display_name, description in github_nodes:
            all_nodes[node_type] = {
                'display_name': display_name or node_type,
                'extra': description or '',
                'source': 'GitHub'
            }

        # Überschreibe mit API Nodes (da diese aktueller sind)
        for node_type, display_name, category in api_nodes:
            all_nodes[node_type] = {
                'display_name': display_name or node_type,
                'extra': category or '',
                'source': 'API'
            }

        # Konvertiere zu Liste für Kategorisierung
        nodes_list = [(k, v['display_name'], v['extra']) for k, v in all_nodes.items()]

        categories = self.categorize_nodes(nodes_list)

        # Schreibe Markdown
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("# n8n Node Types\n\n")
            f.write(f"Exportiert am: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Gesamt:** {len(all_nodes)} einzigartige Node-Types\n\n")

            f.write("---\n\n")

            # Statistiken
            f.write("## Übersicht\n\n")
            f.write("| Kategorie | Anzahl |\n")
            f.write("|-----------|--------|\n")
            for cat_name, cat_nodes in categories.items():
                if cat_nodes:
                    f.write(f"| {cat_name} | {len(cat_nodes)} |\n")
            f.write(f"| **Gesamt** | **{len(all_nodes)}** |\n\n")

            f.write("---\n\n")

            # Detaillierte Listen pro Kategorie
            for cat_name, cat_nodes in categories.items():
                if not cat_nodes:
                    continue

                f.write(f"## {cat_name}\n\n")
                f.write(f"**Anzahl:** {len(cat_nodes)}\n\n")

                # Sortiere alphabetisch
                cat_nodes.sort(key=lambda x: x[0])

                # Tabelle
                f.write("| Node Type | Display Name | Info |\n")
                f.write("|-----------|--------------|------|\n")

                for node_type, display_name, extra in cat_nodes:
                    # Escape Pipe-Zeichen in den Daten
                    node_type_escaped = node_type.replace('|', '\\|')
                    display_name_escaped = (display_name or '').replace('|', '\\|')
                    extra_escaped = (extra or '').replace('|', '\\|')[:50]  # Kürze auf 50 Zeichen

                    f.write(f"| `{node_type_escaped}` | {display_name_escaped} | {extra_escaped} |\n")

                f.write("\n")

            # Alphabetische Gesamtliste
            f.write("---\n\n")
            f.write("## Alphabetische Gesamtliste\n\n")

            sorted_nodes = sorted(nodes_list, key=lambda x: x[0].lower())

            for node_type, display_name, extra in sorted_nodes:
                node_type_escaped = node_type.replace('|', '\\|')
                display_name_escaped = (display_name or '').replace('|', '\\|')
                f.write(f"- **`{node_type_escaped}`** - {display_name_escaped}\n")

        print(f"\n✓ Markdown-Datei erstellt: {self.output_file}")
        print(f"📊 {len(all_nodes)} Node-Types exportiert")

    def print_stats(self):
        """Zeigt Datenbankstatistiken"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM node_types_api")
        api_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM node_types_github")
        github_count = cursor.fetchone()[0]

        print(f"\n📈 Datenbankstatistiken:")
        print(f"   • API Nodes: {api_count}")
        print(f"   • GitHub Nodes: {github_count}")

    def close(self):
        """Schließt die Datenbankverbindung"""
        if self.conn:
            self.conn.close()

def main():
    """Hauptfunktion"""
    print("🚀 Starte Node-Types Export...\n")

    exporter = NodeTypesExporter()

    try:
        exporter.connect_db()
        exporter.print_stats()
        exporter.generate_markdown()

    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
    finally:
        exporter.close()

    print("\n✅ Export abgeschlossen!")

if __name__ == '__main__':
    main()

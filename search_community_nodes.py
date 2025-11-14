#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Community Nodes Searcher
Sucht nach Community Nodes auf npm und GitHub
"""

import sys
import io
import requests
import sqlite3
from datetime import datetime
import time

# Fix für Windows Console Encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class CommunityNodesSearcher:
    def __init__(self, db_name='n8n_docs.db'):
        self.db_name = db_name
        self.conn = None
        self.setup_database()

    def setup_database(self):
        """Verbindet mit der Datenbank"""
        self.conn = sqlite3.connect(self.db_name)
        cursor = self.conn.cursor()

        # Tabelle für Community Nodes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS community_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                package_name TEXT UNIQUE NOT NULL,
                node_types TEXT,
                description TEXT,
                version TEXT,
                author TEXT,
                repository TEXT,
                downloads INTEGER,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()
        print(f"✓ Datenbank '{self.db_name}' verbunden")

    def search_npm_community_nodes(self):
        """Sucht nach n8n Community Nodes auf npm"""
        print("\n🔍 Suche n8n Community Nodes auf npm...\n")

        # NPM Registry API
        # Suche nach Paketen mit "n8n-nodes" im Namen
        search_url = "https://registry.npmjs.org/-/v1/search"

        all_packages = []
        page = 0
        size = 250  # Max items per page

        while True:
            params = {
                'text': 'n8n-nodes',
                'size': size,
                'from': page * size
            }

            try:
                print(f"📄 Seite {page + 1} wird abgerufen...")
                response = requests.get(search_url, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()
                objects = data.get('objects', [])

                if not objects:
                    break

                all_packages.extend(objects)
                print(f"   ✓ {len(objects)} Pakete gefunden")

                # Prüfe ob es weitere Seiten gibt
                total = data.get('total', 0)
                if len(all_packages) >= total:
                    break

                page += 1
                time.sleep(0.5)  # Rate limiting

            except requests.exceptions.RequestException as e:
                print(f"❌ Fehler: {e}")
                break

        print(f"\n📊 Gesamt: {len(all_packages)} Pakete gefunden")
        return all_packages

    def filter_community_nodes(self, packages):
        """Filtert echte Community Nodes (externe Pakete mit @)"""
        community_nodes = []

        for pkg_obj in packages:
            pkg = pkg_obj.get('package', {})
            name = pkg.get('name', '')

            # Nur Pakete die mit @ beginnen (scoped packages) oder n8n-nodes-* heißen
            # Aber nicht offizielle n8n Pakete
            if (name.startswith('@') or name.startswith('n8n-nodes-')) and \
               not name.startswith('n8n/') and \
               not name.startswith('@n8n/') and \
               'n8n' in name.lower() and \
               'nodes' in name.lower():
                community_nodes.append(pkg)

        return community_nodes

    def extract_node_types_from_package(self, package_name):
        """Versucht Node-Types aus dem Package zu extrahieren"""
        # Hole package.json vom npm registry
        try:
            url = f"https://registry.npmjs.org/{package_name}/latest"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            pkg_data = response.json()

            # Suche nach n8n Nodes Definitionen
            node_types = []

            # n8n nodes werden oft in package.json unter "n8n" definiert
            if 'n8n' in pkg_data:
                n8n_config = pkg_data['n8n']
                if 'nodes' in n8n_config:
                    node_types = n8n_config['nodes']

            return node_types

        except Exception as e:
            return []

    def save_community_node(self, package):
        """Speichert Community Node in der Datenbank"""
        cursor = self.conn.cursor()

        try:
            name = package.get('name', '')
            description = package.get('description', '')
            version = package.get('version', '')

            # Author extrahieren
            author = ''
            if 'author' in package:
                if isinstance(package['author'], dict):
                    author = package['author'].get('name', '')
                else:
                    author = str(package['author'])

            # Repository
            repository = ''
            if 'repository' in package:
                if isinstance(package['repository'], dict):
                    repository = package['repository'].get('url', '')
                else:
                    repository = str(package['repository'])

            # Downloads (falls verfügbar in npm metadata)
            downloads = 0

            # Versuche Node-Types zu extrahieren
            node_types_list = self.extract_node_types_from_package(name)
            node_types_str = ', '.join(node_types_list) if node_types_list else ''

            cursor.execute('''
                INSERT OR REPLACE INTO community_nodes
                (package_name, node_types, description, version, author, repository, downloads, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                name,
                node_types_str,
                description,
                version,
                author,
                repository,
                downloads,
                datetime.now()
            ))

            self.conn.commit()
            return True

        except sqlite3.Error as e:
            print(f"  ❌ Datenbankfehler: {e}")
            return False

    def search_and_save(self):
        """Sucht und speichert alle Community Nodes"""
        # Suche auf npm
        packages = self.search_npm_community_nodes()

        # Filtere Community Nodes
        community_nodes = self.filter_community_nodes(packages)

        print(f"\n✅ {len(community_nodes)} Community Nodes gefunden")
        print(f"\n💾 Speichere in Datenbank...\n")

        saved = 0
        for idx, pkg in enumerate(community_nodes, 1):
            name = pkg.get('name', '')
            desc = pkg.get('description', '')[:50] if pkg.get('description') else ''

            print(f"[{idx}/{len(community_nodes)}] {name}")
            if desc:
                print(f"    {desc}...")

            if self.save_community_node(pkg):
                saved += 1

            time.sleep(0.2)  # Rate limiting

        print(f"\n✅ {saved}/{len(community_nodes)} Community Nodes gespeichert!")

    def print_stats(self):
        """Zeigt Statistiken"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM community_nodes")
        total = cursor.fetchone()[0]

        print(f"\n📈 Statistiken:")
        print(f"   ✓ Community Nodes: {total}")

        # Top 10 Community Nodes
        print(f"\n🏆 Beispiele:")
        cursor.execute("""
            SELECT package_name, description
            FROM community_nodes
            LIMIT 10
        """)

        for name, desc in cursor.fetchall():
            desc_short = (desc[:60] + '...') if desc and len(desc) > 60 else desc
            print(f"   • {name}")
            if desc_short:
                print(f"     {desc_short}")

    def export_to_node_types_api(self):
        """Exportiert Community Nodes auch in die node_types_api Tabelle"""
        cursor = self.conn.cursor()

        print(f"\n📤 Exportiere Community Nodes zu node_types_api...\n")

        # Hole alle Community Nodes
        cursor.execute("""
            SELECT package_name, node_types, description
            FROM community_nodes
        """)

        community_nodes = cursor.fetchall()
        exported = 0

        for package_name, node_types_str, description in community_nodes:
            # Wenn node_types vorhanden sind, füge sie einzeln hinzu
            if node_types_str:
                node_types = [nt.strip() for nt in node_types_str.split(',')]
                for node_type in node_types:
                    if node_type:
                        try:
                            cursor.execute('''
                                INSERT OR REPLACE INTO node_types_api
                                (node_type, display_name, description, version, icon, category, scraped_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                node_type,
                                node_type,
                                f"Community Node: {description}" if description else f"Community Node from {package_name}",
                                1,
                                '',
                                'Community',
                                datetime.now()
                            ))
                            exported += 1
                        except sqlite3.Error:
                            pass
            else:
                # Wenn keine node_types, füge Package als Ganzes hinzu
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO node_types_api
                        (node_type, display_name, description, version, icon, category, scraped_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        package_name,
                        package_name,
                        f"Community Package: {description}" if description else f"Community Package",
                        1,
                        '',
                        'Community',
                        datetime.now()
                    ))
                    exported += 1
                except sqlite3.Error:
                    pass

        self.conn.commit()
        print(f"✅ {exported} Community Nodes zu node_types_api exportiert")

    def close(self):
        """Schließt die Datenbankverbindung"""
        if self.conn:
            self.conn.close()


def main():
    """Hauptfunktion"""
    searcher = CommunityNodesSearcher()

    try:
        searcher.search_and_save()
        searcher.print_stats()
        searcher.export_to_node_types_api()

    except KeyboardInterrupt:
        print("\n\n⚠️  Suche abgebrochen")
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
    finally:
        searcher.close()


if __name__ == '__main__':
    main()

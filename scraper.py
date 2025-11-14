#!/usr/bin/env python3
"""
n8n Documentation Scraper mit Jina AI Reader API
Scraped die komplette n8n Dokumentation und speichert sie in einer SQLite-Datenbank
"""

import sqlite3
import requests
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from datetime import datetime

class N8nDocScraper:
    def __init__(self, db_name='n8n_docs.db', jina_api_key=None):
        self.db_name = db_name
        self.base_url = 'https://docs.n8n.io'
        self.jina_api_base = 'https://r.jina.ai/'
        self.jina_api_key = jina_api_key
        self.visited_urls = set()
        self.conn = None
        self.setup_database()

    def setup_database(self):
        """Erstellt die SQLite-Datenbank und Tabellen"""
        self.conn = sqlite3.connect(self.db_name)
        cursor = self.conn.cursor()

        # Tabelle für gescrapte Seiten
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                node_type TEXT,
                content TEXT,
                markdown_content TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'success'
            )
        ''')

        # Tabelle für Links zwischen Seiten
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url TEXT NOT NULL,
                target_url TEXT NOT NULL,
                link_text TEXT,
                FOREIGN KEY (source_url) REFERENCES pages(url)
            )
        ''')

        # Index für schnellere Suche
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_url ON pages(url)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_source_url ON links(source_url)
        ''')

        self.conn.commit()
        print(f"✓ Datenbank '{self.db_name}' initialisiert")

    def fetch_with_jina(self, url):
        """
        Holt den Inhalt einer URL über Jina AI Reader API
        Returns: (markdown_content, title, links)
        """
        jina_url = self.jina_api_base + url

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # API-Key hinzufügen wenn vorhanden
        if self.jina_api_key:
            headers['Authorization'] = f'Bearer {self.jina_api_key}'

        try:
            print(f"  📥 Fetching via Jina AI: {url}")
            response = requests.get(jina_url, headers=headers, timeout=30)
            response.raise_for_status()

            markdown_content = response.text

            # Titel aus dem Markdown extrahieren (erste # Überschrift)
            title_match = re.search(r'^#\s+(.+)$', markdown_content, re.MULTILINE)
            title = title_match.group(1) if title_match else url

            # Node Type aus URL extrahieren (z.B. n8n-nodes-base.httpRequest)
            node_type = self.extract_node_type(url)

            # Links aus dem Markdown extrahieren
            links = self.extract_links_from_markdown(markdown_content, url)

            return markdown_content, title, node_type, links

        except requests.exceptions.RequestException as e:
            print(f"  ❌ Fehler beim Abrufen von {url}: {e}")
            return None, None, None, []

    def extract_node_type(self, url):
        """
        Extrahiert den technischen Node-Type aus der URL
        z.B. https://docs.n8n.io/.../n8n-nodes-base.httpRequest/ -> n8n-nodes-base.httpRequest
        """
        # Pattern für Node-Types: n8n-nodes-base.xyz oder @namespace/package.xyz
        patterns = [
            r'/(n8n-nodes-[^/]+\.[^/]+)/?$',  # n8n-nodes-base.httpRequest
            r'/(@[^/]+/[^/]+\.[^/]+)/?$',      # @zurdai/n8n-nodes-bexio.bexio
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def extract_links_from_markdown(self, markdown_content, base_url):
        """Extrahiert Links aus Markdown-Inhalt"""
        links = []

        # Markdown Links: [text](url)
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        matches = re.findall(link_pattern, markdown_content)

        for link_text, url in matches:
            # Absolute URL erstellen
            absolute_url = urljoin(base_url, url)

            # Nur Links von docs.n8n.io behalten
            if absolute_url.startswith(self.base_url):
                # Fragment-Identifier entfernen (#section)
                clean_url = absolute_url.split('#')[0]
                links.append({
                    'url': clean_url,
                    'text': link_text
                })

        return links

    def save_page(self, url, title, markdown_content, node_type=None, status='success'):
        """Speichert eine Seite in der Datenbank"""
        cursor = self.conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO pages (url, title, node_type, markdown_content, status, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (url, title, node_type, markdown_content, status, datetime.now()))

            self.conn.commit()
            print(f"  ✓ Gespeichert: {title}")
            return True

        except sqlite3.Error as e:
            print(f"  ❌ Datenbankfehler: {e}")
            return False

    def save_links(self, source_url, links):
        """Speichert gefundene Links in der Datenbank"""
        cursor = self.conn.cursor()

        for link in links:
            try:
                cursor.execute('''
                    INSERT INTO links (source_url, target_url, link_text)
                    VALUES (?, ?, ?)
                ''', (source_url, link['url'], link['text']))
            except sqlite3.Error:
                pass  # Link existiert bereits

        self.conn.commit()

    def should_crawl(self, url):
        """Prüft, ob eine URL gecrawlt werden soll"""
        # URL bereits besucht?
        if url in self.visited_urls:
            return False

        # Ist es eine docs.n8n.io URL?
        if not url.startswith(self.base_url):
            return False

        # Ausschluss von bestimmten URLs (z.B. API endpoints, downloads)
        exclude_patterns = [
            '/api/',
            '/downloads/',
            '.pdf',
            '.zip',
            '/search'
        ]

        for pattern in exclude_patterns:
            if pattern in url:
                return False

        return True

    def crawl(self, start_url, max_pages=None):
        """
        Startet das rekursive Crawling
        start_url: Die Start-URL
        max_pages: Maximale Anzahl zu crawlender Seiten (None = unbegrenzt)
        """
        to_visit = [start_url]
        pages_crawled = 0

        print(f"\n🚀 Starte Crawling von: {start_url}")
        print(f"📊 Max. Seiten: {max_pages if max_pages else 'unbegrenzt'}\n")

        while to_visit and (max_pages is None or pages_crawled < max_pages):
            url = to_visit.pop(0)

            if not self.should_crawl(url):
                continue

            self.visited_urls.add(url)
            pages_crawled += 1

            print(f"\n[{pages_crawled}/{max_pages if max_pages else '∞'}] Crawling: {url}")

            # Mit Jina AI abrufen
            markdown_content, title, node_type, links = self.fetch_with_jina(url)

            if markdown_content:
                # In Datenbank speichern
                self.save_page(url, title, markdown_content, node_type)
                self.save_links(url, links)

                # Neue Links zur Warteschlange hinzufügen
                for link in links:
                    if link['url'] not in self.visited_urls and link['url'] not in to_visit:
                        to_visit.append(link['url'])

                print(f"  📎 {len(links)} Links gefunden, {len(to_visit)} in Warteschlange")
            else:
                # Fehlerseite speichern
                self.save_page(url, f"Error: {url}", "", status='error')

            # Höfliche Verzögerung zwischen Requests
            time.sleep(1)

        print(f"\n✅ Crawling abgeschlossen!")
        print(f"📊 Insgesamt {pages_crawled} Seiten gecrawlt")
        self.print_stats()

    def print_stats(self):
        """Zeigt Statistiken über die gescrapten Daten"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM pages WHERE status='success'")
        success_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM pages WHERE status='error'")
        error_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM links")
        links_count = cursor.fetchone()[0]

        print(f"\n📈 Statistiken:")
        print(f"   ✓ Erfolgreiche Seiten: {success_count}")
        print(f"   ✗ Fehlerhafte Seiten: {error_count}")
        print(f"   🔗 Gespeicherte Links: {links_count}")

    def close(self):
        """Schließt die Datenbankverbindung"""
        if self.conn:
            self.conn.close()
            print(f"\n💾 Datenbank geschlossen")


def main():
    """Hauptfunktion"""
    # Jina AI API Key
    jina_api_key = 'jina_9d6ab8e62b4146a584a7fd1ad8d3aab6SI6-AFVXbSDaojuSInhduGLQcG0t'

    scraper = N8nDocScraper(jina_api_key=jina_api_key)

    try:
        # Wichtige Bereiche die gecrawlt werden sollen
        start_urls = [
            'https://docs.n8n.io/integrations/builtin/core-nodes/',
            'https://docs.n8n.io/integrations/builtin/app-nodes/',
            'https://docs.n8n.io/integrations/builtin/trigger-nodes/',
            'https://docs.n8n.io/integrations/builtin/cluster-nodes/',
            'https://docs.n8n.io/integrations/builtin/credentials/',
            'https://docs.n8n.io/integrations/custom-operations/'
        ]

        # Jeden Bereich einzeln crawlen
        for start_url in start_urls:
            print(f"\n{'='*80}")
            print(f"Starte neuen Crawl-Bereich: {start_url}")
            print(f"{'='*80}\n")

            # Crawl mit Limit (für Testing: 50 Seiten, für vollständig: None)
            # Setzen Sie max_pages=None für vollständiges Crawling
            scraper.crawl(start_url, max_pages=None)

    except KeyboardInterrupt:
        print("\n\n⚠️  Crawling durch Benutzer abgebrochen")
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
    finally:
        scraper.close()


if __name__ == '__main__':
    main()

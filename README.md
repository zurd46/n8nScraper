# n8n Documentation Scraper

Ein Python-basierter Web Scraper, der die komplette n8n Dokumentation mit der Jina AI Reader API scraped und in einer SQLite-Datenbank speichert.

## Features

- Verwendet Jina AI Reader API für sauberes Markdown-Format
- Rekursives Crawling aller verlinkten Seiten
- SQLite-Datenbank für strukturierte Speicherung
- Automatische Link-Extraktion und -Verfolgung
- Fortschrittsanzeige während des Crawlings
- Duplikat-Erkennung (keine doppelten URLs)
- Statistiken über gescrapte Daten

## Voraussetzungen

- Python 3.7+
- Jina AI API Key (bereits im Code eingetragen)
- Virtuelle Umgebung (empfohlen)

## Installation

1. Repository klonen oder Dateien herunterladen

2. Virtuelle Umgebung erstellen und aktivieren:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

## Verwendung

### Einfacher Start

Das Skript startet automatisch beim Integrations-Bereich und crawled alle verlinkten Seiten:

```bash
python scraper.py
```

### Konfiguration

Im Code können Sie folgende Parameter anpassen:

```python
# In scraper.py, main() Funktion:

# Start-URL ändern
start_url = 'https://docs.n8n.io/integrations/'

# Maximale Anzahl Seiten begrenzen (für Tests)
scraper.crawl(start_url, max_pages=50)

# Unbegrenztes Crawling
scraper.crawl(start_url, max_pages=None)
```

## Datenbank-Schema

### Tabelle: `pages`
Speichert die gescrapten Seiten:
- `id`: Primärschlüssel
- `url`: Eindeutige URL der Seite
- `title`: Seitentitel (extrahiert aus Markdown)
- `markdown_content`: Vollständiger Inhalt im Markdown-Format
- `scraped_at`: Zeitstempel des Scrapings
- `status`: Status (success/error)

### Tabelle: `links`
Speichert Links zwischen Seiten:
- `id`: Primärschlüssel
- `source_url`: Quell-URL
- `target_url`: Ziel-URL
- `link_text`: Text des Links

## Ausgabe

Während des Crawlings sehen Sie:
```
🚀 Starte Crawling von: https://docs.n8n.io/integrations/
📊 Max. Seiten: unbegrenzt

[1/∞] Crawling: https://docs.n8n.io/integrations/
  📥 Fetching via Jina AI: https://docs.n8n.io/integrations/
  ✓ Gespeichert: Integrations
  📎 45 Links gefunden, 45 in Warteschlange

[2/∞] Crawling: https://docs.n8n.io/integrations/builtin/
  ...
```

Nach Abschluss:
```
✅ Crawling abgeschlossen!
📊 Insgesamt 250 Seiten gecrawlt

📈 Statistiken:
   ✓ Erfolgreiche Seiten: 248
   ✗ Fehlerhafte Seiten: 2
   🔗 Gespeicherte Links: 1250

💾 Datenbank geschlossen
```

## Datenbank-Abfragen

Nach dem Scraping können Sie die SQLite-Datenbank abfragen:

```python
import sqlite3

conn = sqlite3.connect('n8n_docs.db')
cursor = conn.cursor()

# Alle Seiten anzeigen
cursor.execute("SELECT title, url FROM pages WHERE status='success'")
pages = cursor.fetchall()

# Nach bestimmtem Inhalt suchen
cursor.execute("SELECT title, url FROM pages WHERE markdown_content LIKE '%webhook%'")
results = cursor.fetchall()

# Alle Links einer Seite
cursor.execute("SELECT target_url, link_text FROM links WHERE source_url = ?",
               ('https://docs.n8n.io/integrations/',))
links = cursor.fetchall()
```

Oder mit einem SQLite-Browser wie [DB Browser for SQLite](https://sqlitebrowser.org/).

## Features im Detail

### Jina AI Reader API
- Konvertiert HTML automatisch in sauberes Markdown
- Entfernt Navigation und Footer
- Behält die Struktur und Formatierung bei
- Extrahiert alle Links aus dem Content

### Intelligentes Crawling
- Vermeidet Duplikate durch URL-Tracking
- Filtert externe Links automatisch
- Höfliche Verzögerung (1 Sekunde) zwischen Requests
- Kann jederzeit mit Ctrl+C abgebrochen werden

### Fehlerbehandlung
- Bei Fehlern wird die Seite als 'error' markiert
- Crawling wird fortgesetzt
- Statistiken zeigen erfolgreiche und fehlerhafte Seiten

## Einschränkungen

- Crawled nur Seiten von `docs.n8n.io`
- Überspringt API-Endpoints, Downloads und Suchseiten
- PDF und ZIP-Dateien werden nicht heruntergeladen

## Anpassungen

### Andere Domains crawlen
```python
self.base_url = 'https://ihre-domain.de'
```

### Filter anpassen
In der `should_crawl()` Methode:
```python
exclude_patterns = [
    '/api/',
    '/downloads/',
    '.pdf',
    # Ihre eigenen Ausschlüsse hier
]
```

### Verzögerung ändern
```python
time.sleep(1)  # In Sekunden
```

## Lizenz

MIT License - Frei verwendbar für private und kommerzielle Projekte

## Support

Bei Fragen oder Problemen erstellen Sie bitte ein Issue auf GitHub.

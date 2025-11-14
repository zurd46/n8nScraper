# n8n Nodes Scraper & Explorer

Eine umfassende Sammlung von Tools zum Scrapen, Speichern und Durchsuchen aller n8n Node-Types (Official, Community & Custom).

## 🎯 Features

- **Intelligente Suche** - Synonym-basierte Suche mit Relevanz-Ranking
- **Multi-Source Scraping** - Holt Nodes aus n8n Docs, GitHub, npm Registry und n8n API
- **SQLite Datenbank** - Zentrale Speicherung aller Node-Informationen
- **Streamlit Web-App** - Interaktive UI zum Durchsuchen aller Nodes
- **Automatische camelCase Korrektur** - Stellt sicher, dass Node-Namen workflow-kompatibel sind

## 📁 Projekt-Struktur

```
n8nScraper/
├── scripts/                    # Scraping Scripts
│   ├── scraper.py             # Jina AI Documentation Scraper
│   ├── github_node_scraper.py # GitHub Repository Scraper
│   ├── n8n_api_scraper.py     # n8n API Scraper
│   ├── search_community_nodes.py # npm Registry Community Nodes
│   └── populate_all_nodes.py  # Populate DB with complete node list
│
├── utils/                      # Utility Scripts
│   ├── check_casing.py        # Verify node name casing
│   ├── check_community_stats.py # Community nodes statistics
│   ├── show_stats.py          # Database statistics
│   ├── export_nodes_to_md.py  # Export to Markdown
│   └── fix_node_casing.py     # Fix lowercase to camelCase
│
├── docs/                       # Documentation
│   ├── README.md              # This file
│   ├── README_APP.md          # Streamlit App Documentation
│   └── INTELLIGENT_SEARCH.md  # Search algorithm docs
│
├── data/                       # Data files
│   └── n8n_docs.db           # SQLite database (auto-generated)
│
├── output/                     # Generated output
│   └── n8n_node_types.md     # Markdown export of all nodes
│
├── n8n_nodes_app.py           # Main Streamlit Application
├── requirements.txt           # Python dependencies
└── .gitignore                # Git ignore rules
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone Repository
git clone https://github.com/yourusername/n8nScraper.git
cd n8nScraper

# Install Dependencies
pip install -r requirements.txt
```

### 2. Daten sammeln (Optional)

Die Datenbank ist bereits vorausgefüllt. Falls du sie neu erstellen möchtest:

```bash
# Offizielle Nodes (443 Nodes)
python scripts/populate_all_nodes.py

# GitHub Nodes (bis zu 307 Nodes, API-limitiert)
python scripts/github_node_scraper.py

# n8n API Nodes (aus deinen Workflows)
python scripts/n8n_api_scraper.py

# Community Nodes von npm (~20.000+ Nodes)
python scripts/search_community_nodes.py

# camelCase Korrektur anwenden
python utils/fix_node_casing.py
```

### 3. Streamlit App starten

```bash
streamlit run n8n_nodes_app.py
```

Die App öffnet sich automatisch unter `http://localhost:8501`

## 📊 Datenquellen

| Quelle | Nodes | Beschreibung |
|--------|-------|--------------|
| **populate_all_nodes.py** | 443 | Vollständige Liste offizieller n8n Nodes |
| **github_node_scraper.py** | ~66 | Direkt aus GitHub Repository .node.json Files |
| **n8n_api_scraper.py** | 31 | Extrahiert aus eigenen n8n Workflows |
| **search_community_nodes.py** | ~20.000+ | Community Nodes von npm Registry |

**Gesamt:** ~21.000+ Nodes in der Datenbank

## 🔍 Intelligente Suche

Die Streamlit App verwendet eine intelligente Suche mit:

- **Synonym-Erweiterung** - "email" findet automatisch Gmail, Outlook, SMTP, etc.
- **Relevanz-Ranking** - Beste Matches zuerst
- **Kategorie-Filter** - Nach App, Trigger, Core, LangChain, Community
- **Quick Search Buttons** - Häufige Suchen mit einem Klick

### Beispiel-Suchen:

```
email     → Gmail, Outlook, SMTP, IMAP, Mailchimp, SendGrid...
database  → Postgres, MySQL, MongoDB, Redis, SQL...
ai        → OpenAI, Anthropic, Claude, GPT, Gemini, LangChain...
chat      → Slack, Teams, Discord, Telegram, WhatsApp...
cloud     → AWS, Azure, Google Cloud, S3, Drive, Dropbox...
```

Siehe [INTELLIGENT_SEARCH.md](docs/INTELLIGENT_SEARCH.md) für Details.

## 🗃️ Datenbank-Schema

```sql
-- Offizielle Nodes aus Dokumentation
CREATE TABLE node_types_api (
    node_type TEXT UNIQUE NOT NULL,      -- z.B. n8n-nodes-base.gmail
    display_name TEXT,                   -- z.B. Gmail
    description TEXT,
    category TEXT,                       -- App, Trigger, Core, LangChain
    version INTEGER,
    icon TEXT,
    scraped_at TIMESTAMP
);

-- Nodes aus GitHub Repository
CREATE TABLE node_types_github (
    node_type TEXT UNIQUE NOT NULL,
    display_name TEXT,
    description TEXT,
    version INTEGER,
    folder_path TEXT,
    scraped_at TIMESTAMP
);

-- Community Nodes von npm
CREATE TABLE community_nodes (
    package_name TEXT UNIQUE NOT NULL,  -- z.B. @apify/n8n-nodes-apify
    node_types TEXT,
    description TEXT,
    version TEXT,
    author TEXT,
    repository TEXT,
    downloads INTEGER,
    scraped_at TIMESTAMP
);

-- Scraping Queue/Log
CREATE TABLE pages (
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    node_type TEXT,
    markdown_content TEXT,
    scraped_at TIMESTAMP
);
```

## 🛠️ Utility Scripts

### Statistiken anzeigen

```bash
python utils/show_stats.py
```

Zeigt Anzahl der Nodes pro Kategorie.

### Community Nodes Status

```bash
python utils/check_community_stats.py
```

Zeigt Fortschritt des Community Node Scrapings.

### Casing überprüfen

```bash
python utils/check_casing.py
```

Vergleicht Groß-/Kleinschreibung zwischen GitHub und API Nodes.

### Export zu Markdown

```bash
python utils/export_nodes_to_md.py
```

Exportiert alle Nodes in eine übersichtliche Markdown-Datei.

## ⚙️ Konfiguration

### n8n API Key (für n8n_api_scraper.py)

Setze deine n8n API Credentials in `scripts/n8n_api_scraper.py`:

```python
API_URL = "https://your-n8n-instance.com"
API_KEY = "your-api-key-here"
```

### Jina AI Key (für scraper.py - optional)

Für Dokumentations-Scraping via Jina AI Reader:

```python
JINA_API_KEY = "your-jina-api-key"
```

## 📈 Performance

- **Suche:** <100ms für vollständige Suche über 20.000+ Nodes
- **Caching:** 60 Sekunden TTL für Datenbankabfragen
- **Scraping Rate Limits:**
  - GitHub API: 60 req/h (unauth) / 5000 req/h (auth)
  - npm Registry: keine bekannten Limits
  - n8n API: abhängig von deiner Instanz

## 🔧 Entwicklung

### Neue Synonyme hinzufügen

Bearbeite `n8n_nodes_app.py`:

```python
def expand_search_terms(search_term):
    synonyms = {
        'dein_begriff': ['synonym1', 'synonym2', 'synonym3'],
        # ... weitere
    }
```

### Neue Datenquelle hinzufügen

1. Erstelle neues Script in `scripts/`
2. Verbinde mit `n8n_docs.db`
3. Füge Daten in entsprechende Tabelle ein
4. Aktualisiere `n8n_nodes_app.py` um neue Quelle zu laden

## 📝 Wichtige Hinweise

### camelCase ist wichtig!

n8n Workflow JSON Files benötigen **exakte camelCase** Node-Namen:

```json
{
  "type": "n8n-nodes-base.microsoftOutlook"  // ✅ Richtig
}
```

**NICHT:**
```json
{
  "type": "n8n-nodes-base.microsoftoutlook"  // ❌ Falsch - funktioniert nicht!
}
```

Das Script `utils/fix_node_casing.py` korrigiert automatisch alle lowercase Namen zu camelCase.

## 🤝 Contributing

Contributions sind willkommen! Besonders:

- Neue Synonyme für die intelligente Suche
- Weitere Datenquellen
- Verbesserungen der Streamlit App
- Dokumentation

## 📄 Lizenz

MIT License

## 🔗 Links

- [n8n Documentation](https://docs.n8n.io/)
- [n8n GitHub](https://github.com/n8n-io/n8n)
- [n8n Community](https://community.n8n.io/)
- [npm Registry](https://www.npmjs.com/search?q=n8n-nodes)

## 👨‍💻 Autor

Erstellt mit Claude Code

---

**Status:**
- ✅ 443 Official Nodes
- ✅ 66 GitHub Nodes
- ✅ 20.000+ Community Nodes
- ✅ Intelligente Suche
- ✅ Streamlit Web-App

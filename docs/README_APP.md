# n8n Nodes Explorer - Streamlit App

Eine interaktive Web-App zum Durchsuchen und Erkunden aller n8n Node-Types.

## Features

- 🔍 **Volltext-Suche**: Durchsuche Node-Type, Display Name und Description
- 🏷️ **Kategorie-Filter**: Filtere nach App, Trigger, Core, LangChain und Community Nodes
- 📊 **Statistiken**: Echtzeit-Übersicht über alle Node-Kategorien
- 🎨 **3 Ansichten**: Cards, Table und Compact List
- ⚡ **Schnell**: Gecachte Datenbank-Abfragen für optimale Performance
- 📱 **Responsive**: Funktioniert auf Desktop und Mobile

## Installation

```bash
# Dependencies installieren
pip install -r requirements.txt
```

## Starten

```bash
# Streamlit App starten
streamlit run n8n_nodes_app.py
```

Die App öffnet sich automatisch im Browser unter `http://localhost:8501`

## Datenquellen

Die App liest aus der SQLite Datenbank `n8n_docs.db` und kombiniert Daten aus:

- **node_types_api**: Offizielle n8n Nodes aus der Dokumentation (467 Nodes)
- **node_types_github**: Nodes aus dem GitHub Repository (66 Nodes)
- **community_nodes**: Community Nodes von npm (~20.000+ Nodes)

## Verwendung

### Suche
Gib einfach einen Suchbegriff ein, z.B.:
- `gmail` - Findet Gmail Node
- `microsoft` - Findet alle Microsoft Nodes
- `trigger` - Findet alle Trigger Nodes
- `langchain` - Findet LangChain Nodes

### Filter
- **Kategorien**: Wähle eine oder mehrere Kategorien aus
- **Sortierung**: Sortiere nach Name, Node-Type oder Kategorie
- **Ansicht**: Wechsle zwischen Card, Table und Compact List

### Kategorien

- **App**: Integration Nodes für externe Dienste (Gmail, Slack, etc.)
- **Trigger**: Event-basierte Nodes die Workflows starten
- **Core**: Utility Nodes (Code, Set, If, Merge, etc.)
- **LangChain**: KI/LLM Nodes für LangChain
- **Community**: Community-entwickelte Nodes von npm

## Screenshots

### Card View
Detaillierte Ansicht mit Beschreibungen und Kategorien

### Table View
Übersichtliche Tabellenansicht für schnelles Scannen

### Compact List
Kompakte Liste für maximale Übersicht

## Technologie

- **Streamlit**: Web-Framework
- **SQLite**: Datenbank
- **Pandas**: Datenverarbeitung
- **Python 3.13**: Runtime

## Datenbankschema

```sql
-- Offizielle Nodes
CREATE TABLE node_types_api (
    node_type TEXT UNIQUE NOT NULL,
    display_name TEXT,
    description TEXT,
    category TEXT,
    version INTEGER
);

-- GitHub Nodes
CREATE TABLE node_types_github (
    node_type TEXT UNIQUE NOT NULL,
    display_name TEXT,
    description TEXT,
    version INTEGER
);

-- Community Nodes
CREATE TABLE community_nodes (
    package_name TEXT UNIQUE NOT NULL,
    description TEXT,
    version TEXT
);
```

## Entwicklung

Die App ist vollständig in Python geschrieben und nutzt Streamlit's Caching-Mechanismen für optimale Performance.

### Code-Struktur

- `n8n_nodes_app.py`: Haupt-App Datei
- `n8n_docs.db`: SQLite Datenbank
- `requirements.txt`: Python Dependencies

### Anpassungen

Du kannst die App anpassen durch:
- Custom CSS in `st.markdown()`
- Neue Filter hinzufügen
- Weitere Ansichten implementieren
- Export-Funktionen hinzufügen

## Updates

Um die Datenbank zu aktualisieren:

```bash
# Offizielle Nodes
python populate_all_nodes.py

# Community Nodes
python search_community_nodes.py

# GitHub Nodes
python github_node_scraper.py

# n8n API Nodes
python n8n_api_scraper.py
```

## Performance

- **Load Time**: <1 Sekunde
- **Search**: Instant (clientseitig)
- **Caching**: 60 Sekunden TTL
- **Database**: SQLite (schnell für Lese-Operationen)

## Lizenz

MIT License

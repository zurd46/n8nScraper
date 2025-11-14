# Intelligente Suche - n8n Nodes Explorer

Die n8n Nodes Explorer App verwendet eine **intelligente Suche** mit Synonym-Erweiterung und Relevanz-Ranking.

## Features

### 1. Synonym-Erweiterung

Die Suche erweitert automatisch deine Suchbegriffe mit relevanten Synonymen und verwandten Begriffen.

#### Beispiele:

**Suche nach "email"** findet automatisch:
- Gmail
- Outlook
- SMTP
- IMAP
- Mail-bezogene Nodes

**Suche nach "database"** findet:
- Postgres
- MySQL
- MongoDB
- SQL
- DB-bezogene Nodes

**Suche nach "ai"** findet:
- OpenAI
- Anthropic
- LangChain
- GPT
- Claude
- Gemini
- Alle KI-bezogenen Nodes

**Suche nach "chat"** findet:
- Slack
- Microsoft Teams
- Discord
- Telegram
- WhatsApp
- Messenger
- Alle Chat-Plattformen

**Suche nach "cloud"** findet:
- AWS (S3, Lambda, etc.)
- Azure
- Google Cloud Platform
- Storage-Dienste
- Drive, Dropbox, Box

### 2. Relevanz-Ranking

Die Suchergebnisse werden nach Relevanz sortiert:

**Scoring-System:**
- ✅ Exakte Übereinstimmung im Display Name: **+100 Punkte**
- ✅ Teilweise Übereinstimmung im Display Name: **+50 Punkte**
- ✅ Exakte Übereinstimmung im Node Type: **+80 Punkte**
- ✅ Teilweise Übereinstimmung im Node Type: **+30 Punkte**
- ✅ Übereinstimmung in der Description: **+10 Punkte**
- ✅ Ganzes Wort Match (Word Boundary): **+20 Punkte** (Display Name)
- ✅ Ganzes Wort Match (Word Boundary): **+15 Punkte** (Node Type)

Die relevantesten Ergebnisse erscheinen zuerst!

### 3. Vollständige Synonym-Liste

```python
'email': ['mail', 'gmail', 'outlook', 'smtp', 'imap']
'mail': ['email', 'gmail', 'outlook', 'smtp']
'calendar': ['schedule', 'event', 'appointment', 'google calendar']
'database': ['db', 'sql', 'postgres', 'mysql', 'mongodb']
'db': ['database', 'sql', 'postgres', 'mysql']
'sheet': ['spreadsheet', 'excel', 'google sheets', 'airtable']
'spreadsheet': ['sheet', 'excel', 'google sheets']
'storage': ['drive', 'dropbox', 'box', 's3', 'cloud']
'cloud': ['storage', 'drive', 'aws', 'azure', 'gcp']
'chat': ['slack', 'teams', 'discord', 'telegram', 'whatsapp', 'messenger']
'message': ['chat', 'sms', 'whatsapp', 'telegram']
'crm': ['salesforce', 'hubspot', 'pipedrive', 'zoho']
'payment': ['stripe', 'paypal', 'paddle']
'automation': ['workflow', 'trigger', 'cron', 'schedule']
'ai': ['openai', 'anthropic', 'langchain', 'gpt', 'claude', 'gemini']
'llm': ['ai', 'openai', 'anthropic', 'langchain', 'gpt']
'social': ['twitter', 'facebook', 'linkedin', 'instagram']
'document': ['doc', 'pdf', 'google docs', 'notion']
'form': ['typeform', 'google forms', 'jotform']
'video': ['youtube', 'vimeo']
'sms': ['twilio', 'message', 'text']
'webhook': ['http', 'api', 'trigger']
'api': ['http', 'rest', 'webhook']
'code': ['javascript', 'python', 'function']
'microsoft': ['outlook', 'teams', 'onedrive', 'excel', 'sharepoint']
'google': ['gmail', 'sheets', 'drive', 'calendar', 'docs']
'aws': ['s3', 'lambda', 'dynamodb', 'sns', 'sqs']
```

## Quick Search Buttons

Die App bietet Quick Search Buttons für häufige Suchen:

- 📧 **Email** - Alle E-Mail-bezogenen Nodes
- 💬 **Chat** - Alle Chat/Messaging Nodes
- 🤖 **AI** - Alle KI/LLM Nodes
- 💾 **Database** - Alle Datenbank Nodes
- ☁️ **Cloud** - Alle Cloud-Storage Nodes
- 💳 **Payment** - Alle Payment-Provider Nodes

## Verwendungsbeispiele

### Beispiel 1: E-Mail Nodes finden

```
Suche: "email"
```

**Ergebnisse (sortiert nach Relevanz):**
1. Gmail (exakte Übereinstimmung in Synonymen)
2. Microsoft Outlook (exakte Übereinstimmung in Synonymen)
3. SMTP (Protokoll-Match)
4. IMAP (Protokoll-Match)
5. Mailchimp (enthält "mail")
6. Mailgun (enthält "mail")
7. SendGrid (E-Mail in Description)

### Beispiel 2: Datenbank Nodes finden

```
Suche: "database"
```

**Ergebnisse:**
1. Postgres (Synonym)
2. MySQL (Synonym)
3. MongoDB (Synonym)
4. Microsoft SQL (Synonym)
5. Redis (Datenbank in Description)
6. QuestDB (enthält "db")
7. CrateDB (enthält "db")

### Beispiel 3: KI Nodes finden

```
Suche: "ai"
```

**Ergebnisse:**
1. OpenAI (exakte Übereinstimmung)
2. Anthropic (Synonym)
3. Google Gemini (Synonym)
4. LangChain Nodes (alle)
5. Mistral AI (enthält "ai")

### Beispiel 4: Microsoft Produkte finden

```
Suche: "microsoft"
```

**Ergebnisse:**
1. Microsoft Outlook
2. Microsoft Teams
3. Microsoft OneDrive
4. Microsoft Excel 365
5. Microsoft SharePoint
6. Microsoft Dynamics CRM
7. Microsoft To Do
8. Microsoft SQL

## Technische Details

### Algorithmus

1. **Term Expansion**: Suchbegriff wird mit Synonymen erweitert
2. **Pattern Matching**: Alle erweiterten Begriffe werden gegen Node Type, Display Name und Description geprüft
3. **Scoring**: Jeder Match erhält Punkte basierend auf Position und Art des Matches
4. **Ranking**: Ergebnisse werden nach Gesamt-Score sortiert
5. **Präsentation**: Top-Ergebnisse zuerst

### Performance

- **Suchzeit**: <100ms für vollständige Suche
- **Caching**: 60 Sekunden TTL für Datenbankabfragen
- **Clientseitig**: Keine zusätzlichen Server-Requests nach initialem Load

## Erweiterung

Du kannst eigene Synonyme hinzufügen in der Datei `n8n_nodes_app.py`:

```python
def expand_search_terms(search_term):
    synonyms = {
        'dein_begriff': ['synonym1', 'synonym2', 'synonym3'],
        # ... weitere Einträge
    }
```

## Verwendungstipps

1. **Kurze Begriffe verwenden**: "email" statt "e-mail integration"
2. **Kategorie-spezifische Begriffe**: "crm", "payment", "storage"
3. **Technologie-Namen**: "postgres", "slack", "aws"
4. **Funktions-Begriffe**: "trigger", "webhook", "schedule"
5. **Kombiniere mit Kategorie-Filter** für präzisere Ergebnisse

## Fallback

Wenn die intelligente Suche keine Ergebnisse liefert:
- Versuche allgemeinere Begriffe
- Nutze die Kategorie-Filter
- Suche nach Teilwörtern im Node-Type (z.B. "google" findet alle Google-Nodes)
- Verwende die Quick Search Buttons

## Feedback

Die Synonym-Liste wird kontinuierlich erweitert. Vorschläge sind willkommen!

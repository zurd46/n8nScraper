# AI-Powered Workflow Generation - Requirements

## Zusammenfassung

Um einen **KI-gestützten n8n Workflow Generator** zu bauen (z.B. mit OpenAI GPT-4), benötigen wir mehr Daten als aktuell in der Datenbank vorhanden sind.

---

## Was wir HABEN ✅

Unsere aktuelle Datenbank enthält:

```
- Node-Namen (z.B. "n8n-nodes-base.gmail")
- Display-Namen (z.B. "Gmail")
- Beschreibungen
- Kategorien (App, Trigger, Core, LangChain, Community)
- Versionen
- ~2,000 Nodes total
```

### Was die AI damit machen KANN:

- ✅ Empfehlen, welche Nodes für ein Problem relevant sind
- ✅ Einfache Workflows mit Platzhaltern erstellen
- ❌ **KEINE funktionierenden Workflows** (Parameter fehlen!)

---

## Was uns FEHLT ❌

### 1. Node Parameters (KRITISCH!)

Für jeden Node brauchen wir die **verfügbaren Felder**:

```json
{
  "node_type": "n8n-nodes-base.gmail",
  "operations": [
    {
      "resource": "message",
      "operation": "send",
      "parameters": [
        {
          "name": "to",
          "type": "string",
          "required": true,
          "description": "Email recipients (comma-separated)"
        },
        {
          "name": "subject",
          "type": "string",
          "required": true
        },
        {
          "name": "message",
          "type": "string",
          "required": true,
          "description": "Email body (HTML or text)"
        },
        {
          "name": "attachments",
          "type": "string",
          "required": false,
          "description": "Binary property name for attachments"
        }
      ]
    }
  ]
}
```

**Ohne diese Infos:** AI weiß nicht, wie man `to`, `subject`, `message` setzt!

### 2. Credentials

Welche Authentifizierung braucht der Node?

```json
{
  "node_type": "n8n-nodes-base.gmail",
  "credentials": [
    {
      "type": "gmailOAuth2",
      "required": true,
      "display_name": "Gmail OAuth2 API"
    }
  ]
}
```

### 3. Resource & Operations

Was kann der Node tun?

```json
{
  "node_type": "n8n-nodes-base.googleSheets",
  "resources": {
    "spreadsheet": ["append", "clear", "create", "delete", "get", "update"],
    "sheet": ["append", "clear", "create", "delete", "remove", "update"]
  }
}
```

### 4. Input/Output Schema

- Was erwartet der Node als Input?
- Was gibt der Node als Output zurück?

```json
{
  "node_type": "n8n-nodes-base.httpRequest",
  "output_schema": {
    "json": "object",
    "headers": "object",
    "statusCode": "number",
    "statusMessage": "string"
  }
}
```

**Wichtig für:** Node-Chaining (Output von Node A → Input von Node B)

### 5. Example Workflows

Typische Workflow-Patterns:

```json
{
  "use_case": "Send email when webhook received",
  "nodes": [
    {
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300]
    },
    {
      "type": "n8n-nodes-base.gmail",
      "position": [450, 300],
      "parameters": {
        "resource": "message",
        "operation": "send"
      }
    }
  ],
  "connections": {
    "Webhook": { "main": [[{ "node": "Gmail", "type": "main", "index": 0 }]] }
  }
}
```

---

## Wie bekommen wir diese Daten?

### Option 1: n8n Repository klonen (BESTE METHODE)

```bash
# 1. Clone n8n repo
git clone https://github.com/n8n-io/n8n.git

# 2. Node-Definitionen liegen hier:
cd n8n/packages/nodes-base/nodes/

# 3. Jeder Node hat eine .node.ts Datei mit allen Details
```

**Beispiel:** [Gmail.node.ts](https://github.com/n8n-io/n8n/blob/master/packages/nodes-base/nodes/Gmail/Gmail.node.ts)

```typescript
properties: [
  {
    displayName: 'Resource',
    name: 'resource',
    type: 'options',
    options: [
      { name: 'Draft', value: 'draft' },
      { name: 'Label', value: 'label' },
      { name: 'Message', value: 'message' }
    ],
    default: 'message'
  },
  {
    displayName: 'Operation',
    name: 'operation',
    type: 'options',
    displayOptions: {
      show: { resource: ['message'] }
    },
    options: [
      { name: 'Send', value: 'send' },
      { name: 'Get', value: 'get' },
      { name: 'Get All', value: 'getAll' }
    ]
  }
]
```

**Parser schreiben:**
- TypeScript (.node.ts) → JSON parsen
- `properties` Array extrahieren
- In SQL Tabellen speichern

### Option 2: n8n API direkt nutzen

```bash
# n8n hat eine interne API für Node-Definitionen
GET /types/nodes.json
```

**Vorteil:** Fertig strukturierte Daten
**Nachteil:** Nur für installierte Nodes

### Option 3: Dokumentation scrapen (LIMITIERT)

https://docs.n8n.io/integrations/builtin/app-nodes/

**Problem:** Nicht alle Parameter dokumentiert!

---

## Datenbank-Schema (erweiterter Vorschlag)

```sql
-- Node operations
CREATE TABLE node_operations (
    node_type TEXT,
    resource TEXT,
    operation TEXT,
    description TEXT,
    PRIMARY KEY (node_type, resource, operation)
);

-- Node parameters (für jede Operation)
CREATE TABLE node_parameters (
    node_type TEXT,
    resource TEXT,
    operation TEXT,
    parameter_name TEXT,
    parameter_type TEXT,  -- string, number, boolean, options, json
    required BOOLEAN,
    default_value TEXT,
    description TEXT,
    options TEXT,  -- JSON array für dropdowns
    PRIMARY KEY (node_type, resource, operation, parameter_name)
);

-- Node credentials
CREATE TABLE node_credentials (
    node_type TEXT,
    credential_type TEXT,
    required BOOLEAN,
    display_name TEXT,
    PRIMARY KEY (node_type, credential_type)
);

-- Example workflows
CREATE TABLE example_workflows (
    id INTEGER PRIMARY KEY,
    use_case TEXT,
    workflow_json TEXT,  -- Komplettes n8n Workflow JSON
    description TEXT,
    tags TEXT,  -- z.B. "email, automation, webhook"
    node_types_used TEXT  -- Komma-separierte Liste
);
```

---

## Was ist MINIMAL nötig?

Für **einfache Workflows** reichen:

1. **Node-Namen & Beschreibungen** ✅ (haben wir!)
2. **Operations Liste** (z.B. Gmail: send, get, getAll)
3. **Pflichtparameter** (z.B. `to`, `subject`, `message`)
4. **Credentials** (z.B. gmailOAuth2)

---

## Beispiel-Prompt für AI (mit aktuellen Daten)

```
User: "Erstelle einen Workflow, der bei jedem Webhook-Aufruf eine Email sendet"

AI mit aktueller DB:
{
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook"
    },
    {
      "name": "Gmail",
      "type": "n8n-nodes-base.gmail",
      "parameters": {
        "???": "???"  // ❌ AI weiß nicht welche Parameter!
      }
    }
  ]
}
```

## Beispiel-Prompt mit vollständigen Daten

```
User: "Erstelle einen Workflow, der bei jedem Webhook-Aufruf eine Email sendet"

AI mit vollständiger DB:
{
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "my-webhook",
        "httpMethod": "POST"
      }
    },
    {
      "name": "Gmail",
      "type": "n8n-nodes-base.gmail",
      "credentials": {
        "gmailOAuth2": "{{ $credentials.gmailOAuth2 }}"
      },
      "parameters": {
        "resource": "message",
        "operation": "send",
        "to": "{{ $json.email }}",
        "subject": "{{ $json.subject }}",
        "message": "{{ $json.body }}"
      }
    }
  ]
}
```

---

## Nächste Schritte

1. **n8n Repository klonen:**
   ```bash
   git clone https://github.com/n8n-io/n8n.git
   ```

2. **Parser für .node.ts Dateien schreiben**
   - TypeScript → JSON
   - Extrahiere `properties`, `credentials`, `resources`

3. **Datenbank erweitern:**
   - Tabellen: `node_operations`, `node_parameters`, `node_credentials`
   - Import: Parsed data

4. **AI Prompt Engineering:**
   - Context: Node-Definitionen
   - Output: n8n Workflow JSON
   - Validation: Schema-Check

5. **Testing:**
   - Einfache Workflows (Webhook → Email)
   - Komplexe Workflows (API → Transform → Database)

---

## Tools & Resources

- **n8n Repository:** https://github.com/n8n-io/n8n
- **n8n API Docs:** https://docs.n8n.io/api/
- **Workflow Schema:** https://docs.n8n.io/workflows/
- **TypeScript Parser:** `ts-morph` (npm package)

---

## Fazit

**Aktueller Stand:**
- ✅ Basis vorhanden (Node-Liste)
- ❌ Nicht genug für funktionierende Workflows

**Was fehlt:**
- Node-Parameter (kritisch!)
- Credentials
- Example Workflows

**Aufwand:**
- Parser schreiben: ~1-2 Tage
- Daten extrahieren: ~1 Tag
- AI Integration: ~2-3 Tage

**Resultat:**
- 🤖 AI kann funktionierende n8n Workflows generieren!

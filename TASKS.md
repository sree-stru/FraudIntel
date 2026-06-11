# 🛡️ FraudIntel — MASTER BUILD TASKS

## 28 Copy-Paste Prompts to Build the Entire Project

---

> ### 📌 HOW TO USE THIS FILE
>
> 1. **Execute prompts in EXACT order** — Prompt 1 → 2 → 3 → ... → 28
> 2. **Copy the entire prompt** (everything inside the code fence ```text ... ```) and paste it into the specified AI agent
> 3. **Wait for completion** before moving to the next prompt
> 4. **After every 5 prompts**, run a quick sanity check (open the files, make sure they exist)
> 5. **Do NOT skip prompts** — later prompts depend on earlier ones
> 6. **Estimated total time:** 10–14 hours across all prompts
>
> ### 🤖 AI AGENTS USED
>
> | Icon | Agent | When to Use |
> |------|-------|-------------|
> | 🤖 | **Antigravity / Gemini Code Assist / Cursor / Claude** | For all code generation prompts (copy-paste into your IDE AI chat) |
> | 🌐 | **Browser (Manual)** | For Google Cloud Console and MongoDB Atlas setup |
> | 💻 | **Terminal (You)** | For running commands directly |
>
> ### 📂 PROJECT LOCATION: `d:\FraudIntel`

---
---

## PHASE 0 — MANUAL PREREQUISITES

> ⚠️ Do these BEFORE starting any prompts. No AI agent needed — just follow the steps.

### Step 0A — Google Cloud Project (🌐 Browser)

1. Go to https://console.cloud.google.com
2. Create new project → name: `fraudintel`
3. Enable APIs: **Vertex AI API**, **Cloud Run API**, **Cloud Build API**, **Secret Manager API**
4. Note your **Project ID** (e.g., `fraudintel-123456`)

### Step 0B — MongoDB Atlas Cluster (🌐 Browser)

1. Go to https://cloud.mongodb.com → Sign up / Login
2. Create a **FREE M0 cluster** → name: `fraudintel-cluster`, region: `us-central1`
3. Create database user: choose a username & password
4. Network Access → Add IP: `0.0.0.0/0` (allows all — fine for hackathon)
5. Get connection string → **Copy it** (looks like `mongodb+srv://user:pass@cluster.mongodb.net/`)
6. Create a database named **`fraudintel`** (via Atlas UI → Browse Collections → Create Database)

### Step 0C — Local Environment (💻 Terminal)

```bash
cd d:\FraudIntel
python -m venv venv
venv\Scripts\activate
copy .env.example .env
```
Then **edit `.env`** and fill in your actual values for `GOOGLE_CLOUD_PROJECT`, `MONGODB_URI`, etc.

---
---

## PHASE 1 — PROJECT FOUNDATION (Prompts 1–3)

---

### ✅ PROMPT 1 of 28 — Python Dependencies & Git Config
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude (paste into IDE AI chat)

```text
I have a project at d:\FraudIntel. Create these 3 files exactly:

FILE 1: d:\FraudIntel\requirements.txt
Contents:
google-adk>=1.2.0
google-cloud-aiplatform>=1.74.0
google-generativeai>=0.8.0
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
python-dotenv>=1.0.0
pydantic>=2.10.0
pydantic-settings>=2.7.0
pymongo>=4.10.0
motor>=3.6.0
httpx>=0.28.0

FILE 2: d:\FraudIntel\pyproject.toml
A standard pyproject.toml with:
- [project] section: name="fraudintel", version="1.0.0", description="AI Fraud Investigation Agent - Multi-agent system powered by Gemini and MongoDB", requires-python=">=3.11"
- Include all dependencies from requirements.txt
- [project.scripts] section: fraudintel = "agent.main:main"

FILE 3: d:\FraudIntel\.gitignore
Standard Python gitignore that ignores: venv/, __pycache__/, *.pyc, *.pyo, .env (NOT .env.example), node_modules/, .idea/, .vscode/, *.egg-info/, dist/, build/, *.db, .DS_Store

Create ONLY these 3 files. Do not modify any existing files.
```

---

### ✅ PROMPT 2 of 28 — Core Configuration Module
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel. Create these 2 files:

FILE 1: d:\FraudIntel\agent\__init__.py
Just a docstring: """FraudIntel AI Agent System - Multi-agent fraud investigation platform."""

FILE 2: d:\FraudIntel\agent\config.py
A configuration module that:

1. Imports load_dotenv from python-dotenv and calls it at module level
2. Imports BaseSettings from pydantic_settings
3. Defines a Settings class (extends BaseSettings) with these fields and defaults:
   - google_cloud_project: str (no default — required)
   - google_cloud_location: str = "us-central1"
   - gemini_model: str = "gemini-3.0-flash"
   - mongodb_uri: str (no default — required)
   - mongodb_database: str = "fraudintel"
   - app_host: str = "0.0.0.0"
   - app_port: int = 8080
   - app_env: str = "development"
   - log_level: str = "INFO"
   - agent_timeout_seconds: int = 30
   - max_graph_depth: int = 4
   - vector_search_limit: int = 5
   
   model_config with env_file=".env" and env_file_encoding="utf-8" and extra="ignore"

4. Creates a singleton: settings = Settings()

5. Defines a constant COLLECTION_NAMES as a list:
   ["transactions", "customers", "entity_relationships", "investigations", "fraud_patterns", "alerts"]

6. Defines a constant FRAUD_TYPOLOGIES as a dictionary mapping 12 typology keys to their display names:
   {
     "account_takeover": "Account Takeover (ATO)",
     "synthetic_identity": "Synthetic Identity Fraud",
     "bust_out": "Bust-Out Scheme",
     "money_laundering": "Money Laundering",
     "cnp_fraud": "Card-Not-Present Fraud",
     "bec": "Business Email Compromise",
     "check_kiting": "Check Fraud / Kiting",
     "first_party_fraud": "First-Party Fraud",
     "app_fraud": "Authorized Push Payment Fraud",
     "structuring": "Structuring (Smurfing)",
     "mule_account": "Mule Account",
     "insider_threat": "Insider Threat"
   }

Use proper type hints and docstrings. Handle the case where .env file doesn't exist gracefully.
Create ONLY these 2 files.
```

---

### ✅ PROMPT 3 of 28 — Database Connection Module
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel with a config module at agent/config.py that exports `settings` (has fields: mongodb_uri, mongodb_database) and COLLECTION_NAMES (list of 6 collection names).

Create this file:

FILE: d:\FraudIntel\agent\database.py

A MongoDB connection module using the `motor` async driver (motor.motor_asyncio). It should:

1. Import AsyncIOMotorClient from motor.motor_asyncio
2. Import settings, COLLECTION_NAMES from agent.config
3. Import logging and set up a logger

4. Create a module-level variable `_client = None` and `_db = None`

5. Define function get_client() -> AsyncIOMotorClient:
   - Uses the module-level _client (lazy singleton)
   - Creates AsyncIOMotorClient(settings.mongodb_uri) on first call
   - Returns the client

6. Define function get_database():
   - Gets client via get_client()
   - Returns client[settings.mongodb_database]

7. Define function get_collection(name: str):
   - Returns get_database()[name]

8. Define async function check_connection() -> bool:
   - Tries to ping the database (await get_client().admin.command('ping'))
   - Returns True on success, False on exception
   - Logs the result

9. Define async function get_collection_stats() -> dict:
   - For each collection in COLLECTION_NAMES, counts documents
   - Returns dict like {"transactions": 500, "customers": 50, ...}
   - Handles errors gracefully (returns 0 count if collection doesn't exist)

10. Define async function ensure_indexes():
    - Creates these indexes (using create_index, ignore errors if they exist):
      * transactions: [("account_id", 1), ("timestamp", -1)]
      * transactions: [("device_fingerprint", 1)]
      * transactions: [("ip_address", 1)]
      * entity_relationships: [("entity_id", 1), ("linked_entity_id", 1)]
      * entity_relationships: [("entity_type", 1)]
      * alerts: [("status", 1), ("severity", -1), ("created_at", -1)]
      * investigations: [("case_id", 1)] with unique=True
      * investigations: [("status", 1)]
    - Wrap each in try/except, log errors, continue on failure

11. Define async function close_connection():
    - Closes the client if it exists
    - Sets _client and _db back to None

Use proper error handling with try/except and logging throughout.
Create ONLY this 1 file.
```

---
---

## PHASE 2 — SEED DATA (Prompts 4–5)

---

### ✅ PROMPT 4 of 28 — Fraud Pattern & Scenario JSON Files
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel. Create these 3 files:

FILE 1: d:\FraudIntel\data\__init__.py
Just an empty file with docstring: """FraudIntel seed data and sample scenarios."""

FILE 2: d:\FraudIntel\data\fraud_patterns.json
A JSON array of 12 fraud pattern objects. Each object has these fields:
- "pattern_id": "PAT-001" through "PAT-012"
- "typology": one of: account_takeover, synthetic_identity, bust_out, money_laundering, cnp_fraud, bec, check_kiting, first_party_fraud, app_fraud, structuring, mule_account, insider_threat
- "name": Human-readable name (e.g., "Account Takeover Attack")
- "description": 2-3 realistic sentences about this fraud type
- "risk_weight": integer 1-10
- "indicators": array of 5 specific detection signals as strings (e.g., "New device login within 24 hours of password reset")
- "detection_rules": {"velocity_threshold": number, "amount_threshold": number, "time_window_hours": number}
- "example_scenario": 1 sentence realistic example

Make all 12 entries realistic with proper financial crime terminology.

FILE 3: d:\FraudIntel\data\sample_scenarios.json
A JSON array of 3 demo scenarios:

SCENARIO 1 — "The Bust-Out Ring" (HIGH RISK, expected score: 78):
- 4 linked accounts (ACC-001 to ACC-004) sharing 2 devices and 1 VPN IP
- Pattern: credit build-up then rapid extraction
- Include accounts array, key_transactions array (5-6 transactions), entity_links array, expected_findings array

SCENARIO 2 — "Account Takeover" (CRITICAL, expected score: 91):
- Single account ACC-010 with new device + password reset + $25,000 wire transfer
- Geographic impossibility: New York login then London 10 min later
- Include same structure as above

SCENARIO 3 — "Legitimate Travel" (LOW RISK, expected score: 15):
- Customer ACC-030 with consistent travel history, purchases in Paris matching their profile
- All transactions match behavioral baseline
- False positive case

Each scenario: scenario_id, name, description, risk_level, expected_risk_score, expected_classification, accounts, key_transactions, entity_links, expected_findings.
Use realistic 2026 dates, proper amounts, plausible names.

Create ONLY these 3 files.
```

---

### ✅ PROMPT 5 of 28 — Database Seed Script
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel with:
- agent/config.py (exports settings with mongodb_uri and mongodb_database)
- data/fraud_patterns.json (12 fraud patterns)
- data/sample_scenarios.json (3 demo scenarios)

Create this file:

FILE: d:\FraudIntel\data\seed_data.py

A database seeder script runnable with: python -m data.seed_data
Uses pymongo (SYNC driver, not motor) since this is a one-time script.

The script should:

1. Load MONGODB_URI from .env file using python-dotenv
2. Connect using pymongo.MongoClient
3. Access the "fraudintel" database
4. Print a banner: "🛡️ FraudIntel Database Seeder"
5. Ask for confirmation before dropping existing data (or just print a warning and proceed)
6. Drop all 6 collections: transactions, customers, entity_relationships, investigations, fraud_patterns, alerts

Then seed each collection:

A) CUSTOMERS (50 documents):
- Generate CUS-001 to CUS-050 with realistic names from a hardcoded list of 50 names
- Each has: customer_id, name, email (name-based), phone (+1-555-XXXX), accounts (list with one ACC-XXX matching customer number)
- kyc: {verified: True for most, False for 5 suspicious ones, verification_date, documents: ["passport", "utility_bill"]}
- risk_profile: {score: random 5-40 for most, 60-90 for 5 suspicious, category: based on score, last_updated}
- behavioral_baseline: {avg_monthly_transactions: random 5-30, avg_transaction_amount: random 100-5000, typical_merchants: pick 3 from ["grocery","retail","dining","travel","electronics","gas"], typical_geo: ["New York, US"]}
- account_created_at: random date in 2024-2025, but for 5 suspicious ones in Jan 2026

B) TRANSACTIONS (500 documents):
- Generate for accounts ACC-001 to ACC-050
- Each transaction: transaction_id (TXN-2026-XXXXXX with 6 random digits), account_id, type (random from wire_transfer/ach/card_purchase/atm_withdrawal/deposit/internal_transfer), amount (random $10-$5000, but include some $8000-$50000 for suspicious), currency "USD", direction (inbound/outbound), counterparty {name: random, account: random, institution: random bank name}
- timestamp: spread across Jan-Mar 2026
- device_fingerprint: DFP-XXX (generate 20 unique fingerprints, reuse them)
- ip_address: generate 30 unique IPs, some normal, some VPN (45.33.X.X range)
- geo: {lat, lng, city, country} — pick from 5 US cities plus some international
- risk_flags: empty array
- merchant_category: random from [retail, grocery, crypto, gambling, travel, electronics, dining, gas, utilities]
- embedding: list of 128 random floats between -1 and 1

IMPORTANT suspicious patterns to embed:
- ACC-001 to ACC-004: share device DFP-RING1 and IP 45.33.32.100 (fraud ring)
- ACC-010: sudden large wire transfers ($25000) with new device DFP-ATO1
- ACC-020 to ACC-022: circular transfers between each other (money laundering)
- ACC-040 to ACC-044: multiple deposits just under $10000 (structuring)

C) ENTITY_RELATIONSHIPS (300+ documents):
- Link every account to 1-3 devices, 1-2 IPs, 1 phone, 1 email
- For each link: entity_id, entity_type, linked_entity_id, linked_entity_type, relationship_type (uses_device/logged_from_ip/registered_phone/registered_email/transacted_with_merchant), first_seen, last_seen, strength (0.5-1.0)
- FRAUD RINGS — Create specific shared links:
  * ACC-001,002,003,004 all share device DFP-RING1 and IP 45.33.32.100
  * ACC-010,011 share phone +1-555-0199 and email ring2@tempmail.com
  * ACC-020,021,022 share IP 192.168.50.1

D) FRAUD_PATTERNS (12 documents):
- Load from data/fraud_patterns.json
- Add an "embedding" field to each: list of 128 random floats between -1 and 1

E) ALERTS (20 documents):
- alert_id: ALT-2026-0001 to ALT-2026-0020
- source: random from [transaction_monitor, rule_engine, ml_model, manual_report]
- severity: 5 critical, 5 high, 5 medium, 5 low
- trigger_rule: random from [velocity_anomaly, large_transfer, geo_impossible, device_anomaly, structuring_pattern, new_account_risk]
- related_entities: [1-2 account IDs]
- status: 5 "new", 5 "investigating", 5 "resolved", 5 "false_positive"
- created_at: dates in March 2026
- Link 5 "new" alerts to the suspicious accounts (ACC-001, ACC-010, ACC-020, ACC-040, ACC-044)

F) INVESTIGATIONS (5 documents):
- INV-2026-0538 to INV-2026-0542
- Status: 2 "resolved", 2 "under_investigation", 1 "pending_review"
- fraud_score: varying scores
- evidence: basic dict with {accounts_reviewed: N, transactions_analyzed: N}
- timeline: array of 3-5 timeline event dicts {timestamp, event, description}
- network_map: {nodes: [{id, type}], edges: [{source, target}]}
- sar_draft: null for most, a short string for the critical one
- audit_trail: array of 2-3 entries {timestamp, action, agent, description}
- INV-2026-0542 should be the "bust-out ring" case (ACC-001 to ACC-004) with score 78

7. After seeding, print summary: collection name → document count for each
8. Close the connection

Use proper imports: pymongo, json, random, datetime, os, pathlib.
Set random.seed(42) for reproducible data.
Use if __name__ == "__main__": block.

Create ONLY this 1 file. It will be long but should be a single complete file.
```

---
---

## PHASE 3 — AGENT TOOLS (Prompts 6–8)

---

### ✅ PROMPT 6 of 28 — MongoDB Query Tools
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel with:
- agent/config.py: exports `settings` (has mongodb_uri, mongodb_database, max_graph_depth)
- MongoDB database "fraudintel" with collections: transactions, customers, entity_relationships, investigations, fraud_patterns, alerts

Create these 2 files:

FILE 1: d:\FraudIntel\agent\tools\__init__.py
Docstring: """FraudIntel agent tool functions for MongoDB operations, scoring, and investigation utilities."""

FILE 2: d:\FraudIntel\agent\tools\mongodb_tools.py

This file defines Python functions that ADK agents will call as tools. Use pymongo SYNC driver (not motor) because ADK tool functions work best as regular sync functions.

At the top:
- import pymongo, logging, json, datetime
- from bson import ObjectId, json_util
- from agent.config import settings

Create a module-level MongoClient and database:
_client = pymongo.MongoClient(settings.mongodb_uri)
_db = _client[settings.mongodb_database]

Define a helper function _serialize(doc) that converts a MongoDB document to a JSON-safe dict:
- Convert ObjectId to str
- Convert datetime to isoformat string
- Handle nested dicts and lists recursively
- Return the cleaned dict

Now define these 12 tool functions. EACH function MUST have a detailed docstring (Google ADK uses docstrings as the tool description for the LLM). EACH function must have complete type hints. EACH function must use try/except and return a sensible default on error (never crash).

1. get_account_transactions(account_id: str, limit: int = 50) -> list:
   """Retrieve transaction history for a specific account from the database. Returns a list of transaction records sorted by timestamp (newest first)."""
   Query transactions collection, sort by timestamp desc, limit results, serialize and return.

2. get_customer_profile(account_id: str) -> dict:
   """Retrieve the customer profile associated with a given account ID. Returns customer details including KYC status, risk profile, and behavioral baseline."""
   Find in customers where accounts array contains account_id. Return serialized doc or empty dict.

3. get_entity_network(entity_id: str, max_depth: int = 3) -> dict:
   """Discover the network of related entities using graph traversal. Finds all accounts, devices, IPs, and other entities connected to the given entity within the specified depth. Uses MongoDB $graphLookup for recursive relationship traversal."""
   Run aggregate pipeline on entity_relationships:
   [
     {"$match": {"entity_id": entity_id}},
     {"$graphLookup": {"from": "entity_relationships", "startWith": "$linked_entity_id", "connectFromField": "linked_entity_id", "connectToField": "entity_id", "maxDepth": max_depth, "depthField": "hop_count", "as": "network"}},
   ]
   Return {"root_entity": entity_id, "network_size": N, "nodes": [...], "max_depth_reached": max_hop}

4. get_alert_details(alert_id: str) -> dict:
   """Retrieve full details of a specific fraud alert by its alert ID."""
   Find by alert_id, serialize, return.

5. search_fraud_history(entity_ids: list) -> list:
   """Search for previous fraud investigations involving any of the given entity IDs. Returns summaries of past investigations for correlation analysis."""
   Query investigations where any value in related entity fields matches. Return list of summaries.

6. get_transaction_velocity(account_id: str, hours: int = 24) -> dict:
   """Calculate transaction velocity metrics for an account over a specified time window. Returns transaction count, total amount, and average amount."""
   Query transactions for account within last N hours.
   Return {"account_id": str, "period_hours": int, "transaction_count": int, "total_amount": float, "avg_amount": float, "transactions": [...]}

7. get_linked_accounts_by_device(device_fingerprint: str) -> list:
   """Find all accounts that have used a specific device. Useful for detecting shared device fraud patterns."""
   Query entity_relationships where entity_type="device" and entity_id matches or linked_entity_id matches.
   Return list of account IDs.

8. get_linked_accounts_by_ip(ip_address: str) -> list:
   """Find all accounts that have logged in from a specific IP address. Useful for detecting shared IP fraud patterns."""
   Similar to above but for IP type.

9. save_investigation(case_data: dict) -> str:
   """Save or update an investigation case in the database. Creates a new case or updates an existing one based on case_id."""
   Upsert into investigations collection using case_id.
   Return the case_id.

10. append_audit_trail(case_id: str, action: str, agent_name: str, description: str) -> bool:
    """Append an entry to the audit trail of an investigation case. Records agent actions for compliance and transparency."""
    Push to audit_trail array. Include timestamp. Return True/False.

11. get_pending_alerts(limit: int = 10) -> list:
    """Retrieve pending alerts that need investigation, sorted by severity (critical first) and recency."""
    Find alerts with status "new", sort by severity desc + created_at desc.

12. update_alert_status(alert_id: str, new_status: str) -> bool:
    """Update the status of a fraud alert (e.g., from 'new' to 'investigating' or 'resolved')."""
    Update the status field. Return True/False.

Create ONLY these 2 files.
```

---

### ✅ PROMPT 7 of 28 — Risk Scoring Tools
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel. Create this file:

FILE: d:\FraudIntel\agent\tools\scoring_tools.py

Risk scoring tool functions — pure Python computation (no database calls). These take data as input and return scores/classifications.

Define these 3 functions with detailed docstrings and type hints:

1. calculate_fraud_risk_score(evidence: dict) -> dict:
   """Calculate a composite fraud risk score (0-100) based on collected evidence. Evaluates multiple risk factors including transaction patterns, device anomalies, network connections, and behavioral deviations. Returns detailed scoring breakdown with factor-by-factor explanation."""
   
   The evidence dict may contain keys: transactions (list), customer (dict), velocity (dict), network (dict), device_info (dict), geo_info (dict).
   
   Scoring factors — check each and add/subtract points:
   - vpn_proxy_detected (+18): Check if any IP in evidence starts with "45.33" or customer has is_vpn flag
   - multiple_accounts_same_device (+15): Check if network has >1 account linked to same device
   - kyc_mismatch (+12): Check if customer.kyc.verified is False
   - velocity_anomaly (+14): Check if velocity.transaction_count > 5 in 24h
   - high_risk_merchant (+11): Check if any transaction merchant_category in ["crypto", "gambling"]
   - large_unusual_transfer (+10): Check if any transaction amount > 3x customer.behavioral_baseline.avg_transaction_amount (default 2000 if missing)
   - geo_impossibility (+16): Check if geo_info has impossible_travel flag
   - new_account (+8): Check if customer account_created_at is within 90 days
   - new_device (+7): Check if device_info.first_seen within 7 days
   - fraud_ring_connection (+20): Check if network has any node with risk_level "confirmed_fraud" or "flagged"
   - clean_history (-5): Check if no prior fraud flags exist
   - verified_phone (-3): Check if customer has verified phone
   - consistent_behavior (-4): Check if transactions match behavioral baseline
   
   For each factor, store: {"name": str, "points": int, "triggered": bool, "reason": str}
   
   Clamp total between 0 and 100.
   
   Classification: 0-25 "low_risk", 26-50 "medium_risk", 51-75 "high_risk", 76-100 "critical_risk"
   Confidence: 0.5 + (number_of_factors_evaluated / 26) — capped at 1.0
   Recommended action: low→"approve", medium→"monitor", high→"escalate", critical→"freeze"
   
   Return: {"total_score": int, "classification": str, "confidence": float, "factors": list, "recommended_action": str, "factors_triggered": int, "factors_total": int}

2. classify_fraud_typology(indicators: list) -> dict:
   """Match detected indicators against known fraud typologies to identify the most likely type of fraud. Returns top matching typologies with confidence scores."""
   
   Load patterns from d:\FraudIntel\data\fraud_patterns.json
   For each pattern, calculate how many of the input indicators match the pattern's indicators list (fuzzy string matching — just check if any indicator keyword appears in any pattern indicator).
   Score = matched_count / total_pattern_indicators * 100
   
   Return: {"primary_typology": {"name": str, "match_score": float, "description": str}, "secondary_matches": [top 2 more], "indicators_matched": int, "indicators_total": int}
   
   Handle case where no match found — return "Unknown" typology.

3. generate_risk_summary(score_result: dict, typology_result: dict) -> str:
   """Generate a human-readable risk assessment summary combining the fraud risk score and typology classification. Suitable for inclusion in investigation reports."""
   
   Build a paragraph like:
   "Risk Assessment Summary: The investigation revealed a [classification] risk level with a composite score of [score]/100 (Confidence: [X]%). The primary fraud typology identified is [typology] ([match]% match). Key contributing factors include: [list top 3 triggered factors]. Recommended action: [action]."
   
   Return the string.

Handle all errors gracefully — never crash. Use try/except with logging.
Create ONLY this 1 file.
```

---

### ✅ PROMPT 8 of 28 — Investigation Utility Tools
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel. Create this file:

FILE: d:\FraudIntel\agent\tools\investigation_tools.py

Investigation utility functions for timeline building, network graphing, SAR generation, and report formatting.

Import: datetime, random, logging, json

Define these 5 functions with detailed docstrings and type hints:

1. build_investigation_timeline(transactions: list, alerts: list, logins: list = None) -> list:
   """Build a unified, chronological investigation timeline from multiple data sources. Merges transactions, alerts, and login events into a single sorted timeline with severity classifications."""
   
   For each transaction: create entry with timestamp, event_type="transaction", description=f"{tx['type']} of ${tx['amount']} ({tx['direction']})", severity based on amount (>10000="critical", >5000="warning", else "info")
   For each alert: create entry with timestamp=alert["created_at"], event_type="alert", description=f"Alert: {alert['trigger_rule']} - {alert['severity']}", severity=alert["severity"]
   For logins (if provided): event_type="login", severity="info"
   
   Sort all entries by timestamp ascending.
   Return list of dicts: [{"timestamp": iso_string, "event_type": str, "description": str, "severity": str, "details": dict}]

2. build_network_graph(relationships: list) -> dict:
   """Transform raw entity relationship data into a graph structure suitable for D3.js force-directed visualization. Creates nodes and edges with visual properties."""
   
   Extract unique nodes from relationships (both entity_id and linked_entity_id).
   For each node: {"id": str, "type": str (from entity_type/linked_entity_type), "label": str (same as id), "risk_level": "clean" (default)}
   For each relationship: {"source": entity_id, "target": linked_entity_id, "relationship": relationship_type, "strength": strength}
   
   Calculate stats: total_nodes, total_edges, unique_entity_types
   
   Return: {"nodes": [...], "edges": [...], "stats": {"total_nodes": int, "total_edges": int, "unique_types": int}}

3. generate_sar_narrative(investigation: dict) -> str:
   """Generate a FinCEN-compliant Suspicious Activity Report (SAR) draft narrative from investigation findings. This is a DRAFT that requires human analyst review before submission."""
   
   Build a multi-paragraph narrative:
   
   Paragraph 1 (Opening): "This SAR is being filed to report suspected [typology if available, else 'suspicious financial activity'] involving [subject/account]. The activity was identified on [date] through [source]."
   
   Paragraph 2 (Activity Summary): Summarize the key transactions, amounts, dates from investigation.evidence
   
   Paragraph 3 (Indicators): List the fraud indicators detected
   
   Paragraph 4 (Network): Describe connected entities if network analysis was performed
   
   Paragraph 5 (Conclusion): "Based on the investigation, the activity presents a [risk_level] risk with a score of [score]/100. Recommended action: [action]."
   
   Footer: "STATUS: DRAFT — Requires human analyst review before submission to FinCEN. Generated by FraudIntel AI Investigation Agent."
   
   Return the narrative as a formatted string.

4. generate_case_id() -> str:
   """Generate a unique investigation case ID in the format INV-2026-XXXX."""
   Return f"INV-2026-{random.randint(1000, 9999)}"

5. format_investigation_report(case_id: str, evidence: dict, risk_score: dict, timeline: list, network: dict, sar_narrative: str = None) -> dict:
   """Compile all investigation components into a structured investigation report document. Returns a complete report ready for storage and display."""
   
   Build executive_summary from risk_score data (2-3 sentences).
   Extract key_findings from risk_score.factors where triggered=True (list of strings).
   Extract fraud_indicators similarly.
   
   Return dict:
   {
     "case_id": case_id,
     "timestamp": datetime.utcnow().isoformat(),
     "status": "pending_review",
     "executive_summary": str,
     "evidence_collected": evidence,
     "key_findings": [str],
     "fraud_indicators": [str],
     "relationship_analysis": network,
     "timeline": timeline,
     "risk_assessment": risk_score,
     "recommended_actions": [risk_score.get("recommended_action", "investigate")],
     "confidence_level": "High" if risk_score.get("confidence",0) > 0.8 else "Medium" if > 0.6 else "Low",
     "sar_draft": sar_narrative,
     "fraud_score": risk_score.get("total_score", 0),
     "classification": risk_score.get("classification", "unknown")
   }

Handle all errors gracefully. Create ONLY this 1 file.
```

---
---

## PHASE 4 — AI SUB-AGENTS (Prompts 9–13)

---

### ✅ PROMPT 9 of 28 — System Prompts for All Agents
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel. Create these 2 files:

FILE 1: d:\FraudIntel\agent\prompts\__init__.py
Docstring: """System prompts for FraudIntel AI agents."""

FILE 2: d:\FraudIntel\agent\prompts\system_prompts.py

Define 6 string constants — one system prompt for each agent. Each prompt should be 200-400 words, professional, and specific about which tools to use.

ORCHESTRATOR_PROMPT = """You are FraudIntel, an AI Fraud Investigation Lead. You coordinate comprehensive fraud investigations by delegating tasks to specialized sub-agents.

When you receive a fraud alert, account ID, or investigation request:
1. Determine the investigation scope — identify the target account(s) and alert details
2. Delegate evidence collection to the Evidence Gatherer agent
3. Once evidence is collected, send it to the Risk Scorer for fraud probability assessment
4. Have the Auditor review all findings for gaps and contradictions
5. Check compliance requirements through the Compliance Agent
6. Generate the final investigation report

Guidelines:
- Never assume fraud without evidence. Distinguish facts from assumptions.
- Explain your reasoning at every step. Show supporting evidence.
- Maintain a complete audit trail of all actions taken.
- Present findings objectively and transparently.
- Recommend actions proportional to the evidence strength.
- You are an investigator, not a judge. Your role is to present evidence, not make final decisions.

When communicating results, structure your response with clear sections: Summary, Key Findings, Risk Assessment, and Recommended Actions."""

EVIDENCE_GATHERER_PROMPT = """You are the Evidence Gatherer agent for FraudIntel. Your job is to collect ALL relevant data for a fraud investigation from the MongoDB database.

When given an account ID or alert to investigate:
1. Retrieve the full transaction history using get_account_transactions
2. Get the customer profile using get_customer_profile
3. Calculate transaction velocity using get_transaction_velocity
4. Find accounts sharing the same device using get_linked_accounts_by_device
5. Find accounts sharing the same IP using get_linked_accounts_by_ip
6. Map the complete entity network using get_entity_network
7. Search for prior fraud history using search_fraud_history

Be thorough and systematic. Collect everything available. Report both what you found AND what data was missing or unavailable. Organize your findings by category: transactions, customer profile, device analysis, network connections, and historical flags.

Never filter or prejudge the data. Collect it all and let the analysis agents draw conclusions."""

RISK_SCORER_PROMPT = """You are the Risk Scorer agent for FraudIntel. Your job is to analyze collected evidence and calculate a fraud risk score.

When you receive evidence data:
1. Use the calculate_fraud_risk_score tool with the complete evidence data
2. Use classify_fraud_typology to identify the type of fraud
3. Use generate_risk_summary to create a human-readable assessment

Evaluate every scoring factor carefully. For each factor that contributes to the score, explain WHY it was triggered and what specific evidence supports it. Be precise — every point in the score must be justified with evidence.

Present your results clearly: Total Score, Classification (Low/Medium/High/Critical), Top Contributing Factors, Fraud Typology Match, and Confidence Level."""

COMPLIANCE_AGENT_PROMPT = """You are the Compliance Agent for FraudIntel. Your role is to evaluate investigation findings against regulatory requirements (BSA/AML/FinCEN).

When you receive investigation findings:
1. Determine if the findings warrant filing a Suspicious Activity Report (SAR)
   - SAR threshold: transactions over $5,000 with suspicious indicators
   - Multiple related transactions that individually fall below thresholds but collectively exceed them
2. If SAR is warranted, use generate_sar_narrative to create a draft narrative
3. Flag any regulatory concerns (structuring, money laundering indicators, sanctions matches)
4. Use save_investigation to update the case with compliance findings
5. Use append_audit_trail to log your compliance review

Remember: You ADVISE — the human analyst makes the final filing decision. Always mark SAR narratives as DRAFT requiring human review. Never auto-file."""

AUDITOR_PROMPT = """You are the Auditor agent for FraudIntel. Your job is to challenge the investigation's findings and identify weaknesses.

When you receive the investigation evidence and risk score:
1. Review all evidence for completeness — is anything missing?
2. Look for contradictory evidence that might lower the risk score
3. Consider alternative explanations (legitimate business activity, travel, etc.)
4. Check if the risk score factors are properly justified
5. Identify any logical gaps in the investigation chain

Rate your confidence in the overall findings (0-100%). If confidence is below 85%, explain what additional investigation is needed.

You are the devil's advocate. Your job is to ensure the investigation is thorough and fair, preventing false positives while not missing real fraud."""

REPORT_GENERATOR_PROMPT = """You are the Report Generator agent for FraudIntel. Your job is to compile all investigation findings into a comprehensive, professional report.

When you receive the complete investigation data:
1. Use generate_case_id to create a unique case identifier
2. Use build_investigation_timeline to create a chronological event timeline
3. Use build_network_graph to prepare the entity relationship visualization
4. Use format_investigation_report to compile the complete report
5. Use save_investigation to store the report in the database
6. Use append_audit_trail to log the report generation

Structure the report with clear sections: Executive Summary, Evidence Collected, Key Findings, Fraud Indicators, Relationship Analysis, Timeline, Risk Assessment, Recommended Actions, and Confidence Level.

Write for a compliance officer audience — be clear, factual, and avoid jargon."""

Create ONLY these 2 files.
```

---

### ✅ PROMPT 10 of 28 — Evidence Gatherer Sub-Agent
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel using Google ADK. Create these 2 files:

FILE 1: d:\FraudIntel\agent\sub_agents\__init__.py
Docstring: """FraudIntel specialized sub-agents for fraud investigation."""

FILE 2: d:\FraudIntel\agent\sub_agents\evidence_gatherer.py

The Evidence Gatherer sub-agent using Google ADK (Agent Development Kit).

Code:
```python
"""Evidence Gatherer Sub-Agent — Collects all relevant investigation data from MongoDB."""

from google.adk.agents import LlmAgent
from agent.tools.mongodb_tools import (
    get_account_transactions,
    get_customer_profile,
    get_entity_network,
    get_transaction_velocity,
    get_linked_accounts_by_device,
    get_linked_accounts_by_ip,
    search_fraud_history,
    get_alert_details,
)
from agent.prompts.system_prompts import EVIDENCE_GATHERER_PROMPT
from agent.config import settings

evidence_gatherer_agent = LlmAgent(
    name="evidence_gatherer",
    model=settings.gemini_model,
    instruction=EVIDENCE_GATHERER_PROMPT,
    description="Collects and organizes evidence for fraud investigations by querying the MongoDB database for transactions, customer profiles, device fingerprints, and entity networks.",
    tools=[
        get_account_transactions,
        get_customer_profile,
        get_entity_network,
        get_transaction_velocity,
        get_linked_accounts_by_device,
        get_linked_accounts_by_ip,
        search_fraud_history,
        get_alert_details,
    ],
)
```

Write this EXACTLY as shown. In Google ADK, regular Python functions are automatically converted to tools using their docstrings and type hints. Create ONLY these 2 files.
```

---

### ✅ PROMPT 11 of 28 — Risk Scorer Sub-Agent
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel using Google ADK. Create this file:

FILE: d:\FraudIntel\agent\sub_agents\risk_scorer.py

```python
"""Risk Scorer Sub-Agent — Analyzes evidence and calculates composite fraud risk scores."""

from google.adk.agents import LlmAgent
from agent.tools.scoring_tools import (
    calculate_fraud_risk_score,
    classify_fraud_typology,
    generate_risk_summary,
)
from agent.prompts.system_prompts import RISK_SCORER_PROMPT
from agent.config import settings

risk_scorer_agent = LlmAgent(
    name="risk_scorer",
    model=settings.gemini_model,
    instruction=RISK_SCORER_PROMPT,
    description="Analyzes collected evidence and calculates composite fraud risk scores with full explainability, identifying fraud typologies and generating risk summaries.",
    tools=[
        calculate_fraud_risk_score,
        classify_fraud_typology,
        generate_risk_summary,
    ],
)
```

Write this EXACTLY as shown. Create ONLY this 1 file.
```

---

### ✅ PROMPT 12 of 28 — Compliance & Auditor Sub-Agents
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel using Google ADK. Create these 2 files:

FILE 1: d:\FraudIntel\agent\sub_agents\compliance_agent.py

```python
"""Compliance Agent — Evaluates regulatory requirements and generates SAR drafts."""

from google.adk.agents import LlmAgent
from agent.tools.investigation_tools import generate_sar_narrative
from agent.tools.mongodb_tools import save_investigation, append_audit_trail
from agent.prompts.system_prompts import COMPLIANCE_AGENT_PROMPT
from agent.config import settings

compliance_agent = LlmAgent(
    name="compliance_agent",
    model=settings.gemini_model,
    instruction=COMPLIANCE_AGENT_PROMPT,
    description="Evaluates investigation findings against BSA/AML/FinCEN regulatory requirements and generates SAR draft narratives when warranted.",
    tools=[
        generate_sar_narrative,
        save_investigation,
        append_audit_trail,
    ],
)
```

FILE 2: d:\FraudIntel\agent\sub_agents\auditor_agent.py

```python
"""Auditor Agent — Challenges investigation findings and identifies evidence gaps."""

from google.adk.agents import LlmAgent
from agent.tools.mongodb_tools import (
    get_account_transactions,
    search_fraud_history,
    get_entity_network,
)
from agent.prompts.system_prompts import AUDITOR_PROMPT
from agent.config import settings

auditor_agent = LlmAgent(
    name="auditor_agent",
    model=settings.gemini_model,
    instruction=AUDITOR_PROMPT,
    description="Reviews investigation findings, challenges assumptions, identifies contradictory evidence, and rates confidence in the overall assessment.",
    tools=[
        get_account_transactions,
        search_fraud_history,
        get_entity_network,
    ],
)
```

Write both files EXACTLY as shown. Create ONLY these 2 files.
```

---

### ✅ PROMPT 13 of 28 — Report Generator Sub-Agent
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel using Google ADK. Create this file:

FILE: d:\FraudIntel\agent\sub_agents\report_generator.py

```python
"""Report Generator Sub-Agent — Compiles investigation findings into comprehensive reports."""

from google.adk.agents import LlmAgent
from agent.tools.investigation_tools import (
    format_investigation_report,
    build_investigation_timeline,
    build_network_graph,
    generate_case_id,
)
from agent.tools.mongodb_tools import save_investigation, append_audit_trail
from agent.prompts.system_prompts import REPORT_GENERATOR_PROMPT
from agent.config import settings

report_generator_agent = LlmAgent(
    name="report_generator",
    model=settings.gemini_model,
    instruction=REPORT_GENERATOR_PROMPT,
    description="Compiles all investigation components into structured reports with executive summaries, timelines, network graphs, and recommended actions.",
    tools=[
        format_investigation_report,
        build_investigation_timeline,
        build_network_graph,
        generate_case_id,
        save_investigation,
        append_audit_trail,
    ],
)
```

Write this EXACTLY as shown. Create ONLY this 1 file.
```

---
---

## PHASE 5 — ORCHESTRATOR (Prompts 14–15)

---

### ✅ PROMPT 14 of 28 — Main Orchestrator Agent
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel using Google ADK with these sub-agents already created:
- agent/sub_agents/evidence_gatherer.py → evidence_gatherer_agent
- agent/sub_agents/risk_scorer.py → risk_scorer_agent
- agent/sub_agents/auditor_agent.py → auditor_agent
- agent/sub_agents/compliance_agent.py → compliance_agent
- agent/sub_agents/report_generator.py → report_generator_agent
- agent/prompts/system_prompts.py → ORCHESTRATOR_PROMPT
- agent/config.py → settings (has gemini_model field)

Create this file:

FILE: d:\FraudIntel\agent\orchestrator.py

The main orchestrator that coordinates all sub-agents using ADK's SequentialAgent.

```python
"""
FraudIntel Orchestrator — Main agent that coordinates the multi-agent investigation pipeline.

Agent Hierarchy:
  fraudintel_agent (LlmAgent — Entry Point)
    └── investigation_pipeline (SequentialAgent)
        ├── evidence_gatherer_agent (LlmAgent)
        ├── risk_scorer_agent (LlmAgent)
        ├── auditor_agent (LlmAgent)
        ├── compliance_agent (LlmAgent)
        └── report_generator_agent (LlmAgent)
"""

from google.adk.agents import LlmAgent, SequentialAgent
from agent.sub_agents.evidence_gatherer import evidence_gatherer_agent
from agent.sub_agents.risk_scorer import risk_scorer_agent
from agent.sub_agents.compliance_agent import compliance_agent
from agent.sub_agents.auditor_agent import auditor_agent
from agent.sub_agents.report_generator import report_generator_agent
from agent.prompts.system_prompts import ORCHESTRATOR_PROMPT
from agent.config import settings


# Sequential pipeline: Evidence → Risk Score → Audit → Compliance → Report
investigation_pipeline = SequentialAgent(
    name="investigation_pipeline",
    description="Executes the full fraud investigation pipeline sequentially: evidence collection, risk scoring, audit review, compliance check, and report generation.",
    sub_agents=[
        evidence_gatherer_agent,
        risk_scorer_agent,
        auditor_agent,
        compliance_agent,
        report_generator_agent,
    ],
)

# Main entry-point agent that users interact with
fraudintel_agent = LlmAgent(
    name="fraudintel",
    model=settings.gemini_model,
    instruction=ORCHESTRATOR_PROMPT,
    description="FraudIntel - AI Fraud Investigation Agent. Investigates suspicious financial activity using a multi-agent orchestration pipeline with evidence collection, risk scoring, compliance review, and report generation.",
    sub_agents=[investigation_pipeline],
)


def get_agent() -> LlmAgent:
    """Returns the main FraudIntel agent for use with ADK Runner or API integration."""
    return fraudintel_agent
```

Write this EXACTLY as shown. Create ONLY this 1 file.
```

---

### ✅ PROMPT 15 of 28 — Agent CLI Entry Point
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel with:
- agent/orchestrator.py: exports get_agent() function returning the main ADK LlmAgent
- agent/database.py: exports check_connection(), get_collection_stats(), ensure_indexes()
- agent/config.py: exports settings

Create this file:

FILE: d:\FraudIntel\agent\main.py

Entry point for running FraudIntel agent interactively. Run with: python -m agent.main

The file should:
1. Import asyncio, logging, sys
2. Import Runner from google.adk.runners
3. Import InMemorySessionService from google.adk.sessions
4. Import types from google.genai
5. Import get_agent from agent.orchestrator
6. Import check_connection, get_collection_stats from agent.database
7. Import settings from agent.config

Define an async function main():
   a) Set up logging with settings.log_level
   b) Print banner:
      ╔═══════════════════════════════════════════╗
      ║  🛡️  FraudIntel Investigation Agent        ║
      ║  AI-Powered Fraud Investigation System     ║
      ╚═══════════════════════════════════════════╝
   c) Print settings: Model={settings.gemini_model}, DB={settings.mongodb_database}
   d) Check MongoDB: connected = await check_connection()
      If not connected, print error and exit
   e) Print collection stats: stats = await get_collection_stats()
      Print each collection name and count
   f) Create session service and runner:
      session_service = InMemorySessionService()
      agent = get_agent()
      runner = Runner(agent=agent, app_name="fraudintel", session_service=session_service)
   g) Create session:
      session = await session_service.create_session(app_name="fraudintel", user_id="investigator")
   h) Print: "Ready! Type your investigation request. Type 'quit' to exit."
   i) Print example: "Example: Investigate account ACC-001 for suspicious activity"
   j) Interactive loop:
      while True:
          try:
              user_input = input("\n🔍 Investigator > ").strip()
              if not user_input:
                  continue
              if user_input.lower() in ("quit", "exit", "q"):
                  print("👋 FraudIntel shutting down.")
                  break
              content = types.Content(role="user", parts=[types.Part(text=user_input)])
              print("\n⏳ Investigating...")
              async for event in runner.run_async(
                  user_id="investigator",
                  session_id=session.id,
                  new_message=content
              ):
                  if event.is_final_response():
                      if event.content and event.content.parts:
                          for part in event.content.parts:
                              if part.text:
                                  print(f"\n🛡️ FraudIntel:\n{part.text}")
          except KeyboardInterrupt:
              print("\n👋 Investigation interrupted.")
              break
          except Exception as e:
              logging.error(f"Error: {e}")
              print(f"\n❌ Error: {e}")

At the bottom:
if __name__ == "__main__":
    asyncio.run(main())

Create ONLY this 1 file.
```

---
---

## PHASE 6 — API BACKEND (Prompts 16–18)

---

### ✅ PROMPT 16 of 28 — Pydantic API Schemas
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel. Create these 3 files:

FILE 1: d:\FraudIntel\api\__init__.py
Docstring: """FraudIntel REST API."""

FILE 2: d:\FraudIntel\api\models\__init__.py
Docstring: """API data models."""

FILE 3: d:\FraudIntel\api\models\schemas.py

Pydantic v2 models for the REST API. Use from pydantic import BaseModel, Field. Use from typing import Optional.

Define these models:

1. InvestigationRequest(BaseModel):
   alert_id: Optional[str] = None
   account_id: Optional[str] = None
   query: str = Field(..., description="Natural language investigation request or account ID to investigate")

2. InvestigationResponse(BaseModel):
   case_id: str
   status: str
   fraud_score: Optional[int] = None
   classification: Optional[str] = None
   summary: str
   timestamp: str
   network_size: Optional[int] = None
   sar_required: Optional[bool] = None

3. AlertResponse(BaseModel):
   alert_id: str
   source: str
   severity: str
   trigger_rule: str
   related_entities: list[str] = []
   status: str
   created_at: str

4. CaseResponse(BaseModel):
   case_id: str
   status: str
   fraud_score: Optional[int] = None
   classification: Optional[str] = None
   executive_summary: Optional[str] = None
   evidence_summary: Optional[str] = None
   key_findings: Optional[list[str]] = None
   timeline: Optional[list[dict]] = None
   network_map: Optional[dict] = None
   sar_draft: Optional[str] = None
   audit_trail: Optional[list[dict]] = None
   recommended_actions: Optional[list[str]] = None
   confidence_level: Optional[str] = None
   created_at: Optional[str] = None
   updated_at: Optional[str] = None

5. DashboardStats(BaseModel):
   total_cases: int = 0
   active_investigations: int = 0
   pending_alerts: int = 0
   high_risk_cases: int = 0
   resolved_cases: int = 0
   avg_fraud_score: float = 0.0
   cases_today: int = 0

6. NetworkGraphData(BaseModel):
   nodes: list[dict] = []
   edges: list[dict] = []
   stats: dict = {}

7. HealthResponse(BaseModel):
   status: str
   mongodb_connected: bool
   collections: dict = {}
   version: str = "1.0.0"

Create ONLY these 3 files.
```

---

### ✅ PROMPT 17 of 28 — API Route Handlers
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel with:
- api/models/schemas.py: Pydantic models (InvestigationRequest, InvestigationResponse, AlertResponse, CaseResponse, DashboardStats, NetworkGraphData, HealthResponse)
- agent/tools/mongodb_tools.py: Functions (get_account_transactions, get_customer_profile, get_entity_network, get_transaction_velocity, get_linked_accounts_by_device, get_linked_accounts_by_ip, search_fraud_history, get_alert_details, get_pending_alerts, save_investigation, append_audit_trail, update_alert_status)
- agent/tools/scoring_tools.py: Functions (calculate_fraud_risk_score, classify_fraud_typology, generate_risk_summary)
- agent/tools/investigation_tools.py: Functions (build_investigation_timeline, build_network_graph, generate_sar_narrative, generate_case_id, format_investigation_report)

Create these 2 files:

FILE 1: d:\FraudIntel\api\routes\__init__.py
Docstring: """API route modules."""

FILE 2: d:\FraudIntel\api\routes\investigations.py

A FastAPI APIRouter with prefix="/api" that handles investigation and data endpoints.

Import: APIRouter, HTTPException, from typing import Optional
Import all schemas from api.models.schemas
Import tool functions from agent.tools.mongodb_tools, scoring_tools, investigation_tools
Import datetime, logging

router = APIRouter(prefix="/api", tags=["Investigations"])

Define these endpoints:

1. POST /api/investigate → InvestigationResponse
   Takes InvestigationRequest body.
   Implementation (simplified for hackathon — direct tool calls, no ADK runner):
   a) Extract account_id from request (from account_id field or parse from query string)
   b) If no account_id found, return error
   c) Call get_account_transactions(account_id)
   d) Call get_customer_profile(account_id)
   e) Call get_transaction_velocity(account_id)
   f) Build evidence dict: {"transactions": txns, "customer": customer, "velocity": velocity}
   g) Call get_entity_network(account_id) — add to evidence as "network"
   h) Call calculate_fraud_risk_score(evidence)
   i) Call classify_fraud_typology(list of triggered factor names from risk score)
   j) Call generate_risk_summary(risk_score, typology)
   k) Call build_investigation_timeline(transactions, [])
   l) Call build_network_graph(network.get("nodes", []))
   m) case_id = generate_case_id()
   n) If risk_score["total_score"] >= 50: sar = generate_sar_narrative(evidence) else sar = None
   o) Call format_investigation_report(case_id, evidence, risk_score, timeline, network_graph, sar)
   p) Call save_investigation(report)
   q) Return InvestigationResponse with case_id, status, fraud_score, classification, summary, timestamp

2. GET /api/cases → list[CaseResponse]
   Query params: status: Optional[str] = None, limit: int = 20
   Query investigations collection directly using pymongo (import from agent/tools/mongodb_tools the _db reference, or create a direct query)
   Actually better: use the mongodb_tools module-level _db. Add this import at top:
   from agent.tools.mongodb_tools import _db
   Filter by status if provided, sort by created_at desc, limit.
   Serialize and return.

3. GET /api/cases/{case_id} → CaseResponse
   Find investigation by case_id. Return 404 if not found.

4. GET /api/alerts → list[AlertResponse]
   Query params: status: Optional[str], severity: Optional[str], limit: int = 20
   Query alerts collection. Filter, sort, limit, serialize, return.

5. GET /api/alerts/{alert_id} → AlertResponse
   Find alert by alert_id. 404 if not found.

6. POST /api/alerts/{alert_id}/investigate → InvestigationResponse
   Read the alert, get related_entities[0] as account_id, then run the same investigation logic as POST /api/investigate.

7. GET /api/network/{entity_id} → NetworkGraphData
   Call get_entity_network(entity_id).
   If network has nodes, call build_network_graph on the relationships.
   Return NetworkGraphData.

8. GET /api/timeline/{case_id} → list[dict]
   Find investigation, return its timeline field. 404 if not found.

Each endpoint: use try/except, return proper HTTPException on errors. Use the _serialize helper from mongodb_tools (import it) or handle ObjectId/datetime conversion inline.

Create ONLY these 2 files.
```

---

### ✅ PROMPT 18 of 28 — FastAPI Main Server + Dashboard Route
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel with:
- api/routes/investigations.py: router with /api/* endpoints
- api/models/schemas.py: HealthResponse, DashboardStats
- agent/database.py: check_connection(), get_collection_stats(), ensure_indexes(), close_connection()
- agent/config.py: settings

Create these 2 files:

FILE 1: d:\FraudIntel\api\routes\dashboard.py

FastAPI router for dashboard-specific endpoints:

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

Endpoints:

A) GET /api/dashboard/stats → DashboardStats
   Query MongoDB directly (import _db from agent.tools.mongodb_tools):
   - total_cases: count investigations
   - active_investigations: count investigations where status="under_investigation"
   - pending_alerts: count alerts where status="new"
   - high_risk_cases: count investigations where fraud_score >= 70
   - resolved_cases: count investigations where status="resolved"
   - avg_fraud_score: average of fraud_score across all investigations (use aggregate with $avg)
   - cases_today: count investigations created today
   Return DashboardStats. Handle errors, return zeros on failure.

B) GET /api/dashboard/recent-activity → list[dict]
   Fetch last 10 alerts + last 10 investigation updates.
   Merge them, sort by timestamp desc, return top 20.
   Each entry: {"type": "alert"|"investigation", "timestamp": str, "description": str, "severity": str, "id": str}

FILE 2: d:\FraudIntel\api\server.py

Main FastAPI application. Run with: uvicorn api.server:app --host 0.0.0.0 --port 8080

```python
"""FraudIntel API Server — Main FastAPI application."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from api.routes.investigations import router as investigations_router
from api.routes.dashboard import router as dashboard_router
from agent.database import check_connection, get_collection_stats, ensure_indexes, close_connection
from agent.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=getattr(logging, settings.log_level))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    logger.info("🛡️ FraudIntel API starting up...")
    connected = await check_connection()
    if connected:
        logger.info("✅ MongoDB connected")
        await ensure_indexes()
        stats = await get_collection_stats()
        logger.info(f"📊 Collections: {stats}")
    else:
        logger.warning("⚠️ MongoDB not connected — some features will be unavailable")
    yield
    # Shutdown
    await close_connection()
    logger.info("👋 FraudIntel API shut down")


app = FastAPI(
    title="FraudIntel API",
    description="AI Fraud Investigation Agent — Multi-agent system for financial fraud investigation powered by Gemini and MongoDB",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes (register BEFORE static files)
app.include_router(investigations_router)
app.include_router(dashboard_router)


@app.get("/api", tags=["Root"])
async def api_root():
    """API information and available endpoints."""
    return {
        "name": "FraudIntel API",
        "version": "1.0.0",
        "description": "AI Fraud Investigation Agent",
        "endpoints": {
            "investigate": "POST /api/investigate",
            "cases": "GET /api/cases",
            "alerts": "GET /api/alerts",
            "network": "GET /api/network/{entity_id}",
            "dashboard_stats": "GET /api/dashboard/stats",
            "health": "GET /api/health",
        },
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    connected = await check_connection()
    stats = await get_collection_stats() if connected else {}
    return {
        "status": "healthy" if connected else "degraded",
        "mongodb_connected": connected,
        "collections": stats,
        "version": "1.0.0",
    }


# Static files — Mount LAST so API routes take priority
dashboard_dir = Path(__file__).parent.parent / "dashboard"
if dashboard_dir.exists():
    app.mount("/", StaticFiles(directory=str(dashboard_dir), html=True), name="dashboard")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.server:app", host=settings.app_host, port=settings.app_port, reload=True)
```

Write server.py EXACTLY as shown above. Create ONLY these 2 files.
```

---
---

## PHASE 7 — DASHBOARD FRONTEND (Prompts 19–22)

---

### ✅ PROMPT 19 of 28 — Dashboard HTML
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel. Create this file:

FILE: d:\FraudIntel\dashboard\index.html

A modern, premium, dark-mode investigation dashboard. Single HTML file with these sections:

HEAD:
- Title: "FraudIntel — AI Fraud Investigation Dashboard"
- Meta description: "AI-powered fraud investigation agent with real-time network analysis, risk scoring, and SAR generation"
- Google Fonts: Inter (weights 300,400,500,600,700)
- D3.js v7 from CDN: <script src="https://d3js.org/d3.v7.min.js"></script>
- Link to css/styles.css
- Viewport meta for responsive

BODY:

1. HEADER (<header>):
   - Logo: "🛡️ FraudIntel" (h1 with class "logo")
   - Search input (id="search-input", placeholder="Search cases, accounts, alerts...")
   - Notification badge: bell icon + span with count (id="notification-count")

2. STATS BAR (<section id="stats-bar">):
   Four stat cards in a row, each with:
   - Card 1: id="stat-active-cases" — label "Active Cases", value "—"
   - Card 2: id="stat-pending-alerts" — label "Pending Alerts", value "—"
   - Card 3: id="stat-high-risk" — label "High Risk", value "—"
   - Card 4: id="stat-avg-score" — label "Avg Score", value "—"

3. MAIN CONTENT (<main>) — two-column layout:

   LEFT SIDEBAR (<aside id="sidebar">):
   - Button: id="btn-new-investigation", text "+ New Investigation", class="btn-primary"
   - Case list container: <div id="case-queue"></div>
   - Each case will be dynamically inserted as cards

   RIGHT PANEL (<section id="main-panel">):
   - Tab bar with 4 buttons:
     <button class="tab active" data-tab="network">Network</button>
     <button class="tab" data-tab="timeline">Timeline</button>
     <button class="tab" data-tab="report">Report</button>
     <button class="tab" data-tab="sar">SAR Draft</button>
   - Tab content panels (only one visible at a time):
     <div id="tab-network" class="tab-content active"><div id="network-graph">Select a case to view network</div></div>
     <div id="tab-timeline" class="tab-content"><div id="investigation-timeline">Select a case to view timeline</div></div>
     <div id="tab-report" class="tab-content"><div id="investigation-report">Select a case to view report</div></div>
     <div id="tab-sar" class="tab-content"><div id="sar-draft">Select a case to view SAR draft</div></div>

4. ALERT FEED (<section id="alert-section">):
   - Heading: "🚨 Live Alerts"
   - Container: <div id="alert-feed"></div>

5. MODAL (<div id="investigation-modal" class="modal hidden">):
   - Overlay backdrop
   - Modal content box:
     - Title: "🔍 New Investigation"
     - Input: id="investigation-input", placeholder="Enter account ID (e.g., ACC-001) or describe what to investigate"
     - Button: id="btn-start-investigation", text "Start Investigation"
     - Loading area: id="investigation-progress", class="hidden" — shows "⏳ Investigating..." with progress messages
     - Close button (×)

6. TOAST CONTAINER: <div id="toast-container"></div>

Scripts at bottom:
<script src="js/network-graph.js"></script>
<script src="js/app.js"></script>

Use semantic HTML5 tags. Give ALL interactive elements unique IDs. Use proper ARIA labels for accessibility.
Create ONLY this 1 file.
```

---

### ✅ PROMPT 20 of 28 — Dashboard CSS
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel with dashboard/index.html already created. Create this file:

FILE: d:\FraudIntel\dashboard\css\styles.css

A premium, stunning, dark-mode CSS file. The user must be WOWED at first glance.

Design system using CSS variables:

:root {
  --bg-primary: #0a0e1a;
  --bg-secondary: #0f1425;
  --bg-card: rgba(18, 22, 43, 0.85);
  --bg-card-hover: rgba(25, 30, 55, 0.95);
  --border-subtle: rgba(59, 130, 246, 0.12);
  --border-glow: rgba(59, 130, 246, 0.4);
  --text-primary: #e2e8f0;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --accent-blue: #3b82f6;
  --accent-red: #ef4444;
  --accent-amber: #f59e0b;
  --accent-green: #22c55e;
  --accent-purple: #8b5cf6;
  --radius: 12px;
  --radius-sm: 8px;
  --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

Style EVERY element in the HTML. Include:

1. Reset + base styles: box-sizing border-box, Inter font, smooth scrolling, custom dark scrollbar
2. Header: sticky, glassmorphism (backdrop-filter: blur(20px)), z-index 100, logo with gradient text (blue to purple), search with glow on focus, notification badge pulsing
3. Stats bar: 4-column CSS Grid, gap 16px. Each card: glassmorphism background, subtle border, hover translateY(-2px) + shadow glow, large bold number, small muted label
4. Main layout: CSS Grid with 320px sidebar + 1fr main, gap 20px, padding 20px
5. Sidebar: .btn-primary with gradient blue background, hover glow, rounded. Case queue scrollable (max-height calc(100vh - 300px)). Case cards with left-border color by risk (critical=red, high=amber, medium=blue, low=green), risk score pill badge, hover scale(1.01), active case with glowing border
6. Tabs: horizontal flex, tab buttons with padding, border-bottom 3px transparent, active tab blue underline + brighter text, hover dim blue
7. Tab content: .tab-content hidden (display none), .tab-content.active shown. #network-graph min-height 450px. Placeholder text centered and muted
8. Timeline: vertical left-border line (gradient blue), timeline entries with colored dot, content card, alternating subtle bg
9. Report: formatted sections with left accent border, .report-section styling, key findings as styled list
10. SAR: monospace font area, "DRAFT" watermark style, copy button absolute top-right
11. Alert feed: horizontal scrolling or vertical list, severity dots (pulsing for critical), "Investigate" mini buttons
12. Modal: .modal full-screen overlay with rgba(0,0,0,0.7) backdrop, .modal.hidden display none. Modal content centered, glassmorphism, max-width 500px, slide-in animation. Input large rounded, button gradient blue
13. Toast: fixed top-right, toast cards with colored left border, fade+slide animation, auto-dismiss
14. Animations: @keyframes fadeIn, slideUp, pulse, gradientShift
15. Responsive: @media (max-width: 768px) stack sidebar/main vertically
16. Utility: .hidden {display:none}, .risk-critical/.risk-high/.risk-medium/.risk-low color classes, .glass-card base class, .badge pill class

Make this CSS production-quality, visually stunning. Every hover, transition, and color must feel premium.
Create ONLY this 1 file.
```

---

### ✅ PROMPT 21 of 28 — Dashboard JavaScript (Main App)
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel with dashboard/index.html and dashboard/css/styles.css already created. The HTML has these IDs: search-input, notification-count, stat-active-cases, stat-pending-alerts, stat-high-risk, stat-avg-score, btn-new-investigation, case-queue, network-graph, investigation-timeline, investigation-report, sar-draft, alert-feed, investigation-modal, investigation-input, btn-start-investigation, investigation-progress, toast-container. Tab buttons have data-tab attributes: network, timeline, report, sar. Tab content divs: tab-network, tab-timeline, tab-report, tab-sar.

The API endpoints are:
- GET /api/health
- GET /api/dashboard/stats → {total_cases, active_investigations, pending_alerts, high_risk_cases, avg_fraud_score, cases_today, resolved_cases}
- GET /api/cases → list of case objects
- GET /api/cases/{case_id} → single case with all fields
- GET /api/alerts → list of alert objects
- POST /api/investigate → body {query: str, account_id: str} → InvestigationResponse
- GET /api/network/{entity_id} → {nodes, edges, stats}
- GET /api/timeline/{case_id} → list of timeline events
- POST /api/alerts/{alert_id}/investigate → InvestigationResponse

Create this file:

FILE: d:\FraudIntel\dashboard\js\app.js

Vanilla JavaScript (no frameworks). Structure as a self-contained module.

Implement ALL of these functions:

1. API helper:
   const API = { async get(url), async post(url, body) } — fetch with error handling, returns JSON

2. initDashboard() — called on DOMContentLoaded:
   - Call loadStats(), loadCases(), loadAlerts()
   - Set interval to refresh every 30 seconds

3. loadStats() — GET /api/dashboard/stats, update the 4 stat card values

4. loadCases() — GET /api/cases, call renderCaseQueue(cases)

5. renderCaseQueue(cases) — populate #case-queue:
   For each case create a clickable card div with:
   - case_id text
   - risk score badge (colored by classification: critical=red, high=amber, medium=blue, low=green)
   - status text
   - Click handler: selectCase(case_id)

6. selectCase(caseId) — highlight the case in sidebar, call loadCaseDetail(caseId)

7. loadCaseDetail(caseId):
   - GET /api/cases/{caseId} → populate report tab, SAR tab
   - GET /api/network/{first account from case} → call renderNetworkGraph(data)
   - GET /api/timeline/{caseId} → call renderTimeline(events)
   - Activate the network tab

8. renderNetworkGraph(graphData) — use the FraudNetworkGraph class from network-graph.js:
   const graph = new FraudNetworkGraph('network-graph');
   graph.render(graphData);

9. renderTimeline(events) — build vertical timeline in #investigation-timeline:
   For each event: create a div with colored dot (by severity), timestamp, description, details

10. renderReport(caseData) — populate #investigation-report:
    Show: executive_summary, key_findings (bulleted list), fraud_indicators, risk score gauge (colored bar from 0-100), recommended_actions, confidence_level

11. renderSAR(sarText) — populate #sar-draft:
    If sarText: show formatted text with "Copy" button
    If null: show "No SAR required for this case"

12. loadAlerts() — GET /api/alerts, populate #alert-feed:
    For each alert: severity dot + timestamp + description + "Investigate" button
    Investigate button calls investigateAlert(alert_id)

13. setupTabs() — tab click handlers:
    Click a tab → add "active" class to that tab button + show matching tab-content, hide others

14. setupModal():
    - btn-new-investigation click → show modal
    - Close button / overlay click / Escape → hide modal
    - btn-start-investigation click → startInvestigation()

15. startInvestigation():
    - Get input value from investigation-input
    - Show progress area with "⏳ Collecting evidence..."
    - POST /api/investigate with {query: inputValue, account_id: inputValue}
    - On success: hide modal, showToast("Investigation complete!", "success"), reload cases, select the new case
    - On error: showToast("Investigation failed", "error")

16. investigateAlert(alertId):
    - POST /api/alerts/{alertId}/investigate
    - On success: reload, select new case
    - On error: show toast

17. showToast(message, type="info"):
    - Create toast div in #toast-container
    - Types: success=green, error=red, info=blue, warning=amber
    - Auto-remove after 4 seconds
    - Slide-in animation

18. Utility functions:
    - formatTimeAgo(dateStr) → "2h ago", "3d ago", "just now"
    - getRiskColor(classification) → CSS color string
    - getRiskClass(classification) → CSS class name

At bottom:
document.addEventListener('DOMContentLoaded', () => {
    initDashboard();
    setupTabs();
    setupModal();
});

Create ONLY this 1 file. Make all the functions complete and working.
```

---

### ✅ PROMPT 22 of 28 — D3.js Network Graph Module
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel with a dashboard at dashboard/index.html that has a container div with id="network-graph". D3.js v7 is loaded from CDN. The dashboard uses a dark theme (background #0a0e1a, text #e2e8f0).

Create this file:

FILE: d:\FraudIntel\dashboard\js\network-graph.js

A self-contained FraudNetworkGraph class for D3.js force-directed graph visualization.

class FraudNetworkGraph:

  constructor(containerId):
    - Store containerId
    - Store reference to the DOM container
    - Initialize simulation, svg, etc. as null

  render(graphData):
    graphData format: { nodes: [{id, type, label, risk_level}], edges: [{source, target, relationship, strength}], stats: {} }
    
    a) Clear any existing SVG in the container
    b) Get container dimensions
    c) Create SVG with viewBox, responsive sizing
    d) Add zoom behavior (d3.zoom) to a <g> group
    e) Define node colors by type:
       account: #3b82f6, device: #f59e0b, ip: #ef4444, phone: #8b5cf6, email: #06b6d4, merchant: #22c55e, default: #64748b
    f) Define node radius by type:
       account: 22, device: 18, ip: 16, phone: 15, email: 15, merchant: 18, default: 14
    g) Create edges as <line> elements:
       stroke: #334155, stroke-width based on strength (1 + strength * 3), stroke-opacity: 0.6
    h) Create nodes as <circle> elements (or <rect> for devices):
       fill by type color, stroke: #1e293b, stroke-width: 2
       If risk_level is "flagged" or "confirmed_fraud": add red stroke (#ef4444), stroke-width 3
       If risk_level is "suspicious": add amber stroke (#f59e0b)
    i) Add labels as <text> elements below nodes:
       text: node.label (truncate if >12 chars), fill: #94a3b8, font-size: 10px, text-anchor: middle
    j) Create force simulation:
       d3.forceSimulation(nodes)
         .force("link", d3.forceLink(edges).id(d => d.id).distance(100))
         .force("charge", d3.forceManyBody().strength(-200))
         .force("center", d3.forceCenter(width/2, height/2))
         .force("collision", d3.forceCollide().radius(30))
       On tick: update line x1,y1,x2,y2 and circle cx,cy and text x,y
    k) Add drag behavior to nodes:
       On drag start: restart simulation with alpha 0.3
       On drag: update node position
       On drag end: release
    l) Add hover effects:
       On mouseenter: increase node radius, show tooltip, highlight connected edges
       On mouseleave: reset radius, hide tooltip, reset edges
    m) Create a tooltip div (absolute positioned, glass-card style with dark bg):
       Shows: Entity Type, Entity ID, Risk Level, Connections count

  clear():
    Remove SVG, stop simulation

  highlightNode(nodeId):
    Highlight a specific node and its connections, dim everything else

  resetHighlight():
    Reset all nodes and edges to normal

Make sure the graph looks stunning on the dark background. Use smooth transitions. Node connections should be clearly visible. Add a subtle glow effect on high-risk nodes.

At bottom: window.FraudNetworkGraph = FraudNetworkGraph;

Create ONLY this 1 file.
```

---
---

## PHASE 8 — DEPLOYMENT (Prompts 23–24)

---

### ✅ PROMPT 23 of 28 — Docker Configuration
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel. Create these 2 files:

FILE 1: d:\FraudIntel\Dockerfile

Multi-stage Docker build for the FraudIntel application:

FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    npm install -g mongodb-mcp-server && \
    apt-get purge -y curl && apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*
COPY --from=builder /install /usr/local
WORKDIR /app
COPY agent/ ./agent/
COPY api/ ./api/
COPY dashboard/ ./dashboard/
COPY data/ ./data/
EXPOSE 8080
ENV PORT=8080
CMD ["python", "-m", "uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8080"]

FILE 2: d:\FraudIntel\deploy\cloudbuild.yaml

Google Cloud Build configuration:

steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/fraudintel:$SHORT_SHA', '-t', 'gcr.io/$PROJECT_ID/fraudintel:latest', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/fraudintel:$SHORT_SHA']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/fraudintel:latest']
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args: ['run', 'deploy', 'fraudintel', '--image=gcr.io/$PROJECT_ID/fraudintel:$SHORT_SHA', '--region=us-central1', '--platform=managed', '--allow-unauthenticated', '--memory=1Gi', '--timeout=300', '--set-env-vars=APP_ENV=production']
images: ['gcr.io/$PROJECT_ID/fraudintel:$SHORT_SHA', 'gcr.io/$PROJECT_ID/fraudintel:latest']
timeout: '900s'

Create ONLY these 2 files.
```

---

### ✅ PROMPT 24 of 28 — Deployment Script
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel. Create this file:

FILE: d:\FraudIntel\deploy\deploy.sh

A bash deployment script for Google Cloud Run:

#!/bin/bash
set -e
echo ""
echo "🛡️  FraudIntel — Google Cloud Run Deployment"
echo "============================================="
echo ""

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
REGION="us-central1"
SERVICE_NAME="fraudintel"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "📋 Configuration:"
echo "   Project:  ${PROJECT_ID}"
echo "   Region:   ${REGION}"
echo "   Service:  ${SERVICE_NAME}"
echo ""

echo "📦 Building Docker image..."
docker build -t ${IMAGE_NAME}:latest .

echo "⬆️  Pushing to Container Registry..."
docker push ${IMAGE_NAME}:latest

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME}:latest \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --timeout 300 \
  --set-env-vars "APP_ENV=production,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION}"

URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo "🌐 Application URL: ${URL}"
echo ""
echo "🧪 Test endpoints:"
echo "   Health:    ${URL}/api/health"
echo "   Stats:     ${URL}/api/dashboard/stats"
echo "   Dashboard: ${URL}/"
echo ""

Create ONLY this 1 file.
```

---
---

## PHASE 9 — TESTING & POLISH (Prompts 25–28)

---

### ✅ PROMPT 25 of 28 — Setup Verification Script
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel. Create this file:

FILE: d:\FraudIntel\test_setup.py

A verification script runnable with: python test_setup.py
It checks that everything is properly set up.

The script should:

1. Print "🛡️ FraudIntel — Setup Verification" header
2. Check Python version >= 3.11 — print ✅ or ❌
3. Try importing key packages one by one (each in try/except):
   - google.adk → print ✅ Google ADK
   - google.generativeai → print ✅ Google GenAI
   - fastapi → print ✅ FastAPI
   - uvicorn → print ✅ Uvicorn
   - pymongo → print ✅ PyMongo
   - motor → print ✅ Motor
   - pydantic → print ✅ Pydantic
   - dotenv → print ✅ python-dotenv
   - httpx → print ✅ HTTPX
   For any failure: print ❌ with error message

4. Check .env file exists at d:\FraudIntel\.env — ✅ or ❌ with "Copy .env.example to .env"

5. Try loading settings from agent.config — ✅ or ❌

6. Check MongoDB connection:
   - Import pymongo, try connecting and pinging
   - If success: print ✅ MongoDB connected
   - Print each collection name and document count
   - If fail: print ❌ with error

7. Check if all required directories exist:
   - agent/, agent/tools/, agent/sub_agents/, agent/prompts/
   - api/, api/routes/, api/models/
   - dashboard/, dashboard/css/, dashboard/js/
   - data/, deploy/
   For each: ✅ exists or ❌ missing

8. Check if key files exist:
   - agent/orchestrator.py
   - agent/main.py
   - api/server.py
   - dashboard/index.html
   - dashboard/css/styles.css
   - dashboard/js/app.js
   - dashboard/js/network-graph.js
   - data/seed_data.py
   - data/fraud_patterns.json
   - Dockerfile
   For each: ✅ or ❌

9. Print summary: "X/Y checks passed"
10. If all pass: "🎉 FraudIntel is ready! Run: python -m uvicorn api.server:app --port 8080"
    If some fail: "⚠️ Fix the issues above before running"

Use if __name__ == "__main__": block.
Create ONLY this 1 file.
```

---

### ✅ PROMPT 26 of 28 — Fix All Imports & Missing Init Files
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel. Please do the following checks and fixes:

1. Ensure ALL these __init__.py files exist (create if missing — each just needs a docstring):
   - d:\FraudIntel\agent\__init__.py
   - d:\FraudIntel\agent\tools\__init__.py
   - d:\FraudIntel\agent\sub_agents\__init__.py
   - d:\FraudIntel\agent\prompts\__init__.py
   - d:\FraudIntel\api\__init__.py
   - d:\FraudIntel\api\models\__init__.py
   - d:\FraudIntel\api\routes\__init__.py
   - d:\FraudIntel\data\__init__.py

2. Check every Python file for import errors:
   - Open each .py file in agent/, api/, and data/
   - Verify all imports reference modules that actually exist
   - Fix any circular imports
   - Fix any wrong module paths

3. Verify dashboard file references:
   - Check that index.html links to css/styles.css (not /css/styles.css)
   - Check that index.html links to js/app.js and js/network-graph.js
   - Check that D3.js CDN URL is correct and uses https

4. Verify API route paths match what app.js expects:
   - /api/dashboard/stats
   - /api/cases
   - /api/cases/{case_id}
   - /api/alerts
   - /api/investigate
   - /api/network/{entity_id}
   - /api/timeline/{case_id}
   - /api/health

5. List every fix you made. If nothing needs fixing, confirm "All checks passed."
```

---

### ✅ PROMPT 27 of 28 — Demo Script Document
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a project at d:\FraudIntel. Create this file:

FILE: d:\FraudIntel\docs\demo-script.md

A detailed 3-minute demo video script for the hackathon submission. Format it as a screenplay with timing, visuals, and narration.

Structure:

# FraudIntel — Demo Video Script (3 minutes)

## 0:00 – 0:30 | THE HOOK
Visual: Show a striking statistic on screen "$4.4 TRILLION lost to financial crime annually"
Narration: "Every year, four point four trillion dollars disappears to financial crime. Legacy systems generate millions of alerts, but up to 95% are false positives. Investigators are drowning in noise."
Visual: Show the FraudIntel dashboard — dark mode, cases loaded, alerts streaming
Narration: "Meet FraudIntel — an AI investigation agent that doesn't just detect fraud. It investigates it."

## 0:30 – 1:30 | THE LIVE INVESTIGATION
Visual: Click "New Investigation" → type "ACC-001"
Narration: "Watch what happens when we investigate a suspicious account. FraudIntel's multi-agent system activates..."
Visual: Show the loading progress messages
Narration: "Five specialized AI agents — an Evidence Gatherer, Risk Scorer, Auditor, Compliance Agent, and Report Generator — work together to conduct a complete investigation."
Visual: Investigation completes, new case appears in sidebar with score 78 (HIGH RISK)
Narration: "In just 90 seconds, FraudIntel has completed what would take a human analyst 4 to 6 hours."
Visual: Click on the case, show the Network Graph tab
Narration: "The network graph reveals a hidden fraud ring — four accounts sharing the same device and VPN IP address. This is a classic bust-out scheme."
Visual: Show nodes and connections in the graph

## 1:30 – 2:15 | THE FEATURES
Visual: Switch to Timeline tab
Narration: "FraudIntel reconstructs the complete investigation timeline — from account creation to the alert trigger, highlighting critical moments."
Visual: Switch to Report tab
Narration: "The investigation report provides full transparency: evidence collected, risk score breakdown, key findings, and recommended actions. Every conclusion is traced back to specific evidence."
Visual: Show the risk score gauge (78/100) with factor breakdown
Visual: Switch to SAR tab
Narration: "For high-risk cases, FraudIntel automatically generates a FinCEN-compliant Suspicious Activity Report draft, saving compliance teams hours of manual documentation."
Visual: Show the SAR narrative text

## 2:15 – 2:45 | THE ARCHITECTURE
Visual: Show architecture diagram (can be a slide or overlay)
Narration: "Under the hood, FraudIntel is built on Google Cloud Agent Builder using the ADK framework with Gemini 3 as the reasoning engine. The MongoDB Atlas MCP server provides standardized database access — enabling graph traversal for fraud ring detection, vector search for pattern matching, and real-time aggregation pipelines for risk scoring."
Visual: Highlight the key components: Gemini → ADK → MCP → MongoDB

## 2:45 – 3:00 | THE CLOSE
Visual: Return to dashboard showing all cases
Narration: "FraudIntel transforms fraud investigation from a manual, error-prone process into an AI-powered, transparent, and auditable system. Because in the fight against financial crime, you don't just need alerts — you need an investigator."
Visual: FraudIntel logo + tagline

## Production Notes
- Screen record at 1080p or higher
- Use a clean browser (no bookmarks bar, no other tabs)
- Pre-seed the database with sample data before recording
- Keep the mouse movements smooth and deliberate
- Use a professional microphone for narration
- Add subtle background music (royalty-free, instrumental)
- Include captions/subtitles

Create ONLY this 1 file.
```

---

### ✅ PROMPT 28 of 28 — Final Integration Test & README Polish
> 🤖 **Agent:** Antigravity / Gemini / Cursor / Claude

```text
I have a completed project at d:\FraudIntel. Please do these final tasks:

1. Run a mental walkthrough of the entire application flow:
   a) User opens http://localhost:8080 → dashboard/index.html is served
   b) Dashboard JS calls GET /api/dashboard/stats → stats cards update
   c) Dashboard JS calls GET /api/cases → case queue populates
   d) Dashboard JS calls GET /api/alerts → alert feed populates
   e) User clicks "New Investigation" → modal opens
   f) User types "ACC-001" → clicks Start
   g) JS calls POST /api/investigate → backend runs tools → returns response
   h) New case appears in sidebar
   i) User clicks case → JS loads case detail, network graph, timeline
   j) Network graph renders with D3.js

2. Check for any potential runtime errors:
   - Are there any missing function arguments?
   - Are any MongoDB queries using wrong field names?
   - Are there any undefined variables?
   - Does the _serialize function in mongodb_tools handle all BSON types?
   
3. Fix any issues you find.

4. Verify the README.md at d:\FraudIntel\README.md:
   - Does the Quick Start section have correct commands?
   - Are all badge URLs working?
   - Is the project structure accurate and up-to-date?
   Update if needed to match the actual project structure.

5. Create a final summary of the complete project file tree, listing EVERY file with a one-line description. Print this summary so I can verify everything is in place.
```

---
---

## 📋 POST-BUILD CHECKLIST

After completing all 28 prompts, run these in terminal (💻):

```bash
# 1. Activate environment
cd d:\FraudIntel
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run setup verification
python test_setup.py

# 4. Seed the database (only needed once)
python -m data.seed_data

# 5. Start the server
python -m uvicorn api.server:app --host 0.0.0.0 --port 8080 --reload

# 6. Open browser
start http://localhost:8080

# 7. Test API
curl http://localhost:8080/api/health
curl http://localhost:8080/api/dashboard/stats
```

---

## 📤 SUBMISSION CHECKLIST

- [ ] Code pushed to **public** GitHub repository
- [ ] **MIT LICENSE** visible in repo (About section)
- [ ] App deployed to **Google Cloud Run** (hosted URL)
- [ ] **3-minute demo video** recorded and uploaded (YouTube)
- [ ] **Devpost submission** completed:
  - [ ] Project URL (Cloud Run)
  - [ ] GitHub repo URL
  - [ ] Video URL
  - [ ] Partner track: **MongoDB**
  - [ ] All form fields filled

---

> 🏆 **You now have everything you need to build FraudIntel and win the MongoDB track. Execute the prompts in order, verify as you go, and crush the competition!**

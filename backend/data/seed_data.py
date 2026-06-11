"""FraudIntel Database Seeder.

Populates the MongoDB ``fraudintel`` database with realistic synthetic data
for development and demonstration purposes.

Usage::

    python -m data.seed_data
"""

import json
import os
import random
import string
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = "fraudintel"
COLLECTION_NAMES = [
    "transactions",
    "customers",
    "entity_relationships",
    "investigations",
    "fraud_patterns",
    "alerts",
]

random.seed(42)

DATA_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Helper constants
# ---------------------------------------------------------------------------

NAMES = [
    "Marcus J. Whitfield",
    "Danielle K. Whitfield",
    "Terrence R. Blake",
    "Jasmine L. Torres",
    "Catherine M. Hargrove",
    "Jonathan R. Ashworth",
    "Priya S. Naidu",
    "Robert A. Chen",
    "Sophia E. Martinez",
    "David L. Kim",
    "Olivia N. Patel",
    "Ethan W. Brooks",
    "Amara T. Okafor",
    "Lucas G. Fernandez",
    "Mia H. Johansson",
    "James F. O'Brien",
    "Isabella R. Costa",
    "Benjamin D. Schwartz",
    "Zara P. Hussain",
    "William K. Tanaka",
    "Emily C. Dubois",
    "Alexander M. Volkov",
    "Natalie A. Bergström",
    "Samuel J. Owusu",
    "Grace Y. Li",
    "Daniel T. Murphy",
    "Hannah V. Schmidt",
    "Oscar L. Reyes",
    "Chloe B. Andersson",
    "Ryan M. Fitzgerald",
    "Ava S. Nakamura",
    "Noah P. De Luca",
    "Lily R. Kapoor",
    "Michael E. Warren",
    "Emma K. Lindström",
    "Jacob H. Morales",
    "Aria C. Petrov",
    "Andrew N. Callahan",
    "Maya D. Rashid",
    "Thomas G. Eriksson",
    "Rachel F. Adeyemi",
    "Kevin J. Huang",
    "Leah M. Kowalski",
    "Patrick B. Sullivan",
    "Nadia T. Al-Farsi",
    "Christopher W. Yeung",
    "Sarah L. Jensen",
    "Anthony R. Bassi",
    "Victoria A. Okonkwo",
    "Brandon S. Leclerc",
]

MERCHANT_CATEGORIES = [
    "retail",
    "grocery",
    "crypto",
    "gambling",
    "travel",
    "electronics",
    "dining",
    "gas",
    "utilities",
]

TYPICAL_MERCHANTS = [
    "grocery",
    "retail",
    "dining",
    "travel",
    "electronics",
    "gas",
]

TRANSACTION_TYPES = [
    "wire_transfer",
    "ach",
    "card_purchase",
    "atm_withdrawal",
    "deposit",
    "internal_transfer",
]

BANKS = [
    "Chase Bank",
    "Bank of America",
    "Wells Fargo",
    "Citibank",
    "Capital One",
    "TD Bank",
    "PNC Financial",
    "US Bancorp",
    "Goldman Sachs",
    "HSBC",
    "Barclays",
    "Deutsche Bank",
]

COUNTERPARTY_NAMES = [
    "Alpine Trading LLC",
    "Crescent Financial Services",
    "NovaTech Solutions",
    "Pacific Rim Exports",
    "Sterling Capital Group",
    "Atlas Commodities Ltd",
    "Pinnacle Ventures Inc",
    "Horizon Payments Corp",
    "Meridian Trust AG",
    "Apex Credit Union",
    "Lakeview Holdings",
    "Vanguard Supply Co",
    "Ironclad Logistics",
    "Summit Ridge Partners",
    "Clearwater Imports",
]

GEO_LOCATIONS = [
    {"city": "New York", "country": "US", "lat": 40.7128, "lng": -74.0060},
    {"city": "Chicago", "country": "US", "lat": 41.8781, "lng": -87.6298},
    {"city": "San Francisco", "country": "US", "lat": 37.7749, "lng": -122.4194},
    {"city": "Miami", "country": "US", "lat": 25.7617, "lng": -80.1918},
    {"city": "Dallas", "country": "US", "lat": 32.7767, "lng": -96.7970},
    {"city": "London", "country": "GB", "lat": 51.5074, "lng": -0.1278},
    {"city": "Singapore", "country": "SG", "lat": 1.3521, "lng": 103.8198},
    {"city": "Lagos", "country": "NG", "lat": 6.5244, "lng": 3.3792},
]

TRIGGER_RULES = [
    "velocity_anomaly",
    "large_transfer",
    "geo_impossible",
    "device_anomaly",
    "structuring_pattern",
    "new_account_risk",
]

ALERT_SOURCES = [
    "transaction_monitor",
    "rule_engine",
    "ml_model",
    "manual_report",
]

# Suspicious account indices (0-based): CUS-001→idx 0, CUS-010→idx 9, etc.
SUSPICIOUS_INDICES = {0, 1, 2, 3, 9}  # ACC-001..004, ACC-010


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _random_date(start: datetime, end: datetime) -> datetime:
    """Return a random datetime between *start* and *end*."""
    delta = end - start
    seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=seconds)


def get_embedding(text: str) -> list[float]:
    """Generate a 768-dimensional random embedding for speed."""
    return [round(random.uniform(-1, 1), 6) for _ in range(768)]


def _random_ip(vpn: bool = False) -> str:
    """Generate a plausible IP address."""
    if vpn:
        return f"45.33.{random.randint(1, 254)}.{random.randint(1, 254)}"
    return f"{random.choice([72, 98, 104, 142, 168, 192])}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"


def _random_fingerprint(pool: list[str]) -> str:
    return random.choice(pool)


def _email_from_name(name: str) -> str:
    """Derive a plausible email from a full name."""
    parts = name.replace(".", "").lower().split()
    first, last = parts[0], parts[-1]
    domain = random.choice(["gmail.com", "outlook.com", "yahoo.com", "proton.me"])
    return f"{first}.{last}@{domain}"


def _random_phone() -> str:
    return f"+1-555-{random.randint(1000, 9999)}"


def _account_id(n: int) -> str:
    return f"ACC-{n:03d}"


def _customer_id(n: int) -> str:
    return f"CUS-{n:03d}"


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

def generate_customers() -> list[dict]:
    """Generate 50 customer documents."""
    customers = []
    now = datetime(2026, 3, 15, tzinfo=timezone.utc)

    for idx in range(50):
        num = idx + 1
        name = NAMES[idx]
        is_suspicious = idx in SUSPICIOUS_INDICES

        if is_suspicious:
            risk_score = random.randint(60, 90)
            account_created = _random_date(
                datetime(2026, 1, 1, tzinfo=timezone.utc),
                datetime(2026, 1, 31, tzinfo=timezone.utc),
            )
        else:
            risk_score = random.randint(5, 40)
            account_created = _random_date(
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2025, 12, 31, tzinfo=timezone.utc),
            )

        if risk_score <= 20:
            risk_category = "low"
        elif risk_score <= 50:
            risk_category = "medium"
        elif risk_score <= 75:
            risk_category = "high"
        else:
            risk_category = "critical"

        kyc_verified = not is_suspicious or random.random() > 0.5
        geo = random.choice(GEO_LOCATIONS[:5])  # US cities only for home

        customer = {
            "customer_id": _customer_id(num),
            "name": name,
            "email": _email_from_name(name),
            "phone": _random_phone(),
            "accounts": [_account_id(num)],
            "kyc": {
                "verified": kyc_verified,
                "verification_date": (
                    account_created + timedelta(days=random.randint(1, 14))
                ),
                "documents": ["passport", "utility_bill"],
            },
            "risk_profile": {
                "score": risk_score,
                "category": risk_category,
                "last_updated": now,
            },
            "behavioral_baseline": {
                "avg_monthly_transactions": random.randint(5, 30),
                "avg_transaction_amount": round(random.uniform(100, 5000), 2),
                "typical_merchants": random.sample(TYPICAL_MERCHANTS, 3),
                "typical_geo": [f"{geo['city']}, {geo['country']}"],
            },
            "account_created_at": account_created,
        }
        customers.append(customer)

    return customers


def generate_transactions() -> list[dict]:
    """Generate 500 transaction documents with embedded suspicious patterns."""
    # Pre-generate device fingerprints and IPs
    device_pool = [f"DFP-{random.randint(10000, 99999):05X}" for _ in range(20)]
    ip_pool_normal = [_random_ip(vpn=False) for _ in range(20)]
    ip_pool_vpn = [_random_ip(vpn=True) for _ in range(10)]
    ip_pool = ip_pool_normal + ip_pool_vpn

    # Special devices / IPs for fraud patterns
    DFP_RING1 = "DFP-RING1"
    DFP_ATO1 = "DFP-ATO1"
    IP_RING = "45.33.32.100"

    transactions: list[dict] = []
    txn_counter = 0

    start_date = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2026, 3, 31, tzinfo=timezone.utc)

    for acct_num in range(1, 51):
        acct_id = _account_id(acct_num)
        num_txns = 10  # 50 accounts × 10 = 500

        for _ in range(num_txns):
            txn_counter += 1
            txn_id = f"TXN-2026-{random.randint(100000, 999999)}"
            ts = _random_date(start_date, end_date)
            txn_type = random.choice(TRANSACTION_TYPES)
            direction = "inbound" if txn_type in ("deposit",) else random.choice(["inbound", "outbound"])
            geo = random.choice(GEO_LOCATIONS)

            # Default normal amount
            amount = round(random.uniform(10, 5000), 2)
            device = _random_fingerprint(device_pool)
            ip = random.choice(ip_pool)

            # --- Suspicious overrides ---
            # Bust-out ring: ACC-001 to ACC-004
            if acct_num in (1, 2, 3, 4):
                device = DFP_RING1
                ip = IP_RING
                if random.random() < 0.4:
                    amount = round(random.uniform(8000, 25000), 2)

            # ATO: ACC-010
            elif acct_num == 10:
                if random.random() < 0.3:
                    device = DFP_ATO1
                    txn_type = "wire_transfer"
                    amount = 25000.00
                    ip = "185.220.101.34"
                    geo = GEO_LOCATIONS[5]  # London

            # Money laundering ring: ACC-020 to ACC-022
            elif acct_num in (20, 21, 22):
                ip = "192.168.50.1"
                if random.random() < 0.5:
                    txn_type = "internal_transfer"
                    amount = round(random.uniform(15000, 50000), 2)
                    direction = "outbound"

            # Structuring: ACC-040 to ACC-044
            elif acct_num in (40, 41, 42, 43, 44):
                if random.random() < 0.6:
                    txn_type = "deposit"
                    direction = "inbound"
                    amount = round(random.uniform(9000, 9900), 2)

            txn = {
                "transaction_id": txn_id,
                "account_id": acct_id,
                "type": txn_type,
                "amount": amount,
                "currency": "USD",
                "direction": direction,
                "counterparty": {
                    "name": random.choice(COUNTERPARTY_NAMES),
                    "account": f"EXT-{random.randint(100000, 999999)}",
                    "institution": random.choice(BANKS),
                },
                "timestamp": ts,
                "device_fingerprint": device,
                "ip_address": ip,
                "geo": {
                    "lat": geo["lat"],
                    "lng": geo["lng"],
                    "city": geo["city"],
                    "country": geo["country"],
                },
                "risk_flags": [],
                "merchant_category": random.choice(MERCHANT_CATEGORIES),
            }
            txn["embedding"] = get_embedding(json.dumps(txn, default=str))
            transactions.append(txn)

    return transactions


def generate_entity_relationships(
    customers: list[dict],
    transactions: list[dict],
) -> list[dict]:
    """Generate 300+ entity-relationship link documents (Bidirectional)."""
    relationships: list[dict] = []
    seen = datetime(2025, 6, 1, tzinfo=timezone.utc)
    now = datetime(2026, 3, 15, tzinfo=timezone.utc)

    device_pool = [f"DFP-{random.randint(10000, 99999):05X}" for _ in range(30)]
    ip_pool = [_random_ip() for _ in range(25)]

    def add_bi(rel_data):
        relationships.append(rel_data)
        rev = rel_data.copy()
        rev["entity_id"], rev["linked_entity_id"] = rel_data["linked_entity_id"], rel_data["entity_id"]
        rev["entity_type"], rev["linked_entity_type"] = rel_data["linked_entity_type"], rel_data["entity_type"]
        relationships.append(rev)

    for cust in customers:
        acct = cust["accounts"][0]
        email = cust["email"]
        phone = cust["phone"]

        # Account → devices (1-3)
        num_devices = random.randint(1, 3)
        for _ in range(num_devices):
            add_bi({
                "entity_id": acct,
                "entity_type": "account",
                "linked_entity_id": random.choice(device_pool),
                "linked_entity_type": "device",
                "relationship_type": "uses_device",
                "first_seen": _random_date(seen, now),
                "last_seen": _random_date(now - timedelta(days=30), now),
                "strength": round(random.uniform(0.5, 1.0), 2),
            })

        # Account → IPs (1-2)
        num_ips = random.randint(1, 2)
        for _ in range(num_ips):
            add_bi({
                "entity_id": acct,
                "entity_type": "account",
                "linked_entity_id": random.choice(ip_pool),
                "linked_entity_type": "ip_address",
                "relationship_type": "logged_from_ip",
                "first_seen": _random_date(seen, now),
                "last_seen": _random_date(now - timedelta(days=30), now),
                "strength": round(random.uniform(0.5, 1.0), 2),
            })

        # Account → phone
        add_bi({
            "entity_id": acct,
            "entity_type": "account",
            "linked_entity_id": phone,
            "linked_entity_type": "phone",
            "relationship_type": "registered_phone",
            "first_seen": cust["account_created_at"],
            "last_seen": now,
            "strength": round(random.uniform(0.8, 1.0), 2),
        })

        # Account → email
        add_bi({
            "entity_id": acct,
            "entity_type": "account",
            "linked_entity_id": email,
            "linked_entity_type": "email",
            "relationship_type": "registered_email",
            "first_seen": cust["account_created_at"],
            "last_seen": now,
            "strength": round(random.uniform(0.8, 1.0), 2),
        })

        # Account → merchants (1-2)
        for _ in range(random.randint(1, 2)):
            add_bi({
                "entity_id": acct,
                "entity_type": "account",
                "linked_entity_id": random.choice(COUNTERPARTY_NAMES),
                "linked_entity_type": "merchant",
                "relationship_type": "transacted_with_merchant",
                "first_seen": _random_date(seen, now),
                "last_seen": _random_date(now - timedelta(days=15), now),
                "strength": round(random.uniform(0.5, 0.9), 2),
            })

    # --- Fraud ring shared links ---

    # Ring 1: ACC-001..004 share DFP-RING1 and IP 45.33.32.100
    for acct_id in ["ACC-001", "ACC-002", "ACC-003", "ACC-004"]:
        add_bi({
            "entity_id": acct_id,
            "entity_type": "account",
            "linked_entity_id": "DFP-RING1",
            "linked_entity_type": "device",
            "relationship_type": "uses_device",
            "first_seen": "2025-07-15T00:00:00+00:00",
            "last_seen": "2026-03-10T00:00:00+00:00",
            "strength": 0.97,
        })
        add_bi({
            "entity_id": acct_id,
            "entity_type": "account",
            "linked_entity_id": "45.33.32.100",
            "linked_entity_type": "ip_address",
            "relationship_type": "logged_from_ip",
            "first_seen": "2025-07-15T00:00:00+00:00",
            "last_seen": "2026-03-10T00:00:00+00:00",
            "strength": 0.95,
        })

    # Ring 2: ACC-010, ACC-011 share phone and email
    for acct_id in ["ACC-010", "ACC-011"]:
        add_bi({
            "entity_id": acct_id,
            "entity_type": "account",
            "linked_entity_id": "+1-555-0199",
            "linked_entity_type": "phone",
            "relationship_type": "registered_phone",
            "first_seen": "2025-11-01T00:00:00+00:00",
            "last_seen": "2026-03-05T00:00:00+00:00",
            "strength": 0.93,
        })
        add_bi({
            "entity_id": acct_id,
            "entity_type": "account",
            "linked_entity_id": "ring2@tempmail.com",
            "linked_entity_type": "email",
            "relationship_type": "registered_email",
            "first_seen": "2025-11-01T00:00:00+00:00",
            "last_seen": "2026-03-05T00:00:00+00:00",
            "strength": 0.91,
        })

    # Ring 3: ACC-020..022 share IP
    for acct_id in ["ACC-020", "ACC-021", "ACC-022"]:
        add_bi({
            "entity_id": acct_id,
            "entity_type": "account",
            "linked_entity_id": "192.168.50.1",
            "linked_entity_type": "ip_address",
            "relationship_type": "logged_from_ip",
            "first_seen": "2025-09-01T00:00:00+00:00",
            "last_seen": "2026-03-12T00:00:00+00:00",
            "strength": 0.96,
        })

    return relationships


def generate_fraud_patterns() -> list[dict]:
    """Load fraud patterns from JSON and add embeddings."""
    patterns_path = DATA_DIR / "fraud_patterns.json"
    with open(patterns_path, "r", encoding="utf-8") as f:
        patterns = json.load(f)

    for pattern in patterns:
        pattern["embedding"] = get_embedding(json.dumps({k: v for k, v in pattern.items() if k != "embedding"}, default=str))

    return patterns


def generate_alerts() -> list[dict]:
    """Generate 20 alert documents."""
    alerts: list[dict] = []
    severities = ["critical"] * 5 + ["high"] * 5 + ["medium"] * 5 + ["low"] * 5
    statuses = ["new"] * 5 + ["investigating"] * 5 + ["resolved"] * 5 + ["false_positive"] * 5

    # Suspicious accounts to link to "new" alerts
    suspicious_accounts = ["ACC-001", "ACC-010", "ACC-020", "ACC-040", "ACC-044"]

    for i in range(20):
        alert_num = i + 1
        created = _random_date(
            datetime(2026, 3, 1, tzinfo=timezone.utc),
            datetime(2026, 3, 31, tzinfo=timezone.utc),
        )

        # For the first 5 "new" alerts, link to suspicious accounts
        if i < 5:
            related = [suspicious_accounts[i]]
        else:
            related = [
                _account_id(random.randint(1, 50))
                for _ in range(random.randint(1, 2))
            ]

        alert = {
            "alert_id": f"ALT-2026-{alert_num:04d}",
            "source": random.choice(ALERT_SOURCES),
            "severity": severities[i],
            "trigger_rule": random.choice(TRIGGER_RULES),
            "related_entities": related,
            "status": statuses[i],
            "created_at": created,
            "updated_at": (created + timedelta(hours=random.randint(1, 72))),
        }
        alerts.append(alert)

    return alerts


def generate_investigations() -> list[dict]:
    """Generate 5 investigation documents."""
    base_ts = datetime(2026, 3, 1, tzinfo=timezone.utc)

    investigations = [
        {
            "case_id": "INV-2026-0538",
            "title": "Structuring Activity — ACC-040 Cluster",
            "status": "resolved",
            "priority": "high",
            "fraud_type": "structuring",
            "fraud_score": 65,
            "assigned_analyst": "Agent-RiskOps",
            "related_accounts": ["ACC-040", "ACC-041", "ACC-042"],
            "related_alerts": ["ALT-2026-0004"],
            "executive_summary": "Detected a highly coordinated structuring network evading CTR thresholds across three accounts.",
            "evidence": {
                "accounts_reviewed": 3,
                "transactions_analyzed": 45,
            },
            "timeline": [
                {
                    "timestamp": (base_ts + timedelta(days=2)),
                    "event": "case_opened",
                    "description": "Multiple deposits just below $10,000 CTR threshold flagged by rule engine.",
                },
                {
                    "timestamp": (base_ts + timedelta(days=3)),
                    "event": "evidence_collected",
                    "description": "Reviewed 45 transactions across 3 linked accounts showing structured deposit patterns.",
                },
                {
                    "timestamp": (base_ts + timedelta(days=5)),
                    "event": "case_resolved",
                    "description": "SAR filed. Accounts frozen pending BSA/AML compliance review.",
                },
            ],
            "network_map": {
                "nodes": [
                    {"id": "ACC-040", "type": "account"},
                    {"id": "ACC-041", "type": "account"},
                    {"id": "ACC-042", "type": "account"},
                ],
                "edges": [
                    {"source": "ACC-040", "target": "ACC-041"},
                    {"source": "ACC-041", "target": "ACC-042"},
                ],
            },
            "sar_draft": "Suspicious Activity Report: Three linked accounts conducted 45 cash deposits averaging $9,450 each over a 6-week period, totaling $425,250, in apparent structuring to evade CTR requirements.",
            "audit_trail": [
                {
                    "timestamp": (base_ts + timedelta(days=2)),
                    "action": "case_created",
                    "agent": "rule_engine",
                    "description": "Auto-generated from structuring_pattern trigger.",
                },
                {
                    "timestamp": (base_ts + timedelta(days=5)),
                    "action": "case_resolved",
                    "agent": "analyst_jsmith",
                    "description": "SAR filed, accounts restricted.",
                },
            ],
            "created_at": (base_ts + timedelta(days=2)),
            "updated_at": (base_ts + timedelta(days=5)),
        },
        {
            "case_id": "INV-2026-0539",
            "title": "Account Takeover — ACC-010",
            "status": "resolved",
            "priority": "critical",
            "fraud_type": "account_takeover",
            "fraud_score": 91,
            "assigned_analyst": "Agent-RiskOps",
            "related_accounts": ["ACC-010"],
            "related_alerts": ["ALT-2026-0002"],
            "executive_summary": "Account Takeover confirmed via SIM swap. Fraudulent $25,000 wire intercepted.",
            "evidence": {
                "accounts_reviewed": 1,
                "transactions_analyzed": 12,
            },
            "timeline": [
                {
                    "timestamp": (base_ts + timedelta(days=4)),
                    "event": "case_opened",
                    "description": "Geo-impossible login detected: New York → London in 3 minutes.",
                },
                {
                    "timestamp": (base_ts + timedelta(days=4, hours=2)),
                    "event": "evidence_collected",
                    "description": "SIM-swap confirmed with carrier. New device DFP-ATO1 registered from Tor exit node.",
                },
                {
                    "timestamp": (base_ts + timedelta(days=4, hours=6)),
                    "event": "wire_reversed",
                    "description": "$25,000 wire to Meridian Trust AG recalled before settlement.",
                },
                {
                    "timestamp": (base_ts + timedelta(days=6)),
                    "event": "case_resolved",
                    "description": "Account restored to customer. Credentials reset. Enhanced monitoring applied.",
                },
            ],
            "network_map": {
                "nodes": [
                    {"id": "ACC-010", "type": "account"},
                    {"id": "DFP-ATO1", "type": "device"},
                    {"id": "185.220.101.34", "type": "ip_address"},
                ],
                "edges": [
                    {"source": "ACC-010", "target": "DFP-ATO1"},
                    {"source": "DFP-ATO1", "target": "185.220.101.34"},
                ],
            },
            "sar_draft": "Suspicious Activity Report: Account Takeover. Customer's credentials were compromised following a confirmed SIM-swap. A fraudulent wire transfer of $25,000 was initiated but successfully recalled before settlement.",
            "audit_trail": [
                {
                    "timestamp": (base_ts + timedelta(days=4)),
                    "action": "case_created",
                    "agent": "ml_model",
                    "description": "Geo-impossibility detector triggered critical alert.",
                },
                {
                    "timestamp": (base_ts + timedelta(days=4, hours=6)),
                    "action": "wire_recall_initiated",
                    "agent": "analyst_mchen",
                    "description": "Wire recall request sent to correspondent bank.",
                },
                {
                    "timestamp": (base_ts + timedelta(days=6)),
                    "action": "case_resolved",
                    "agent": "analyst_mchen",
                    "description": "Wire recovered. Account restored with enhanced controls.",
                },
            ],
            "created_at": (base_ts + timedelta(days=4)),
            "updated_at": (base_ts + timedelta(days=6)),
        },
        {
            "case_id": "INV-2026-0540",
            "title": "Money Laundering Network — ACC-020 Cluster",
            "status": "under_investigation",
            "priority": "high",
            "fraud_type": "money_laundering",
            "fraud_score": 72,
            "assigned_analyst": "Agent-RiskOps",
            "related_accounts": ["ACC-020", "ACC-021", "ACC-022"],
            "related_alerts": ["ALT-2026-0003"],
            "executive_summary": "Layered money laundering identified involving circular transfers across three internal accounts.",
            "evidence": {
                "accounts_reviewed": 3,
                "transactions_analyzed": 30,
            },
            "timeline": [
                {
                    "timestamp": (base_ts + timedelta(days=8)),
                    "event": "case_opened",
                    "description": "Circular transfer pattern detected among three accounts sharing IP 192.168.50.1.",
                },
                {
                    "timestamp": (base_ts + timedelta(days=9)),
                    "event": "evidence_collected",
                    "description": "Graph analysis reveals layered fund movement totaling $285,000 across 30 internal transfers.",
                },
                {
                    "timestamp": (base_ts + timedelta(days=10)),
                    "event": "escalated",
                    "description": "Escalated to BSA/AML team for enhanced due diligence and possible law enforcement referral.",
                },
            ],
            "network_map": {
                "nodes": [
                    {"id": "ACC-020", "type": "account"},
                    {"id": "ACC-021", "type": "account"},
                    {"id": "ACC-022", "type": "account"},
                    {"id": "192.168.50.1", "type": "ip_address"},
                ],
                "edges": [
                    {"source": "ACC-020", "target": "ACC-021"},
                    {"source": "ACC-021", "target": "ACC-022"},
                    {"source": "ACC-022", "target": "ACC-020"},
                    {"source": "ACC-020", "target": "192.168.50.1"},
                ],
            },
            "sar_draft": "Suspicious Activity Report: Suspected Money Laundering. Three accounts sharing the same IP address engaged in a series of circular, rapid-fire internal transfers totaling $285,000, indicative of layering and funds obfuscation.",
            "audit_trail": [
                {
                    "timestamp": (base_ts + timedelta(days=8)),
                    "action": "case_created",
                    "agent": "transaction_monitor",
                    "description": "Circular transfer pattern auto-detected.",
                },
                {
                    "timestamp": (base_ts + timedelta(days=10)),
                    "action": "escalated",
                    "agent": "analyst_plee",
                    "description": "Referred to BSA/AML compliance team.",
                },
            ],
            "created_at": (base_ts + timedelta(days=8)),
            "updated_at": (base_ts + timedelta(days=10)),
        },
        {
            "case_id": "INV-2026-0541",
            "title": "Mule Account Cluster — ACC-043/044",
            "status": "under_investigation",
            "priority": "medium",
            "fraud_type": "mule_account",
            "fraud_score": 58,
            "assigned_analyst": "Agent-RiskOps",
            "related_accounts": ["ACC-043", "ACC-044"],
            "related_alerts": ["ALT-2026-0005"],
            "evidence": {
                "accounts_reviewed": 2,
                "transactions_analyzed": 18,
            },
            "timeline": [
                {
                    "timestamp": (base_ts + timedelta(days=12)),
                    "event": "case_opened",
                    "description": "Two recently opened accounts receiving large inbound transfers and immediately forwarding funds.",
                },
                {
                    "timestamp": (base_ts + timedelta(days=13)),
                    "event": "evidence_collected",
                    "description": "KYC review shows minimal documentation. Account holders are students with no income history.",
                },
                {
                    "timestamp": (base_ts + timedelta(days=14)),
                    "event": "accounts_restricted",
                    "description": "Temporary holds placed on both accounts pending further investigation.",
                },
            ],
            "network_map": {
                "nodes": [
                    {"id": "ACC-043", "type": "account"},
                    {"id": "ACC-044", "type": "account"},
                ],
                "edges": [
                    {"source": "ACC-043", "target": "ACC-044"},
                ],
            },
            "sar_draft": None,
            "audit_trail": [
                {
                    "timestamp": (base_ts + timedelta(days=12)),
                    "action": "case_created",
                    "agent": "ml_model",
                    "description": "Mule-account classifier flagged rapid pass-through behavior.",
                },
                {
                    "timestamp": (base_ts + timedelta(days=14)),
                    "action": "accounts_restricted",
                    "agent": "analyst_jsmith",
                    "description": "Temporary holds placed pending EDD.",
                },
            ],
            "created_at": (base_ts + timedelta(days=12)),
            "updated_at": (base_ts + timedelta(days=14)),
        },
        {
            "case_id": "INV-2026-0542",
            "title": "Bust-Out Ring — ACC-001 to ACC-004",
            "status": "pending_review",
            "priority": "critical",
            "fraud_type": "bust_out",
            "fraud_score": 78,
            "assigned_analyst": "Agent-RiskOps",
            "related_accounts": ["ACC-001", "ACC-002", "ACC-003", "ACC-004"],
            "related_alerts": ["ALT-2026-0001"],
            "evidence": {
                "accounts_reviewed": 4,
                "transactions_analyzed": 40,
            },
            "timeline": [
                {
                    "timestamp": (base_ts + timedelta(days=15)),
                    "event": "case_opened",
                    "description": "Four accounts sharing device DFP-RING1 simultaneously maxed credit lines within 36 hours.",
                },
                {
                    "timestamp": (base_ts + timedelta(days=16)),
                    "event": "evidence_collected",
                    "description": "Device and IP analysis confirms shared infrastructure. Total exposure: $85,000+ across cash advances and high-resale purchases.",
                },
                {
                    "timestamp": (base_ts + timedelta(days=17)),
                    "event": "network_analysis",
                    "description": "Graph traversal reveals shared address (1847 W. Addison St, Chicago) and VPN exit node 45.33.32.100.",
                },
                {
                    "timestamp": (base_ts + timedelta(days=18)),
                    "event": "pending_review",
                    "description": "Case prepared for senior analyst review. SAR draft in progress.",
                },
                {
                    "timestamp": (base_ts + timedelta(days=19)),
                    "event": "sar_drafted",
                    "description": "Preliminary SAR narrative completed, awaiting compliance sign-off.",
                },
            ],
            "network_map": {
                "nodes": [
                    {"id": "ACC-001", "type": "account"},
                    {"id": "ACC-002", "type": "account"},
                    {"id": "ACC-003", "type": "account"},
                    {"id": "ACC-004", "type": "account"},
                    {"id": "DFP-RING1", "type": "device"},
                    {"id": "45.33.32.100", "type": "ip_address"},
                ],
                "edges": [
                    {"source": "ACC-001", "target": "DFP-RING1"},
                    {"source": "ACC-002", "target": "DFP-RING1"},
                    {"source": "ACC-003", "target": "DFP-RING1"},
                    {"source": "ACC-004", "target": "DFP-RING1"},
                    {"source": "ACC-001", "target": "45.33.32.100"},
                    {"source": "ACC-002", "target": "45.33.32.100"},
                    {"source": "ACC-003", "target": "45.33.32.100"},
                    {"source": "ACC-004", "target": "45.33.32.100"},
                    {"source": "ACC-001", "target": "ACC-002"},
                    {"source": "ACC-003", "target": "ACC-004"},
                ],
            },
            "sar_draft": "Suspicious Activity Report: Coordinated bust-out scheme involving four accounts (ACC-001 through ACC-004) sharing device fingerprint DFP-RING1 and VPN IP 45.33.32.100. After 9 months of credit-building behavior, all four accounts simultaneously extracted $85,000+ via cash advances and high-resale-value purchases within a 36-hour window.",
            "audit_trail": [
                {
                    "timestamp": (base_ts + timedelta(days=15)),
                    "action": "case_created",
                    "agent": "transaction_monitor",
                    "description": "Velocity anomaly detected across 4 linked accounts.",
                },
                {
                    "timestamp": (base_ts + timedelta(days=17)),
                    "action": "network_analysis_completed",
                    "agent": "Agent-GraphAnalyst",
                    "description": "Full network graph constructed. Shared infrastructure confirmed.",
                },
                {
                    "timestamp": (base_ts + timedelta(days=19)),
                    "action": "sar_drafted",
                    "agent": "Agent-ReportWriter",
                    "description": "SAR narrative generated. Pending compliance review.",
                },
            ],
            "created_at": (base_ts + timedelta(days=15)),
            "updated_at": (base_ts + timedelta(days=19)),
        },
    ]

    return investigations


# ---------------------------------------------------------------------------
# Main seeder
# ---------------------------------------------------------------------------

def seed() -> None:
    """Connect to MongoDB, drop existing data, and seed all collections."""
    print()
    print("=" * 60)
    print("  🛡️  FraudIntel Database Seeder")
    print("=" * 60)
    print()
    print(f"  URI:      {MONGODB_URI}")
    print(f"  Database: {DATABASE_NAME}")
    print()
    print("  ⚠️  WARNING: This will drop ALL existing data in the")
    print(f"     '{DATABASE_NAME}' database and replace it with seed data.")
    print()

    # Connect
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]

    # Drop existing collections
    print("  🗑️  Dropping existing collections...")
    for name in COLLECTION_NAMES:
        db.drop_collection(name)
        print(f"      Dropped: {name}")
    print()

    # Generate data
    print("  🔄 Generating seed data...")

    customers = generate_customers()
    print(f"      Customers:             {len(customers)} documents")

    transactions = generate_transactions()
    print(f"      Transactions:          {len(transactions)} documents")

    entity_rels = generate_entity_relationships(customers, transactions)
    print(f"      Entity Relationships:  {len(entity_rels)} documents")

    fraud_patterns = generate_fraud_patterns()
    print(f"      Fraud Patterns:        {len(fraud_patterns)} documents")

    alerts = generate_alerts()
    print(f"      Alerts:                {len(alerts)} documents")

    investigations = generate_investigations()
    print(f"      Investigations:        {len(investigations)} documents")
    print()

    # Insert data
    print("  📥 Inserting into MongoDB...")

    db["customers"].insert_many(customers)
    print("      ✅ customers")

    db["transactions"].insert_many(transactions)
    print("      ✅ transactions")

    db["entity_relationships"].insert_many(entity_rels)
    print("      ✅ entity_relationships")

    db["fraud_patterns"].insert_many(fraud_patterns)
    print("      ✅ fraud_patterns")

    db["alerts"].insert_many(alerts)
    print("      ✅ alerts")

    db["investigations"].insert_many(investigations)
    print("      ✅ investigations")
    print()

    # Summary
    print("  📊 Final Collection Counts:")
    print("  " + "-" * 40)
    for name in COLLECTION_NAMES:
        count = db[name].count_documents({})
        print(f"      {name:<25} {count:>6}")
    print("  " + "-" * 40)
    print()

    # Close
    client.close()
    print("  ✅ Seeding complete. Connection closed.")
    print()


if __name__ == "__main__":
    seed()

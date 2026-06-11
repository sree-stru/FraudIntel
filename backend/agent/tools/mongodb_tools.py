"""MongoDB tool functions for FraudIntel ADK agents.

Routes ALL database operations through the MongoDB MCP Server when
available, with automatic fallback to direct pymongo for reliability.
Each function is designed to be registered as a Google ADK tool.
Docstrings are surfaced to the LLM as tool descriptions, so they
are intentionally detailed.
"""

import json
import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any

from bson import ObjectId

from agent.config import settings
from agent.database import get_database

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level MongoDB connection (pymongo fallback when MCP is unavailable)
# ---------------------------------------------------------------------------
_DB_NAME = settings.mongodb_database


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _serialize(doc: Any) -> Any:
    """Recursively convert a MongoDB document to a JSON-safe structure.

    * ``ObjectId`` → ``str``
    * ``datetime``  → ISO-8601 string
    * Nested dicts and lists are traversed recursively.
    """
    if doc is None:
        return None
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, datetime):
        return doc.isoformat()
    if isinstance(doc, dict):
        return {key: _serialize(value) for key, value in doc.items()}
    if isinstance(doc, list):
        return [_serialize(item) for item in doc]
    return doc


# Severity sort order for alert prioritisation
_SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1}


# ---------------------------------------------------------------------------
# MCP Integration layer
# ---------------------------------------------------------------------------

def _get_mcp_session():
    """Return the active MCP session, or None if unavailable."""
    try:
        from agent.mcp_client import mcp_client
        if mcp_client._session is not None:
            return mcp_client
        return None
    except Exception:
        return None


async def _mcp_find(collection: str, filter_doc: dict,
                    sort: dict | None = None, limit: int | None = None,
                    projection: dict | None = None) -> list[dict] | None:
    """Call MCP find tool. Returns list of docs, or None if MCP unavailable."""
    client = _get_mcp_session()
    if client is None:
        return None
    try:
        args: dict[str, Any] = {
            "collection": collection,
            "database": _DB_NAME,
            "filter": filter_doc if filter_doc else {},
        }
        if sort:
            args["sort"] = sort
        if limit:
            args["limit"] = limit
        if projection:
            args["projection"] = projection
        result = await client.call_tool("find", args)
        logger.info("✅ MCP → find(%s, filter=%s)", collection,
                     json.dumps(filter_doc, default=str)[:120])
        if result:
            parsed = json.loads(result)
            return parsed if isinstance(parsed, list) else [parsed]
        return []
    except Exception as e:
        logger.warning("⚠️ MCP find fallback for %s: %s", collection, e)
        return None


async def _mcp_aggregate(collection: str,
                         pipeline: list[dict]) -> list[dict] | None:
    """Call MCP aggregate tool. Returns list of docs, or None."""
    client = _get_mcp_session()
    if client is None:
        return None
    try:
        result = await client.call_tool("aggregate", {
            "collection": collection,
            "database": _DB_NAME,
            "pipeline": pipeline,
        })
        logger.info("✅ MCP → aggregate(%s, %d stages)", collection,
                     len(pipeline))
        if result:
            parsed = json.loads(result)
            return parsed if isinstance(parsed, list) else [parsed]
        return []
    except Exception as e:
        logger.warning("⚠️ MCP aggregate fallback for %s: %s", collection, e)
        return None


async def _mcp_update_one(collection: str, filter_doc: dict,
                          update: dict,
                          upsert: bool = False) -> bool | None:
    """Call MCP update-many (with filter targeting one doc).

    The official MongoDB MCP Server only exposes ``update-many``; we use
    it with a selective filter to update a single document.
    """
    client = _get_mcp_session()
    if client is None:
        return None
    try:
        await client.call_tool("update-many", {
            "collection": collection,
            "database": _DB_NAME,
            "filter": filter_doc,
            "update": update,
        })
        logger.info("✅ MCP → update-many(%s, filter=%s)", collection,
                     json.dumps(filter_doc, default=str)[:80])
        return True
    except Exception as e:
        logger.warning("⚠️ MCP update fallback for %s: %s", collection, e)
        return None


async def _mcp_insert_one(collection: str,
                          document: dict) -> bool | None:
    """Call MCP insert-many (with a single document).

    The official MongoDB MCP Server only exposes ``insert-many``.
    """
    client = _get_mcp_session()
    if client is None:
        return None
    try:
        await client.call_tool("insert-many", {
            "collection": collection,
            "database": _DB_NAME,
            "documents": [document],
        })
        logger.info("✅ MCP → insert-many(%s)", collection)
        return True
    except Exception as e:
        logger.warning("⚠️ MCP insert fallback for %s: %s", collection, e)
        return None


# ---------------------------------------------------------------------------
# Tool functions (1–14)
# ---------------------------------------------------------------------------


async def get_account_transactions(account_id: str,
                                   limit: int = 50) -> list[dict]:
    """Retrieve transaction history for a specific account from the database.

    Returns a list of transaction records sorted by timestamp (newest first).
    Use this tool when you need to review the recent activity on an account,
    identify suspicious transaction patterns, or analyze spending behavior.

    Args:
        account_id: The account identifier (e.g. ``"ACC-001"``).
        limit: Maximum number of transactions to return. Defaults to 50.

    Returns:
        A list of transaction dicts, each containing fields such as
        ``transaction_id``, ``type``, ``amount``, ``timestamp``,
        ``device_fingerprint``, ``ip_address``, and ``geo``.
    """
    # MCP path
    result = await _mcp_find(
        "transactions",
        {"account_id": account_id},
        sort={"timestamp": -1},
        limit=limit,
    )
    if result is not None:
        return result

    # Pymongo fallback
    try:
        cursor = (
            await get_database()["transactions"]
            .find({"account_id": account_id})
            .sort("timestamp", -1)
            .limit(limit)
            .to_list(length=None)
        )
        return [_serialize(doc) for doc in cursor]
    except Exception as exc:
        logger.error("get_account_transactions failed for %s: %s",
                     account_id, exc)
        return []


async def get_customer_profile(account_id: str) -> dict:
    """Retrieve the customer profile associated with a given account ID.

    Returns customer details including KYC status, risk profile, and
    behavioral baseline.  Use this tool when you need to understand who
    owns an account, assess their risk category, or check KYC verification
    status before making an investigation decision.

    Args:
        account_id: The account identifier (e.g. ``"ACC-010"``).

    Returns:
        A dict with fields such as ``customer_id``, ``name``, ``email``,
        ``kyc``, ``risk_profile``, and ``behavioral_baseline``.
        Returns an empty dict if no customer is found.
    """
    # MCP path
    result = await _mcp_find(
        "customers",
        {"accounts": account_id},
        limit=1,
    )
    if result is not None:
        return result[0] if result else {}

    # Pymongo fallback
    try:
        doc = await get_database()["customers"].find_one({"accounts": account_id})
        if doc is None:
            logger.info("No customer found for account %s", account_id)
            return {}
        return _serialize(doc)
    except Exception as exc:
        logger.error("get_customer_profile failed for %s: %s",
                     account_id, exc)
        return {}


async def get_entity_network(entity_id: str,
                             max_depth: int = 3) -> dict:
    """Discover the network of related entities using graph traversal.

    Finds all accounts, devices, IPs, and other entities connected to the
    given entity within the specified depth.  Uses MongoDB ``$graphLookup``
    for recursive relationship traversal.  Use this tool to map out fraud
    rings, identify shared infrastructure, or visualize entity connections.

    Args:
        entity_id: The starting entity identifier (e.g. ``"ACC-001"``
            or ``"DFP-RING1"``).
        max_depth: Maximum traversal depth.  Defaults to 3.  Capped
            internally by ``settings.max_graph_depth``.

    Returns:
        A dict with ``root_entity``, ``network_size``, ``nodes`` (list of
        entity dicts with hop information), and ``max_depth_reached``.
    """
    effective_depth = min(max_depth, settings.max_graph_depth)
    empty_result: dict = {
        "root_entity": entity_id,
        "network_size": 0,
        "nodes": [],
        "max_depth_reached": 0,
    }

    pipeline = [
        {"$match": {"entity_id": entity_id}},
        {
            "$graphLookup": {
                "from": "entity_relationships",
                "startWith": "$linked_entity_id",
                "connectFromField": "linked_entity_id",
                "connectToField": "entity_id",
                "maxDepth": effective_depth,
                "depthField": "hop_count",
                "as": "network",
            }
        },
    ]

    # MCP path
    results = await _mcp_aggregate("entity_relationships", pipeline)

    # Pymongo fallback
    if results is None:
        try:
            results = list(
                await get_database()["entity_relationships"].aggregate(pipeline).to_list(length=None)
            )
            results = [_serialize(doc) for doc in results]
        except Exception as exc:
            logger.error("get_entity_network failed for %s: %s",
                         entity_id, exc)
            return empty_result

    if not results:
        return empty_result

    # Flatten and deduplicate nodes across all matching root docs
    seen_ids: set[str] = set()
    nodes: list[dict] = []
    max_hop = 0

    for doc in results:
        for node in doc.get("network", []):
            node_id = node.get("linked_entity_id",
                               node.get("entity_id"))
            if node_id and node_id not in seen_ids:
                seen_ids.add(node_id)
                hop = node.get("hop_count", 0)
                max_hop = max(max_hop, hop)
                nodes.append(
                    _serialize(node) if isinstance(node.get("_id"),
                                                     ObjectId) else node
                )

    return {
        "root_entity": entity_id,
        "network_size": len(nodes),
        "nodes": nodes,
        "max_depth_reached": max_hop,
    }


async def get_alert_details(alert_id: str) -> dict:
    """Retrieve full details of a specific fraud alert by its alert ID.

    Use this tool when an alert needs to be reviewed, triaged, or
    correlated with other investigation data.

    Args:
        alert_id: The alert identifier (e.g. ``"ALT-2026-0001"``).

    Returns:
        A dict containing alert fields such as ``severity``,
        ``trigger_rule``, ``related_entities``, and ``status``.
        Returns an empty dict if the alert is not found.
    """
    # MCP path
    result = await _mcp_find("alerts", {"alert_id": alert_id}, limit=1)
    if result is not None:
        return result[0] if result else {}

    # Pymongo fallback
    try:
        doc = await get_database()["alerts"].find_one({"alert_id": alert_id})
        if doc is None:
            logger.info("Alert %s not found", alert_id)
            return {}
        return _serialize(doc)
    except Exception as exc:
        logger.error("get_alert_details failed for %s: %s", alert_id, exc)
        return {}


async def search_fraud_history(entity_ids: list[str]) -> list[dict]:
    """Search for previous fraud investigations involving any of the given entity IDs.

    Returns summaries of past investigations for correlation analysis.
    Use this tool to check whether accounts or entities appearing in the
    current investigation have been involved in prior fraud cases.

    Args:
        entity_ids: A list of entity identifiers (account IDs, device
            fingerprints, IP addresses, etc.).

    Returns:
        A list of investigation summary dicts containing ``case_id``,
        ``title``, ``status``, ``fraud_type``, ``fraud_score``, and
        ``related_accounts``.
    """
    query = {
        "$or": [
            {"related_accounts": {"$in": entity_ids}},
            {"related_alerts": {"$in": entity_ids}},
            {"network_map.nodes.id": {"$in": entity_ids}},
        ]
    }
    projection = {
        "_id": 0,
        "case_id": 1,
        "title": 1,
        "status": 1,
        "fraud_type": 1,
        "fraud_score": 1,
        "related_accounts": 1,
        "created_at": 1,
    }

    # MCP path
    result = await _mcp_find(
        "investigations", query, projection=projection,
    )
    if result is not None:
        return result

    # Pymongo fallback
    try:
        cursor = await get_database()["investigations"].find(query, projection).to_list(length=None)
        return [_serialize(doc) for doc in cursor]
    except Exception as exc:
        logger.error("search_fraud_history failed for %s: %s",
                     entity_ids, exc)
        return []


async def get_transaction_velocity(account_id: str,
                                   hours: int = 24) -> dict:
    """Calculate transaction velocity metrics for an account over a specified time window.

    Returns transaction count, total amount, and average amount.
    Use this tool to detect velocity anomalies — unusually high transaction
    frequency or volume within a short period is a key fraud indicator.

    Args:
        account_id: The account identifier (e.g. ``"ACC-001"``).
        hours: Lookback window in hours.  Defaults to 24.

    Returns:
        A dict with ``account_id``, ``period_hours``,
        ``transaction_count``, ``total_amount``, ``avg_amount``, and
        a ``transactions`` list.
    """
    empty_result: dict = {
        "account_id": account_id,
        "period_hours": hours,
        "transaction_count": 0,
        "total_amount": 0.0,
        "avg_amount": 0.0,
        "transactions": [],
    }

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    filter_doc = {
        "account_id": account_id,
        "timestamp": {"$gte": cutoff},
    }

    # MCP path
    txns = await _mcp_find(
        "transactions", filter_doc, sort={"timestamp": -1},
    )

    # Pymongo fallback
    if txns is None:
        try:
            cursor = (
                get_database()["transactions"]
                .find(filter_doc)
                .sort("timestamp", -1)
            )
            txns = [_serialize(doc) for doc in cursor]
        except Exception as exc:
            logger.error("get_transaction_velocity failed for %s: %s",
                         account_id, exc)
            return empty_result

    total = sum(t.get("amount", 0) for t in txns)
    count = len(txns)

    return {
        "account_id": account_id,
        "period_hours": hours,
        "transaction_count": count,
        "total_amount": round(total, 2),
        "avg_amount": round(total / count, 2) if count else 0.0,
        "transactions": txns,
    }


async def get_linked_accounts_by_device(
    device_fingerprint: str,
) -> list[str]:
    """Find all accounts that have used a specific device.

    Useful for detecting shared-device fraud patterns such as bust-out
    rings or account-takeover campaigns where attackers reuse the same
    hardware.

    Args:
        device_fingerprint: The device identifier (e.g. ``"DFP-RING1"``).

    Returns:
        A deduplicated list of account ID strings.
    """
    query = {
        "$or": [
            {
                "linked_entity_id": device_fingerprint,
                "linked_entity_type": "device",
            },
            {
                "entity_id": device_fingerprint,
                "entity_type": "device",
            },
        ]
    }

    # MCP path
    docs = await _mcp_find("entity_relationships", query)

    # Pymongo fallback
    if docs is None:
        try:
            cursor = await get_database()["entity_relationships"].find(query).to_list(length=None)
            docs = [_serialize(doc) for doc in cursor]
        except Exception as exc:
            logger.error(
                "get_linked_accounts_by_device failed for %s: %s",
                device_fingerprint, exc,
            )
            return []

    accounts: set[str] = set()
    for doc in docs:
        eid = doc.get("entity_id", "")
        lid = doc.get("linked_entity_id", "")
        if eid.startswith("ACC-"):
            accounts.add(eid)
        if lid.startswith("ACC-"):
            accounts.add(lid)
    return sorted(accounts)


async def get_linked_accounts_by_ip(ip_address: str) -> list[str]:
    """Find all accounts that have logged in from a specific IP address.

    Useful for detecting shared-IP fraud patterns such as bot-net
    operations, VPN-masked fraud rings, or co-located mule accounts.

    Args:
        ip_address: The IP address string (e.g. ``"45.33.32.100"``).

    Returns:
        A deduplicated list of account ID strings.
    """
    query = {
        "$or": [
            {
                "linked_entity_id": ip_address,
                "linked_entity_type": "ip_address",
            },
            {
                "entity_id": ip_address,
                "entity_type": "ip_address",
            },
        ]
    }

    # MCP path
    docs = await _mcp_find("entity_relationships", query)

    # Pymongo fallback
    if docs is None:
        try:
            cursor = await get_database()["entity_relationships"].find(query).to_list(length=None)
            docs = [_serialize(doc) for doc in cursor]
        except Exception as exc:
            logger.error(
                "get_linked_accounts_by_ip failed for %s: %s",
                ip_address, exc,
            )
            return []

    accounts: set[str] = set()
    for doc in docs:
        eid = doc.get("entity_id", "")
        lid = doc.get("linked_entity_id", "")
        if eid.startswith("ACC-"):
            accounts.add(eid)
        if lid.startswith("ACC-"):
            accounts.add(lid)
    return sorted(accounts)


async def save_investigation(case_data: dict) -> str:
    """Save or update an investigation case in the database.

    Creates a new case or updates an existing one based on ``case_id``.
    Use this tool when a new investigation is started or when findings,
    evidence, or status changes need to be persisted.

    Args:
        case_data: A dict containing investigation fields.  Must include
            ``case_id``.  All other fields are optional and will be
            merged via upsert.

    Returns:
        The ``case_id`` of the saved investigation, or an empty string
        on failure.
    """
    try:
        case_id = case_data.get("case_id")
        if not case_id:
            logger.error("save_investigation called without case_id")
            return ""

        case_data["updated_at"] = datetime.now(timezone.utc)

        # MCP path
        mcp_ok = await _mcp_update_one(
            "investigations",
            {"case_id": case_id},
            {"$set": case_data},
            upsert=True,
        )

        # Pymongo fallback
        if mcp_ok is None:
            await get_database()["investigations"].update_one(
                {"case_id": case_id},
                {"$set": case_data},
                upsert=True,
            )

        logger.info("Investigation %s saved", case_id)
        return case_id
    except Exception as exc:
        logger.error("save_investigation failed: %s", exc)
        return ""


async def append_audit_trail(
    case_id: str,
    action: str,
    agent_name: str,
    description: str,
) -> bool:
    """Append an entry to the audit trail of an investigation case.

    Records agent actions for compliance and transparency.  Every
    significant action taken during an investigation should be logged
    here to maintain a complete forensic record.

    Args:
        case_id: The investigation case identifier (e.g.
            ``"INV-2026-0542"``).
        action: Short action label (e.g. ``"evidence_collected"``,
            ``"risk_scored"``).
        agent_name: Name of the agent performing the action.
        description: Human-readable description of what was done.

    Returns:
        ``True`` if the entry was appended successfully, ``False``
        otherwise.
    """
    try:
        entry = {
            "timestamp": datetime.now(timezone.utc),
            "action": action,
            "agent": agent_name,
            "description": description,
        }
        update = {
            "$push": {"audit_trail": entry},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        }

        # MCP path
        mcp_ok = await _mcp_update_one(
            "investigations",
            {"case_id": case_id},
            update,
        )

        # Pymongo fallback
        if mcp_ok is None:
            result = await get_database()["investigations"].update_one(
                {"case_id": case_id}, update,
            )
            if result.matched_count == 0:
                logger.warning("append_audit_trail: case %s not found",
                               case_id)
                return False

        logger.info("Audit entry appended to %s: %s", case_id, action)
        return True
    except Exception as exc:
        logger.error("append_audit_trail failed for %s: %s", case_id, exc)
        return False


async def get_pending_alerts(limit: int = 10) -> list[dict]:
    """Retrieve pending alerts that need investigation, sorted by severity (critical first) and recency.

    Use this tool at the start of an investigation session to identify
    which alerts require immediate attention.

    Args:
        limit: Maximum number of alerts to return.  Defaults to 10.

    Returns:
        A list of alert dicts sorted by severity (critical → low) then
        by ``created_at`` (newest first).
    """
    # MCP path
    result = await _mcp_find("alerts", {"status": "new"})

    # Pymongo fallback
    if result is None:
        try:
            cursor = await get_database()["alerts"].find({"status": "new"}).to_list(length=None)
            result = [_serialize(doc) for doc in cursor]
        except Exception as exc:
            logger.error("get_pending_alerts failed: %s", exc)
            return []

    # Sort by severity (critical first), then by created_at desc
    result.sort(
        key=lambda a: (
            -_SEVERITY_ORDER.get(a.get("severity", "low"), 0),
            a.get("created_at", ""),
        ),
        reverse=False,
    )
    return result[:limit]


async def update_alert_status(alert_id: str, new_status: str) -> bool:
    """Update the status of a fraud alert.

    Transitions an alert through its lifecycle — for example from
    ``'new'`` to ``'investigating'`` when work begins, or to
    ``'resolved'`` / ``'false_positive'`` once a determination is made.

    Args:
        alert_id: The alert identifier (e.g. ``"ALT-2026-0001"``).
        new_status: The target status.  Typical values are ``"new"``,
            ``"investigating"``, ``"resolved"``, and
            ``"false_positive"``.

    Returns:
        ``True`` if the alert was found and updated, ``False`` otherwise.
    """
    try:
        update = {
            "$set": {
                "status": new_status,
                "updated_at": datetime.now(timezone.utc),
            },
        }

        # MCP path
        mcp_ok = await _mcp_update_one("alerts", {"alert_id": alert_id},
                                        update)

        # Pymongo fallback
        if mcp_ok is None:
            result = await get_database()["alerts"].update_one(
                {"alert_id": alert_id}, update,
            )
            if result.matched_count == 0:
                logger.warning("update_alert_status: alert %s not found",
                               alert_id)
                return False

        logger.info("Alert %s status updated to '%s'", alert_id, new_status)
        return True
    except Exception as exc:
        logger.error("update_alert_status failed for %s: %s",
                     alert_id, exc)
        return False


# ---------------------------------------------------------------------------
# 13. search_similar_fraud_patterns (was missing — caused ImportError)
# ---------------------------------------------------------------------------

async def search_similar_fraud_patterns(
    query_text: str,
    limit: int = 5,
) -> list[dict]:
    """Search for historically similar fraud patterns using embedding similarity.

    Embeds the query text and compares it against stored fraud pattern
    embeddings using MongoDB Atlas Vector Search. Returns the most similar known
    fraud patterns, enabling analysts to correlate current activity with
    historical cases.

    Args:
        query_text: Text description of the transaction or alert to search for.
        limit: Maximum number of similar patterns to return.
            Defaults to 5.

    Returns:
        A list of fraud pattern dicts, each augmented with a
        ``similarity_score`` (0–1, higher is more similar).  Returns an
        empty list if no patterns are found.
    """
    if not query_text:
        return []

    import os
    from google import genai
    try:
        client = genai.Client()
        response = client.models.embed_content(
            model="models/embedding-001",
            contents=query_text,
        )
        query_embedding = response.embeddings[0].values
    except Exception as exc:
        logger.warning("Failed to generate embedding: %s", exc)
        return []

    effective_limit = min(limit, settings.vector_search_limit)

    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": effective_limit * 10,
                "limit": effective_limit,
            }
        },
        {
            "$project": {
                "embedding": 0,
                "similarity_score": {"$meta": "vectorSearchScore"}
            }
        }
    ]

    # MCP path
    results = await _mcp_aggregate("fraud_patterns", pipeline)

    # Pymongo fallback
    if results is None:
        try:
            cursor = await get_database()["fraud_patterns"].aggregate(pipeline).to_list(length=None)
            results = [_serialize(doc) for doc in cursor]
        except Exception as exc:
            logger.error("search_similar_fraud_patterns failed: %s", exc)
            return []

    logger.info("search_similar_fraud_patterns: found %d matches", len(results))
    return results


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ---------------------------------------------------------------------------
# 14. record_analyst_feedback (for learning loop)
# ---------------------------------------------------------------------------

async def record_analyst_feedback(
    case_id: str,
    analyst_decision: str,
    override_score: int | None = None,
    reason: str = "",
) -> bool:
    """Record analyst feedback on an investigation for continuous improvement.

    Stores analyst overrides and decisions to enable the system to learn
    from human expert corrections over time.  This feedback is used to
    refine scoring weights and reduce false positives.

    Args:
        case_id: The investigation case identifier.
        analyst_decision: The analyst's final decision — one of
            ``"confirmed_fraud"``, ``"false_positive"``,
            ``"needs_more_info"``, or ``"escalated"``.
        override_score: Optional corrected fraud score (0–100).
        reason: Free-text justification for the decision.

    Returns:
        ``True`` if feedback was recorded successfully, ``False``
        otherwise.
    """
    try:
        feedback_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "analyst_decision": analyst_decision,
            "reason": reason,
        }
        if override_score is not None:
            feedback_entry["override_score"] = override_score

        update = {
            "$push": {"analyst_feedback": feedback_entry},
            "$set": {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "status": (
                    "resolved" if analyst_decision in
                    ("confirmed_fraud", "false_positive")
                    else "under_investigation"
                ),
            },
        }

        # MCP path
        mcp_ok = await _mcp_update_one(
            "investigations", {"case_id": case_id}, update,
        )

        # Pymongo fallback
        if mcp_ok is None:
            result = await get_database()["investigations"].update_one(
                {"case_id": case_id}, update,
            )
            if result.matched_count == 0:
                logger.warning("record_analyst_feedback: case %s not found",
                               case_id)
                return False

        logger.info("Analyst feedback recorded for %s: %s",
                     case_id, analyst_decision)
        return True
    except Exception as exc:
        logger.error("record_analyst_feedback failed for %s: %s",
                     case_id, exc)
        return False

async def get_scoring_adjustments() -> dict[str, int]:
    """Calculate scoring weight adjustments based on past analyst feedback.
    
    Returns a dict mapping factor names to their point adjustment delta.
    """
    try:
        result = await _mcp_find("investigations", {"analyst_feedback": {"$exists": True, "$not": {"$size": 0}}}, limit=100)
        if result is None:
            cursor = await get_database()["investigations"].find({"analyst_feedback": {"$exists": True, "$not": {"$size": 0}}}).limit(100).to_list(length=None)
            result = [_serialize(doc) for doc in cursor]
            
        adjustments = {}
        for doc in result:
            feedbacks = doc.get("analyst_feedback", [])
            if not feedbacks:
                continue
            fb = feedbacks[-1]
            decision = fb.get("analyst_decision")
            delta = 0
            if decision == "confirmed_fraud":
                delta = 1
            elif decision == "false_positive":
                delta = -1
                
            if delta != 0:
                factors = doc.get("risk_assessment", {}).get("factors", [])
                for f in factors:
                    if f.get("triggered"):
                        name = f.get("name")
                        if name:
                            adjustments[name] = adjustments.get(name, 0) + delta
                            
        for k in adjustments:
            adjustments[k] = max(-10, min(10, adjustments[k]))
            
        return adjustments
    except Exception as exc:
        logger.error("get_scoring_adjustments failed: %s", exc)
        return {}

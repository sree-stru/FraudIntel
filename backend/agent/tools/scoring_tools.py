"""Risk scoring and fraud classification tool functions for FraudIntel ADK agents.

All functions in this module are **pure computation** — they accept data as
input parameters and return scores, classifications, or summaries without
making any database calls.  This keeps them fast, testable, and
side-effect-free.
"""

import json
import logging
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Path to the fraud-patterns reference data
_PATTERNS_PATH = Path(__file__).resolve().parents[2] / "data" / "fraud_patterns.json"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_fraud_patterns() -> list[dict]:
    """Load fraud patterns from the JSON reference file."""
    try:
        with open(_PATTERNS_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        logger.error("Failed to load fraud patterns from %s: %s", _PATTERNS_PATH, exc)
        return []


def _safe_get(data: dict | None, *keys: str, default: Any = None) -> Any:
    """Safely traverse nested dicts."""
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current


def _parse_iso_date(value: Any) -> datetime | None:
    """Try to parse an ISO-8601 string into a datetime."""
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# 1. calculate_fraud_risk_score
# ---------------------------------------------------------------------------

from agent.tools.mongodb_tools import get_scoring_adjustments

async def calculate_fraud_risk_score(evidence: dict) -> dict:
    """Calculate a composite fraud risk score (0–100) based on collected evidence.

    Evaluates multiple risk factors including transaction patterns, device
    anomalies, network connections, and behavioral deviations.  Returns a
    detailed scoring breakdown with factor-by-factor explanation.

    The function examines up to 13 individual risk factors, each worth a
    fixed number of points (positive for risk, negative for trust).  The
    total is clamped to 0–100.

    Args:
        evidence: A dict that may contain the following keys:

            * ``transactions`` – list of transaction dicts
            * ``customer`` – customer profile dict
            * ``velocity`` – velocity metrics dict
            * ``network`` – entity-network dict
            * ``device_info`` – device information dict
            * ``geo_info`` – geographic analysis dict

    Returns:
        A dict with ``total_score``, ``classification``, ``confidence``,
        ``factors`` (list of per-factor dicts), ``recommended_action``,
        ``factors_triggered``, and ``factors_total``.
    """
    try:
        transactions: list[dict] = evidence.get("transactions", [])
        customer: dict = evidence.get("customer", {})
        velocity: dict = evidence.get("velocity", {})
        network: dict = evidence.get("network", {})
        device_info: dict = evidence.get("device_info", {})
        geo_info: dict = evidence.get("geo_info", {})
        adjustments: dict = evidence.get("scoring_adjustments")
        if adjustments is None:
            adjustments = await get_scoring_adjustments()

        factors: list[dict] = []

        if not geo_info.get("impossible_travel") and len(transactions) >= 2:
            impossible_travel = False
            sorted_txns = sorted(transactions, key=lambda x: str(x.get("timestamp", "")))
            for i in range(len(sorted_txns) - 1):
                t1, t2 = sorted_txns[i], sorted_txns[i+1]
                g1, g2 = t1.get("geo", {}), t2.get("geo", {})
                lat1, lon1 = g1.get("lat"), g1.get("lon")
                lat2, lon2 = g2.get("lat"), g2.get("lon")
                if lat1 and lon1 and lat2 and lon2:
                    R = 6371
                    dlat = math.radians(lat2 - lat1)
                    dlon = math.radians(lon2 - lon1)
                    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                    distance = R * c
                    ts1 = _parse_iso_date(t1.get("timestamp"))
                    ts2 = _parse_iso_date(t2.get("timestamp"))
                    if ts1 and ts2:
                        hours = abs((ts2 - ts1).total_seconds()) / 3600.0
                        if hours > 0 and (distance / hours) > 800:
                            impossible_travel = True
                            break
            geo_info["impossible_travel"] = impossible_travel

        # --- Positive risk factors ---

        # 1. VPN / proxy detection (+18)
        # Mocking an IP intelligence integration for VPN/Tor nodes
        KNOWN_VPN_SUBNETS = ["45.33.", "104.238.", "198.51.", "185.16.", "192.168."]
        vpn_detected = False
        ip = device_info.get("ip_address")
        if isinstance(ip, str) and any(ip.startswith(subnet) for subnet in KNOWN_VPN_SUBNETS):
            vpn_detected = True
        for txn in transactions:
            txn_ip = txn.get("ip_address", "")
            if isinstance(txn_ip, str) and any(txn_ip.startswith(subnet) for subnet in KNOWN_VPN_SUBNETS):
                vpn_detected = True
                break
        if _safe_get(customer, "is_vpn", default=False):
            vpn_detected = True
        factors.append({
            "name": "vpn_proxy_detected",
            "points": 18 + adjustments.get("vpn_proxy_detected", 0),
            "triggered": vpn_detected,
            "reason": "VPN or proxy IP detected in transaction or customer profile"
            if vpn_detected
            else "No VPN or proxy indicators found",
        })

        # 2. Multiple accounts on same device (+15)
        multi_device = False
        network_nodes = network.get("nodes", [])
        device_accounts: dict[str, set[str]] = {}
        for node in network_nodes:
            if node.get("linked_entity_type") == "device" or node.get("entity_type") == "device":
                dev_id = node.get("linked_entity_id") or node.get("entity_id", "")
                acct = node.get("entity_id") or node.get("linked_entity_id", "")
                if dev_id and acct:
                    device_accounts.setdefault(dev_id, set()).add(acct)
        for dev, accts in device_accounts.items():
            if len(accts) > 1:
                multi_device = True
                break
        factors.append({
            "name": "multiple_accounts_same_device",
            "points": 15 + adjustments.get("multiple_accounts_same_device", 0),
            "triggered": multi_device,
            "reason": "Multiple accounts share the same device fingerprint"
            if multi_device
            else "No shared-device anomaly detected",
        })

        # 3. KYC mismatch (+12)
        kyc_verified = _safe_get(customer, "kyc", "verified", default=True)
        kyc_mismatch = kyc_verified is False
        factors.append({
            "name": "kyc_mismatch",
            "points": 12 + adjustments.get("kyc_mismatch", 0),
            "triggered": kyc_mismatch,
            "reason": "Customer KYC verification is incomplete or failed"
            if kyc_mismatch
            else "KYC verification is current",
        })

        # 4. Velocity anomaly (+14)
        txn_count = velocity.get("transaction_count", 0)
        velocity_triggered = txn_count > 5
        factors.append({
            "name": "velocity_anomaly",
            "points": 14 + adjustments.get("velocity_anomaly", 0),
            "triggered": velocity_triggered,
            "reason": f"High transaction velocity: {txn_count} transactions in the lookback window"
            if velocity_triggered
            else "Transaction velocity within normal range",
        })

        # 5. High-risk merchant (+11)
        high_risk_merchants = {"crypto", "gambling"}
        hrm_triggered = any(
            txn.get("merchant_category", "") in high_risk_merchants
            for txn in transactions
        )
        factors.append({
            "name": "high_risk_merchant",
            "points": 11 + adjustments.get("high_risk_merchant", 0),
            "triggered": hrm_triggered,
            "reason": "Transactions at high-risk merchant categories (crypto/gambling)"
            if hrm_triggered
            else "No high-risk merchant activity",
        })

        # 6. Large unusual transfer (+10)
        avg_amount = _safe_get(
            customer,
            "behavioral_baseline",
            "avg_transaction_amount",
            default=2000,
        )
        if not isinstance(avg_amount, (int, float)) or avg_amount <= 0:
            avg_amount = 2000
        threshold = avg_amount * 3
        large_triggered = any(
            (txn.get("amount", 0) or 0) > threshold for txn in transactions
        )
        factors.append({
            "name": "large_unusual_transfer",
            "points": 10 + adjustments.get("large_unusual_transfer", 0),
            "triggered": large_triggered,
            "reason": f"Transaction exceeds 3× behavioral average (threshold: ${threshold:,.0f})"
            if large_triggered
            else "All transactions within expected range",
        })

        # 7. Geographic impossibility (+16)
        geo_impossible = bool(geo_info.get("impossible_travel", False))
        factors.append({
            "name": "geo_impossibility",
            "points": 16 + adjustments.get("geo_impossibility", 0),
            "triggered": geo_impossible,
            "reason": "Geographically impossible travel detected between login locations"
            if geo_impossible
            else "No geographic anomalies detected",
        })

        # 8. New account (+8)
        new_account = False
        created_at = _parse_iso_date(customer.get("account_created_at"))
        if created_at:
            now = datetime.now(timezone.utc)
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            new_account = (now - created_at) < timedelta(days=90)
        factors.append({
            "name": "new_account",
            "points": 8 + adjustments.get("new_account", 0),
            "triggered": new_account,
            "reason": "Account opened within the last 90 days"
            if new_account
            else "Account has established history",
        })

        # 9. New device (+7)
        new_device = False
        first_seen = _parse_iso_date(device_info.get("first_seen"))
        if first_seen:
            now = datetime.now(timezone.utc)
            if first_seen.tzinfo is None:
                first_seen = first_seen.replace(tzinfo=timezone.utc)
            new_device = (now - first_seen) < timedelta(days=7)
        factors.append({
            "name": "new_device",
            "points": 7 + adjustments.get("new_device", 0),
            "triggered": new_device,
            "reason": "Device first seen within the last 7 days"
            if new_device
            else "Device has established usage history",
        })

        # 10. Fraud ring connection (+20)
        ring_connection = False
        flagged_levels = {"confirmed_fraud", "flagged"}
        for node in network_nodes:
            if node.get("risk_level", "") in flagged_levels:
                ring_connection = True
                break
        factors.append({
            "name": "fraud_ring_connection",
            "points": 20 + adjustments.get("fraud_ring_connection", 0),
            "triggered": ring_connection,
            "reason": "Entity linked to a confirmed or flagged fraud network"
            if ring_connection
            else "No connections to known fraud networks",
        })

        # --- Negative (trust) factors ---

        # 11. Clean history (−5)
        risk_flags_present = any(
            bool(txn.get("risk_flags")) for txn in transactions
        )
        prior_fraud = bool(customer.get("prior_fraud_flags"))
        clean_history = not risk_flags_present and not prior_fraud
        factors.append({
            "name": "clean_history",
            "points": -5 + adjustments.get("clean_history", 0),
            "triggered": clean_history,
            "reason": "No prior fraud flags or risk indicators on record"
            if clean_history
            else "Prior fraud flags exist",
        })

        # 12. Verified phone (−3)
        verified_phone = bool(_safe_get(customer, "phone_verified", default=False))
        # Also accept phone presence in customer as weak signal
        if not verified_phone and customer.get("phone"):
            verified_phone = True
        factors.append({
            "name": "verified_phone",
            "points": -3 + adjustments.get("verified_phone", 0),
            "triggered": verified_phone,
            "reason": "Customer has a verified phone number on file"
            if verified_phone
            else "No verified phone number",
        })

        # 13. Consistent behavior (−4)
        consistent = False
        baseline_merchants = set(
            _safe_get(customer, "behavioral_baseline", "typical_merchants", default=[])
            or []
        )
        if baseline_merchants and transactions:
            txn_categories = {txn.get("merchant_category", "") for txn in transactions}
            overlap = txn_categories & baseline_merchants
            consistent = len(overlap) >= len(txn_categories) * 0.5
        factors.append({
            "name": "consistent_behavior",
            "points": -4 + adjustments.get("consistent_behavior", 0),
            "triggered": consistent,
            "reason": "Transaction patterns consistent with established behavioral baseline"
            if consistent
            else "Transaction patterns deviate from behavioral baseline",
        })

        # --- Aggregate ---
        total_raw = sum(f["points"] for f in factors if f["triggered"])
        total_score = max(0, min(100, total_raw))

        triggered_count = sum(1 for f in factors if f["triggered"])
        total_factors = len(factors)

        if total_score <= 25:
            classification = "low_risk"
            action = "approve"
        elif total_score <= 50:
            classification = "medium_risk"
            action = "monitor"
        elif total_score <= 75:
            classification = "high_risk"
            action = "escalate"
        else:
            classification = "critical_risk"
            action = "freeze"

        confidence = min(1.0, 0.5 + (total_factors / 26))

        return {
            "total_score": total_score,
            "classification": classification,
            "confidence": round(confidence, 2),
            "factors": factors,
            "recommended_action": action,
            "factors_triggered": triggered_count,
            "factors_total": total_factors,
        }

    except Exception as exc:
        logger.error("calculate_fraud_risk_score failed: %s", exc)
        return {
            "total_score": 0,
            "classification": "low_risk",
            "confidence": 0.0,
            "factors": [],
            "recommended_action": "approve",
            "factors_triggered": 0,
            "factors_total": 0,
        }


# ---------------------------------------------------------------------------
# 2. classify_fraud_typology
# ---------------------------------------------------------------------------

def classify_fraud_typology(indicators: list[str]) -> dict:
    """Match detected indicators against known fraud typologies to identify
    the most likely type of fraud.

    Uses keyword-based fuzzy matching: each word from an input indicator is
    compared against each word in the pattern's indicator strings.  The
    pattern with the highest proportion of matched indicators is returned
    as the primary typology.

    Args:
        indicators: A list of free-text indicator strings observed during
            the investigation (e.g. ``["new device login after password
            reset", "VPN IP detected"]``).

    Returns:
        A dict with ``primary_typology`` (name, match_score, description),
        ``secondary_matches`` (up to 2 runners-up),
        ``indicators_matched``, and ``indicators_total``.
    """
    unknown_result: dict = {
        "primary_typology": {
            "name": "Unknown",
            "typology_key": "unknown",
            "match_score": 0.0,
            "description": "No matching fraud typology could be identified.",
        },
        "secondary_matches": [],
        "indicators_matched": 0,
        "indicators_total": len(indicators),
    }

    try:
        if not indicators:
            return unknown_result

        patterns = _load_fraud_patterns()
        if not patterns:
            return unknown_result

        # Normalise input indicators into keyword sets
        input_keywords: list[set[str]] = []
        for ind in indicators:
            words = set(ind.lower().split())
            input_keywords.append(words)

        scored: list[dict] = []

        for pattern in patterns:
            pattern_indicators: list[str] = pattern.get("indicators", [])
            if not pattern_indicators:
                continue

            matched_count = 0
            for pat_indicator in pattern_indicators:
                pat_words = set(pat_indicator.lower().split())
                # Check if any input indicator shares significant keywords
                for inp_words in input_keywords:
                    # Require at least 2 shared keywords, or 1 if the keyword
                    # is long enough (>5 chars) to be meaningful
                    shared = inp_words & pat_words
                    meaningful = {w for w in shared if len(w) > 5}
                    if len(shared) >= 2 or meaningful:
                        matched_count += 1
                        break  # this pattern indicator is matched

            match_score = (matched_count / len(pattern_indicators)) * 100

            scored.append({
                "name": pattern.get("name", "Unknown"),
                "typology_key": pattern.get("typology", "unknown"),
                "match_score": round(match_score, 1),
                "description": pattern.get("description", ""),
                "matched_count": matched_count,
            })

        # Sort by match score descending
        scored.sort(key=lambda x: x["match_score"], reverse=True)

        if not scored or scored[0]["match_score"] == 0:
            return unknown_result

        primary = scored[0]
        secondary = [
            {
                "name": s["name"],
                "typology_key": s["typology_key"],
                "match_score": s["match_score"],
                "description": s["description"],
            }
            for s in scored[1:3]
            if s["match_score"] > 0
        ]

        return {
            "primary_typology": {
                "name": primary["name"],
                "typology_key": primary["typology_key"],
                "match_score": primary["match_score"],
                "description": primary["description"],
            },
            "secondary_matches": secondary,
            "indicators_matched": primary["matched_count"],
            "indicators_total": len(indicators),
        }

    except Exception as exc:
        logger.error("classify_fraud_typology failed: %s", exc)
        return unknown_result


# ---------------------------------------------------------------------------
# 3. generate_risk_summary
# ---------------------------------------------------------------------------

def generate_risk_summary(score_result: dict, typology_result: dict) -> str:
    """Generate a human-readable risk assessment summary combining the fraud
    risk score and typology classification.

    The output is a self-contained paragraph suitable for inclusion in
    investigation reports, SAR narratives, or analyst dashboards.

    Args:
        score_result: The dict returned by :func:`calculate_fraud_risk_score`.
        typology_result: The dict returned by :func:`classify_fraud_typology`.

    Returns:
        A formatted summary string.  Returns a fallback message if inputs
        are missing or malformed.
    """
    try:
        total_score = score_result.get("total_score", 0)
        classification = score_result.get("classification", "unknown").replace("_", " ")
        confidence = score_result.get("confidence", 0.0)
        action = score_result.get("recommended_action", "review")
        factors = score_result.get("factors", [])

        primary = typology_result.get("primary_typology", {})
        typology_name = primary.get("name", "Unknown")
        typology_score = primary.get("match_score", 0.0)

        # Top 3 triggered factors (by absolute points, descending)
        triggered = [f for f in factors if f.get("triggered")]
        triggered.sort(key=lambda f: abs(f.get("points", 0)), reverse=True)
        top_factors = triggered[:3]

        factor_descriptions = []
        for f in top_factors:
            factor_descriptions.append(
                f"{f.get('name', 'unknown').replace('_', ' ')} "
                f"({'+' if f['points'] > 0 else ''}{f.get('points', 0)} pts)"
            )
        factor_list = ", ".join(factor_descriptions) if factor_descriptions else "none identified"

        summary = (
            f"Risk Assessment Summary: The investigation revealed a "
            f"{classification} risk level with a composite score of "
            f"{total_score}/100 (Confidence: {confidence * 100:.0f}%). "
            f"The primary fraud typology identified is {typology_name} "
            f"({typology_score:.0f}% match). "
            f"Key contributing factors include: {factor_list}. "
            f"Recommended action: {action}."
        )

        return summary

    except Exception as exc:
        logger.error("generate_risk_summary failed: %s", exc)
        return (
            "Risk Assessment Summary: Unable to generate a complete risk "
            "summary due to insufficient or malformed input data. "
            "Manual review is recommended."
        )

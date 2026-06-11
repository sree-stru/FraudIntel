"""MongoDB connection and database utilities for FraudIntel.

Provides async database access via the motor driver, including lazy
client initialisation, collection helpers, index management, and
connection health checks.
"""

import logging
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase

from agent.config import COLLECTION_NAMES, settings

logger = logging.getLogger(__name__)

# Module-level lazy singletons
_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def get_client() -> AsyncIOMotorClient:
    """Return the shared ``AsyncIOMotorClient``, creating it on first call."""
    global _client
    if _client is None:
        logger.info("Creating new MongoDB client connection")
        _client = AsyncIOMotorClient(settings.mongodb_uri)
    return _client


def get_database() -> AsyncIOMotorDatabase:
    """Return the application database handle."""
    global _db
    if _db is None:
        _db = get_client()[settings.mongodb_database]
    return _db


def get_collection(name: str) -> AsyncIOMotorCollection:
    """Return a collection handle by *name*."""
    return get_database()[name]


async def check_connection() -> bool:
    """Ping the MongoDB server and return ``True`` on success."""
    try:
        await get_client().admin.command("ping")
        logger.info("MongoDB connection check succeeded")
        return True
    except Exception as exc:
        logger.error("MongoDB connection check failed: %s", exc)
        return False


async def get_collection_stats() -> dict[str, int]:
    """Return document counts for every collection in ``COLLECTION_NAMES``.

    Collections that don't yet exist will report a count of ``0``.
    """
    stats: dict[str, int] = {}
    db = get_database()
    for name in COLLECTION_NAMES:
        try:
            count = await db[name].count_documents({})
            stats[name] = count
        except Exception as exc:
            logger.warning("Could not count documents in '%s': %s", name, exc)
            stats[name] = 0
    return stats


async def ensure_indexes() -> None:
    """Create required indexes across application collections.

    Each index creation is wrapped individually so that a single failure
    does not prevent the remaining indexes from being created.
    """
    db = get_database()

    index_definitions: list[tuple[str, list[tuple[str, int]], dict[str, Any]]] = [
        # (collection, keys, kwargs)
        ("transactions", [("account_id", 1), ("timestamp", -1)], {}),
        ("transactions", [("device_fingerprint", 1)], {}),
        ("transactions", [("ip_address", 1)], {}),
        ("entity_relationships", [("entity_id", 1), ("linked_entity_id", 1)], {}),
        ("entity_relationships", [("entity_type", 1)], {}),
        ("alerts", [("status", 1), ("severity", -1), ("created_at", -1)], {}),
        ("investigations", [("case_id", 1)], {"unique": True}),
        ("investigations", [("status", 1)], {}),
    ]

    for collection_name, keys, kwargs in index_definitions:
        try:
            index_name = await db[collection_name].create_index(keys, **kwargs)
            logger.info(
                "Created index '%s' on collection '%s'",
                index_name,
                collection_name,
            )
        except Exception as exc:
            logger.error(
                "Failed to create index %s on '%s': %s",
                keys,
                collection_name,
                exc,
            )


async def close_connection() -> None:
    """Close the MongoDB client and reset module-level singletons."""
    global _client, _db
    if _client is not None:
        logger.info("Closing MongoDB client connection")
        _client.close()
        _client = None
        _db = None

"""Configuration module for FraudIntel AI Agent System.

Loads environment variables from .env and exposes application settings,
collection names, and fraud typology definitions.
"""

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file (no error if missing)
load_dotenv(override=False)


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # Google Cloud
    google_cloud_project: str
    google_cloud_location: str = "us-central1"
    gemini_model: str = "gemini-3.0-pro"
    gemini_api_key: str = ""

    # MongoDB
    mongodb_uri: str
    mongodb_database: str = "fraudintel"

    # Application
    app_host: str = "0.0.0.0"
    app_port: int = 8080
    app_env: str = "development"
    log_level: str = "INFO"

    # Timeouts
    mcp_timeout_seconds: int = 15
    agent_timeout_seconds: int = 60

    # Security
    api_key: str = ""
    max_graph_depth: int = 4
    vector_search_limit: int = 5

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton settings instance
settings = Settings()

# MongoDB collection names used throughout the application
COLLECTION_NAMES: list[str] = [
    "transactions",
    "customers",
    "entity_relationships",
    "investigations",
    "fraud_patterns",
    "alerts",
]

# Fraud typology keys mapped to human-readable display names
FRAUD_TYPOLOGIES: dict[str, str] = {
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
    "insider_threat": "Insider Threat",
}

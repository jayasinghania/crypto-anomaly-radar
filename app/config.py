"""
Shared configuration used across ingestion and analytics, so both sides
of the pipeline agree on the same asset list without importing each
other's unrelated logic.
"""

ASSETS = ["bitcoin", "ethereum", "solana", "cardano", "dogecoin"]

"""Pytest configuration — set required env vars before any backend imports."""

import os

# Set dummy values for required env vars so Settings() can be instantiated in tests.
# Tests that need to verify specific values should monkeypatch these.
os.environ.setdefault("PINECONE_API_KEY", "test-pinecone-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")

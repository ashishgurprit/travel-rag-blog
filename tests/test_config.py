import pytest
from pydantic import ValidationError


def test_settings_loads_from_env_vars(monkeypatch):
    monkeypatch.setenv("PINECONE_API_KEY", "test-pinecone-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")

    from backend.config import Settings

    s = Settings()
    assert s.pinecone_api_key == "test-pinecone-key"
    assert s.anthropic_api_key == "test-anthropic-key"


def test_default_values(monkeypatch):
    monkeypatch.setenv("PINECONE_API_KEY", "test-pinecone-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")

    from backend.config import Settings

    s = Settings()
    assert s.pinecone_index_name == "travel-rag"
    assert s.confidence_threshold == 0.75


def test_missing_required_fields_raises_error(monkeypatch):
    """Settings cannot be instantiated without required env vars."""
    from backend.config import Settings

    monkeypatch.delenv("PINECONE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises((ValidationError, RuntimeError)):
        Settings(_env_file=None)

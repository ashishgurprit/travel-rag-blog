import pytest
from pydantic_settings import SettingsConfigDict


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


def test_required_fields_present_in_class():
    from backend.config import Settings

    assert "pinecone_api_key" in Settings.model_fields
    assert "anthropic_api_key" in Settings.model_fields

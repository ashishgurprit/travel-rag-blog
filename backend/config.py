from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    pinecone_api_key: str
    pinecone_environment: str = ""
    pinecone_index_name: str = "travel-rag"
    anthropic_api_key: str
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "travel-rag-indexer/1.0"
    youtube_api_key: str = ""
    tavily_api_key: str = ""
    booking_affiliate_id: str = ""
    klook_affiliate_id: str = ""
    wise_affiliate_id: str = ""
    redis_url: str = "redis://localhost:6379"
    redis_cache_ttl: int = 86400
    cors_origin: str = "http://localhost:3000"
    confidence_threshold: float = 0.75

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


try:
    settings = Settings()
except ValidationError as exc:
    raise RuntimeError(
        "Missing required configuration. "
        "Ensure PINECONE_API_KEY and ANTHROPIC_API_KEY are set in your environment or .env file.\n"
        f"Details: {exc}"
    ) from exc

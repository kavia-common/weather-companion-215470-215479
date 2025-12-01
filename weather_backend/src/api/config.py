from pydantic import BaseModel


class Settings(BaseModel):
    """Application settings and constants."""
    app_title: str = "Weather Companion Backend"
    app_description: str = (
        "Backend service providing weather and geocoding endpoints, powered by Open‑Meteo."
    )
    app_version: str = "0.1.0"

    # HTTP client settings
    http_timeout_seconds: float = 8.0

    # Simple in-memory cache TTL in seconds (<= 60 as per requirements)
    cache_ttl_seconds: int = 45


settings = Settings()

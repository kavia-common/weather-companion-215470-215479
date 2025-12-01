import time
from typing import Any, Dict, Optional, Tuple

import httpx

from src.api.config import settings


WEATHER_BASE = "https://api.open-meteo.com/v1/forecast"

# Simple in-memory cache with TTL to avoid hammering the free API
_cache: Dict[Tuple[str, Tuple[Tuple[str, Any], ...]], Tuple[float, Any]] = {}


def _cache_get(key: Tuple[str, Tuple[Tuple[str, Any], ...]]) -> Optional[Any]:
    ttl = settings.cache_ttl_seconds
    if ttl <= 0:
        return None
    item = _cache.get(key)
    if not item:
        return None
    ts, data = item
    if (time.time() - ts) <= ttl:
        return data
    # Expired
    try:
        del _cache[key]
    except KeyError:
        pass
    return None


def _cache_set(key: Tuple[str, Tuple[Tuple[str, Any], ...]], data: Any) -> None:
    ttl = settings.cache_ttl_seconds
    if ttl <= 0:
        return
    _cache[key] = (time.time(), data)


def _params_to_key(endpoint: str, params: Dict[str, Any]) -> Tuple[str, Tuple[Tuple[str, Any], ...]]:
    # Normalize to a hashable key
    sorted_items = tuple(sorted(params.items(), key=lambda x: x[0]))
    return (endpoint, sorted_items)


# PUBLIC_INTERFACE
async def get_current_weather(lat: float, lon: float) -> Dict[str, Any]:
    """Fetch current weather from Open-Meteo for given coordinates."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "hourly": "weathercode,temperature_2m",
        "timezone": "auto",
    }
    key = _params_to_key("current", params)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    timeout = httpx.Timeout(settings.http_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(WEATHER_BASE, params=params)
        resp.raise_for_status()
        data = resp.json()

    _cache_set(key, data)
    return data


# PUBLIC_INTERFACE
async def get_forecast(lat: float, lon: float, days: int = 3) -> Dict[str, Any]:
    """Fetch forecast from Open-Meteo for given coordinates."""
    # Constrain days to reasonable bounds per free API and requirement
    days = max(1, min(days, 10))

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "weathercode,temperature_2m_max,temperature_2m_min",
        "hourly": "weathercode,temperature_2m",
        "forecast_days": days,
        "timezone": "auto",
    }
    key = _params_to_key("forecast", params)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    timeout = httpx.Timeout(settings.http_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(WEATHER_BASE, params=params)
        resp.raise_for_status()
        data = resp.json()

    _cache_set(key, data)
    return data


def _weathercode_to_text_icon(code: Optional[int]) -> Tuple[Optional[str], Optional[str]]:
    # Minimal mapping; could be expanded as needed.
    mapping = {
        0: ("Clear sky", "clear"),
        1: ("Mainly clear", "clear"),
        2: ("Partly cloudy", "partly_cloudy"),
        3: ("Overcast", "cloudy"),
        45: ("Fog", "fog"),
        48: ("Depositing rime fog", "fog"),
        51: ("Light drizzle", "drizzle"),
        61: ("Slight rain", "rain"),
        63: ("Moderate rain", "rain"),
        65: ("Heavy rain", "rain"),
        71: ("Slight snow", "snow"),
        80: ("Rain showers", "showers"),
        95: ("Thunderstorm", "thunder"),
    }
    if code is None:
        return None, None
    return mapping.get(code, (f"Code {code}", "unknown"))

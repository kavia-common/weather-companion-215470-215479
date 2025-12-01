import time
from typing import Any, Dict, Optional, Tuple

import httpx

from src.api.config import settings


GEOCODE_SEARCH_BASE = "https://geocoding-api.open-meteo.com/v1/search"
GEOCODE_REVERSE_BASE = "https://geocoding-api.open-meteo.com/v1/reverse"

# Simple in-memory cache with TTL
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
    sorted_items = tuple(sorted(params.items(), key=lambda x: x[0]))
    return (endpoint, sorted_items)


# PUBLIC_INTERFACE
async def geocode_search(query: str, count: int = 10) -> Dict[str, Any]:
    """Search locations by text query using Open-Meteo geocoding."""
    params = {"name": query, "count": max(1, min(count, 20))}
    key = _params_to_key("search", params)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    timeout = httpx.Timeout(settings.http_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(GEOCODE_SEARCH_BASE, params=params)
        resp.raise_for_status()
        data = resp.json()

    _cache_set(key, data)
    return data


# PUBLIC_INTERFACE
async def reverse_geocode(lat: float, lon: float) -> Dict[str, Any]:
    """Reverse geocode coordinates using Open-Meteo."""
    params = {"latitude": lat, "longitude": lon}
    key = _params_to_key("reverse", params)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    timeout = httpx.Timeout(settings.http_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(GEOCODE_REVERSE_BASE, params=params)
        resp.raise_for_status()
        data = resp.json()

    _cache_set(key, data)
    return data

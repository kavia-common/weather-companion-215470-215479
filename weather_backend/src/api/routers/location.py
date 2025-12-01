from typing import List

from fastapi import APIRouter, HTTPException, Query

from src.api.clients.geocoding_client import geocode_search, reverse_geocode
from src.api.models import (
    Coordinates,
    LocationSearchItem,
    LocationSearchResponse,
    ReverseGeocodeResponse,
    ErrorResponse,
)

router = APIRouter(
    prefix="/location",
    tags=["Location"],
    responses={404: {"model": ErrorResponse, "description": "Not found"}},
)


@router.get(
    "/search",
    summary="Search locations",
    description="Search for locations by free-text query using Open‑Meteo geocoding.",
    response_model=LocationSearchResponse,
    responses={
        200: {"description": "Search results"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        502: {"model": ErrorResponse, "description": "Upstream provider error"},
    },
)
async def search(q: str = Query(..., description="Search text, e.g., city or place name")) -> LocationSearchResponse:
    """Search locations by text query."""
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required.")
    try:
        data = await geocode_search(q, count=10)
    except Exception as ex:
        raise HTTPException(status_code=502, detail=f"Failed to search locations: {ex}")

    items: List[LocationSearchItem] = []
    for r in (data or {}).get("results") or []:
        items.append(
            LocationSearchItem(
                id=str(r.get("id")) if r.get("id") is not None else None,
                name=r.get("name") or "",
                country=r.get("country"),
                state=r.get("admin1") or r.get("admin2"),
                coordinates=Coordinates(lat=float(r.get("latitude")), lon=float(r.get("longitude"))),
            )
        )
    return LocationSearchResponse(results=items)


@router.get(
    "/reverse",
    summary="Reverse geocode",
    description="Reverse geocode coordinates to a nearby place name using Open‑Meteo geocoding.",
    response_model=ReverseGeocodeResponse,
    responses={
        200: {"description": "Reverse geocode result"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "Not found"},
        502: {"model": ErrorResponse, "description": "Upstream provider error"},
    },
)
async def reverse(lat: float = Query(..., description="Latitude"), lon: float = Query(..., description="Longitude")) -> ReverseGeocodeResponse:
    """Reverse geocode coordinates and return the best match."""
    try:
        data = await reverse_geocode(lat, lon)
    except Exception as ex:
        raise HTTPException(status_code=502, detail=f"Failed to reverse geocode: {ex}")

    results = (data or {}).get("results") or []
    if not results:
        # Not necessarily an error; return empty result with 200
        return ReverseGeocodeResponse(result=None)

    r0 = results[0]
    item = LocationSearchItem(
        id=str(r0.get("id")) if r0.get("id") is not None else None,
        name=r0.get("name") or "",
        country=r0.get("country"),
        state=r0.get("admin1") or r0.get("admin2"),
        coordinates=Coordinates(lat=float(r0.get("latitude")), lon=float(r0.get("longitude"))),
    )
    return ReverseGeocodeResponse(result=item)

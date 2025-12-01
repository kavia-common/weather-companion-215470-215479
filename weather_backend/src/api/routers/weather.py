from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from src.api.clients.weather_client import get_current_weather, get_forecast, _weathercode_to_text_icon
from src.api.clients.geocoding_client import geocode_search
from src.api.models import (
    Coordinates,
    Location,
    CurrentWeather,
    CurrentWeatherResponse,
    DailyForecastItem,
    HourlyForecastItem,
    ForecastResponse,
    ErrorResponse,
)

router = APIRouter(
    prefix="/weather",
    tags=["Weather"],
    responses={404: {"model": ErrorResponse, "description": "Not found"}},
)


def _resolve_location_from_query(q: Optional[str], lat: Optional[float], lon: Optional[float]):
    if q:
        return q, None, None
    if lat is not None and lon is not None:
        return None, lat, lon
    raise HTTPException(status_code=400, detail="Provide either 'q' or both 'lat' and 'lon' parameters.")


async def _resolve_coordinates_and_location(
    q: Optional[str], lat: Optional[float], lon: Optional[float]
) -> tuple[float, float, Location]:
    name_q, lat_in, lon_in = _resolve_location_from_query(q, lat, lon)

    if name_q:
        geo = await geocode_search(name_q, count=1)
        results = (geo or {}).get("results") or []
        if not results:
            raise HTTPException(status_code=404, detail="Location not found for query.")
        r0 = results[0]
        lat_v = float(r0.get("latitude"))
        lon_v = float(r0.get("longitude"))
        loc = Location(
            name=r0.get("name") or name_q,
            country=r0.get("country"),
            state=r0.get("admin1") or r0.get("admin2"),
            coordinates=Coordinates(lat=lat_v, lon=lon_v),
        )
        return lat_v, lon_v, loc

    # lat/lon provided
    lat_v = float(lat_in)  # type: ignore[arg-type]
    lon_v = float(lon_in)  # type: ignore[arg-type]
    loc = Location(
        name=f"{lat_v:.4f},{lon_v:.4f}",
        country=None,
        state=None,
        coordinates=Coordinates(lat=lat_v, lon=lon_v),
    )
    return lat_v, lon_v, loc


@router.get(
    "/current",
    summary="Get current weather",
    description="Returns current weather for a specified location by text query or coordinates.",
    response_model=CurrentWeatherResponse,
    responses={
        200: {"description": "Current weather response"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "Not found"},
        502: {"model": ErrorResponse, "description": "Upstream provider error"},
    },
)
async def current_weather(
    q: Optional[str] = Query(None, description="Free-text location query (e.g., 'Berlin')"),
    lat: Optional[float] = Query(None, description="Latitude in decimal degrees"),
    lon: Optional[float] = Query(None, description="Longitude in decimal degrees"),
) -> CurrentWeatherResponse:
    """Endpoint to retrieve current weather. Provide either q or lat/lon."""
    try:
        lat_v, lon_v, loc = await _resolve_coordinates_and_location(q, lat, lon)
        data = await get_current_weather(lat_v, lon_v)
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=502, detail=f"Failed to fetch current weather: {ex}")

    cw = (data or {}).get("current_weather") or {}
    weather_code = cw.get("weathercode")
    text, icon = _weathercode_to_text_icon(weather_code)
    current = CurrentWeather(
        temperature_c=cw.get("temperature"),
        wind_speed_kph=(cw.get("windspeed") * 1.0) if cw.get("windspeed") is not None else None,
        wind_direction_deg=cw.get("winddirection"),
        weather_code=weather_code,
        condition_text=text,
        condition_icon=icon,
        observation_time_iso=cw.get("time"),
    )
    return CurrentWeatherResponse(location=loc, current=current)


@router.get(
    "/forecast",
    summary="Get weather forecast",
    description="Returns daily and hourly forecast for a location by text query or coordinates.",
    response_model=ForecastResponse,
    responses={
        200: {"description": "Forecast response"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "Not found"},
        502: {"model": ErrorResponse, "description": "Upstream provider error"},
    },
)
async def forecast(
    q: Optional[str] = Query(None, description="Free-text location query (e.g., 'Berlin')"),
    lat: Optional[float] = Query(None, description="Latitude in decimal degrees"),
    lon: Optional[float] = Query(None, description="Longitude in decimal degrees"),
    days: int = Query(3, ge=1, le=10, description="Number of forecast days (1-10)"),
) -> ForecastResponse:
    """Endpoint to retrieve forecast (daily + hourly). Provide either q or lat/lon."""
    try:
        lat_v, lon_v, loc = await _resolve_coordinates_and_location(q, lat, lon)
        data = await get_forecast(lat_v, lon_v, days=days)
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=502, detail=f"Failed to fetch forecast: {ex}")

    daily_raw = (data or {}).get("daily") or {}
    hourly_raw = (data or {}).get("hourly") or {}

    daily_items: list[DailyForecastItem] = []
    dates = daily_raw.get("time") or []
    tmax = daily_raw.get("temperature_2m_max") or []
    tmin = daily_raw.get("temperature_2m_min") or []
    wcodes = daily_raw.get("weathercode") or []

    for i in range(min(len(dates), len(tmax), len(tmin), len(wcodes))):
        code = wcodes[i]
        text, icon = _weathercode_to_text_icon(code)
        daily_items.append(
            DailyForecastItem(
                date=dates[i],
                min_temp_c=tmin[i],
                max_temp_c=tmax[i],
                weather_code=code,
                condition_text=text,
                condition_icon=icon,
            )
        )

    hourly_items: list[HourlyForecastItem] = []
    times = hourly_raw.get("time") or []
    temps = hourly_raw.get("temperature_2m") or []
    hwcodes = hourly_raw.get("weathercode") or []
    for i in range(min(len(times), len(temps), len(hwcodes))):
        code = hwcodes[i]
        text, icon = _weathercode_to_text_icon(code)
        hourly_items.append(
            HourlyForecastItem(
                time_iso=times[i],
                temp_c=temps[i],
                weather_code=code,
                condition_text=text,
                condition_icon=icon,
            )
        )

    return ForecastResponse(location=loc, daily=daily_items, hourly=hourly_items)

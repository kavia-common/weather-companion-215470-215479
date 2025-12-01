from typing import List, Optional
from pydantic import BaseModel, Field


# PUBLIC_INTERFACE
class ErrorResponse(BaseModel):
    """Structure returned for error responses."""
    detail: str = Field(..., description="Human readable error detail message.")


# PUBLIC_INTERFACE
class Coordinates(BaseModel):
    """Geographic coordinates."""
    lat: float = Field(..., description="Latitude in decimal degrees.")
    lon: float = Field(..., description="Longitude in decimal degrees.")


# PUBLIC_INTERFACE
class Location(BaseModel):
    """Normalized location model."""
    name: str = Field(..., description="Display name of the location.")
    country: Optional[str] = Field(None, description="Country of the location.")
    state: Optional[str] = Field(None, description="State/region of the location.")
    coordinates: Coordinates = Field(..., description="Coordinates of the location.")


# PUBLIC_INTERFACE
class CurrentWeather(BaseModel):
    """Normalized current weather conditions."""
    temperature_c: float = Field(..., description="Current air temperature in °C.")
    wind_speed_kph: Optional[float] = Field(None, description="Wind speed in km/h.")
    wind_direction_deg: Optional[float] = Field(None, description="Wind direction in degrees.")
    weather_code: Optional[int] = Field(None, description="Open-Meteo weather code.")
    condition_text: Optional[str] = Field(None, description="Short textual condition.")
    condition_icon: Optional[str] = Field(None, description="Icon URL or identifier.")
    observation_time_iso: Optional[str] = Field(None, description="ISO8601 observation time.")


# PUBLIC_INTERFACE
class CurrentWeatherResponse(BaseModel):
    """Combined current weather and location response payload."""
    location: Location = Field(..., description="Resolved location information.")
    current: CurrentWeather = Field(..., description="Current weather data.")


# PUBLIC_INTERFACE
class DailyForecastItem(BaseModel):
    """Daily forecast item."""
    date: str = Field(..., description="ISO date (YYYY-MM-DD) for the forecast.")
    min_temp_c: Optional[float] = Field(None, description="Minimum temperature in °C.")
    max_temp_c: Optional[float] = Field(None, description="Maximum temperature in °C.")
    weather_code: Optional[int] = Field(None, description="Open-Meteo weather code.")
    condition_text: Optional[str] = Field(None, description="Short textual condition.")
    condition_icon: Optional[str] = Field(None, description="Icon URL or identifier.")


# PUBLIC_INTERFACE
class HourlyForecastItem(BaseModel):
    """Hourly forecast item."""
    time_iso: str = Field(..., description="ISO8601 timestamp for the forecast hour.")
    temp_c: Optional[float] = Field(None, description="Temperature in °C.")
    weather_code: Optional[int] = Field(None, description="Open-Meteo weather code.")
    condition_text: Optional[str] = Field(None, description="Short textual condition.")
    condition_icon: Optional[str] = Field(None, description="Icon URL or identifier.")


# PUBLIC_INTERFACE
class ForecastResponse(BaseModel):
    """Forecast response containing daily and hourly data."""
    location: Location = Field(..., description="Resolved location information.")
    daily: List[DailyForecastItem] = Field(default_factory=list, description="List of daily forecasts.")
    hourly: List[HourlyForecastItem] = Field(default_factory=list, description="List of hourly forecasts.")


# PUBLIC_INTERFACE
class LocationSearchItem(BaseModel):
    """Single location search result."""
    id: Optional[str] = Field(None, description="Provider-specific ID if available.")
    name: str = Field(..., description="Display name of the result.")
    country: Optional[str] = Field(None, description="Country of the result.")
    state: Optional[str] = Field(None, description="State/region of the result.")
    coordinates: Coordinates = Field(..., description="Coordinates of the result.")


# PUBLIC_INTERFACE
class LocationSearchResponse(BaseModel):
    """Search results for a text query."""
    results: List[LocationSearchItem] = Field(default_factory=list, description="List of search results.")


# PUBLIC_INTERFACE
class ReverseGeocodeResponse(BaseModel):
    """Reverse geocode response by coordinates."""
    result: Optional[LocationSearchItem] = Field(
        None, description="Best match for the provided coordinates."
    )

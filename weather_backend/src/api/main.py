from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.config import settings
from src.api.routers.weather import router as weather_router
from src.api.routers.location import router as location_router

openapi_tags = [
    {"name": "Health", "description": "Service health and meta endpoints."},
    {"name": "Weather", "description": "Weather endpoints powered by Open‑Meteo."},
    {"name": "Location", "description": "Location search and reverse geocoding using Open‑Meteo."},
]

app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    version=settings.app_version,
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Keep permissive CORS as requested
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"], summary="Health check")
def health_check():
    """Simple health check endpoint."""
    return {"message": "Healthy"}


# Mount routers
app.include_router(weather_router)
app.include_router(location_router)

from fastapi import FastAPI, Request, Response
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from contextlib import asynccontextmanager

from models.geocode_model import ReverseGeocodeRequest
from models.search_model import SearchRequest
from database.database import engine, Base
import database.models  # Import models to ensure they are registered with Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables in the database
    async with engine.begin() as conn:
        # Note: In production you would probably use Alembic instead of this
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Clean up (if needed)
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/templates"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"app": app}
    )

@app.post("/api/search")
async def search(request: SearchRequest):
    # TODO: Implement search logic (e.g. forward geocoding or autocomplete)
    # Return a stub response for now
    return {
        "status": "success",
        "query": request.query,
        "results": [
            {"name": f"Stub result for '{request.query}'", "lat": 51.505, "lng": -0.09}
        ]
    }

@app.post("/api/reverse-geocode")
async def reverse_geocode(request: ReverseGeocodeRequest):
    # TODO: Implement reverse geocoding logic based on lat and lng
    # Return a stub response for now
    lat, lng = request.lat, request.lng

    return {
        "status": "success",
        "lat": lat,
        "lng": lng,
        "address": f"Stub address for {lat}, {lng}"
    }
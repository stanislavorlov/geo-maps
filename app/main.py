from fastapi import FastAPI, Request, Response
from fastapi.params import Depends
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio.session import AsyncSession
from database.location_repository import LocationRepository
from database.database import get_db
from models.geocode_model import ReverseGeocodeRequest
from models.search_model import SearchRequest
from database.database import engine, Base
import database.models  # Import models to ensure they are registered with Base
import logging

# configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

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
async def search(request: SearchRequest, db: AsyncSession = Depends(get_db)):
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
async def reverse_geocode(request: ReverseGeocodeRequest, db: AsyncSession = Depends(get_db)):
    # TODO: Implement reverse geocoding logic based on lat and lng
    # Return a stub response for now

    repository = LocationRepository(db=db)

    lat, lng = request.lat, request.lng
    logger.info(f"Quering geocode position: {request}")

    location = await repository.get(lat, lng)
    
    if location:
        # Convert SQLAlchemy model to dict, ignoring internal state
        loc_dict = {c.name: getattr(location, c.name) for c in location.__table__.columns}
        logger.debug(f"Database result: {loc_dict}")
    else:
        logger.debug("Database result: None")

    # Determine a display name based on location data
    address = "Unknown Location"
    if location:
        if location.name:
            address = location.name
        elif location.description:
            address = location.description
        else:
            address = f"Unnamed location (ID: {location.id})"

    return {
        "status": "success",
        "lat": lat,
        "lng": lng,
        "address": address,
        "location": {
            "id": location.id if location else None,
            "name": location.name if location else None,
            "description": location.description if location else None
        }
    }
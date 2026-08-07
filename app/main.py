import asyncio

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
from models.search_model import SearchRequest, RouteRequest
from database.database import engine, Base
import database.models  # Import models to ensure they are registered with Base
import logging

# configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from graph.graph import Graph

async def async_graph_worker_loop(app: FastAPI):
    try:
        logger.info("Starting asynchronous graph loading from file...")
        def load_graph():
            g = Graph(nodes=[], edges=[])
            try:
                try:
                    g.load_file("graph.json.gz")
                    logger.info("Loaded graph from graph.json.gz")
                except FileNotFoundError:
                    g.load_file("graph.json")
                    logger.info("Loaded graph from graph.json")
                return g
            except FileNotFoundError:
                logger.warning("Neither graph.json.gz nor graph.json was found. Make sure to generate it using the parser.")
                return g

        # Load graph in a separate thread to keep event loop unblocked
        graph = await asyncio.to_thread(load_graph)
        app.state.graph = graph
        logger.info(f"Graph loaded successfully: {len(graph.nodes)} nodes, {len(graph.edges)} edges.")
        
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("Graph worker loop caught cancellation. Cleaning up...")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.debug("Application starting up...")

    worker_task = asyncio.create_task(async_graph_worker_loop(app))

    # Create all tables in the database
    async with engine.begin() as conn:
        # Note: In production you would probably use Alembic instead of this
        await conn.run_sync(Base.metadata.create_all)
    yield
    logger.debug("Application shutting down...")
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        print("Worker successfully stopped.")
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

@app.post("/api/find_route")
async def find_route(request: RouteRequest, db: AsyncSession = Depends(get_db)):
    # TODO: Implement route finding logic using Dijkstra's algorithm or A*
    # Return a stub response for now
    return {
        "status": "success",
        "route": [
            # it should be just an array of points
            [ request.from_.lat, request.from_.lng ],
            [ request.to.lat, request.to.lng ]
            # ...
        ]
    }

# var latlngs = [
#     [45.51, -122.68],
#     [37.77, -122.43],
#     [34.04, -118.2]
# ];
#
# var polyline = L.polyline(latlngs, {color: 'red'}).addTo(map);
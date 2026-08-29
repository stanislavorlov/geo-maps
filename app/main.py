import asyncio
from math import cos, radians
from fastapi import FastAPI, Request, Response
from fastapi.params import Depends
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio.session import AsyncSession
from database.location_repository import LocationRepository
from database.database import get_db
from database.route_repository import RouteRepository
from models.geocode_model import ReverseGeocodeRequest
from models.search_model import SearchRequest, RouteRequest
from database.database import engine, Base
import database.models  # Import models to ensure they are registered with Base
import logging
from graph.graph import Graph
from geoalchemy2.shape import to_shape
from routing.dijkstra_routing import shortest_path_map

# configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_LONDON_SPEED = 30  # mph

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

def find_nearest_location(locations, lat: float, lng: float):
    """Return the Location closest to (lat, lng), or None if locations is empty."""
    best, best_dist = None, float("inf")
    # Longitude degrees shrink with latitude; correct for that so the
    # nearest-node choice is not biased along the east-west axis.
    lng_scale = cos(radians(lat))
    for location in locations:
        point = to_shape(location.geom)
        d = (point.y - lat) ** 2 + ((point.x - lng) * lng_scale) ** 2
        if d < best_dist:
            best, best_dist = location, d
    return best

@app.post("/api/find_route")
async def find_route(request: RouteRequest, db: AsyncSession = Depends(get_db)):
    repository = RouteRepository(db=db)

    query_result = await repository.query_route(request.from_, request.to)

    logger.info(f"Query result count: {len(query_result)}")

    '''
    TODO:
    Database already returns a set of points between 2 coordinates (it should also respect roads)
    Based on returned dataset, app should build a graph and apply some algorithm (Dijkstra's algorithm or A*) for finding routes
    Graph should involve the roads (edges) as well, so need to find out on how to query those as well
    Based on algorithm result, return the shortest path
    '''

    # Collect the unique graph nodes returned by the query
    locations: set[database.models.Location] = set()
    for _road, loc_from, loc_to in query_result:
        locations.add(loc_from)
        locations.add(loc_to)

    # Snap request coordinates to the nearest graph node.
    # An exact coordinate match will almost never happen for a user click,
    # so we pick the closest Location instead.
    location_from = find_nearest_location(locations, request.from_.lat, request.from_.lng)
    location_to = find_nearest_location(locations, request.to.lat, request.to.lng)

    if location_from is None or location_to is None:
        logger.warning("No graph nodes found near the requested coordinates")
        return {"status": "error", "message": "No roads found near the requested points"}

    logger.info(f"Location from {location_from.id} to {location_to.id}")

    result : list[database.models.Road] = shortest_path_map(query_result, location_from, location_to)

    if not result:
        logger.warning("No path found between the requested points")
        return {"status": "error", "message": "No route found between the requested points"}

    # id -> (loc_from, loc_to) so the path can be turned back into coordinates
    edges_by_road_id = {road.id: (loc_from, loc_to) for road, loc_from, loc_to in query_result}

    output = []
    total_distance = 0.0
    total_time = 0.0
    for road in result:
        loc_from, loc_to = edges_by_road_id[road.id]

        if not output:
            output.append([to_shape(loc_from.geom).y, to_shape(loc_from.geom).x])
        # Only append the far end - the near end is the previous edge's far end
        output.append([to_shape(loc_to.geom).y, to_shape(loc_to.geom).x])

        total_distance += road.distance
        #'road_type': road.road_type
        total_time += road.distance / (road.speed if road.speed else DEFAULT_LONDON_SPEED)

    return {
        "status": "success",
        "distance": total_distance,
        "time": total_time,
        "path": output,
    }
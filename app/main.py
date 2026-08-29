import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

import database.models  # Import models to ensure they are registered with Base
from database.database import Base, engine
from graph.graph import Graph
from routes import directions, geocoding, pages

# configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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

app.include_router(pages.router)
app.include_router(geocoding.router)
app.include_router(directions.router)

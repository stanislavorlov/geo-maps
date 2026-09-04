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


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.debug("Application starting up...")

    # Create all tables in the database
    async with engine.begin() as conn:
        # Note: In production you would probably use Alembic instead of this
        await conn.run_sync(Base.metadata.create_all)
    yield
    logger.debug("Application shutting down...")

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/templates"), name="static")

app.include_router(pages.router)
app.include_router(geocoding.router)
app.include_router(directions.router)

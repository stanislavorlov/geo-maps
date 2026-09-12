import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
from database.database import Base, engine
from api import directions, geocoding, pages

# configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.debug("Application starting up...")

    # Create all tables in the database and apply incremental column migrations
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        from sqlalchemy import text
        await conn.execute(text("ALTER TABLE roads ADD COLUMN IF NOT EXISTS name VARCHAR;"))
        await conn.execute(text("ALTER TABLE roads ADD COLUMN IF NOT EXISTS tags JSON;"))
    yield
    logger.debug("Application shutting down...")

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/templates"), name="static")

app.include_router(pages.router)
app.include_router(geocoding.router)
app.include_router(directions.router)

import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# PostgreSQL connection string
# We use asyncpg for asynchronous database operations
# Format: postgresql+asyncpg://user:password@host:port/dbname
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://geo_user:geo_password@localhost:5432/geo_maps"
)

# Create the async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create a sessionmaker
async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# Dependency to get DB session for FastAPI routes
async def get_db():
    async with async_session() as session:
        yield session

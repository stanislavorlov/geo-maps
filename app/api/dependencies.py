from fastapi import Depends
from sqlalchemy.ext.asyncio.session import AsyncSession
from database.database import get_db
from database.graph_repository import GraphRepository
from database.location_repository import LocationRepository
from services.speed_limit_service import SpeedLimitService
from services.travel_time_service import TravelTimeService


def get_speed_limit_service() -> SpeedLimitService:
    return SpeedLimitService()


def get_travel_time_service() -> TravelTimeService:
    return TravelTimeService()


def get_location_repository(
    db: AsyncSession = Depends(get_db)
) -> LocationRepository:
    return LocationRepository(db=db)


def get_graph_repository(
    db: AsyncSession = Depends(get_db),
    limit_service: SpeedLimitService = Depends(get_speed_limit_service)
) -> GraphRepository:
    return GraphRepository(
        db=db,
        limit_service=limit_service,
    )
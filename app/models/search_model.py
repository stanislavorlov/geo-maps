from pydantic import BaseModel

from app.models.geocode_model import ReverseGeocodeRequest


class SearchRequest(BaseModel):
    query: str

class RouteRequest(BaseModel):
    from_: ReverseGeocodeRequest
    to: ReverseGeocodeRequest
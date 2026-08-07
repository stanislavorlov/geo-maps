from pydantic import BaseModel
from .geocode_model import ReverseGeocodeRequest


class SearchRequest(BaseModel):
    query: str

class RouteRequest(BaseModel):
    from_: ReverseGeocodeRequest
    to: ReverseGeocodeRequest
from pydantic import BaseModel

class ReverseGeocodeRequest(BaseModel):
    lat: float
    lng: float
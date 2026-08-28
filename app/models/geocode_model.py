from pydantic import BaseModel, ConfigDict


class ReverseGeocodeRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    lat: float
    lng: float

# model = ReverseGeocodeRequest(lat=0.0, lng=0.0)
# dictionary = dict()
# dictionary[model] = "route"
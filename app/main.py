from fastapi import FastAPI, Request, Response
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/templates"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"app": app}
    )

@app.get("/api/search")
async def search(query: str):
    # TODO: Implement search logic (e.g. forward geocoding or autocomplete)
    # Return a stub response for now
    return {
        "status": "success",
        "query": query,
        "results": [
            {"name": f"Stub result for '{query}'", "lat": 51.505, "lng": -0.09}
        ]
    }

@app.get("/api/reverse-geocode")
async def reverse_geocode(lat: float, lng: float):
    # TODO: Implement reverse geocoding logic based on lat and lng
    # Return a stub response for now
    return {
        "status": "success",
        "lat": lat,
        "lng": lng,
        "address": f"Stub address for {lat}, {lng}"
    }
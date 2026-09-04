from math import cos, radians
from geoalchemy2.shape import to_shape


def find_nearest_location(locations, lat: float, lng: float):
    """Return the Location closest to (lat, lng), or None if locations is empty."""
    best, best_dist = None, float("inf")
    # Longitude degrees shrink with latitude; correct for that so the
    # nearest-node choice is not biased along the east-west axis.
    lng_scale = cos(radians(lat))
    for location in locations:
        point = to_shape(location.geom)
        d = (point.y - lat) ** 2 + ((point.x - lng) * lng_scale) ** 2
        if d < best_dist:
            best, best_dist = location, d
    return best
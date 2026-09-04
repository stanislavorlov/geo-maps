from enum import StrEnum


class TravelMode(StrEnum):
    CAR = "car"
    BICYCLE = "bicycle"
    WALK = "walk"


SPEEDS_KMH: dict[str, dict[TravelMode, float]] = {
    "motorway": {
        TravelMode.CAR: 110,
    },
    "motorway_link": {
        TravelMode.CAR: 70,
    },
    "trunk": {
        TravelMode.CAR: 90,
        TravelMode.BICYCLE: 18,
    },
    "primary": {
        TravelMode.CAR: 60,
        TravelMode.BICYCLE: 18,
        TravelMode.WALK: 5,
    },
    "secondary": {
        TravelMode.CAR: 50,
        TravelMode.BICYCLE: 18,
        TravelMode.WALK: 5,
    },
    "tertiary": {
        TravelMode.CAR: 40,
        TravelMode.BICYCLE: 18,
        TravelMode.WALK: 5,
    },
    "residential": {
        TravelMode.CAR: 30,
        TravelMode.BICYCLE: 16,
        TravelMode.WALK: 5,
    },
    "living_street": {
        TravelMode.CAR: 10,
        TravelMode.BICYCLE: 12,
        TravelMode.WALK: 4,
    },
    "service": {
        TravelMode.CAR: 15,
        TravelMode.BICYCLE: 12,
        TravelMode.WALK: 4,
    },
    "cycleway": {
        TravelMode.BICYCLE: 20,
        TravelMode.WALK: 5,
    },
    "path": {
        TravelMode.BICYCLE: 12,
        TravelMode.WALK: 4,
    },
    "footway": {
        TravelMode.WALK: 5,
    },
    "pedestrian": {
        TravelMode.WALK: 4.5,
    },
    "steps": {
        TravelMode.WALK: 2.5,
    },
}
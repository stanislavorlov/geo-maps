METERS_PER_MILE = 1609.344
SECONDS_PER_HOUR = 3600.0
MINUTES_PER_HOUR = 60.0

# 1 mph in meters per second (~0.44704 m/s)
MPH_TO_METERS_PER_SECOND = METERS_PER_MILE / SECONDS_PER_HOUR

# 1 mph in meters per minute (~26.8224 m/min)
MPH_TO_METERS_PER_MINUTE = METERS_PER_MILE / MINUTES_PER_HOUR


def calculate_travel_time(distance_meters: float, speed_mph: float, in_minutes: bool = True) -> float:
    """
    Calculate travel time given distance in meters and speed in mph.

    :param distance_meters: Distance of the road segment in meters.
    :param speed_mph: Speed limit / travel speed in miles per hour (mph).
    :param in_minutes: If True, returns time in minutes. If False, returns time in seconds.
    :return: Travel time (in minutes or seconds).
    """
    if speed_mph <= 0 or distance_meters <= 0:
        return 0.0

    if in_minutes:
        return distance_meters / (speed_mph * MPH_TO_METERS_PER_MINUTE)
    else:
        return distance_meters / (speed_mph * MPH_TO_METERS_PER_SECOND)

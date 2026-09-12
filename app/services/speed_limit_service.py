from enum import StrEnum
from typing import Optional, Union


class TravelMode(StrEnum):
    DRIVING = "driving"
    CYCLING = "cycling"
    WALKING = "walking"
    TRANSIT = "transit"

class SpeedLimitService:
    def __init__(self):
        # Speeds in mph (or km/h converted to mph: 1 km/h = 0.621371 mph)
        # If a road_type is NOT in the mode's dictionary, that road is FORBIDDEN for that mode (unless overridden by tags).
        self.MODE_PROFILES: dict[TravelMode, dict[str, float]] = {
            TravelMode.DRIVING: {
                "motorway": 70.0,
                "motorway_link": 45.0,
                "trunk": 50.0,
                "trunk_link": 40.0,
                "primary": 30.0,
                "primary_link": 25.0,
                "secondary": 30.0,
                "secondary_link": 20.0,
                "tertiary": 25.0,
                "residential": 20.0,
                "living_street": 10.0,
                "service": 10.0,
                "unclassified": 25.0,
            },
            TravelMode.CYCLING: {
                "cycleway": 12.0,
                "path": 10.0,
                "living_street": 10.0,
                "residential": 12.0,
                "tertiary": 12.0,
                "secondary": 10.0,
                "primary": 10.0,
                "service": 8.0,
                "unclassified": 10.0,
                "track": 8.0,
            },
            TravelMode.WALKING: {
                "footway": 3.1,  # ~5 km/h
                "pedestrian": 3.1,
                "steps": 1.5,
                "path": 3.0,
                "living_street": 3.0,
                "residential": 3.0,
                "service": 3.0,
                "tertiary": 3.0,
                "secondary": 2.5,
                "primary": 2.5,
                "unclassified": 3.0,
                "track": 2.5,
            },
        }

    def calculate_allowed_road_types(self, travel_mode: TravelMode):
        return list(self.MODE_PROFILES[travel_mode].keys())

    def get_effective_speed(
            self,
            road_type: Optional[str],
            mode: Union[TravelMode, str],
            explicit_speed: Optional[float] = None,
            tags: Optional[dict] = None,
            is_reverse: bool = False
    ) -> Optional[float]:
        """
        Returns effective speed in mph if the road is accessible by the travel mode in the given direction,
        or None if forbidden.

        Factors considered:
        - General and mode-specific access permissions (e.g. access=private, bicycle=no, foot=no)
        - One-way directionality per mode (including contraflow bicycle lanes and two-way pedestrian access)
        - Mode infrastructure overrides (e.g. cycleway=lane on primary road, sidewalk=both)
        - Surface type speed multiplier (e.g. cobblestone, gravel, mud)
        """
        if isinstance(mode, str):
            mode = TravelMode(mode)

        tags = tags or {}
        road_type = road_type or ""

        # 1. Access Filtering
        access = str(tags.get("access", "")).lower()
        if access in ("private", "no"):
            # Check mode-specific explicit override
            if mode == TravelMode.DRIVING and str(tags.get("motor_vehicle", "")).lower() not in ("yes", "permissive",
                                                                                                 "destination") and str(
                    tags.get("motorcar", "")).lower() not in ("yes", "permissive", "destination"):
                return None
            if mode == TravelMode.CYCLING and str(tags.get("bicycle", "")).lower() not in ("yes", "permissive",
                                                                                           "designated", "destination"):
                return None
            if mode == TravelMode.WALKING and str(tags.get("foot", "")).lower() not in ("yes", "permissive",
                                                                                        "designated", "destination"):
                return None

        # Check explicit mode bans
        if mode == TravelMode.DRIVING:
            if str(tags.get("motor_vehicle", "")).lower() in ("no", "private") or str(
                    tags.get("motorcar", "")).lower() in ("no", "private"):
                return None
        elif mode == TravelMode.CYCLING:
            if str(tags.get("bicycle", "")).lower() in ("no", "use_sidepath", "private"):
                return None
        elif mode == TravelMode.WALKING:
            if str(tags.get("foot", "")).lower() in ("no", "private", "use_sidepath"):
                return None

        # 2. One-Way Directionality
        oneway = str(tags.get("oneway", "")).lower()
        junction = str(tags.get("junction", "")).lower()
        is_default_oneway = (road_type in ("motorway", "motorway_link") or junction == "roundabout") and oneway != "no"

        if is_reverse:
            if mode == TravelMode.DRIVING:
                if oneway in ("yes", "1", "true") or is_default_oneway:
                    return None
            elif mode == TravelMode.CYCLING:
                if oneway in ("yes", "1", "true") or is_default_oneway:
                    # Check for contraflow bicycle infrastructure
                    oneway_bicycle = str(tags.get("oneway:bicycle", "")).lower()
                    cycleway = str(tags.get("cycleway", "")).lower()
                    cycleway_left = str(tags.get("cycleway:left", "")).lower()
                    cycleway_right = str(tags.get("cycleway:right", "")).lower()
                    cycleway_both = str(tags.get("cycleway:both", "")).lower()

                    has_contraflow = (
                            oneway_bicycle in ("no", "0", "false") or
                            cycleway in ("opposite", "opposite_lane", "opposite_track", "share_busway") or
                            any(c in ("opposite", "opposite_lane", "opposite_track") for c in
                                (cycleway_left, cycleway_right, cycleway_both))
                    )
                    if not has_contraflow:
                        return None
            elif mode == TravelMode.WALKING:
                # Pedestrians can walk bidirectional on roads where foot traffic is permitted
                pass
        else:  # Forward traversal (not is_reverse)
            if oneway == "-1":
                if mode == TravelMode.DRIVING:
                    return None
                elif mode == TravelMode.CYCLING:
                    oneway_bicycle = str(tags.get("oneway:bicycle", "")).lower()
                    if oneway_bicycle not in ("no", "0", "false"):
                        return None

        # 3. Base Speed & Road Type Accessibility
        profile = self.MODE_PROFILES.get(mode, {})
        base_speed: Optional[float] = None

        if mode == TravelMode.CYCLING:
            cycleway = str(tags.get("cycleway", "")).lower()
            bicycle = str(tags.get("bicycle", "")).lower()
            if road_type == "cycleway":
                base_speed = 12.0
            elif cycleway in ("lane", "track", "separate", "opposite", "opposite_lane", "opposite_track",
                              "share_busway") or bicycle in ("designated", "yes"):
                # Dedicated cycle infrastructure bonus speed
                base_speed = 14.0
            elif road_type in profile:
                base_speed = profile[road_type]
            else:
                return None
        elif mode == TravelMode.WALKING:
            sidewalk = str(tags.get("sidewalk", "")).lower()
            foot = str(tags.get("foot", "")).lower()
            if sidewalk in ("both", "left", "right", "yes", "separate") or foot in ("yes", "designated"):
                base_speed = 3.1
            elif road_type in profile:
                base_speed = profile[road_type]
            else:
                return None
        elif mode == TravelMode.DRIVING:
            if road_type in profile:
                if explicit_speed and explicit_speed > 0:
                    base_speed = explicit_speed
                else:
                    base_speed = profile[road_type]
            else:
                return None
        else:
            if road_type in profile:
                base_speed = profile[road_type]
            else:
                return None

        # 4. Surface Factor Multiplier
        surface = str(tags.get("surface", "")).lower()
        surface_factor = 1.0

        if surface in ("cobblestone", "sett", "unpaved", "gravel", "fine_gravel", "compacted", "ground", "dirt",
                       "earth", "grass", "wood"):
            surface_factor = 0.6 if mode == TravelMode.CYCLING else 0.8
        elif surface in ("sand", "mud"):
            surface_factor = 0.4
        elif surface in ("paving_stones",):
            surface_factor = 0.85 if mode == TravelMode.CYCLING else 1.0

        effective_speed = base_speed * surface_factor
        return max(0.1, effective_speed)
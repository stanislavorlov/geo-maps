from typing import Optional, Any, Dict


class GeocodeService:
    @staticmethod
    def get_location_display_data(location: Optional[Any]) -> Dict[str, Any]:
        """Extracts and formats display strings from a location object."""
        if not location:
            return {
                "address": "Unknown Location",
                "id": None,
                "name": "Unknown location"
            }

        return {
            "address": location.name or location.description or f"Unnamed location (ID: {location.id})",
            "id": location.id,
            "name": location.description or location.name or "Unknown location"
        }
import urllib.request
import urllib.parse
import sys

def download_osm_map(min_lon: float, min_lat: float, max_lon: float, max_lat: float, output_file: str):
    """
    Downloads OSM data for a given bounding box using the Overpass API.
    Uses the standard library urllib.request.
    """
    # Overpass API endpoint
    url = "https://overpass-api.de/api/interpreter"
    
    # Optimized Overpass QL query to only fetch roads (highways) and their referenced nodes
    query = f"""[out:xml][timeout:90];
(
  way["highway"]({min_lat},{min_lon},{max_lat},{max_lon});
);
(._;>;);
out body;"""
    
    print(f"Requesting map data for bounding box:")
    print(f"  Latitude:  {min_lat} to {max_lat}")
    print(f"  Longitude: {min_lon} to {max_lon}")
    print(f"Sending query to Overpass API: {url} ...")
    
    data = urllib.parse.urlencode({'data': query}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'User-Agent': 'GeoMapsParser/1.0 PythonUrllib'})
    
    try:
        with urllib.request.urlopen(req) as response:
            print("Download started...")
            osm_data = response.read()
            with open(output_file, 'wb') as f:
                f.write(osm_data)
            print(f"Successfully downloaded and saved map data to: {output_file}")
    except Exception as e:
        print(f"Failed to download map data: {e}")
        # Fallback to direct OSM API if Overpass fails
        print("Attempting fallback to standard OSM API...")
        fallback_url = f"https://api.openstreetmap.org/api/0.6/map?bbox={min_lon},{min_lat},{max_lon},{max_lat}"
        fallback_req = urllib.request.Request(fallback_url, headers={'User-Agent': 'GeoMapsParser/1.0 PythonUrllib'})
        try:
            with urllib.request.urlopen(fallback_req) as response:
                osm_data = response.read()
                with open(output_file, 'wb') as f:
                    f.write(osm_data)
                print(f"Successfully downloaded map using standard API to: {output_file}")
        except Exception as fallback_err:
            print(f"Fallback failed too: {fallback_err}")

if __name__ == "__main__":
    # Coordinates from user's URL query parameter
    # minlon=-0.15071868896484378&minlat=51.600559935576975&maxlon=-0.10085105895996095&maxlat=51.62198665798708
    min_lon = -0.15071868896484378
    min_lat = 51.600559935576975
    max_lon = -0.10085105895996095
    max_lat = 51.62198665798708
    
    output_filename = "london_large.osm"
    download_osm_map(min_lon, min_lat, max_lon, max_lat, output_filename)

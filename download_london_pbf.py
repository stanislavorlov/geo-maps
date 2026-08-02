import urllib.request
import os

def download_london_pbf():
    url = "https://download.geofabrik.de/europe/united-kingdom/england/greater-london-latest.osm.pbf"
    output_filename = "greater-london-latest.osm.pbf"
    
    print(f"Downloading Greater London extract from Geofabrik...")
    print(f"URL: {url}")
    
    req = urllib.request.Request(url, headers={'User-Agent': 'GeoMapsParser/1.0 PythonUrllib'})
    try:
        with urllib.request.urlopen(req) as response:
            meta = response.info()
            content_length_header = meta.get("Content-Length")
            file_size = int(content_length_header) if content_length_header else None
            
            if file_size:
                print(f"File size: {file_size / (1024 * 1024):.2f} MB")
            else:
                print("File size unknown.")
                
            block_size = 8192
            downloaded = 0
            
            with open(output_filename, 'wb') as f:
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    downloaded += len(buffer)
                    f.write(buffer)
                    if file_size:
                        percent = downloaded * 100 / file_size
                        # Print progress updates every 10%
                        if int(percent) % 10 == 0 and int((downloaded - len(buffer)) * 100 / file_size) % 10 != 0:
                            print(f"Progress: {percent:.1f}% ({downloaded / (1024 * 1024):.2f} MB)")
            
            print(f"Successfully downloaded and saved: {output_filename}")
    except Exception as e:
        print(f"Error downloading file: {e}")

if __name__ == "__main__":
    download_london_pbf()

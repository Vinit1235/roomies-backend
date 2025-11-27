import csv
import json
import time
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# Initialize Geocoder
geolocator = Nominatim(user_agent="roomies_demo_fetcher")

def get_coordinates(college_name, city, area):
    """Fetch coordinates for a college."""
    search_query = f"{college_name}, {area}, {city}"
    try:
        location = geolocator.geocode(search_query)
        if location:
            return location.latitude, location.longitude
        
        # Fallback: Try just College Name and City
        search_query = f"{college_name}, {city}"
        location = geolocator.geocode(search_query)
        if location:
            return location.latitude, location.longitude
            
        return None, None
    except Exception as e:
        print(f"Error geocoding {college_name}: {e}")
        return None, None

def get_nearby_hostels(lat, lon, radius=2000):
    """
    Fetch hostels/PGs within 'radius' meters of (lat, lon) using OpenStreetMap Overpass API.
    """
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      node["tourism"="hostel"](around:{radius},{lat},{lon});
      node["building"="dormitory"](around:{radius},{lat},{lon});
      node["amenity"="student_accommodation"](around:{radius},{lat},{lon});
      way["tourism"="hostel"](around:{radius},{lat},{lon});
      way["building"="dormitory"](around:{radius},{lat},{lon});
    );
    out center;
    """
    try:
        response = requests.get(overpass_url, params={'data': overpass_query})
        data = response.json()
        places = []
        for element in data.get('elements', []):
            name = element.get('tags', {}).get('name', 'Unknown Hostel')
            
            # Get coordinates (node has lat/lon, way has center lat/lon)
            if element['type'] == 'node':
                p_lat, p_lon = element['lat'], element['lon']
            else:
                p_lat, p_lon = element.get('center', {}).get('lat'), element.get('center', {}).get('lon')
                
            if p_lat and p_lon:
                places.append({
                    "name": name,
                    "lat": p_lat,
                    "lon": p_lon,
                    "type": element.get('tags', {}).get('tourism', 'accommodation')
                })
        return places
    except Exception as e:
        print(f"Error fetching OSM data: {e}")
        return []

def main():
    colleges_data = []
    
    with open('data/mumbai_engineering_colleges.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        print(f"CSV Columns: {reader.fieldnames}")
        for row in reader:
            name = row.get('Name') or row.get('name') # Try both case
            if not name:
                print(f"Skipping row: {row}")
                continue
            city = row['City']
            area = row['Area']
            
            print(f"Processing: {name}...")
            
            # 1. Get College Location
            lat, lon = get_coordinates(name, city, area)
            
            if lat and lon:
                print(f"  Found Location: {lat}, {lon}")
                
                # 2. Get Nearby Hostels
                print(f"  Searching for hostels nearby...")
                hostels = get_nearby_hostels(lat, lon)
                print(f"  Found {len(hostels)} hostels/dorms.")
                
                colleges_data.append({
                    "college": name,
                    "location": {"lat": lat, "lon": lon},
                    "nearby_hostels": hostels
                })
            else:
                print(f"  Could not find location for {name}")
            
            # Be nice to the APIs
            time.sleep(1.5)

    # Save to JSON
    with open('data/real_data_dump.json', 'w', encoding='utf-8') as f:
        json.dump(colleges_data, f, indent=2)
    
    print("\nDone! Data saved to data/real_data_dump.json")

if __name__ == "__main__":
    main()

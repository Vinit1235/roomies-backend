import urllib.request
import json
import os
import time

API_KEY = "rnd_cTOdDdx1JHDHkidZ96UQkWGRe1Ay"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json"
}
SERVICE_NAME_FILTER = "roomies-app"

def get_json(url):
    print(f"Fetching: {url}")
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Error fetching {url}: {e} (Body: {e.read().decode() if hasattr(e, 'read') else 'No body'})")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    # 1. Get Service ID
    services = get_json("https://api.render.com/v1/services")
    if not services:
        print("Failed to list services")
        return

    target_service = None
    for service_entry in services:
        srv = service_entry.get('service', service_entry)
        if srv.get('name') == SERVICE_NAME_FILTER:
            target_service = srv
            break
    
    if not target_service:
        print(f"Service '{SERVICE_NAME_FILTER}' not found.")
        return

    service_id = target_service['id']
    print(f"Service ID: {service_id}")
    
    # 2. Try fetching Service Logs (if endpoint exists)
    # common endpoint pattern: /services/{id}/logs
    print("\n--- Attempting GET /services/{id}/logs ---")
    logs = get_json(f"https://api.render.com/v1/services/{service_id}/logs?limit=100")
    if logs:
        print(f"Found {len(logs)} log entries")
        with open("render_service_logs.json", "w") as f:
            json.dump(logs, f, indent=2)
            
        print("Preview:")
        for entry in logs[:5]:
             print(entry)
    else:
        print("Failed to get logs via /service/{id}/logs")

    # 3. Try fetching deploy logs for the latest deploy specificially if not found
    # But search said /logs is general.
    
    # 4. Try fetching events
    print("\n--- Attempting GET /services/{id}/events ---")
    events = get_json(f"https://api.render.com/v1/services/{service_id}/events?limit=20")
    if events:
        print(f"Found {len(events)} events")
        with open("render_events.json", "w") as f:
            json.dump(events, f, indent=2)

if __name__ == "__main__":
    main()

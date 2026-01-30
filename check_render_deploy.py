import urllib.request
import json
import os

API_KEY = "rnd_cTOdDdx1JHDHkidZ96UQkWGRe1Ay"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json"
}
SERVICE_NAME_FILTER = "roomies-app"

def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Error fetching {url}: {e}")
        return None

def main():
    print("Fetching services...")
    services = get_json("https://api.render.com/v1/services")
    if not services:
        return

    target_service = None
    for service_entry in services:
        # The API usually returns a list or a list wrapper. 
        # Render API returns structured data. Let's inspect carefully.
        # It's usually a list of dicts.
        # Actually checking the structure might be safer, but let's assume list of dicts.
        # Handle pagination if necessary? For now just check first page.
        srv = service_entry.get('service', service_entry) # sometimes it's wrapped
        if srv.get('name') == SERVICE_NAME_FILTER:
            target_service = srv
            break
    
    with open("deploy_status.txt", "w") as f:
        if not target_service:
            f.write(f"Service '{SERVICE_NAME_FILTER}' not found.\n")
            f.write(f"Available services: {[s.get('service', s).get('name') for s in services]}\n")
            return

        service_id = target_service['id']
        f.write(f"Found service '{SERVICE_NAME_FILTER}' (ID: {service_id})\n")

        print(f"Fetching deployments for service {service_id}...")
        deployments = get_json(f"https://api.render.com/v1/services/{service_id}/deploys")
        
        if not deployments:
            f.write("No deployments found or error fetching deployments.\n")
            return

        f.write("\nRecent Deployments:\n")
        for dep in deployments[:3]: # Show top 3
            d = dep.get('deploy', dep)
            status = d.get('status')
            commit = d.get('commit', {}).get('message', 'No commit msg')
            created_at = d.get('createdAt')
            f.write(f"- Status: {status}\n")
            f.write(f"  Created: {created_at}\n")
            f.write(f"  Commit: {commit}\n")
            f.write("-" * 20 + "\n")

if __name__ == "__main__":
    main()

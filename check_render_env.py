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
    services = get_json("https://api.render.com/v1/services")
    if not services:
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
    
    # Fetch environment variables
    # Note: Render API endpoint for env vars is /services/{serviceId}/env-vars
    print(f"Fetching env vars for service {service_id}...")
    env_vars = get_json(f"https://api.render.com/v1/services/{service_id}/env-vars")
    
    with open("env_check_status.txt", "w") as f:
        f.write(f"Environment Verification for '{SERVICE_NAME_FILTER}'\n")
        f.write("="*40 + "\n\n")
        
        if not env_vars:
            f.write("Could not fetch environment variables.\n")
            return

        # Render API returns a list of objects like [{'key': '...', 'value': '...'}]
        # Let's map them for easier checking
        # Format might be list of dicts with 'envVar' key containing name/value
        
        current_vars = {}
        for item in env_vars:
            # Structure check: might be item['envVar']['key']
            ev = item.get('envVar', item) 
            current_vars[ev['key']] = ev['value']

        # List of expected keys based on RENDER_FIX_GUIDE.md or app knowledge
        expected_keys = [
            "RAZORPAY_KEY_ID",
            "RAZORPAY_KEY_SECRET",
            "MAIL_SERVER",
            "MAIL_PORT",
            "MAIL_USERNAME",
            "MAIL_PASSWORD",
            # Add other common ones if known, e.g. DATABASE_URL usually handled by Render linking
        ]

        f.write("Variable Status:\n")
        for key in expected_keys:
            if key in current_vars:
                # Mask sensitive values
                val = current_vars[key]
                masked = val[:4] + "*" * (len(val)-4) if len(val) > 4 else "****"
                f.write(f"[OK] {key} is set. (Value: {masked})\n")
            else:
                f.write(f"[MISSING] {key} is NOT set.\n")

        f.write("\nAll Variables Found:\n")
        for key, val in current_vars.items():
            if key not in expected_keys:
                 f.write(f"- {key}\n")

if __name__ == "__main__":
    main()

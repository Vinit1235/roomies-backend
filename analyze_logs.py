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
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Error fetching {url}: {e}")
        return None

def main():
    # 1. Get Service ID
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
    
    # 2. Get Recent Logs via Deployment
    # Fetching general service logs might fail if not correctly scoped. 
    # Let's try fetching logs for the LATEST DEPLOYMENT instead.
    print(f"Fetching deployments for service {service_id}...")
    deploys_url = f"https://api.render.com/v1/services/{service_id}/deploys?limit=1"
    deploys = get_json(deploys_url)
    
    if not deploys or len(deploys) == 0:
        print("No deployments found.")
        return

    latest_deploy = deploys[0].get('deploy', deploys[0])
    deploy_id = latest_deploy['id']
    print(f"Latest deploy ID: {deploy_id}")

    # Log URL: https://api.render.com/v1/services/{serviceId}/deploys/{deployId}/logs
    # Actually, the endpoint is https://api.render.com/v1/services/{serviceId}/deploys/{deployId}/logs
    # Use that.
    
    logs_url = f"https://api.render.com/v1/services/{service_id}/deploys/{deploy_id}/logs?limit=100"
    logs = get_json(logs_url)
    
    with open("render_logs_analysis.txt", "w") as f:
        f.write(f"Log Analysis for '{SERVICE_NAME_FILTER}' (Deploy: {deploy_id})\n")
        f.write("="*40 + "\n")
        f.write(f"Status: {latest_deploy.get('status')}\n")
        f.write(f"Commit: {latest_deploy.get('commit', {}).get('message')}\n")
        f.write(f"Created: {latest_deploy.get('createdAt')}\n")
        f.write("="*40 + "\n\n")
        
        # If status is not 'live', it might be why logs are weird or empty, or build failed.
        if latest_deploy.get('status') != 'live':
             f.write("WARNING: Deployment is NOT live. Check build logs in dashboard.\n")

        f.write("Attempting to fetch logs...\n")

        
        if not logs:
            f.write("No logs returned or error fetching logs.\n")
            return
            
        keywords = ['error', 'exception', 'fail', 'mail', 'smtp', 'supabase', 'database']
        found_issues = []
        
        f.write("--- Recent Log Entries ---\n")
        
        for entry in logs:
            msg = entry.get('message', '')
            ts = entry.get('timestamp', '')
            f.write(f"[{ts}] {msg}\n")
            
            msg_lower = msg.lower()
            if any(k in msg_lower for k in keywords):
                found_issues.append(f"[{ts}] {msg}")
        
        f.write("\n" + "="*40 + "\n")
        f.write("POTENTIAL ISSUES FOUND:\n")
        if found_issues:
            for issue in found_issues:
                f.write(f"{issue}\n")
        else:
            f.write("No obvious error keywords found.\n")

if __name__ == "__main__":
    main()

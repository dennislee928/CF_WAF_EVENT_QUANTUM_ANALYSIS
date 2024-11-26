import requests
import os

def fetch_waf_data():
    url = f"https://api.cloudflare.com/client/v4/accounts/{os.getenv('CLOUDFLARE_ACCOUNT_ID')}/firewall/events"
    headers = {
        "Authorization": f"Bearer {os.getenv('CLOUDFLARE_API_TOKEN')}",
        "Content-Type": "application/json",
    }
    params = {
        "per_page": 100,  # Adjust the number of records per request
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch WAF data:", response.text)
        return None

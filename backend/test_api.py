import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def get_auth_token():
    # Try register first
    email = "testuser_judge@example.com"
    pwd = "testpassword123"
    requests.post(f"{BASE_URL}/api/auth/register", json={"name": "Test User", "email": email, "password": pwd})
    
    # Login
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": pwd})
    if resp.status_code == 200:
        return resp.json()["token"]
    raise Exception(f"Auth failed: {resp.text}")

token = get_auth_token()
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

scenarios = [
    "My daughter got into NIT Trichy starting August.",
    "Going trekking to Kashmir next month. Need gear.",
    "Starting my first corporate job in Bangalore next week.",
    "My daughter's wedding is next month in Jaipur.",
    "I want to buy a car."
]

for idx, q in enumerate(scenarios):
    print(f"\n--- Scenario {idx+1}: {q} ---")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/prism/analyze",
            json={"user_input": q, "user_pincode": "600001", "budget": None},
            headers=headers,
            timeout=120
        )
        if resp.status_code == 200:
            data = resp.json()
            print("SUCCESS! Detected event:", data.get("detected_event"))
            print("Top recommendation:", data.get("top_recommendation", {}).get("name"))
        else:
            print("FAILED!", resp.status_code, resp.text)
    except Exception as e:
        print("ERROR!", e)

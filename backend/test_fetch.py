import urllib.request, json, time, urllib.error

def fetch(url, data=None, token=None):
    req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
    if data:
        req.data = json.dumps(data).encode("utf-8")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        res = urllib.request.urlopen(req, timeout=15)
        return json.loads(res.read())
    except urllib.error.HTTPError as e:
        print(f"HTTPError {e.code}: {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

print("Registering test user...")
register = fetch("http://localhost:8000/api/auth/register", data={"name":"Test User", "email":"test@example.com", "password":"password123"})
if not register:
    print("Registration failed. Trying login...")
login = fetch("http://localhost:8000/api/auth/login", data={"email":"test@example.com", "password":"password123"})

if login and "access_token" in login:
    token = login["access_token"]
    print("Login successful. Token acquired.")
    
    print("\nFetching analyze endpoint...")
    analyze_data = {"user_input":"I need a new phone", "user_pincode":"400001", "budget":15000}
    result = fetch("http://localhost:8000/api/prism/analyze", data=analyze_data, token=token)
    
    if result:
        print(f"Fetch successful! Event Key: {result.get('event_key')}")
        print(f"Top Picks: {len(result.get('top_picks', []))}")
        print(f"Other Products: {len(result.get('all_products', []))}")
    else:
        print("Analyze request failed.")
else:
    print("Login failed.")

import urllib.request, json, time

def test(label, payload_bytes):
    try:
        req = urllib.request.Request("http://localhost:8000/api/prism/analyze", data=payload_bytes, headers={"Content-Type": "application/json"})
        res = urllib.request.urlopen(req, timeout=60)
        data = json.loads(res.read())
        print(f"\n=== {label} ===")
        print(f"Event: {data.get('event_key')} | Intent: {data.get('user_intent_type')}")
        print(f"Top picks ({len(data.get('top_picks',[]))}): ", [p.get("name","")[:35] for p in data.get("top_picks",[])[:3]])
        print(f"Others ({len(data.get('all_products',[]))})")
    except Exception as e:
        print(f"ERROR [{label}]: {e}")

test("I need a phone", b'{"user_input":"I need a phone","user_pincode":"400001","budget":15000}')
time.sleep(3)
test("I bought a car", b'{"user_input":"I bought a new car","user_pincode":"400001"}')

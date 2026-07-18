import urllib.request, json
try:
    req = urllib.request.Request('http://localhost:8000/api/prism/analyze', data=b'{"user_input":"I need a new smartphone","user_pincode":"400001","budget":15000}', headers={'Content-Type': 'application/json'})
    res = urllib.request.urlopen(req)
    data = json.loads(res.read())
    print('TOP PICKS (ROW 1):')
    for p in data.get('top_picks', []): print('  -', p.get('name')[:50], '[', p.get('subcategory'), ']')
    print('ALL PRODUCTS (ROW 2):')
    for p in data.get('all_products', []): print('  -', p.get('name')[:50], '[', p.get('subcategory'), ']')
except Exception as e:
    print('Error:', e)

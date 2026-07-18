import urllib.request, json
req = urllib.request.Request('http://localhost:8001/api/prism/analyze', data=b'{\"user_input\":\"I need a new smartphone\",\"user_pincode\":\"400001\",\"budget\":15000}', headers={'Content-Type': 'application/json'})
res = urllib.request.urlopen(req)
data = json.loads(res.read())
print('top_picks count:', len(data.get('top_picks', [])))
print('all_products count:', len(data.get('all_products', [])))
print('is_specific:', data.get('is_specific_product_ask'))
print('primary_item:', data.get('primary_item_label'))
print('user_intent_type:', data.get('user_intent_type'))


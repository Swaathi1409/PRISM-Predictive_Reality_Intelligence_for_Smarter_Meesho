import sys; sys.path.insert(0, '.'); from app.engines.product_matcher import _load_products, split_by_primary_and_accessories;
prods = _load_products()
pri, acc = split_by_primary_and_accessories(prods, 'phone')
prices = [p.get('price') for p in pri if p.get('price')]
print('Phones count:', len(pri))
print('Min price:', min(prices))
print('Max price:', max(prices))
under_15k = [p for p in pri if p.get('price') and p.get('price') <= 15000]
print('Phones <= 15000:', len(under_15k))


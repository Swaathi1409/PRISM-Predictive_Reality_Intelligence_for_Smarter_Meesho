import sys; sys.path.insert(0, '.'); from app.engines.product_matcher import _load_products, split_by_primary_and_accessories;
prods = _load_products()
pri, acc = split_by_primary_and_accessories(prods, 'phone')
print(f'Total: {len(prods)}, Primary: {len(pri)}, Accessories: {len(acc)}')
print('Primary items:')
for p in pri[:5]:
    print(' -', p.get('name')[:60])


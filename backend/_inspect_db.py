import sqlite3
conn=sqlite3.connect('app/data/prism_catalog.db')
c=conn.cursor()
c.execute('SELECT subcategory, COUNT(1) FROM products WHERE category=\"electronics\" GROUP BY subcategory')
print('subcats:', c.fetchall())
c.execute('SELECT id, name, subcategory FROM products WHERE category=\"electronics\"')
rows=c.fetchall()
print('count', len(rows))
for r in rows[:50]:
    print(r)

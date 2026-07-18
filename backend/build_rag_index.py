"""
build_rag_index.py — One-time script to build the PRISM embedding index.
Run from backend/ directory: python build_rag_index.py
"""
import sys, os, sqlite3, json

sys.path.insert(0, ".")

from app.engines.embedding_index import get_index, is_rag_available, _product_to_text

def row_to_product(row):
    p = dict(row)
    for col in ("available_pincodes", "tags", "event_tags"):
        raw = p.get(col)
        if isinstance(raw, str):
            try:
                p[col] = json.loads(raw)
            except Exception:
                p[col] = []
    return p

def main():
    print("=" * 60)
    print("PRISM RAG Index Builder")
    print("=" * 60)

    print(f"RAG available: {is_rag_available()}")

    db_path = os.path.join(os.path.dirname(__file__), "app/data/prism_catalog.db")
    if not os.path.exists(db_path):
        print(f"ERROR: DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM products")
    count = cur.fetchone()["cnt"]
    print(f"Total products in DB: {count}")

    cur.execute("SELECT * FROM products")
    rows = cur.fetchall()
    products = [row_to_product(r) for r in rows]
    conn.close()

    print(f"\nSample product texts (first 3):")
    for p in products[:3]:
        print(f"  [{p.get('category')}] {_product_to_text(p)[:120]}")

    print(f"\nBuilding embedding index for {len(products)} products...")
    index = get_index()
    success = index.build_index(products)

    if success:
        print("\n✅ Index built and saved successfully!")
        print("  Testing: searching for 'smartphone'...")
        results = index.search("smartphone mobile phone", k=5)
        for pid, score in results:
            p = next((x for x in products if str(x.get("id")) == str(pid)), None)
            name = p.get("name", "?")[:60] if p else pid
            cat = p.get("category", "?") if p else ""
            print(f"    score={score:.3f} [{cat}] {name}")

        print("\n  Testing: searching for 'warm woolen shawl Kashmir trek'...")
        results2 = index.search("warm woolen shawl Kashmir trek blanket thermal", k=5)
        for pid, score in results2:
            p = next((x for x in products if str(x.get("id")) == str(pid)), None)
            name = p.get("name", "?")[:60] if p else pid
            cat = p.get("category", "?") if p else ""
            print(f"    score={score:.3f} [{cat}] {name}")
    else:
        print("\n❌ Index build failed — check logs above for details.")
        print("   The system will fall back to keyword matching.")


if __name__ == "__main__":
    main()

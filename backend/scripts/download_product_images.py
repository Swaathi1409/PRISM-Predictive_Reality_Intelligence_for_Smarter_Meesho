import sqlite3
import os
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

DB_PATH = os.path.join(os.path.dirname(__file__), '../app/data/prism_catalog.db')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '../../frontend/public/images/products')

os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_image(args):
    idx, (pid, category) = args
    out_path = os.path.join(OUTPUT_DIR, f"{pid}.jpg")
    if os.path.exists(out_path):
        if os.path.getsize(out_path) > 0:
            return True
    
    cat_cleaned = category.split('_')[0] if category else "object"
    url = f"https://loremflickr.com/400/400/product,{cat_cleaned}?lock={idx}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response, open(out_path, 'wb') as out_file:
            data = response.read()
            out_file.write(data)
        return True
    except Exception as e:
        fallback_url = f"https://picsum.photos/seed/{pid}/400/400"
        try:
            req = urllib.request.Request(fallback_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response, open(out_path, 'wb') as out_file:
                data = response.read()
                out_file.write(data)
            return True
        except Exception as e2:
            print(f"Failed to download for {pid}: {e2}")
            return False

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, category FROM products")
    products = cursor.fetchall()
    conn.close()

    total = len(products)
    print(f"Starting download of {total} images to {os.path.abspath(OUTPUT_DIR)}...")
    
    success_count = 0
    with ThreadPoolExecutor(max_workers=30) as executor:
        results = executor.map(download_image, enumerate(products))
        for i, res in enumerate(results):
            if res:
                success_count += 1
            if (i+1) % 50 == 0:
                print(f"Processed {i+1}/{total}...")
                
    print(f"Download complete. Successfully downloaded {success_count}/{total} images.")

if __name__ == "__main__":
    main()

import os
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '../../frontend/public/images/categories')
os.makedirs(OUTPUT_DIR, exist_ok=True)

CATEGORIES = {
    "electronics": ["laptop", "headphones", "smartwatch", "smartphone", "speaker", "camera", "tablet", "monitor", "power bank", "earbuds"],
    "bags_luggage": ["suitcase", "backpack", "duffel bag", "tote bag", "messenger bag", "luggage set", "briefcase", "gym bag", "handbag", "sling bag"],
    "shoes": ["sneakers", "running shoes", "boots", "sandals", "formal shoes", "heels", "loafers", "sports shoes", "slippers", "wedges"],
    "home_kitchen": ["blanket", "water bottle", "storage rack", "bedsheet", "curtains", "cushion", "table lamp", "wall art", "cookware", "cutlery"],
    "kitchen_appliances": ["blender", "microwave", "toaster", "coffee maker", "kettle", "mixer grinder", "air fryer", "juicer", "oven", "induction cooktop"],
    "kitchen_essentials": ["spatula set", "spice rack", "cutting board", "kitchen knife", "storage container", "frying pan", "colander", "peeler", "whisk", "measuring cups"],
    "jewellery": ["necklace", "earrings", "ring", "bracelet", "pendant", "bangles", "anklet", "jewelry set", "chain", "mangalsutra"],
    "fashion_women": ["dress", "saree", "kurti", "top", "leggings", "jeans", "skirt", "jacket", "sweater", "nightwear"],
    "fashion_men": ["t-shirt", "shirt", "jeans", "trousers", "jacket", "suit", "shorts", "sweater", "track pants", "hoodie"],
    "beauty_grooming": ["lipstick", "perfume", "face wash", "moisturizer", "hair oil", "shampoo", "trimmer", "makeup kit", "sunscreen", "body lotion"],
    "personal_care": ["toothbrush", "toothpaste", "body wash", "deodorant", "hair brush", "shaving cream", "razor", "hand sanitizer", "wet wipes", "cotton pads"],
    "baby_products": ["baby stroller", "diaper bag", "baby blanket", "baby toys", "baby clothes", "baby monitor", "feeding bottle", "baby carrier", "baby lotion", "baby wipes"],
    "toys_games": ["board game", "action figure", "puzzle", "doll", "building blocks", "remote control car", "stuffed toy", "educational toy", "card game", "outdoor toy"],
    "sports_fitness": ["yoga mat", "dumbbells", "resistance bands", "treadmill", "bicycle", "tennis racket", "football", "cricket bat", "jump rope", "fitness tracker"],
    "home_decor": ["vase", "photo frame", "wall clock", "candles", "indoor plant", "rug", "mirror", "painting", "decorative bowl", "sculpture"],
    "home_improvement": ["drill machine", "tool kit", "paint brush", "screwdrivers", "step ladder", "door lock", "plumbing tape", "hammer", "measuring tape", "extension cord"],
    "stationery": ["notebook", "pen set", "highlighters", "sticky notes", "planner", "pencil case", "calculator", "stapler", "folders", "whiteboard"],
    "automotive": ["car cover", "car vacuum cleaner", "dash cam", "car air freshener", "tire inflator", "motorcycle helmet", "bike cover", "car wash shampoo", "microfiber cloth", "jumper cables"],
    "festival_decor": ["diya set", "rangoli colors", "fairy lights", "puja thali", "toran", "lantern", "artificial flowers", "incense sticks", "decorative candles", "gift box"],
    "food": ["dry fruits", "tea powder", "coffee beans", "chocolates", "spices combo", "healthy snacks", "honey", "cookies", "olive oil", "pasta"],
    "formal_wear": ["tie", "blazer", "formal shirt", "formal trousers", "cufflinks", "leather belt", "formal suit", "brooch", "pocket square", "formal waistcoat"],
    "wedding_apparel": ["lehenga", "sherwani", "bridal jewellery", "ethnic gown", "safa", "bridal dupatta", "designer saree", "kurta pajama", "wedding clutch", "mojari"],
    "security": ["cctv camera", "smart lock", "video doorbell", "padlock", "safe box", "motion sensor light", "alarm system", "hidden camera", "security cable", "door sensor"],
    "appliances": ["washing machine", "refrigerator", "air conditioner", "vacuum cleaner", "water purifier", "iron", "ceiling fan", "room heater", "sewing machine", "dish washer"]
}

import time

def download_image(args):
    category, idx, keyword = args
    cat_dir = os.path.join(OUTPUT_DIR, category)
    os.makedirs(cat_dir, exist_ok=True)
    
    keyword_slug = keyword.replace(" ", "_")
    out_path = os.path.join(cat_dir, f"{keyword_slug}_{idx}.jpg")
    
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        return True
    
    prompt = f"High quality premium ecommerce product photography of {keyword}, clean white background, sharp focus, professional lighting"
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&nologo=true"
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            import ssl
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            with urllib.request.urlopen(req, timeout=20, context=ctx) as response, open(out_path, 'wb') as out_file:
                data = response.read()
                out_file.write(data)
            return True
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(3 + attempt * 2)
            else:
                break
        except Exception as e:
            time.sleep(2)
    
    print(f"Failed to download {category} - {keyword} after retries")
    return False

def main():
    tasks = []
    for category, keywords in CATEGORIES.items():
        for i, kw in enumerate(keywords):
            tasks.append((category, i, kw))
            
    print(f"Starting generation of {len(tasks)} premium category images with rate limiting...")
    
    success_count = 0
    # Use max_workers=2 to prevent rate limiting
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = executor.map(download_image, tasks)
        for i, res in enumerate(results):
            if res:
                success_count += 1
            if (i+1) % 20 == 0:
                print(f"Processed {i+1}/{len(tasks)} images...")
            time.sleep(1.0)
                
    print(f"Generation complete. Successfully generated {success_count}/{len(tasks)} images.")

if __name__ == "__main__":
    main()

"""
build_catalog.py - One-shot script to build PRISM's SQLite product catalog.
  1. Reads all Amazon India CSV files from amazon-product-sales-data/
  2. Maps them to PRISM categories + synthesizes PRISM-specific fields
  3. Merges with existing JSON catalogs (mock_products, new_products_chunk, enriched_products_v2)
  4. Writes everything into prism_catalog.db (SQLite)

Run from project root:
    python backend/app/data/build_catalog.py
"""

import csv
import json
import os
import re
import sqlite3
import random
import math
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CSV_DIR = PROJECT_ROOT / "amazon-product-sales-data"
DATA_DIR = Path(__file__).resolve().parent
DB_PATH = DATA_DIR / "prism_catalog.db"

JSON_SOURCES = [
    DATA_DIR / "mock_products.json",
    DATA_DIR / "new_products_chunk.json",
    DATA_DIR / "enriched_products_v2.json"
]

ALL_PINCODES = [
    "600001","600036","620015","400076","400001","400069",
    "110016","110001","110011","560001","560034","560100",
    "302001","302004","700001","700019","380001","380015",
    "226001","226010","500001","500032","411001","411014",
    "530001","641001","682001","800001","160001","440001",
    "575001","333031","506004",
]

def _random_pincodes(n=10):
    return random.sample(ALL_PINCODES, min(n, len(ALL_PINCODES)))

SELLERS = {
    "electronics": [("TechMart India",4.5,12400,2.8),("GadgetHub",4.3,8900,3.5),("DigiZone",4.4,6200,3.1)],
    "fashion_men": [("MenStyle India",4.3,7200,4.2),("FashionKart",4.2,5400,5.1),("StyleHub",4.4,9100,3.8)],
    "fashion_women": [("WomenWear Co",4.4,8900,4.5),("TrendSetters",4.2,6700,5.3),("FashionPlaza",4.3,11200,4.0)],
    "fashion_kids": [("KidsWorld",4.5,4200,3.2),("TinyTrends",4.3,3100,3.8),("LittleStyle",4.4,2800,3.5)],
    "jewellery": [("JewelsBazaar",4.4,5100,5.2),("GoldNSilver",4.3,4200,6.1),("BridalJewels",4.5,3800,4.8)],
    "bags_luggage": [("BagWorld",4.4,7800,3.9),("TravelGear India",4.3,6100,4.2),("LuggagePro",4.2,5400,4.5)],
    "beauty_grooming": [("BeautyBazaar",4.5,9200,2.9),("GlowMart",4.3,7800,3.4),("SkincareHub",4.4,5100,3.1)],
    "home_kitchen": [("HomeEssentials",4.4,6300,3.5),("KitchenKart",4.3,5800,3.8),("HomePlus",4.2,4900,4.1)],
    "home_decor": [("DecoMart",4.3,4100,4.5),("HomeArtIndia",4.4,3200,4.0),("StyleHome",4.2,2900,4.8)],
    "appliances": [("AppliancesPro",4.4,8400,3.2),("ElectroHome",4.3,7200,3.5),("SmartAppliances",4.5,6100,2.9)],
    "sports_fitness": [("SportZone",4.3,5200,3.8),("FitnessMart",4.4,4800,3.5),("ActiveLife",4.2,3900,4.2)],
    "baby_products": [("BabyKart",4.6,9800,2.1),("TinyWorld",4.5,7200,2.5),("MomBaby Store",4.4,5100,2.8)],
    "food": [("FreshBasket",4.5,14200,1.2),("GourmetGrocer",4.6,8900,1.8),("NutriMart",4.4,6700,2.1)],
    "personal_care": [("HealthMart",4.4,7800,2.9),("CareZone",4.3,5400,3.2),("WellnessHub",4.5,6100,2.7)],
    "pet_supplies": [("PetWorld",4.5,4200,2.8),("HappyPaws",4.4,3100,3.1),("PetCare India",4.3,2800,3.5)],
    "bedding": [("CottonCraft India",4.6,5400,2.9),("DreamWeave",4.4,3800,3.4),("SleepWell Co",4.3,4200,3.7)],
    "security": [("SafeHomeTech",4.3,4100,4.2),("SmartHomePro",4.4,3200,3.8),("SecureLife",4.2,2800,4.5)],
    "toys_games": [("ToysWorld",4.5,6200,2.5),("FunZone India",4.4,4800,2.8),("PlayMart",4.3,3900,3.1)],
    "garden_outdoor": [("GardenKart",4.3,2900,4.1),("OutdoorLife",4.4,2400,3.8),("GreenThumb",4.2,1900,4.5)],
    "automotive": [("AutoZone India",4.3,5200,3.9),("CarAccessories",4.4,4100,3.5),("DriveMax",4.2,3600,4.2)],
    "stationery": [("StationeryWorld",4.5,9100,1.8),("OfficeEssentials",4.6,7800,1.5),("EduMart India",4.7,12400,1.1)],
    "formal_wear": [("EthnicBoutique",4.4,6200,5.1),("FestiveFashion",4.3,5100,5.4),("WesternWear Co",4.2,4800,4.8)],
    "sportswear": [("SportStyle",4.3,4900,4.1),("ActiveWear India",4.4,4200,3.8),("FitFashion",4.2,3600,4.5)],
    "shoes": [("FootFashion",4.3,8200,4.5),("ShoeWorld",4.4,7100,4.2),("StepStyle",4.2,6400,4.8)],
    "kitchen_appliances": [("KitchenPro",4.4,5100,3.2),("HomeCook",4.3,4200,3.5),("ApplianceMart",4.5,6800,2.9)],
    "watches": [("WatchBazaar",4.4,6100,4.2),("TimeZone India",4.3,5200,4.5),("ClockWorld",4.2,4100,5.1)],
    "home_improvement": [("HardwareKart",4.5,5400,2.8),("ToolDepot India",4.6,4200,3.1),("HomeFixit",4.3,3800,3.5)],
}

def _pick_seller(category):
    pool = SELLERS.get(category, SELLERS["home_kitchen"])
    name, rating, reviews, return_rate = random.choice(pool)
    rating = round(min(5.0, rating + random.uniform(-0.2, 0.2)), 1)
    reviews = int(reviews * random.uniform(0.6, 1.4))
    return_rate = round(max(0.5, return_rate + random.uniform(-0.5, 0.5)), 1)
    return name, rating, reviews, return_rate

EVENT_TAGS_MAP = {
    "electronics": ["hostel_move","first_job","government_exam","new_home"],
    "fashion_men": ["hostel_move","first_job","wedding","cultural_event"],
    "fashion_women": ["wedding","festival_prep","cultural_event","first_job"],
    "fashion_kids": ["new_baby","festival_prep","cultural_event"],
    "jewellery": ["wedding","festival_prep","cultural_event"],
    "bags_luggage": ["hostel_move","travel_adventure","first_job"],
    "beauty_grooming": ["hostel_move","wedding","festival_prep","first_job"],
    "home_kitchen": ["new_home","hostel_move","wedding"],
    "home_decor": ["new_home","wedding","festival_prep"],
    "appliances": ["new_home","wedding","shop_opening"],
    "sports_fitness": ["hostel_move","travel_adventure","first_job"],
    "baby_products": ["new_baby","wedding"],
    "food": ["hostel_move","new_home","festival_prep"],
    "personal_care": ["hostel_move","travel_adventure","first_job"],
    "pet_supplies": ["new_home"],
    "bedding": ["hostel_move","new_home","wedding","new_baby"],
    "security": ["new_home","shop_opening"],
    "toys_games": ["new_baby","festival_prep","cultural_event"],
    "garden_outdoor": ["new_home","travel_adventure"],
    "automotive": ["first_job","travel_adventure","new_home"],
    "stationery": ["hostel_move","government_exam","first_job"],
    "formal_wear": ["wedding","festival_prep","cultural_event","first_job"],
    "sportswear": ["hostel_move","travel_adventure","first_job"],
    "shoes": ["hostel_move","first_job","wedding","travel_adventure"],
    "kitchen_appliances": ["new_home","hostel_move","shop_opening"],
    "watches": ["first_job","wedding","festival_prep"],
    "home_improvement": ["new_home","shop_opening"],
    "shop_supplies": ["shop_opening"],
    "exam_supplies": ["government_exam","hostel_move"],
    "study_accessories": ["hostel_move","government_exam"],
    "kitchen_essentials": ["hostel_move","new_home"],
}

CSV_CATEGORY_MAP = {
    "all electronics.csv": ("electronics","general"),
    "headphones.csv": ("electronics","headphones"),
    "cameras.csv": ("electronics","cameras"),
    "camera accessories.csv": ("electronics","camera_accessories"),
    "security cameras.csv": ("security","cctv"),
    "speakers.csv": ("electronics","speakers"),
    "televisions.csv": ("electronics","television"),
    "home audio and theater.csv": ("electronics","home_audio"),
    "home entertainment systems.csv": ("electronics","home_entertainment"),
    "mens fashion.csv": ("fashion_men","general"),
    "shirts.csv": ("fashion_men","shirts"),
    "jeans.csv": ("fashion_men","jeans"),
    "t-shirts and polos.csv": ("fashion_men","tshirts"),
    "formal shoes.csv": ("shoes","formal_shoes"),
    "sports shoes.csv": ("shoes","sports_shoes"),
    "casual shoes.csv": ("shoes","casual_shoes"),
    "womens fashion.csv": ("fashion_women","general"),
    "western wear.csv": ("fashion_women","western"),
    "ethnic wear.csv": ("formal_wear","ethnic"),
    "clothing.csv": ("fashion_women","general"),
    "innerwear.csv": ("fashion_women","innerwear"),
    "lingerie and nightwear.csv": ("fashion_women","nightwear"),
    "fashion sandals.csv": ("shoes","sandals"),
    "ballerinas.csv": ("shoes","ballerinas"),
    "shoes.csv": ("shoes","general"),
    "kids clothing.csv": ("fashion_kids","clothing"),
    "kids fashion.csv": ("fashion_kids","general"),
    "kids shoes.csv": ("shoes","kids_shoes"),
    "baby fashion.csv": ("fashion_kids","baby"),
    "amazon fashion.csv": ("fashion_women","general"),
    "the designer boutique.csv": ("fashion_women","designer"),
    "fashion sales and deals.csv": ("fashion_women","deals"),
    "jewellery.csv": ("jewellery","general"),
    "fashion and silver jewellery.csv": ("jewellery","silver"),
    "gold and diamond jewellery.csv": ("jewellery","gold_diamond"),
    "watches.csv": ("watches","general"),
    "kids watches.csv": ("watches","kids"),
    "sunglasses.csv": ("fashion_women","sunglasses"),
    "bags and luggage.csv": ("bags_luggage","general"),
    "backpacks.csv": ("bags_luggage","backpack"),
    "handbags and clutches.csv": ("bags_luggage","handbags"),
    "rucksacks.csv": ("bags_luggage","rucksack"),
    "suitcases and trolley bags.csv": ("bags_luggage","suitcase"),
    "wallets.csv": ("bags_luggage","wallet"),
    "travel duffles.csv": ("bags_luggage","duffle"),
    "school bags.csv": ("bags_luggage","school_bag"),
    "travel accessories.csv": ("bags_luggage","travel_accessories"),
    "beauty and grooming.csv": ("beauty_grooming","general"),
    "make-up.csv": ("beauty_grooming","makeup"),
    "luxury beauty.csv": ("beauty_grooming","luxury"),
    "personal care appliances.csv": ("beauty_grooming","appliances"),
    "all home and kitchen.csv": ("home_kitchen","general"),
    "kitchen and dining.csv": ("home_kitchen","dining"),
    "kitchen storage and containers.csv": ("home_kitchen","storage"),
    "home furnishing.csv": ("home_kitchen","furnishing"),
    "home storage.csv": ("home_kitchen","storage"),
    "household supplies.csv": ("home_kitchen","supplies"),
    "bedroom linen.csv": ("bedding","linen"),
    "home dcor.csv": ("home_decor","general"),
    "indoor lighting.csv": ("home_decor","lighting"),
    "furniture.csv": ("home_decor","furniture"),
    "all appliances.csv": ("appliances","general"),
    "washing machines.csv": ("appliances","washing_machine"),
    "refrigerators.csv": ("appliances","refrigerator"),
    "air conditioners.csv": ("appliances","air_conditioner"),
    "heating and cooling appliances.csv": ("appliances","heating_cooling"),
    "kitchen and home appliances.csv": ("kitchen_appliances","general"),
    "all sports fitness and outdoors.csv": ("sports_fitness","general"),
    "all exercise and fitness.csv": ("sports_fitness","exercise"),
    "yoga.csv": ("sports_fitness","yoga"),
    "cycling.csv": ("sports_fitness","cycling"),
    "running.csv": ("sports_fitness","running"),
    "cricket.csv": ("sports_fitness","cricket"),
    "badminton.csv": ("sports_fitness","badminton"),
    "football.csv": ("sports_fitness","football"),
    "fitness accessories.csv": ("sports_fitness","accessories"),
    "cardio equipment.csv": ("sports_fitness","cardio"),
    "strength training.csv": ("sports_fitness","strength"),
    "camping and hiking.csv": ("garden_outdoor","camping"),
    "garden and outdoors.csv": ("garden_outdoor","garden"),
    "sportswear.csv": ("sportswear","general"),
    "baby products.csv": ("baby_products","general"),
    "baby bath skin and grooming.csv": ("baby_products","bath_grooming"),
    "diapers.csv": ("baby_products","diapers"),
    "nursing and feeding.csv": ("baby_products","feeding"),
    "strollers and prams.csv": ("baby_products","stroller"),
    "toys and games.csv": ("toys_games","general"),
    "stem toys store.csv": ("toys_games","stem"),
    "international toy store.csv": ("toys_games","international"),
    "toys gifting store.csv": ("toys_games","gifting"),
    "all grocery and gourmet foods.csv": ("food","grocery"),
    "coffee tea and beverages.csv": ("food","beverages"),
    "snack foods.csv": ("food","snacks"),
    "diet and nutrition.csv": ("food","nutrition"),
    "health and personal care.csv": ("personal_care","general"),
    "all pet supplies.csv": ("pet_supplies","general"),
    "dog supplies.csv": ("pet_supplies","dog"),
    "all car and motorbike products.csv": ("automotive","general"),
    "car accessories.csv": ("automotive","car_accessories"),
    "car electronics.csv": ("automotive","car_electronics"),
    "car parts.csv": ("automotive","car_parts"),
    "car and bike care.csv": ("automotive","care"),
    "motorbike accessories and parts.csv": ("automotive","motorbike"),
    "industrial and scientific supplies.csv": ("stationery","scientific"),
    "lab and scientific.csv": ("stationery","lab"),
    "sewing and craft supplies.csv": ("stationery","craft"),
    "home improvement.csv": ("home_improvement","general"),
    "janitorial and sanitation supplies.csv": ("home_kitchen","cleaning"),
    "test measure and inspect.csv": ("stationery","lab"),
    "musical instruments and professional audio.csv": ("electronics","instruments"),
}

SKIP_FILES = {
    "all books.csv","all english.csv","all hindi.csv","all movies and tv shows.csv",
    "all music.csv","all video games.csv","amazon pharmacy.csv","blu-ray.csv",
    "childrens books.csv","entertainment collectibles.csv","exam central.csv",
    "fiction books.csv","film songs.csv","fine art.csv","indian classical.csv",
    "indian language books.csv","international music.csv","kindle ebooks.csv",
    "pantry.csv","pc games.csv","school textbooks.csv","sports collectibles.csv",
    "subscribe and save.csv","textbooks.csv","video games deals.csv",
    "refurbished and open box.csv","value bazaar.csv","gaming accessories.csv",
    "gaming consoles.csv",
}

def _sample_count(sz):
    if sz < 100: return 0
    if sz < 200000: return 5
    if sz < 500000: return 8
    if sz < 1000000: return 10
    return 12


# ── Per-category name rejection filters ─────────────────────────────────────
# Prevents clearly miscategorized products from polluting the DB.
# If ANY reject term is found in the product name (case-insensitive),
# the row is dropped BEFORE being inserted into the catalog.
CATEGORY_REJECT_KEYWORDS: dict = {
    # Bedding CSVs include baby mattress covers, changing mats, etc.
    "bedding": ["baby", "infant", "neonatal", "newborn", "new born", "nursery",
                "steriliz", "feeding bottle", "nipple", "pacifier", "nappy",
                "diaper", "pram", "stroller", "teether", "swaddle", "bib"],
    # fashion_women broad CSVs dump books, electronics, bags into this category
    "fashion_women": ["laptop", "mobile", "tablet", "smartphone", "hard disk",
                      "usb hub", "hdmi", "earphone", "headphone", "speaker",
                      "router", "keyboard", "mouse pad", "monitor",
                      "book", "novel", "textbook",
                      "baby", "diaper", "stroller", "formula milk",
                      "dog ", " cat ", "pet food", "aquarium",
                      "car oil", "engine", "tyre", "lubricant",
                      "supplement", "whey protein", "creatine"],
    # home_kitchen picks up baby milestone blankets etc.
    "home_kitchen": ["baby milestone", "baby shower", "neonatal"],
}

GLOBAL_REJECT_KEYWORDS = ["alexvyan"]

def _parse_price(raw):
    if not raw or not str(raw).strip(): return 0.0
    cleaned = re.sub(r'[^\d.]', '', str(raw).replace(',', ''))
    try: return float(cleaned)
    except: return 0.0

KNOWN_BRANDS_LOWER = {b.lower(): b for b in [
    "Samsung","Apple","OnePlus","Xiaomi","Redmi","Realme","Oppo","Vivo","Nokia","Motorola",
    "Sony","LG","Panasonic","Philips","Havells","Bajaj","Crompton","Voltas","Daikin","Whirlpool",
    "Godrej","Bosch","Siemens","HP","Dell","Lenovo","Asus","Acer","boAt","Noise","Fastrack",
    "Titan","Fossil","Casio","Timex","Levi's","Wrangler","Lee","Spykar","Pepe","UCB",
    "Van Heusen","Arrow","Louis Philippe","Park Avenue","Peter England","Raymond","Mufti",
    "Roadster","HRX","Jockey","Puma","Nike","Adidas","Reebok","Skechers","Bata","Red Tape",
    "Woodland","Campus","Sparx","Liberty","Khadims","Lakme","Mamaearth","WOW","Himalaya",
    "Biotique","Lotus","Revlon","Garnier","Plum","mCaffeine","Minimalist","Milton","Cello",
    "Tupperware","Prestige","Hawkins","Pigeon","Wonderchef","Inalsa","Maharaja","Orpat","Usha",
    "Anchor","Finolex","Polycab","Syska","Wipro","Surya","Haldiram's","MTR","Tata","Nestle",
    "ITC","Britannia","Amul","Dabur","Patanjali","Borges","Del Monte","Sunfeast","Wildcraft",
    "Skybags","American Tourister","Samsonite","VIP","Safari","Aristocrat","Lavie","Caprese",
    "Baggit","Hidesign","iQOO","Poco","Nothing","Infinix","Tecno","Qubo","CP Plus","Hikvision",
    "D-Link","TP-Link","Fevicol","3M","Pidilite","Asian Paints","Berger","Dulux","Nerolac",
]}

def _extract_brand(name):
    nl = name.lower()
    for bl, bv in KNOWN_BRANDS_LOWER.items():
        if nl.startswith(bl):
            return bv
    first = name.split()[0] if name.split() else "Generic"
    return re.sub(r'[^A-Za-z0-9& ]', '', first).strip() or "Generic"

STOP_WORDS = {
    "and","or","the","with","for","a","an","of","in","to","is","by","on","at",
    "from","this","that","are","was","were","pack","set","combo","kit","size","color",
}

def _generate_tags(name, category, subcategory):
    words = re.sub(r'[^A-Za-z0-9 ]', ' ', name.lower()).split()
    tags = list({w for w in words if len(w) > 2 and w not in STOP_WORDS})[:6]
    tags.append(category)
    if subcategory and subcategory != "general":
        tags.append(subcategory.replace("_", "-"))
    return list(set(tags))[:8]

def _get_image_url(cat, amz=""):
    if amz and str(amz).startswith("http"):
        return amz
    return ""

WATTAGE_MAP = {
    "air_conditioner": 1500, "washing_machine": 500, "refrigerator": 150,
    "television": 100, "home_audio": 50, "home_entertainment": 80,
    "heating_cooling": 1200, "kitchen_appliances": 750, "appliances": 500, "security": 5,
}

def _get_wattage(subcat):
    return WATTAGE_MAP.get(subcat)

def _generate_desc(name, category, subcat, brand, price, rating):
    rt = "top-rated" if rating >= 4.5 else "highly rated" if rating >= 4.0 else "popular"
    phrases = {
        "electronics": f"Premium {brand} electronics with advanced features.",
        "fashion_men": f"Stylish {brand} men's fashion for everyday wear.",
        "fashion_women": f"Elegant {brand} women's fashion for modern lifestyles.",
        "fashion_kids": f"Comfortable and fun {brand} kids wear.",
        "jewellery": f"Beautiful {brand} jewellery for special occasions.",
        "bags_luggage": f"Durable {brand} bag designed for travel and daily use.",
        "beauty_grooming": f"Premium {brand} beauty product for glowing skin and hair.",
        "home_kitchen": f"Quality {brand} product to upgrade your kitchen and home.",
        "home_decor": f"Stylish {brand} decor to transform your living space.",
        "appliances": f"Energy-efficient {brand} appliance for modern homes.",
        "sports_fitness": f"{brand} sports gear to fuel your active lifestyle.",
        "baby_products": f"Safe and gentle {brand} product for babies.",
        "food": f"Premium quality {brand} food for healthy eating.",
        "personal_care": f"{brand} personal care product for daily wellness.",
        "pet_supplies": f"Quality {brand} pet supplies for your furry friends.",
        "bedding": f"Comfortable {brand} bedding for a restful sleep.",
        "security": f"Reliable {brand} security solution for home protection.",
        "toys_games": f"Fun and educational {brand} toy for kids.",
        "garden_outdoor": f"{brand} outdoor product for garden and adventure.",
        "automotive": f"Quality {brand} automotive accessory for your vehicle.",
        "stationery": f"Premium {brand} stationery for office and study.",
        "formal_wear": f"Elegant {brand} ethnic and formal wear for celebrations.",
        "sportswear": f"Performance {brand} sportswear for training and workouts.",
        "shoes": f"Comfortable {brand} footwear for all occasions.",
        "kitchen_appliances": f"Efficient {brand} kitchen appliance for easy cooking.",
        "watches": f"Stylish {brand} watch combining style and precision.",
        "home_improvement": f"Quality {brand} product for home repairs and improvement.",
    }
    base = phrases.get(category, f"Quality {brand} product.")
    return f"{base} A {rt} choice at Rs.{int(price):,}."


def ingest_csv_products():
    products = []
    csv_files = list(CSV_DIR.glob("*.csv"))
    file_sizes = {f.name.lower(): f.stat().st_size for f in csv_files}
    processed = 0
    for csv_file in sorted(csv_files):
        fname_lower = csv_file.name.lower()
        if fname_lower in SKIP_FILES:
            continue
        n_sample = _sample_count(file_sizes.get(fname_lower, 0))
        if n_sample == 0:
            continue
        mapping = CSV_CATEGORY_MAP.get(fname_lower)
        if not mapping:
            continue
        prism_cat, prism_subcat = mapping
        try:
            rows = []
            with open(csv_file, encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = (row.get("name") or "").strip()
                    if 'amazon' in name.lower():
                        parts = re.split(r'(?i)amazon', name, maxsplit=1)
                        if len(parts[0].strip()) > 5:
                            name = parts[0].strip()
                        else:
                            name = re.sub(r'(?i)amazon', '', name).strip()
                            name = re.sub(r'\s+', ' ', name)
                        name = re.sub(r'^[-:,\s]+|[-:,\s]+$', '', name)

                    if not name or len(name) < 5:
                        continue
                    dp = _parse_price(row.get("discount_price", ""))
                    ap = _parse_price(row.get("actual_price", ""))
                    try:
                        rating = float((row.get("ratings") or "").strip())
                    except Exception:
                        rating = round(random.uniform(3.8, 4.5), 1)
                    rating = max(1.0, min(5.0, rating))
                    no_r_str = re.sub(r'[^\d]', '', row.get("no_of_ratings", "") or "")
                    try:
                        no_r = int(no_r_str)
                    except Exception:
                        no_r = random.randint(100, 5000)
                    price = dp if dp > 0 else ap
                    orig = ap if ap >= price else price
                    if price == 0:
                        continue
                    disc = round((orig - price) / orig * 100) if orig > price > 0 else 0
                    rows.append({
                        "name": name[:200], "price": round(price, 2),
                        "original_price": round(orig, 2), "discount_percent": disc,
                        "rating": rating, "no_ratings": no_r,
                        "image": (row.get("image") or "").strip(),
                    })
            seen_names = set()
            unique_rows = []
            for r in rows:
                nm = r["name"][:60].lower()
                if nm not in seen_names:
                    seen_names.add(nm)
                    unique_rows.append(r)
            unique_rows = [r for r in unique_rows if 50 < r["price"] < 200000]
            # ── Apply name-based category rejection ──────────────────────────
            reject_terms = CATEGORY_REJECT_KEYWORDS.get(prism_cat, []) + GLOBAL_REJECT_KEYWORDS
            if reject_terms:
                def _is_valid(row):
                    nl = row["name"].lower()
                    return not any(term in nl for term in reject_terms)
                unique_rows = [r for r in unique_rows if _is_valid(r)]
            sample = unique_rows[:n_sample]
            for i, row in enumerate(sample):
                brand = _extract_brand(row["name"])
                sname, srat, srev, sret = _pick_seller(prism_cat)
                pincodes = _random_pincodes(random.randint(8, 12))
                ev_tags = EVENT_TAGS_MAP.get(prism_cat, ["hostel_move", "new_home"])
                tags = _generate_tags(row["name"], prism_cat, prism_subcat)
                wattage = _get_wattage(prism_subcat)
                desc = _generate_desc(
                    row["name"], prism_cat, prism_subcat,
                    brand, row["price"], row["rating"]
                )
                img = _get_image_url(prism_cat, row["image"])
                price_trend = round(random.uniform(-5.0, 3.0), 1)
                delivery = random.choice([2, 3, 3, 4, 5])
                rfactor = math.log1p(row["no_ratings"]) / math.log1p(50000)
                conf = int(60 + (row["rating"] - 1) / 4 * 25 + rfactor * 15)
                conf = max(50, min(99, conf))
                cat_prefix = prism_cat.upper()[:6]
                pid = f"{cat_prefix}_{fname_lower[:4].upper()}{i + 1:03d}"
                products.append({
                    "id": pid, "name": row["name"], "category": prism_cat,
                    "subcategory": prism_subcat, "brand": brand,
                    "price": row["price"], "original_price": row["original_price"],
                    "discount_percent": row["discount_percent"],
                    "seller_name": sname, "seller_rating": srat,
                    "seller_review_count": srev, "seller_return_rate": sret,
                    "delivery_days": delivery, "available_pincodes": pincodes,
                    "stock_status": "in_stock", "price_trend_7d": price_trend,
                    "tags": tags, "wattage": wattage, "event_tags": ev_tags,
                    "description": desc, "image_url": img, "confidence_score": conf,
                })
            processed += 1
        except Exception as e:
            print(f"  [WARN] Skipped {csv_file.name}: {e}")
    print(f"  Processed {processed} CSV files -> {len(products)} Amazon products")
    return products


def load_json_products():
    all_p = []
    for path in JSON_SOURCES:
        if not path.exists():
            print(f"  [WARN] Not found: {path}")
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        print(f"  Loaded {len(data)} from {path.name}")
        all_p.extend(data)
    return all_p


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT,
    brand TEXT,
    price REAL NOT NULL,
    original_price REAL,
    discount_percent INTEGER DEFAULT 0,
    seller_name TEXT,
    seller_rating REAL DEFAULT 4.0,
    seller_review_count INTEGER DEFAULT 0,
    seller_return_rate REAL DEFAULT 3.0,
    delivery_days INTEGER DEFAULT 3,
    available_pincodes TEXT DEFAULT '[]',
    stock_status TEXT DEFAULT 'in_stock',
    price_trend_7d REAL DEFAULT 0.0,
    tags TEXT DEFAULT '[]',
    wattage REAL,
    event_tags TEXT DEFAULT '[]',
    description TEXT,
    image_url TEXT,
    image_placeholder TEXT,
    confidence_score INTEGER DEFAULT 75,
    source TEXT DEFAULT 'amazon'
);
"""

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_category ON products(category);",
    "CREATE INDEX IF NOT EXISTS idx_price ON products(price);",
    "CREATE INDEX IF NOT EXISTS idx_stock ON products(stock_status);",
    "CREATE INDEX IF NOT EXISTS idx_seller_rating ON products(seller_rating);",
]

INSERT_SQL = """INSERT OR REPLACE INTO products (
    id,name,category,subcategory,brand,price,original_price,discount_percent,
    seller_name,seller_rating,seller_review_count,seller_return_rate,delivery_days,
    available_pincodes,stock_status,price_trend_7d,tags,wattage,event_tags,
    description,image_url,image_placeholder,confidence_score,source
) VALUES (
    :id,:name,:category,:subcategory,:brand,:price,:original_price,:discount_percent,
    :seller_name,:seller_rating,:seller_review_count,:seller_return_rate,:delivery_days,
    :available_pincodes,:stock_status,:price_trend_7d,:tags,:wattage,:event_tags,
    :description,:image_url,:image_placeholder,:confidence_score,:source
)"""


def _clean_name(name):
    name = str(name).strip()
    if 'amazon' in name.lower():
        parts = re.split(r'(?i)amazon', name, maxsplit=1)
        if len(parts[0].strip()) > 5:
            name = parts[0].strip()
        else:
            name = re.sub(r'(?i)amazon', '', name).strip()
            name = re.sub(r'\s+', ' ', name)
        name = re.sub(r'^[-:,\s]+|[-:,\s]+$', '', name)
    return name[:200]

import hashlib

MANUAL_IMAGES_DIR = PROJECT_ROOT / "frontend/public/images"
MANUAL_IMAGES = [f.name for f in MANUAL_IMAGES_DIR.glob("*.jpg")] if MANUAL_IMAGES_DIR.exists() else []

def _get_manual_image(name):
    if not MANUAL_IMAGES:
        return None
    name_lower = name.lower()
    best_match = None
    best_score = 1  # Require at least 2 matching words
    for f in MANUAL_IMAGES:
        name_parts = f.replace('.jpg', '').split('_')
        score = sum(1 for part in name_parts if part and part.lower() in name_lower)
        if score > best_score:
            best_score = score
            best_match = f
    if best_match:
        return f"/images/{best_match}"
    return None

def _assign_mock_image(product_id, category, name):
    manual_img = _get_manual_image(name)
    if manual_img:
        return manual_img
        
    base_dir = PROJECT_ROOT / "frontend/public/images/categories" / category
    if not base_dir.exists():
        return f"/images/placeholder.jpg"
    
    files = list(base_dir.glob("*.jpg"))
    if not files:
        return f"/images/placeholder.jpg"
        
    name_lower = name.lower()
    
    matching_files = []
    for f in files:
        kw = f.name.rsplit('_', 1)[0].replace('_', ' ')
        if kw in name_lower:
            matching_files.append(f)
            
    pool = matching_files if matching_files else files
    
    h = int(hashlib.md5(f"{category}_{product_id}".encode()).hexdigest(), 16)
    selected = pool[h % len(pool)]
    return f"/images/categories/{category}/{selected.name}"

def _norm(p, source):
    img_url = str(p.get("image_url", "")).strip()
    if not img_url.startswith("http"):
        img_url = _assign_mock_image(
            str(p.get("id", "")), 
            str(p.get("category", "general")), 
            str(p.get("name", ""))
        )
        
    return {
        "id": str(p.get("id", "")),
        "name": _clean_name(p.get("name", "")),
        "category": str(p.get("category", "general")),
        "subcategory": str(p.get("subcategory", "")) or None,
        "brand": str(p.get("brand", "")) or None,
        "price": float(p.get("price", 0)),
        "original_price": float(p.get("original_price") or p.get("price", 0)),
        "discount_percent": int(p.get("discount_percent", 0)),
        "seller_name": str(p.get("seller_name", "")) or None,
        "seller_rating": float(p.get("seller_rating", 4.0)),
        "seller_review_count": int(p.get("seller_review_count", 0)),
        "seller_return_rate": float(p.get("seller_return_rate", 3.0)),
        "delivery_days": int(p.get("delivery_days", 3)),
        "available_pincodes": json.dumps(p.get("available_pincodes", [])),
        "stock_status": str(p.get("stock_status", "in_stock")),
        "price_trend_7d": float(p.get("price_trend_7d", 0.0)),
        "tags": json.dumps(p.get("tags", [])),
        "wattage": p.get("wattage"),
        "event_tags": json.dumps(p.get("event_tags", [])),
        "description": str(p.get("description", "")) or None,
        "image_url": img_url,
        "image_placeholder": str(p.get("image_placeholder", "")) or None,
        "confidence_score": int(p.get("confidence_score", 75)),
        "source": source,
    }

def build_sqlite(all_products):
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)
    for idx in INDEXES:
        cur.execute(idx)
    inserted = 0
    for p in all_products:
        try:
            n = _norm(p, p.get("_source", "mock"))
            if n["price"] <= 0 or not n["id"]:
                continue
            cur.execute(INSERT_SQL, n)
            inserted += 1
        except Exception as e:
            print(f"  [WARN] {p.get('id', '?')}: {e}")
    conn.commit()
    conn.close()
    return inserted


def print_stats():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT category, COUNT(*) FROM products GROUP BY category ORDER BY COUNT(*) DESC")
    rows = cur.fetchall()
    conn.close()
    print("\n  Products per category:")
    for cat, cnt in rows:
        bar = "=" * min(cnt, 50)
        print(f"    {cat:<26} {cnt:>4}  {bar}")


if __name__ == "__main__":
    print("\nPRISM Catalog Builder\n")
    print("Loading existing JSON catalogs...")
    json_products = load_json_products()
    for p in json_products:
        p["_source"] = "mock"

    print(f"\nIngesting Amazon CSV files from: {CSV_DIR}")
    amazon_products = ingest_csv_products()
    for p in amazon_products:
        p["_source"] = "amazon"

    all_products = []
    seen_ids = set()
    for p in json_products + amazon_products:
        pid = str(p.get("id", ""))
        if pid and pid not in seen_ids:
            seen_ids.add(pid)
            all_products.append(p)

    print(f"\nBuilding SQLite database at: {DB_PATH}")
    inserted = build_sqlite(all_products)
    print(f"Total products inserted: {inserted}")
    print_stats()
    print("\nDone!\n")

# Triggered reload

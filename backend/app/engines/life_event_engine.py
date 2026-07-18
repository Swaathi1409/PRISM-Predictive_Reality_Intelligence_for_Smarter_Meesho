"""
life_event_engine.py — Detects life events and Bharat context from user input.

WHY THIS MODULE EXISTS:
The central intelligence of PRISM. By detecting the life event before product
matching, we ensure every product recommendation is contextually relevant. A
bedsheet recommendation for a hostel move is very different from a woolen
layer recommendation for a Kashmir trek — this engine makes that distinction.

DETECTION STRATEGY (Revised):
- PRIMARY: A single LLM call (`detect_event_with_llm`) understands ANY free-text
  input and returns: event, location, cultural context, climate, product needs,
  purchase phases, and emotional message — all in one shot.
- FALLBACK: If LLM fails (timeout, API error), keyword-based `detect_event()` 
  is used as an emergency path. This preserves uptime while LLM is unavailable.
- The old separate calls (detect_event + detect_location + generate_llm_roadmap)
  are replaced by this unified approach: same LLM budget, vastly better results.

WHY ONE LLM CALL INSTEAD OF THREE:
Previously: detect_event() [keyword] → detect_location() [keyword] → generate_llm_roadmap() [LLM]
Now: detect_event_with_llm() [LLM] handles all three in a single structured prompt.
This is cheaper (one API call), more coherent (location informs event informs phases),
and handles ANY input — not just the 8 pre-defined events.

Library: json (stdlib), re (stdlib), groq (Apache 2.0), app.config (internal).
"""

import json
import os
import re
from typing import Dict, Any, Optional, Tuple, List

from groq import Groq
from app.config import settings

_client = Groq(api_key=settings.groq_api_key)

_TEMPLATES_PATH = os.path.join(os.path.dirname(__file__), "../data/life_event_templates.json")
_CONTEXT_PATH = os.path.join(os.path.dirname(__file__), "../data/bharat_context.json")

# Module-level cache — loaded once, reused for every request
_templates: Optional[Dict] = None
_context: Optional[Dict] = None

# Category aliases: LLM can use these natural names, they map to product catalog categories
CATEGORY_ALIASES = {
    # ── Trek / Outdoor / Travel ───────────────────────────────────────────
    "trekking_gear": "bags_luggage",
    "outdoor_gear": "bags_luggage",
    "travel_bag": "bags_luggage",
    "hiking_bag": "bags_luggage",
    "backpack": "bags_luggage",
    "duffel_bag": "bags_luggage",
    "luggage": "bags_luggage",
    "suitcase": "bags_luggage",
    "handbag": "bags_luggage",
    "wallet": "bags_luggage",
    "school_bag": "bags_luggage",
    "rucksack": "bags_luggage",
    # ── Clothing / Apparel ────────────────────────────────────────────────
    "thermal_wear": "formal_wear",
    "woolen_wear": "formal_wear",
    "winter_clothing": "formal_wear",
    "modest_dress": "formal_wear",
    "traditional_dress": "formal_wear",
    "cultural_clothing": "formal_wear",
    "rain_gear": "formal_wear",
    "ethnic_wear": "formal_wear",
    "kurta": "formal_wear",
    "saree": "formal_wear",
    "lehenga": "formal_wear",
    "sherwani": "formal_wear",
    "salwar": "formal_wear",
    "dupatta": "formal_wear",
    "men_clothing": "fashion_men",
    "mens_clothing": "fashion_men",
    "shirt": "fashion_men",
    "jeans": "fashion_men",
    "trousers": "fashion_men",
    "tshirt": "fashion_men",
    "t_shirt": "fashion_men",
    "polo": "fashion_men",
    "men_wear": "fashion_men",
    "office_wear": "fashion_men",
    "blazer": "fashion_men",
    "women_clothing": "fashion_women",
    "womens_clothing": "fashion_women",
    "western_wear": "fashion_women",
    "dress": "fashion_women",
    "top": "fashion_women",
    "kurti": "fashion_women",
    "nightwear": "fashion_women",
    "innerwear": "fashion_women",
    "kids_clothing": "fashion_kids",
    "children_clothing": "fashion_kids",
    "kids_wear": "fashion_kids",
    "uniform": "fashion_kids",
    "baby_clothes": "fashion_kids",
    # ── Shoes / Footwear ──────────────────────────────────────────────────
    "shoes": "shoes",
    "footwear": "shoes",
    "sandals": "shoes",
    "slippers": "shoes",
    "heels": "shoes",
    "formal_shoes": "shoes",
    "sports_shoes": "shoes",
    "running_shoes": "shoes",
    "casual_shoes": "shoes",
    "kids_shoes": "shoes",
    "sneakers": "shoes",
    "boots": "shoes",
    # ── Sportswear ────────────────────────────────────────────────────────
    "sportswear": "sportswear",
    "tracksuit": "sportswear",
    "joggers": "sportswear",
    "gym_wear": "sportswear",
    "athletic_wear": "sportswear",
    "jersey": "sportswear",
    "sports_kit": "sportswear",
    # ── Bedding ────────────────────────────────────────────────────────────
    "thermal_bedding": "bedding",
    "sleeping_bag": "bedding",
    "warm_bedding": "bedding",
    "bedsheet": "bedding",
    "pillow": "bedding",
    "comforter": "bedding",
    "blanket": "bedding",
    "mattress": "bedding",
    # ── Personal Care ─────────────────────────────────────────────────────
    "moisture_wicking": "personal_care",
    "sunscreen": "personal_care",
    "first_aid": "personal_care",
    "hygiene_kit": "personal_care",
    "toiletry": "personal_care",
    "grooming": "personal_care",
    # ── Beauty ────────────────────────────────────────────────────────────
    "beauty": "beauty_grooming",
    "makeup": "beauty_grooming",
    "skincare": "beauty_grooming",
    "cosmetics": "beauty_grooming",
    "haircare": "beauty_grooming",
    "beauty_grooming": "beauty_grooming",
    "perfume": "beauty_grooming",
    "deodorant": "beauty_grooming",
    "serum": "beauty_grooming",
    # ── Kitchen / Food ────────────────────────────────────────────────────
    "portable_cooker": "kitchen_essentials",
    "water_bottle": "kitchen_essentials",
    "tiffin": "kitchen_essentials",
    "flask": "kitchen_essentials",
    "home_kitchen": "home_kitchen",
    "kitchen_items": "home_kitchen",
    "cookware": "home_kitchen",
    "utensils": "home_kitchen",
    "crockery": "home_kitchen",
    "storage_containers": "home_kitchen",
    "kitchen_appliances": "kitchen_appliances",
    "mixer": "kitchen_appliances",
    "blender": "kitchen_appliances",
    "microwave": "kitchen_appliances",
    "induction": "kitchen_appliances",
    "pressure_cooker": "kitchen_appliances",
    # ── Home Decor ────────────────────────────────────────────────────────
    "home_decor": "home_decor",
    "wall_decor": "home_decor",
    "lighting": "home_decor",
    "furniture": "home_decor",
    "curtains": "home_decor",
    "rugs": "home_decor",
    "photo_frames": "home_decor",
    # ── Appliances ────────────────────────────────────────────────────────
    "appliances": "appliances",
    "washing_machine": "appliances",
    "refrigerator": "appliances",
    "fridge": "appliances",
    "air_conditioner": "appliances",
    "ac": "appliances",
    "television": "appliances",
    "tv": "appliances",
    "geyser": "appliances",
    # ── Sports & Fitness ──────────────────────────────────────────────────
    "sports_equipment": "sports_fitness",
    "fitness_equipment": "sports_fitness",
    "gym_equipment": "sports_fitness",
    "yoga_mat": "sports_fitness",
    "cycling_gear": "sports_fitness",
    "cricket_kit": "sports_fitness",
    "badminton": "sports_fitness",
    "football": "sports_fitness",
    "sports_accessories": "sports_fitness",
    "dumbbells": "sports_fitness",
    "treadmill": "sports_fitness",
    "protein_supplements": "sports_fitness",
    # ── Jewellery & Watches ───────────────────────────────────────────────
    "jewellery": "jewellery",
    "jewelry": "jewellery",
    "necklace": "jewellery",
    "earrings": "jewellery",
    "bracelet": "jewellery",
    "ring": "jewellery",
    "gold_jewellery": "jewellery",
    "silver_jewellery": "jewellery",
    "bridal_jewellery": "jewellery",
    "watches": "watches",
    "watch": "watches",
    "smartwatch": "watches",
    # ── Baby Products ─────────────────────────────────────────────────────
    "baby_products": "baby_products",
    "baby": "baby_products",
    "diapers": "baby_products",
    "baby_care": "baby_products",
    "feeding": "baby_products",
    "stroller": "baby_products",
    "pram": "baby_products",
    "nursing": "baby_products",
    "baby_food": "baby_products",
    # ── Toys & Games ──────────────────────────────────────────────────────
    "toys_games": "toys_games",
    "toys": "toys_games",
    "games": "toys_games",
    "board_games": "toys_games",
    "kids_toys": "toys_games",
    "stem_toys": "toys_games",
    # ── Pet Supplies ──────────────────────────────────────────────────────
    "pet_supplies": "pet_supplies",
    "pet_food": "pet_supplies",
    "dog_supplies": "pet_supplies",
    "cat_supplies": "pet_supplies",
    # ── Garden & Outdoor ──────────────────────────────────────────────────
    "garden_outdoor": "garden_outdoor",
    "gardening": "garden_outdoor",
    "camping": "garden_outdoor",
    "hiking_gear": "garden_outdoor",
    "outdoor_furniture": "garden_outdoor",
    "trekking": "garden_outdoor",
    # ── Automotive ────────────────────────────────────────────────────────
    "automotive": "automotive",
    "car_accessories": "automotive",
    "bike_accessories": "automotive",
    "car_care": "automotive",
    "vehicle": "automotive",
    # ── Security ─────────────────────────────────────────────────────────
    "security": "security",
    "cctv": "security",
    "smart_lock": "security",
    "door_lock": "security",
    "alarm": "security",
    # ── Stationery / Study ────────────────────────────────────────────────
    "stationery": "stationery",
    "study_accessories": "study_accessories",
    "exam_supplies": "exam_supplies",
    "notebooks": "stationery",
    "pens": "stationery",
    "calculator": "stationery",
    "craft_supplies": "stationery",
    # ── Food / Grocery ────────────────────────────────────────────────────
    "food": "food",
    "grocery": "food",
    "snacks": "food",
    "beverages": "food",
    "health_food": "food",
    "instant_food": "food",
    "spices": "food",
    # ── Passthrough (original catalog categories) ─────────────────────────
    "bedding": "bedding",
    "personal_care": "personal_care",
    "bags_luggage": "bags_luggage",
    "kitchen_essentials": "kitchen_essentials",
    "formal_wear": "formal_wear",
    "festival_decor": "festival_decor",
    "electronics": "electronics",
    "shop_supplies": "shop_supplies",
    "home_improvement": "home_improvement",
    "wedding_apparel": "wedding_apparel",
    # ── New passthrough ───────────────────────────────────────────────────
    "fashion_men": "fashion_men",
    "fashion_women": "fashion_women",
    "fashion_kids": "fashion_kids",
    "beauty_grooming": "beauty_grooming",
    "home_kitchen": "home_kitchen",
    "home_decor": "home_decor",
    "appliances": "appliances",
    "sports_fitness": "sports_fitness",
    "sportswear": "sportswear",
    "shoes": "shoes",
    "watches": "watches",
    "jewellery": "jewellery",
    "baby_products": "baby_products",
    "toys_games": "toys_games",
    "pet_supplies": "pet_supplies",
    "garden_outdoor": "garden_outdoor",
    "automotive": "automotive",
    "kitchen_appliances": "kitchen_appliances",
    "security": "security",
    "food": "food",
    "stationery": "stationery",
    "exam_supplies": "exam_supplies",
    "wedding_apparel": "wedding_apparel",
    "home_improvement": "home_improvement",
}

VALID_CATEGORIES = list(set(CATEGORY_ALIASES.values()))
VALID_EVENT_KEYS = [
    "hostel_move", "wedding", "new_baby", "first_job", "festival_prep",
    "new_home", "government_exam", "shop_opening", "travel_adventure",
    "religious_travel", "cultural_event", "seasonal_prep", "generic"
]

# Comprehensive city → state key mapping for keyword fallback detection.
# Covers capitals, major cities, tier-2 cities, pilgrimage sites, hill stations,
# and popular tourist destinations across all 28 states + 8 UTs.
# The LLM handles this naturally, but this map ensures the fallback path works correctly.
CITY_TO_STATE: dict = {
    # Andhra Pradesh
    "vijayawada": "andhra_pradesh", "visakhapatnam": "andhra_pradesh",
    "vizag": "andhra_pradesh", "tirupati": "andhra_pradesh",
    "amaravati": "andhra_pradesh", "guntur": "andhra_pradesh",
    "nellore": "andhra_pradesh", "kurnool": "andhra_pradesh",
    "rajahmundry": "andhra_pradesh", "kakinada": "andhra_pradesh",

    # Arunachal Pradesh
    "itanagar": "arunachal_pradesh", "tawang": "arunachal_pradesh",
    "naharlagun": "arunachal_pradesh", "ziro": "arunachal_pradesh",
    "bomdila": "arunachal_pradesh", "aalo": "arunachal_pradesh",

    # Assam
    "guwahati": "assam", "dispur": "assam", "silchar": "assam",
    "dibrugarh": "assam", "jorhat": "assam", "nagaon": "assam",
    "tinsukia": "assam", "sivasagar": "assam", "kaziranga": "assam",
    "majuli": "assam",

    # Bihar
    "patna": "bihar", "gaya": "bihar", "bhagalpur": "bihar",
    "muzaffarpur": "bihar", "purnia": "bihar", "darbhanga": "bihar",
    "arrah": "bihar", "begusarai": "bihar", "nalanda": "bihar",
    "bodh gaya": "bihar", "bodhgaya": "bihar", "vaishali": "bihar",
    "rajgir": "bihar", "sitamarhi": "bihar", "sasaram": "bihar",

    # Chandigarh
    "chandigarh": "chandigarh",

    # Chhattisgarh
    "raipur": "chhattisgarh", "bhilai": "chhattisgarh", "bilaspur": "chhattisgarh",
    "durg": "chhattisgarh", "korba": "chhattisgarh", "jagdalpur": "chhattisgarh",
    "raigarh": "chhattisgarh", "bastar": "chhattisgarh", "ambikapur": "chhattisgarh",

    # Dadra & NH / Daman & Diu
    "daman": "dadra_nagar_haveli_daman_diu", "diu": "dadra_nagar_haveli_daman_diu",
    "silvassa": "dadra_nagar_haveli_daman_diu", "dadra": "dadra_nagar_haveli_daman_diu",

    # Delhi
    "delhi": "delhi", "new delhi": "delhi", "gurgaon": "delhi",
    "noida": "delhi", "faridabad": "delhi", "gurugram": "delhi",
    "greater noida": "delhi", "dwarka": "delhi", "rohini": "delhi",
    "connaught place": "delhi", "south delhi": "delhi", "north delhi": "delhi",
    "east delhi": "delhi", "west delhi": "delhi",

    # Goa
    "panaji": "goa", "vasco da gama": "goa", "margao": "goa",
    "panjim": "goa", "calangute": "goa", "baga": "goa",
    "anjuna": "goa", "colva": "goa", "madgaon": "goa", "mapusa": "goa",
    "north goa": "goa", "south goa": "goa",

    # Gujarat
    "ahmedabad": "gujarat", "surat": "gujarat", "vadodara": "gujarat",
    "rajkot": "gujarat", "gandhinagar": "gujarat", "bhavnagar": "gujarat",
    "jamnagar": "gujarat", "junagadh": "gujarat", "anand": "gujarat",
    "nadiad": "gujarat", "mehsana": "gujarat", "morbi": "gujarat",
    "dwarka": "gujarat", "somnath": "gujarat", "kutch": "gujarat",
    "rann of kutch": "gujarat", "kevadia": "gujarat", "statue of unity": "gujarat",

    # Haryana
    "ambala": "haryana", "karnal": "haryana", "panipat": "haryana",
    "rohtak": "haryana", "hisar": "haryana", "sonipat": "haryana",
    "yamunanagar": "haryana", "gurugram haryana": "haryana", "bahadurgarh": "haryana",
    "bhiwani": "haryana", "sirsa": "haryana", "fatehabad": "haryana",
    "kurukshetra": "haryana",

    # Himachal Pradesh
    "shimla": "himachal_pradesh", "manali": "himachal_pradesh",
    "dharamshala": "himachal_pradesh", "solan": "himachal_pradesh",
    "mandi": "himachal_pradesh", "kullu": "himachal_pradesh",
    "bilaspur": "himachal_pradesh", "hamirpur": "himachal_pradesh",
    "dalhousie": "himachal_pradesh", "kasauli": "himachal_pradesh",
    "chail": "himachal_pradesh", "narkanda": "himachal_pradesh",
    "spiti": "himachal_pradesh", "lahaul": "himachal_pradesh",
    "mcleod ganj": "himachal_pradesh", "mcleodganj": "himachal_pradesh",

    # Jammu & Kashmir
    "srinagar": "jammu_kashmir", "jammu": "jammu_kashmir",
    "kashmir": "jammu_kashmir", "gulmarg": "jammu_kashmir",
    "pahalgam": "jammu_kashmir", "sonamarg": "jammu_kashmir",
    "vaishno devi": "jammu_kashmir", "katra": "jammu_kashmir",
    "anantnag": "jammu_kashmir", "baramulla": "jammu_kashmir",
    "kupwara": "jammu_kashmir", "dal lake": "jammu_kashmir",

    # Jharkhand
    "ranchi": "jharkhand", "jamshedpur": "jharkhand", "dhanbad": "jharkhand",
    "bokaro": "jharkhand", "deoghar": "jharkhand", "hazaribagh": "jharkhand",
    "dumka": "jharkhand", "giridih": "jharkhand", "ramgarh": "jharkhand",
    "palamau": "jharkhand",

    # Karnataka
    "bengaluru": "karnataka", "bangalore": "karnataka", "mysuru": "karnataka",
    "mysore": "karnataka", "hubli": "karnataka", "dharwad": "karnataka",
    "mangaluru": "karnataka", "mangalore": "karnataka", "belagavi": "karnataka",
    "bellary": "karnataka", "gulbarga": "karnataka", "kalaburagi": "karnataka",
    "tumkur": "karnataka", "shimoga": "karnataka", "hassan": "karnataka",
    "udupi": "karnataka", "chikmagalur": "karnataka", "coorg": "karnataka",
    "hampi": "karnataka", "badami": "karnataka",

    # Kerala
    "thiruvananthapuram": "kerala", "trivandrum": "kerala",
    "kochi": "kerala", "cochin": "kerala", "kozhikode": "kerala",
    "calicut": "kerala", "thrissur": "kerala", "kollam": "kerala",
    "malappuram": "kerala", "palakkad": "kerala", "kannur": "kerala",
    "alappuzha": "kerala", "alleppey": "kerala", "munnar": "kerala",
    "wayanad": "kerala", "varkala": "kerala", "kovalam": "kerala",

    # Ladakh
    "leh": "ladakh", "ladakh": "ladakh", "kargil": "ladakh",
    "nubra": "ladakh", "pangong": "ladakh", "zanskar": "ladakh",
    "khardung la": "ladakh", "diskit": "ladakh", "hunder": "ladakh",

    # Lakshadweep
    "kavaratti": "lakshadweep", "lakshadweep": "lakshadweep",
    "agatti": "lakshadweep", "minicoy": "lakshadweep",
    "bangaram": "lakshadweep", "amini": "lakshadweep",

    # Madhya Pradesh
    "bhopal": "madhya_pradesh", "indore": "madhya_pradesh",
    "jabalpur": "madhya_pradesh", "gwalior": "madhya_pradesh",
    "ujjain": "madhya_pradesh", "sagar": "madhya_pradesh",
    "rewa": "madhya_pradesh", "satna": "madhya_pradesh",
    "dewas": "madhya_pradesh", "khandwa": "madhya_pradesh",
    "khajuraho": "madhya_pradesh", "sanchi": "madhya_pradesh",
    "pachmarhi": "madhya_pradesh", "chanderi": "madhya_pradesh",
    "maheshwar": "madhya_pradesh",

    # Maharashtra
    "mumbai": "maharashtra", "pune": "maharashtra", "nagpur": "maharashtra",
    "nashik": "maharashtra", "aurangabad": "maharashtra",
    "solapur": "maharashtra", "kolhapur": "maharashtra",
    "thane": "maharashtra", "pimpri": "maharashtra", "amravati": "maharashtra",
    "nanded": "maharashtra", "sangli": "maharashtra", "akola": "maharashtra",
    "latur": "maharashtra", "dhule": "maharashtra", "jalgaon": "maharashtra",
    "shirdi": "maharashtra", "lonavala": "maharashtra", "mahabaleshwar": "maharashtra",
    "ajanta": "maharashtra", "ellora": "maharashtra",

    # Manipur
    "imphal": "manipur", "thoubal": "manipur", "bishnupur": "manipur",
    "churachandpur": "manipur", "ukhrul": "manipur", "senapati": "manipur",
    "loktak": "manipur",

    # Meghalaya
    "shillong": "meghalaya", "cherrapunji": "meghalaya",
    "sohra": "meghalaya", "tura": "meghalaya", "jowai": "meghalaya",
    "mawsynram": "meghalaya", "dawki": "meghalaya",

    # Mizoram
    "aizawl": "mizoram", "lunglei": "mizoram", "champhai": "mizoram",
    "serchhip": "mizoram",

    # Nagaland
    "kohima": "nagaland", "dimapur": "nagaland", "mokokchung": "nagaland",
    "tuensang": "nagaland", "wokha": "nagaland", "mon": "nagaland",
    "hornbill festival": "nagaland",

    # Odisha
    "bhubaneswar": "odisha", "cuttack": "odisha", "puri": "odisha",
    "rourkela": "odisha", "sambalpur": "odisha", "berhampur": "odisha",
    "konark": "odisha", "chilika": "odisha", "kendujhar": "odisha",
    "balasore": "odisha", "jagannath puri": "odisha",

    # Puducherry
    "pondicherry": "puducherry", "puducherry": "puducherry",
    "auroville": "puducherry", "mahe": "puducherry",

    # Punjab
    "amritsar": "punjab", "ludhiana": "punjab", "jalandhar": "punjab",
    "patiala": "punjab", "bathinda": "punjab", "mohali": "punjab",
    "pathankot": "punjab", "hoshiarpur": "punjab", "gurdaspur": "punjab",
    "golden temple": "punjab", "wagah": "punjab", "anandpur sahib": "punjab",

    # Rajasthan
    "jaipur": "rajasthan", "jodhpur": "rajasthan", "udaipur": "rajasthan",
    "ajmer": "rajasthan", "kota": "rajasthan", "bikaner": "rajasthan",
    "pushkar": "rajasthan", "jaisalmer": "rajasthan", "mount abu": "rajasthan",
    "chittorgarh": "rajasthan", "ranthambore": "rajasthan",
    "alwar": "rajasthan", "bharatpur": "rajasthan", "sikar": "rajasthan",

    # Sikkim
    "gangtok": "sikkim", "pelling": "sikkim", "namchi": "sikkim",
    "yuksom": "sikkim", "ravangla": "sikkim", "lachung": "sikkim",
    "lachen": "sikkim", "rumtek": "sikkim", "tsomgo": "sikkim",

    # Tamil Nadu
    "chennai": "tamil_nadu", "madras": "tamil_nadu", "coimbatore": "tamil_nadu",
    "madurai": "tamil_nadu", "tiruchirappalli": "tamil_nadu", "trichy": "tamil_nadu",
    "salem": "tamil_nadu", "tirunelveli": "tamil_nadu", "vellore": "tamil_nadu",
    "erode": "tamil_nadu", "tiruppur": "tamil_nadu", "ooty": "tamil_nadu",
    "kodaikanal": "tamil_nadu", "kumbakonam": "tamil_nadu",
    "thanjavur": "tamil_nadu", "rameswaram": "tamil_nadu",
    "kanyakumari": "tamil_nadu", "mahabalipuram": "tamil_nadu",

    # Telangana
    "hyderabad": "telangana", "warangal": "telangana", "nizamabad": "telangana",
    "karimnagar": "telangana", "khammam": "telangana", "mahbubnagar": "telangana",
    "nalgonda": "telangana", "adilabad": "telangana", "secunderabad": "telangana",
    "cyberabad": "telangana",

    # Tripura
    "agartala": "tripura", "udaipur tripura": "tripura",
    "dharmanagar": "tripura", "sabroom": "tripura",

    # Uttar Pradesh
    "lucknow": "uttar_pradesh", "kanpur": "uttar_pradesh",
    "agra": "uttar_pradesh", "varanasi": "uttar_pradesh",
    "allahabad": "uttar_pradesh", "prayagraj": "uttar_pradesh",
    "meerut": "uttar_pradesh", "ghaziabad": "uttar_pradesh",
    "mathura": "uttar_pradesh", "vrindavan": "uttar_pradesh",
    "ayodhya": "uttar_pradesh", "bareilly": "uttar_pradesh",
    "aligarh": "uttar_pradesh", "moradabad": "uttar_pradesh",
    "gorakhpur": "uttar_pradesh", "firozabad": "uttar_pradesh",
    "saharanpur": "uttar_pradesh", "taj mahal": "uttar_pradesh",
    "kashi": "uttar_pradesh", "banaras": "uttar_pradesh",

    # Uttarakhand
    "dehradun": "uttarakhand", "haridwar": "uttarakhand",
    "rishikesh": "uttarakhand", "nainital": "uttarakhand",
    "mussoorie": "uttarakhand", "kedarnath": "uttarakhand",
    "badrinath": "uttarakhand", "gangotri": "uttarakhand",
    "yamunotri": "uttarakhand", "auli": "uttarakhand",
    "corbett": "uttarakhand", "char dham": "uttarakhand",
    "chardham": "uttarakhand", "tehri": "uttarakhand",
    "rudraprayag": "uttarakhand", "chamoli": "uttarakhand",

    # West Bengal
    "kolkata": "west_bengal", "calcutta": "west_bengal",
    "darjeeling": "west_bengal", "siliguri": "west_bengal",
    "asansol": "west_bengal", "durgapur": "west_bengal",
    "howrah": "west_bengal", "bardhaman": "west_bengal",
    "cooch behar": "west_bengal", "malda": "west_bengal",
    "murshidabad": "west_bengal", "shantiniketan": "west_bengal",
    "sundarbans": "west_bengal",

    # Andaman & Nicobar
    "port blair": "andaman_nicobar", "andaman": "andaman_nicobar",
    "nicobar": "andaman_nicobar", "neil island": "andaman_nicobar",
    "havelock": "andaman_nicobar", "ross island": "andaman_nicobar",
}


def _load_templates() -> Dict:
    global _templates
    if _templates is None:
        with open(_TEMPLATES_PATH, encoding="utf-8") as f:
            _templates = json.load(f)
    return _templates


def _load_context() -> Dict:
    global _context
    if _context is None:
        with open(_CONTEXT_PATH, encoding="utf-8") as f:
            _context = json.load(f)
    return _context


def _resolve_categories(raw_categories: List[str]) -> List[str]:
    """Maps any LLM-generated category name to a valid catalog category."""
    resolved = []
    for cat in raw_categories:
        cat_lower = cat.lower().replace(" ", "_")
        if cat_lower in CATEGORY_ALIASES:
            resolved.append(CATEGORY_ALIASES[cat_lower])
        else:
            # Partial match fallback
            for alias, target in CATEGORY_ALIASES.items():
                if alias in cat_lower or cat_lower in alias:
                    resolved.append(target)
                    break
            else:
                # Last resort: keep as-is if it's already valid
                if cat_lower in VALID_CATEGORIES:
                    resolved.append(cat_lower)
    # Deduplicate while preserving order
    seen = set()
    return [c for c in resolved if not (c in seen or seen.add(c))]


def _get_default_template(event_key: str) -> Dict:
    """Returns a safe default template for a given event key."""
    templates = _load_templates()
    if event_key in templates:
        return templates[event_key]
    # Generic fallback
    return {
        "label": "Shopping Assistance",
        "timeline_days": 30,
        "emotion_level": "moderate",
        "family_significance": "moderate",
        "suggested_budget_range": {"min": 1000, "max": 50000},
        "purchase_phases": [
            {
                "phase_name": "Immediate Needs (Days 1-3)",
                "days_from_now": 0,
                "categories": ["personal_care", "bags_luggage"],
                "priority": "must_have",
                "note": "Get the essentials first."
            },
            {
                "phase_name": "Main Purchases (Days 4-7)",
                "days_from_now": 4,
                "categories": ["formal_wear", "bedding"],
                "priority": "should_have",
                "note": "Core items for your situation."
            },
            {
                "phase_name": "Nice to Have (Week 2)",
                "days_from_now": 7,
                "categories": ["kitchen_essentials"],
                "priority": "nice_to_have",
                "note": "Comfort and convenience upgrades."
            }
        ]
    }


class LifeEventEngine:
    """Detects life events and geographic/cultural context from ANY free text."""

    def get_template(self, event_key: str) -> Dict:
        """Returns the fallback template for a given event key."""
        return _get_default_template(event_key)

    def detect_event_with_llm(self, user_input: str, user_context: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        PRIMARY detection method. Single LLM call that understands ANY input:
        - Trek to Kashmir, cultural travel, religious pilgrimage, seasonal prep
        - All 8 original events (hostel, wedding, baby, etc.)
        - Completely novel contexts not in any template

        Args:
            user_input: The raw natural language query from the user.
            user_context: Optional PRISM Memory Intelligence string assembled by the frontend.
                          Contains prior session signals (city, employer, owned categories, budget
                          affinity) so the LLM can personalise this session's recommendations.

        Returns a comprehensive dict with event, location, cultural context,
        product needs, purchase phases, and emotional message — all in one call.
        Replaces: detect_event() + detect_location() + generate_llm_roadmap().
        """
        # Prepend memory intelligence block if available
        memory_block = ""
        if user_context and user_context.strip():
            memory_block = f"""\n[PRISM Memory Intelligence — from user's prior sessions]\n{user_context.strip()}\n\nUSE THIS CONTEXT: Avoid re-recommending categories the user already owns. Prioritise accessories/complements for those categories and fresh categories they haven\'t seen yet. Let their budget affinity and city/employer inform tone and product range.\n\n"""

        prompt = f"""You are PRISM, the world's most culturally intelligent Indian shopping assistant.{memory_block}
A user has typed: "{user_input}"

Your job: Deeply understand what they need, where they are/going, what cultural context matters, and what products will actually help them. Think like a smart Indian friend who knows local customs, climates, and regional products.

EXAMPLES of excellent reasoning:
- "Going trekking to Kashmir" → Detect: travel_adventure to cold mountain Islamic-majority region. Cultural: modest dress, warm layers, halal food storage. Products: thermal wear, trek bag, woolen shawls, warm bedding.
- "Son got into IIT Bombay hostel" → Detect: hostel_move to humid coastal city. Products: cotton bedding, study accessories, personal care.
- "Navratri coming up" → Detect: festival_prep. Products: festive dress, decor.
- "Getting married in Rajasthan in winter" → Detect: wedding in dry cold climate. Products: layered wedding attire, warm occasion wear.
- "Moving to new flat in Bangalore" → Detect: new_home in tech-hub mild climate. Products: kitchen setup, bedding, decor.
- "Setting up my music studio" or "recording studio setup" or "home studio" or "setting up studio" → Detect: generic (creative workspace). Intent: 'Setting up a professional music/recording/photo studio'. Products: electronics (microphone, audio interface, studio monitors/speakers, headphones), home_decor (acoustic panels, studio lighting), bags_luggage (equipment bags), stationery (cables, adapters). NEVER show bedding, pillows, kitchen items, or clothing for studio setups.
- "Setting up photo studio" or "photography studio" → Detect: generic. Products: electronics (camera, studio lights, tripod, backdrop), bags_luggage (camera bag).
- "I want to buy a car" or "Book a flight to Delhi" or "Invest in stocks" → Detect: unsupported. Intent: "User wants a non-retail service". Purchase phases: []. Message: "I specialize in retail shopping and event planning on Meesho. I cannot help with cars, flights, or stocks."

Available event keys: hostel_move, wedding, new_baby, first_job, festival_prep, new_home, government_exam, shop_opening, travel_adventure, religious_travel, cultural_event, seasonal_prep, generic, unsupported

CRITICAL GUARDRAIL:
If the user's request is completely unrelated to buying physical retail products (e.g., booking flights, investing in stocks, insurance, restaurant recommendations, software), you MUST set "event_key" to "unsupported". In this case, set "purchase_phases" to [] and write a brief apology in "emotional_message". Note: Buying a car or bike means they need automotive accessories (which IS supported).

Available product categories: bedding, study_accessories, personal_care, bags_luggage, kitchen_essentials, formal_wear, festival_decor, baby_products, electronics, kitchen_appliances, shop_supplies, food, security, home_decor, jewellery, stationery, exam_supplies, wedding_apparel, home_improvement, fashion_men, fashion_women, fashion_kids, beauty_grooming, home_kitchen, appliances, sports_fitness, sportswear, shoes, watches, toys_games, pet_supplies, garden_outdoor, automotive

CATEGORY MAPPING GUIDE (map user needs to these):
- Trekking bag / luggage / backpack / suitcase / wallet / handbag → bags_luggage
- Men's shirts / jeans / trousers / polo / blazer / office wear → fashion_men
- Women's western wear / dress / kurti / tops / nightwear → fashion_women
- Kids clothing / children's wear / school uniform / baby clothes → fashion_kids
- Ethnic wear / kurta / saree / lehenga / sherwani / traditional dress / modest wear / woolen / thermal → formal_wear
- Sports shoes / running shoes / formal shoes / sandals / heels / slippers → shoes
- Tracksuit / joggers / gym wear / jersey / sports kit / athletic wear → sportswear
- Sleeping bag / warm blanket / thermal sheets / bedsheet / pillow / comforter → bedding
- Sunscreen / first aid / toiletries / grooming kits → personal_care
- Skincare / makeup / beauty products / cosmetics / haircare / perfume → beauty_grooming
- Water bottle / flask / tiffin / portable cooker → kitchen_essentials
- Cookware / utensils / kitchen containers / storage / crockery → home_kitchen
- Mixer / blender / microwave / induction / pressure cooker → kitchen_appliances
- Washing machine / fridge / refrigerator / AC / air conditioner / TV / geyser → appliances
- Wall decor / lighting / furniture / curtains / rugs / photo frames → home_decor
- Yoga mat / dumbbells / cricket kit / cycling gear / badminton / treadmill → sports_fitness
- Watches / smartwatch → watches
- Necklace / earrings / ring / bracelet / gold jewellery / bridal jewellery → jewellery
- Diapers / baby care / stroller / nursing / baby food → baby_products
- Toys / board games / STEM toys / kids toys → toys_games
- Pet food / dog supplies / cat supplies → pet_supplies
- Gardening / camping / trekking / hiking gear / outdoor furniture → garden_outdoor
- Car accessories / bike accessories / car care / vehicle → automotive
- CCTV / smart lock / door lock / security camera / alarm → security
- Study materials / books / prep materials → study_accessories
- Pens / notebooks / writing materials / calculator / craft → stationery
- Decorations / lights / rangoli / puja items → festival_decor
- Commercial items / shelves / POS systems / signage / billing → shop_supplies
- Tools / hardware / repair items → home_improvement
- Laptops / chargers / tech gadgets / speakers / headphones / camera → electronics
- Wedding dresses / bridal wear / groom wear → wedding_apparel
- Food / groceries / snacks / beverages → food

CRITICAL: For "purchase_phases", you MUST generate EXACTLY 2 or 3 distinct chronological phases. Do NOT generate fewer than 2 phases for valid retail queries.

Return ONLY valid JSON with this exact structure:
{{
  "is_supported_retail_query": true,
  "event_key": "one of the valid event keys above",
  "event_label": "Natural 3-5 word description of what they are doing",
  "intent": "The core underlying need in 1 sentence",
  "detected_location": {{
    "place_name": "Kashmir / Tamil Nadu / Mumbai / null",
    "state_key": "jammu_kashmir / tamil_nadu / maharashtra / null (use snake_case state name)",
    "climate": "cold mountain / tropical humid / arid desert / semi-arid / moderate / null",
    "season_guess": "winter / summer / monsoon / null",
    "is_travel_destination": true
  }},
  "cultural_context": "Specific cultural norms that affect product choices. E.g. 'Islamic majority region, modest dress expected, halal food storage important, conservative attire for women' OR 'Tamil Hindu culture, Kancheevaram silk appropriate for occasions' OR null if no special cultural context",
  "climate_product_note": "How climate affects what they should buy. E.g. 'Cold mountain air requires thermal layers, wool, moisture-wicking base' OR null",
  "product_needs": [
    "specific product need 1 (e.g. 'warm woolen shawl for cold evenings')",
    "specific product need 2 (e.g. 'trekking backpack 40-60L')",
    "specific product need 3"
  ],
  "category_mapping": ["formal_wear", "bags_luggage", "bedding"],
  "emotional_message": "2-3 warm sentences acknowledging their situation. Warm Indian English. No product names. No prices. Do NOT start with I. Start with the emotion or the moment.",
  "budget_constraint_detected": true_or_false,
  "detected_budget": 500, // The exact budget number in rupees if detected, else null
  "exact_items_requested": ["specific items they literally asked for"],
  "purchase_phases": [
    {{
      "phase_name": "Phase 1: Immediate Needs (Week 1)",
      "days_from_now": 0,
      "categories": ["bags_luggage", "bedding"],
      "suggested_items": ["travel backpack", "bedsheet"],
      "priority": "must_have",
      "note": "Why they need this first, with cultural/climate context."
    }},
    {{
      "phase_name": "Phase 2: Settle In (Week 2)",
      "days_from_now": 7,
      "categories": ["study_accessories", "personal_care"],
      "suggested_items": ["study lamp", "toiletry kit"],
      "priority": "should_have",
      "note": "Items needed after first week of settling in."
    }},
    {{
      "phase_name": "Phase 3: Long-Term Comfort (Week 3-4)",
      "days_from_now": 14,
      "categories": ["kitchen_essentials", "fashion_men"],
      "suggested_items": ["water bottle", "casual wear"],
      "priority": "nice_to_have",
      "note": "Comfort and lifestyle upgrades once settled."
    }}
  ],
  "timeline_days": 30,
  "emotion_level": "very_high or high or moderate or low",
  "family_significance": "extremely_high or very_high or high or moderate",
  "budget_constraint_detected": false,
  "urgency_override": false
}}

CRITICAL INSTRUCTION FOR NON-SHOPPING QUERIES:
If the user's intent is NOT about buying physical retail products (e.g., book flights, get restaurant recommendations, invest in stocks, buy insurance, get a software/app, etc.), YOU MUST STRICTLY DO THE FOLLOWING:
1. Set "is_supported_retail_query" to false.
2. Set "event_key" to "unsupported".
3. Set "intent" to "Unsupported non-retail request".
4. Set "purchase_phases" to an empty list: [].
5. Set "exact_items_requested" to [].
6. Write an apology in "emotional_message" stating that you only specialize in retail shopping and event planning on Meesho.
Failure to do this will result in the system hallucinating products.

RULES:
1. All categories in purchase_phases MUST be from the valid categories list above
2. Use the CATEGORY MAPPING GUIDE to convert user needs → valid categories
3. emotional_message must be warm, specific to their situation, in Indian English
4. cultural_context and climate_product_note must be genuinely useful, not generic
5. If location is a travel destination, set is_travel_destination: true
6. timeline_days: hostel/first_job=28-30, wedding=90, trek/travel=14-21, festival=7-14, government_exam=60
7. PHASE NAMING RULE — CRITICAL:
   - If timeline_days >= 21 (hostel move, first job, new home, wedding etc.), name phases as:
     Phase 1: Immediate Needs (Week 1), Phase 2: Settle In (Week 2), Phase 3: Long-Term Comfort (Week 3-4)
   - If timeline_days < 21 (festival, travel, exam within 2 weeks, next week, day trip, temple visit, single-day event), name phases as:
     Phase 1: Get Ready (Days 1-2), Phase 2: Main Purchases (Days 3-5), Phase 3: Final Touches (Days 5-7)
   - ALWAYS generate EXACTLY 3 phases. Never fewer.
   - If the user says "next week" or implies an event within 7 days, set timeline_days=7 and ALWAYS use the DAY-based naming (Days 1-2 etc), NOT week-based.
8. CATEGORY GUARDRAILS — CRITICAL (avoid irrelevant categories):
   - hostel_move / first_job / government_exam: NEVER use baby_products, wedding_apparel, toys_games, pet_supplies, automotive, power_tools, kitchen_appliances (use kitchen_essentials for mini kettles/tiffins instead)
   - wedding: NEVER use baby_products, exam_supplies, power_tools, pet_supplies
   - festival_prep: NEVER use baby_products, exam_supplies, automotive, power_tools
   - new_baby: NEVER use exam_supplies, shop_supplies, automotive, power_tools
   - religious_travel / cultural_event (e.g. visiting temple, attending puja, pilgrimage): ONLY use formal_wear (modest/traditional attire), personal_care (hygiene basics), festival_decor (prasad/puja items), food (offerings/prasad sweets), shoes, bags_luggage (small bag/wallet). NEVER use study_accessories, exam_supplies, electronics, appliances, kitchen_appliances, baby_products, toys_games, automotive, shop_supplies, home_improvement, sportswear, sports_fitness, security, garden_outdoor, pet_supplies.
   - generic (studio setup / music studio / recording studio / photo studio / creative workspace): ONLY use electronics (microphone, speakers, headphones, studio monitors, audio interface, camera, lighting), home_decor (studio lighting, acoustic panels), bags_luggage (equipment bag), stationery (cables, adapters). NEVER use bedding, pillow, kitchen_essentials, home_kitchen, kitchen_appliances, fashion_men, fashion_women, personal_care, baby_products.
   - For hostel_move specifically: bedding means bedsheets/pillows for a college student, NOT baby bedding/mattress covers
   - BUDGET GUARDRAIL: If the user specifies a budget (e.g. "under ₹100", "under 500"), set detected_budget to that value. Do NOT include categories whose typical minimum price exceeds the stated budget. For budgets under ₹200, limit categories to food, stationery, festival_decor, personal_care only.
9. If a user says "next month" or "starting [month]", set timeline_days=28-30 and use WEEK-based phase naming
10. exact_items_requested: only list items the user literally mentioned by name
11. SPECIFIC ITEM RULE: If the user asks for a very specific product type (e.g. "phone", "earphones", "laptop", "charger"), set exact_items_requested to that item and limit purchase_phases categories STRICTLY to the one category that matches it. Do NOT add adjacent/complementary categories in phase categories — those can be suggested in phase notes only.
"""

        try:
            response = _client.chat.completions.create(
                model=settings.llm_model,
                temperature=0.2,  # Low temp for structured extraction
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=1200,
                timeout=25.0,
            )
            content = response.choices[0].message.content.strip()
            result = json.loads(content)

            # Resolve and validate categories
            for phase in result.get("purchase_phases", []):
                phase["categories"] = _resolve_categories(phase.get("categories", []))
            result["category_mapping"] = _resolve_categories(result.get("category_mapping", []))

            # Ensure event_key is valid
            if result.get("event_key") not in VALID_EVENT_KEYS:
                result["event_key"] = "generic"

            return result

        except Exception as e:
            error_str = str(e).lower()
            print(f"[LLM Event Detection Error]: {e}")
            if "429" in error_str or "rate limit" in error_str or "rate_limit_exceeded" in error_str:
                return {"rate_limit_exceeded": True, "error_message": str(e)}
            return None

    def detect_event(self, user_input: str) -> Dict[str, Any]:
        """
        FALLBACK keyword-based detection. Used when LLM is unavailable.
        Scans all templates and their keywords, returns the best match.
        Falls back to 'festival_prep' if nothing matches.
        """
        templates = _load_templates()
        text = user_input.lower()

        best_key = None
        best_score = 0
        best_template = None
        best_matched = []

        for event_key, template in templates.items():
            keywords = template.get("keywords", [])
            matched = [kw for kw in keywords if kw.lower() in text]
            score = len(matched)
            if score > best_score:
                best_score = score
                best_key = event_key
                best_template = template
                best_matched = matched

        if not best_key or best_score == 0:
            best_key = "generic"
            best_template = _get_default_template("generic")
            best_matched = []

        confidence = min(1.0, best_score / max(3, 1))

        return {
            "event_key": best_key,
            "label": best_template.get("label", "Shopping Assistance"),
            "timeline_days": best_template.get("timeline_days", 30),
            "purchase_phases": best_template.get("purchase_phases", []),
            "emotion_level": best_template.get("emotion_level", "moderate"),
            "family_significance": best_template.get("family_significance", "moderate"),
            "suggested_budget_range": best_template.get("suggested_budget_range", {"min": 1000, "max": 50000}),
            "confidence": confidence,
            "matched_keywords": best_matched,
        }

    def detect_location(self, user_input: str) -> Tuple[Optional[str], Optional[Dict], Optional[str], Optional[Dict]]:
        """
        FALLBACK location detection via string matching.
        Used when LLM detection fails. Scans bharat_context.json.
        
        Returns: (institution_key, institution_data, state_key, state_data)
        """
        context = _load_context()
        text = user_input.lower()

        institution_key = None
        institution_data = None

        for key, inst in context.get("institutions", {}).items():
            for keyword in inst.get("keywords", []):
                if keyword.lower() in text:
                    institution_key = key
                    institution_data = inst
                    break
            if institution_key:
                break

        state_key = None
        state_data = None

        if institution_data:
            inst_state = institution_data.get("state")
            if inst_state and inst_state in context.get("states", {}):
                state_key = inst_state
                state_data = context["states"][inst_state]

        if not state_key:
            for key, state in context.get("states", {}).items():
                display = state.get("display_name", "").lower()
                if display in text or key.replace("_", " ") in text:
                    state_key = key
                    state_data = state
                    break

        # Third tier: check CITY_TO_STATE map (200+ cities, pilgrimage sites, landmarks)
        if not state_key:
            for city, mapped_state in CITY_TO_STATE.items():
                if city in text:
                    state_key = mapped_state
                    state_data = context.get("states", {}).get(mapped_state)
                    break

        return institution_key, institution_data, state_key, state_data

    def get_state_data_for_key(self, state_key: Optional[str]) -> Optional[Dict]:
        """Retrieves state data from bharat_context.json for a given state key."""
        if not state_key:
            return None
        context = _load_context()
        return context.get("states", {}).get(state_key)

    def enrich_with_context(
        self,
        purchase_phases: list,
        institution_data: Optional[Dict],
        state_data: Optional[Dict],
        cultural_context: Optional[str] = None,
        climate_note: Optional[str] = None,
    ) -> list:
        """
        Applies institution constraints and climate/cultural notes to purchase phases.
        Now accepts LLM-generated cultural_context and climate_note for richer enrichment.
        """
        enriched = []
        for phase in purchase_phases:
            note = phase.get("note", "")
            additions = []
            categories_str = " ".join(phase.get("categories", [])).lower()

            if institution_data:
                wattage = institution_data.get("appliance_wattage_limit")
                if wattage and "kitchen" in categories_str:
                    additions.append(
                        f"For kitchen items, note: {institution_data.get('display_name', 'Your institution')} "
                        f"limits appliances to {wattage}W — check before buying electrical items."
                    )

            if state_data:
                climate = state_data.get("climate", "")
                if "humid" in climate and "bedding" in categories_str:
                    additions.append("For bedding, choose breathable fabrics — the local climate is humid.")
                if ("desert" in climate or "arid" in climate) and ("personal_care" in categories_str or "wear" in categories_str):
                    additions.append("For personal care and clothing, dust-resistant and cooling items are priority in this climate.")
                if ("mountain" in climate or "cold" in climate or "alpine" in climate) and ("wear" in categories_str or "bedding" in categories_str):
                    additions.append("For bedding and clothing, warm, layered and thermal items are essential for this climate.")

            enriched_note = note + (" " + " ".join(additions) if additions else "")
            enriched.append({**phase, "note": enriched_note.strip()})

        return enriched

    def generate_llm_roadmap(
        self,
        event_data: Dict,
        location_summary: str,
        user_input: str,
    ) -> Optional[Dict]:
        """
        LEGACY FALLBACK: Called only when detect_event_with_llm() fails.
        Provides a roadmap for the fallback keyword-detected event.
        """
        prompt = f"""You are a caring Indian shopping assistant helping someone with a major life event.

Life event detected: {event_data.get('label', 'Shopping')}
Location context: {location_summary}
What they said: "{user_input}"
Days until the event: {event_data.get('timeline_days', 30)}

Task:
1. Write a 2-sentence warm emotional message acknowledging their specific situation. Use warm Indian English.
2. Provide a 3-phase purchase timeline.
3. Extract any specific items they asked for into exact_items_requested.

Respond ONLY with valid JSON:
{{
  "emotional_message": "Your 2 sentence message here.",
  "exact_items_requested": ["item1", "item2"],
  "purchase_phases": [
    {{
      "phase_name": "Phase 1: Immediate Needs (Days 1-3)",
      "days_from_now": 0,
      "categories": ["category_name"],
      "priority": "must_have",
      "note": "Why they need this now."
    }},
    {{
      "phase_name": "Phase 2: Mid-Preparation (Days 3-7)",
      "days_from_now": 3,
      "categories": ["category_name"],
      "priority": "should_have",
      "note": "..."
    }},
    {{
      "phase_name": "Phase 3: Final Touches (Week 2)",
      "days_from_now": 7,
      "categories": ["category_name"],
      "priority": "nice_to_have",
      "note": "..."
    }}
  ]
}}
Valid categories: [bedding, study_accessories, personal_care, bags_luggage, kitchen_essentials, formal_wear, festival_decor, baby_products]
"""

        try:
            response = _client.chat.completions.create(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=800,
                timeout=20.0,
            )
            content = response.choices[0].message.content.strip()
            return json.loads(content)
        except Exception as e:
            print(f"LLM Roadmap Fallback Error: {e}")
            return None

    def filter_products_with_llm(self, user_input: str, intent: str, products: List[Dict[str, Any]]) -> List[str]:
        """
        Takes the candidate products from the hardcoded matcher and filters out
        any products that logically make zero sense for the user's intent.
        For example, drops a "4 socket junction box" for a "bought new mobile" event.
        Returns a list of approved product_ids.
        """
        if not products:
            return []

        # Minify products to save tokens (price included for budget filtering)
        minified = [
            {
                "id": p.get("id"),
                "name": p.get("name"),
                "category": p.get("category"),
                "subcategory": p.get("subcategory"),
                "price": p.get("price"),
            }
            for p in products
        ]

        # Detect if the user is asking for a very specific product type
        specific_keywords = [
            'phone', 'mobile', 'smartphone', 'laptop', 'earphone', 'earphones',
            'headphone', 'headphones', 'charger', 'tablet', 'ipad', 'watch',
            'camera', 'tv', 'television', 'refrigerator', 'fridge', 'ac',
            'air conditioner', 'washing machine', 'microwave', 'mixer', 'blender',
            'speaker', 'powerbank', 'power bank', 'keyboard', 'mouse',
        ]
        user_lower = user_input.lower()
        is_specific_ask = any(kw in user_lower for kw in specific_keywords)
        
        strictness_note = ""
        if is_specific_ask:
            strictness_note = """
CRITICAL: The user is asking for a SPECIFIC product type. Be VERY STRICT.
- ONLY approve products that ARE that specific item.
- If the user asked for a phone, approve ONLY phones/smartphones. Reject chargers, cables, covers, cases, earphones unless they literally asked for those too.
- If the user asked for earphones, approve ONLY earphones/headphones. Reject chargers, phones, cables.
- In short: match EXACTLY what the user asked for. Reject everything else."""

        prompt = f"""You are a strict logical filter for a shopping assistant.
The user said: "{user_input}"
Their detected intent is: "{intent}"
{strictness_note}

Below is a list of candidate products retrieved from our database. Some products might be completely irrelevant (e.g. a junction box for someone who bought a mobile phone) because they share a broad category like 'electronics'.

Your task is to review each product and filter out the ones that make ZERO logical sense for the user's intent. Keep the ones that are directly relevant or could be reasonably useful accessories (unless the user asked for something very specific — in that case be strict).

ALSO: If the user mentioned a budget (e.g. "under 100", "under ₹500"), reject ALL products whose price exceeds that budget — even if they are the right category.

CRITICAL — OBVIOUS MISMATCH EXAMPLES (ALWAYS reject these patterns):
- Toilet cleaners / floor cleaners / bathroom cleaners (Harpic, Lizol, Domex, Colin) appearing for: skincare, makeup, beauty, sun protection, personal care queries → REJECT
- School textbooks / comprehension books / academic books appearing for: makeup, beauty, fashion, lifestyle queries → REJECT  
- Men's shirt stays / office accessories appearing for: home decor, beauty, kitchen queries → REJECT
- Baby products appearing for: adult personal care, men's grooming queries → REJECT
- Kitchen cleaning tablets / descaling powder appearing for: beauty, grooming, clothing queries → REJECT
- Any product whose name contains 'cleaning', 'cleaner', 'disinfectant', 'toilet', 'floor mop', 'drain', 'pest control' for personal care / beauty / fashion queries → REJECT
- Any product clearly for a different gender or age group than implied by the query → REJECT
- Studio equipment (mic, speaker, headphone) for home/kitchen setup queries → REJECT
- Pillows / bedsheets / kitchen items for music studio / recording studio queries → REJECT

Products:
{json.dumps(minified, indent=2)}

Return ONLY valid JSON in this exact structure:
{{
  "approved_product_ids": ["id1", "id2", ...]
}}
"""
        try:
            # Using a smaller, faster model for this simple filtering task to save tokens and avoid rate limits
            response = _client.chat.completions.create(
                model="llama-3.1-8b-instant",
                temperature=0.0,  # Zero temperature for strict logic
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=2000,
                timeout=20.0,
            )
            content = response.choices[0].message.content.strip()
            result = json.loads(content)
            return result.get("approved_product_ids", [])
        except Exception as e:
            print(f"LLM Product Filter Error: {e}")
            # If the LLM filter fails (timeout, API error, rate limit), fail OPEN:
            # return all candidate product IDs so the user still sees products.
            # Failing closed (returning []) would block ALL products and show nothing,
            # which is far worse UX than showing slightly unfiltered results.
            return [p.get("id") for p in products if p.get("id")]

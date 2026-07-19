import sqlite3

# Product IDs from database search
product_ids = [
    'WED001',
    'JWLRY004', 
    'JWLRY002',
    'BAG001',
    'FESTIVE003',
    'FESTIVE002',
    'TREK009',
    'IMG_PROD_CANVAS_TOTE_CREAM_ZIPPER',
    'TREK014'
]

# Available local images from frontend/public/images/
available_images = [
    'BAB003.jpg', 'BAB004.jpg', 'BAB005.jpg', 'BABY003.jpg', 'BABY006.jpg', 'BABY007.jpg', 'BABY008.jpg',
    'BAG00.jpg', 'BAG001.jpg', 'BAG002.jpg', 'BAG003.jpg', 'BAG004.jpg', 'BAG006.jpg',
    'BED002.jpg', 'BED003.jpg', 'BED004.jpg', 'BED005.jpg', 'BED008.jpg',
    'EDGE002.jpg', 'EDGE005.jpg',
    'ELEC001.jpg', 'ELEC002.jpg', 'ELEC003.jpg', 'ELEC004.jpg', 'ELEC005.jpg', 'ELEC006.jpg',
    'FES003.jpg', 'FES004.jpg', 'FES005.jpg',
    'FESTIVE006.jpg', 'FESTIVE007.jpg',
    'FORMAL001.jpg', 'FORMAL002.jpg', 'FORMAL003.jpg', 'FORMAL004.jpg', 'FORMAL005.jpg', 'FORMAL007.jpg',
    'FRM001.jpg', 'FRM002.jpg', 'FRM003.jpg', 'FRM004.jpg',
    'GOEXAM001.jpg', 'GOEXAM002.jpg', 'GOEXAM003.jpg', 'GOEXAM004.jpg', 'GOEXAM005.jpg',
    'HOMEDECOR002.jpg', 'HOMEDECOR003.jpg', 'HOMEDECOR004.jpg',
    'HOME_IMP001.jpg', 'HOME_IMP002.jpg', 'HOME_IMP003.jpg', 'HOME_IMP004.jpg', 'HOME_IMP005.jpg',
    'HOSTEL001.jpg', 'HOSTEL002.jpg',
    'IMG_PROD_BABY_CARRIER_GREY_ERGONOMIC.jpg', 'IMG_PROD_BLUE_MICROFIBER_COMFORTER.jpg',
    'IMG_PROD_CLAY_DIYAS_100_SET_TERRACOTTA.jpg', 'IMG_PROD_LAUNDRY_BAG_SET_BLUE_WHITE.jpg',
    'IMG_PROD_MENS_FORMAL_SHIRT_WHITE_PACK3.jpg', 'IMG_PROD_NOTEBOOK_SET_BLUE_COVER.jpg',
    'IMG_PROD_PU_LEATHER_PORTFOLIO_BLACK.jpg', 'IMG_PROD_SHAGUN_ENVELOPES_RED_GOLD.jpg',
    'JWLRY001.jpg', 'JWLRY004.jpg',
    'KIT001.jpg', 'KIT002.jpg', 'KIT003.jpg', 'KIT005.jpg',
    'KITCHEN004.jpg', 'KITCHEN007.jpg', 'KITCHEN009.jpg',
    'PERSONAL002.jpg', 'PERSONAL004.jpg',
    'SECURITY002.jpg', 'SECURITY003.jpg', 'SECURITY004.jpg', 'SECURITY005.jpg',
    'SHOP001.jpg', 'SHOP002.jpg', 'SHOP003.jpg', 'SHOP004.jpg', 'SHOP006.jpg', 'SHOP007.jpg',
    'STATIONERY005.jpg',
    'STU001.jpg', 'STU002.jpg', 'STU003.jpg', 'STU004.jpg',
    'STUDY003.jpg', 'STUDY004.jpg', 'STUDY005.jpg', 'STUDY007.jpg',
    'TREK002.jpg', 'TREK003.jpg', 'TREK004.jpg', 'TREK005.jpg', 'TREK006.jpg', 'TREK007.jpg',
    'TREK008.jpg', 'TREK009.jpg', 'TREK010.jpg', 'TREK011.jpg', 'TREK012.jpg', 'TREK013.jpg',
    'TREK014.jpg', 'TREK015.jpg', 'TREK017.jpg', 'TREK018.jpg',
    'WED001.jpg', 'WED002.jpg',
    'WEDDING001.jpg', 'WEDDING002.jpg', 'WEDDING004.jpg', 'WEDDING005.jpg',
    'aluminium_laptop_stand_silver.jpg', 'blue_microfiber_comforter.jpg', 'brass_idols_lakshmi_ganesha.jpg',
    'brass_padlock_set2.jpg', 'brass_puja_thali_7piece.jpg', 'clay_diyas_100_set_terracotta.jpg',
    'cotton_white_bedsheet_double.jpg', 'dove_bodywash_500ml_loofah.jpg', 'dry_fruits_gift_box_festive.jpg',
    'electric_kettle_steel_1500w.jpg', 'extension_board_white_4socket.jpg', 'foam_mattress_single_blue.jpg',
    'granite_kadhai_28cm_black.jpg', 'himalaya_mens_grooming_kit.jpg', 'led_desk_lamp_white.jpg',
    'led_string_lights_warm_white_10m.jpg', 'memory_foam_cushion_grey.jpg', 'notebook_set_blue_cover.jpg',
    'placeholder.jpg', 'rangoli_stencil_kit_colourful.jpg', 'silk_toran_mango_green_gold.jpg',
    'stainless_pressure_cooker_5l.jpg', 'steel_tiffin_3tier_silver.jpg', 'water_purifier_white_wall_mount.jpg',
    'white_cotton_pillow_pair.jpg', 'wooden_study_table_brown.jpg'
]

available_set = set(available_images)

print('Matching products with available local images:\n')

for pid in product_ids:
    # Check for exact match
    if f'{pid}.jpg' in available_set:
        print(f'✓ {pid}: Exact match available -> /images/{pid}.jpg')
    else:
        # Check for close matches
        close_matches = [img for img in available_images if pid.lower() in img.lower() or img.lower().replace('.jpg', '') in pid.lower().replace('_', '')]
        if close_matches:
            print(f'~ {pid}: Close matches: {close_matches}')
        else:
            print(f'✗ {pid}: No local image found')

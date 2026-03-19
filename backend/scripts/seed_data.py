"""
Seed the local-delivery database with realistic sample data.

Generates:
  - 50 distribution centres across 5 US metro areas
  - 100 items across 5 categories
  - Inventory entries for ~30% of (DC, item) pairs

Run from the backend directory:
    python scripts/seed_data.py

Or via:
    make seed
"""
import asyncio
import os
import random
import sys
from pathlib import Path

# Allow imports from the backend root when run standalone
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://delivery_user:delivery_pass@localhost:5432/local_delivery",
)
# asyncpg needs postgresql:// not postgresql+asyncpg://
_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://").replace(
    "postgresql+psycopg2://", "postgresql://"
)

random.seed(42)

# ── Metro area definitions ────────────────────────────────────────────────────
METRO_AREAS = [
    {
        "name": "Los Angeles",
        "state": "CA",
        "zip_prefix": "900",
        "center_lat": 34.0522,
        "center_lng": -118.2437,
        "spread": 0.15,
        "cities": ["Los Angeles", "Santa Monica", "Culver City", "Inglewood", "Compton"],
    },
    {
        "name": "New York",
        "state": "NY",
        "zip_prefix": "100",
        "center_lat": 40.7128,
        "center_lng": -74.0060,
        "spread": 0.12,
        "cities": ["New York", "Brooklyn", "Queens", "Bronx", "Jersey City"],
    },
    {
        "name": "Chicago",
        "state": "IL",
        "zip_prefix": "606",
        "center_lat": 41.8781,
        "center_lng": -87.6298,
        "spread": 0.12,
        "cities": ["Chicago", "Evanston", "Oak Park", "Cicero", "Berwyn"],
    },
    {
        "name": "Houston",
        "state": "TX",
        "zip_prefix": "770",
        "center_lat": 29.7604,
        "center_lng": -95.3698,
        "spread": 0.15,
        "cities": ["Houston", "Pearland", "Sugar Land", "Pasadena", "Baytown"],
    },
    {
        "name": "Miami",
        "state": "FL",
        "zip_prefix": "331",
        "center_lat": 25.7617,
        "center_lng": -80.1918,
        "spread": 0.1,
        "cities": ["Miami", "Hialeah", "Coral Gables", "Doral", "Homestead"],
    },
]

# ── Item catalogue ────────────────────────────────────────────────────────────
ITEMS = [
    # snacks (20)
    ("SNK001", "Classic Potato Chips", "snacks", 299, 150),
    ("SNK002", "Pretzels Sea Salt", "snacks", 249, 120),
    ("SNK003", "Tortilla Chips Nacho", "snacks", 349, 200),
    ("SNK004", "Popcorn Butter", "snacks", 199, 80),
    ("SNK005", "Trail Mix Deluxe", "snacks", 499, 250),
    ("SNK006", "Granola Bar Oats & Honey", "snacks", 179, 45),
    ("SNK007", "Rice Cakes Plain", "snacks", 329, 130),
    ("SNK008", "Cheese Crackers", "snacks", 279, 160),
    ("SNK009", "Peanut Butter Cups", "snacks", 229, 90),
    ("SNK010", "Gummy Bears", "snacks", 199, 100),
    ("SNK011", "Dark Chocolate Bar", "snacks", 349, 80),
    ("SNK012", "Beef Jerky Original", "snacks", 699, 85),
    ("SNK013", "Mixed Nuts Salted", "snacks", 599, 300),
    ("SNK014", "Fruit Snacks Assorted", "snacks", 249, 60),
    ("SNK015", "Microwave Popcorn 3-Pack", "snacks", 449, 360),
    ("SNK016", "Sunflower Seeds Roasted", "snacks", 299, 180),
    ("SNK017", "Pita Chips Hummus", "snacks", 379, 170),
    ("SNK018", "Caramel Popcorn", "snacks", 299, 120),
    ("SNK019", "Veggie Straws", "snacks", 349, 130),
    ("SNK020", "Almonds Raw", "snacks", 799, 450),
    # beverages (20)
    ("BEV001", "Sparkling Water 12-Pack", "beverages", 899, 5400),
    ("BEV002", "Orange Juice 52 oz", "beverages", 499, 1500),
    ("BEV003", "Whole Milk 1 Gallon", "beverages", 549, 3785),
    ("BEV004", "Cold Brew Coffee 32 oz", "beverages", 799, 950),
    ("BEV005", "Energy Drink 4-Pack", "beverages", 999, 1040),
    ("BEV006", "Coconut Water 1L", "beverages", 349, 1000),
    ("BEV007", "Green Tea 16 oz", "beverages", 249, 480),
    ("BEV008", "Lemonade 59 oz", "beverages", 399, 1750),
    ("BEV009", "Apple Cider 1 Gallon", "beverages", 699, 3800),
    ("BEV010", "Almond Milk 64 oz", "beverages", 499, 1900),
    ("BEV011", "Sports Drink 20 oz", "beverages", 179, 590),
    ("BEV012", "Kombucha Original 16 oz", "beverages", 449, 480),
    ("BEV013", "Cranberry Juice 32 oz", "beverages", 399, 960),
    ("BEV014", "Iced Coffee 13.7 oz", "beverages", 299, 412),
    ("BEV015", "Sparkling Juice Grape", "beverages", 349, 750),
    ("BEV016", "Protein Shake Chocolate", "beverages", 549, 414),
    ("BEV017", "Tomato Juice 46 oz", "beverages", 349, 1380),
    ("BEV018", "Oat Milk 32 oz", "beverages", 499, 960),
    ("BEV019", "Ginger Beer 4-Pack", "beverages", 799, 1440),
    ("BEV020", "Mineral Water Still 6-Pack", "beverages", 699, 3000),
    # household (20)
    ("HH001", "Paper Towels 6-Roll", "household", 899, 1200),
    ("HH002", "Dish Soap 24 oz", "household", 399, 700),
    ("HH003", "Laundry Detergent 50 oz", "household", 1199, 1500),
    ("HH004", "Toilet Paper 12-Roll", "household", 1099, 2400),
    ("HH005", "Trash Bags 13 Gallon 30ct", "household", 799, 800),
    ("HH006", "All-Purpose Cleaner 32 oz", "household", 499, 960),
    ("HH007", "Sponges 6-Pack", "household", 349, 200),
    ("HH008", "Ziplock Bags Gallon 30ct", "household", 599, 400),
    ("HH009", "Aluminum Foil 75 sq ft", "household", 499, 350),
    ("HH010", "Plastic Wrap 200 sq ft", "household", 449, 280),
    ("HH011", "Dryer Sheets 120ct", "household", 699, 450),
    ("HH012", "Fabric Softener 64 oz", "household", 799, 1900),
    ("HH013", "Glass Cleaner 32 oz", "household", 399, 900),
    ("HH014", "Bleach 1 Gallon", "household", 499, 3800),
    ("HH015", "Dishwasher Pods 20ct", "household", 999, 600),
    ("HH016", "Hand Soap Refill 50 oz", "household", 699, 1500),
    ("HH017", "Rubber Gloves M", "household", 299, 150),
    ("HH018", "Mop Replacement Head", "household", 899, 400),
    ("HH019", "Air Freshener Spray", "household", 549, 350),
    ("HH020", "Candles Scented 2-Pack", "household", 1299, 400),
    # personal_care (20)
    ("PC001", "Shampoo 12 oz", "personal_care", 799, 360),
    ("PC002", "Conditioner 12 oz", "personal_care", 799, 360),
    ("PC003", "Body Wash 16 oz", "personal_care", 699, 480),
    ("PC004", "Toothpaste Mint 4 oz", "personal_care", 399, 120),
    ("PC005", "Deodorant Stick", "personal_care", 599, 90),
    ("PC006", "Razors 4-Pack", "personal_care", 899, 120),
    ("PC007", "Cotton Swabs 500ct", "personal_care", 499, 100),
    ("PC008", "Face Wash Gentle 6 oz", "personal_care", 999, 180),
    ("PC009", "Moisturizer SPF 30 2 oz", "personal_care", 1299, 60),
    ("PC010", "Lip Balm 3-Pack", "personal_care", 499, 45),
    ("PC011", "Nail Clippers Set", "personal_care", 699, 80),
    ("PC012", "Floss Picks 75ct", "personal_care", 349, 70),
    ("PC013", "Hair Ties 30ct", "personal_care", 299, 60),
    ("PC014", "Feminine Hygiene Pads 36ct", "personal_care", 899, 360),
    ("PC015", "Shaving Cream 7 oz", "personal_care", 499, 200),
    ("PC016", "Sunscreen SPF 50 3 oz", "personal_care", 999, 90),
    ("PC017", "Eye Drops Redness Relief", "personal_care", 799, 30),
    ("PC018", "Bandages Assorted 30ct", "personal_care", 599, 100),
    ("PC019", "Hand Sanitizer 8 oz", "personal_care", 499, 240),
    ("PC020", "Vitamins C 500mg 60ct", "personal_care", 1199, 120),
    # frozen (20)
    ("FRZ001", "Frozen Pizza Pepperoni", "frozen", 799, 750),
    ("FRZ002", "Frozen Burritos 8ct", "frozen", 599, 1000),
    ("FRZ003", "Ice Cream Vanilla 1.5 qt", "frozen", 499, 900),
    ("FRZ004", "Frozen Fries 32 oz", "frozen", 399, 900),
    ("FRZ005", "Chicken Nuggets 32 oz", "frozen", 899, 900),
    ("FRZ006", "Frozen Waffles 10ct", "frozen", 449, 400),
    ("FRZ007", "Mac & Cheese Frozen 8oz", "frozen", 299, 230),
    ("FRZ008", "Frozen Edamame 16 oz", "frozen", 349, 450),
    ("FRZ009", "Frozen Spinach 10 oz", "frozen", 249, 280),
    ("FRZ010", "Fish Sticks 18ct", "frozen", 599, 650),
    ("FRZ011", "Frozen Breakfast Sandwich 4ct", "frozen", 699, 680),
    ("FRZ012", "Frozen Meatballs 32 oz", "frozen", 799, 900),
    ("FRZ013", "Sorbet Mango 14 oz", "frozen", 449, 400),
    ("FRZ014", "Frozen Corn 12 oz", "frozen", 199, 340),
    ("FRZ015", "Frozen Peas 16 oz", "frozen", 199, 450),
    ("FRZ016", "Frozen Stir Fry Vegetables 14 oz", "frozen", 299, 400),
    ("FRZ017", "Frozen Shrimp 2 lb", "frozen", 1299, 900),
    ("FRZ018", "Gelato Chocolate 16 oz", "frozen", 599, 450),
    ("FRZ019", "Frozen Pancakes 8ct", "frozen", 399, 340),
    ("FRZ020", "Tater Tots 32 oz", "frozen", 399, 900),
]


async def main() -> None:
    print(f"Connecting to {_url.split('@')[-1]} ...")
    conn = await asyncpg.connect(_url)

    try:
        # ── Insert DCs ────────────────────────────────────────────────────────
        print("Seeding distribution centres...")
        dc_ids = []
        dc_index = 0
        for metro in METRO_AREAS:
            for i in range(10):  # 10 DCs per metro = 50 total
                dc_index += 1
                lat = metro["center_lat"] + random.uniform(-metro["spread"], metro["spread"])
                lng = metro["center_lng"] + random.uniform(-metro["spread"], metro["spread"])
                zip_suffix = str(random.randint(10, 99))
                zipcode = metro["zip_prefix"] + zip_suffix
                city = random.choice(metro["cities"])
                name = f"{city} DC #{i + 1}"

                row = await conn.fetchrow(
                    """
                    INSERT INTO distribution_centers (name, lat, lng, zipcode, region_id, address, city, state, is_active)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                    """,
                    name, round(lat, 6), round(lng, 6),
                    zipcode, zipcode[:3],
                    f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Elm', 'Maple', 'Industrial'])} St",
                    city, metro["state"], True,
                )
                if row:
                    dc_ids.append(row["id"])

        print(f"  Inserted {len(dc_ids)} distribution centres")

        # ── Insert items ──────────────────────────────────────────────────────
        print("Seeding items...")
        item_ids = []
        for sku, name, category, price_cents, weight_grams in ITEMS:
            row = await conn.fetchrow(
                """
                INSERT INTO items (sku, name, category, unit_price_cents, weight_grams, is_active)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (sku) DO NOTHING
                RETURNING id
                """,
                sku, name, category, price_cents, weight_grams, True,
            )
            if row:
                item_ids.append(row["id"])

        print(f"  Inserted {len(item_ids)} items")

        # ── Insert inventory (~30% coverage) ──────────────────────────────────
        print("Seeding inventory...")
        inventory_count = 0
        records = []
        for dc_id in dc_ids:
            for item_id in item_ids:
                if random.random() < 0.30:  # 30% fill rate
                    quantity = random.randint(0, 500)
                    records.append((dc_id, item_id, quantity))

        # Batch insert to avoid N*M individual queries
        for i in range(0, len(records), 500):
            batch = records[i : i + 500]
            await conn.executemany(
                """
                INSERT INTO inventory (dc_id, item_id, quantity, reorder_threshold)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT ON CONSTRAINT uq_inventory_dc_item DO NOTHING
                """,
                [(dc_id, item_id, qty, 10) for dc_id, item_id, qty in batch],
            )
            inventory_count += len(batch)

        print(f"  Inserted {inventory_count} inventory records")
        print("Seed complete.")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

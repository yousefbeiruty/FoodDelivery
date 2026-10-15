"""Seed FreshBite with repeatable sample restaurant and menu data.

Restaurant brands are recognizable examples; all menu descriptions and prices here are
illustrative demo data, not official menus or current brand pricing.
"""
import asyncio
from pathlib import Path

from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.models import MenuItem, Restaurant

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"

# The artwork is original, locally hosted SVG illustration. It is generic menu imagery,
# not product photography or official restaurant branding.
ART = {
    "burgers": ("#d97706", "#fff7ed", "BURGER", "🍔"),
    "pizza": ("#dc5a36", "#fff1e8", "PIZZA", "🍕"),
    "chicken": ("#b45309", "#fff7ed", "CHICKEN", "🍗"),
    "sandwiches": ("#4d7c0f", "#f7fee7", "SANDWICH", "🥪"),
    "coffee": ("#78350f", "#fef3c7", "COFFEE", "☕"),
    "asian": ("#0f766e", "#ecfeff", "ASIAN", "🍜"),
    "mexican": ("#15803d", "#f0fdf4", "MEXICAN", "🌮"),
    "desserts": ("#be185d", "#fdf2f8", "DESSERT", "🍰"),
    "mediterranean": ("#2563eb", "#eff6ff", "MEDITERRANEAN", "🥙"),
}

BRANDS = [
    ("McDonald's", "burgers"), ("Burger King", "burgers"), ("Wendy's", "burgers"),
    ("Five Guys", "burgers"), ("Shake Shack", "burgers"), ("Fuddruckers", "burgers"),
    ("Hardee's", "burgers"), ("Whataburger", "burgers"), ("In-N-Out Burger", "burgers"),
    ("Jack in the Box", "burgers"),
    ("KFC", "chicken"), ("Popeyes", "chicken"), ("Chick-fil-A", "chicken"),
    ("Nando's", "chicken"), ("ALBAIK", "chicken"), ("Jollibee", "chicken"),
    ("Raising Cane's", "chicken"), ("Church's Texas Chicken", "chicken"),
    ("Zaxby's", "chicken"), ("Wingstop", "chicken"),
    ("Subway", "sandwiches"), ("Jimmy John's", "sandwiches"),
    ("Jersey Mike's Subs", "sandwiches"), ("Panera Bread", "sandwiches"),
    ("Pret A Manger", "sandwiches"), ("Firehouse Subs", "sandwiches"),
    ("Zaatar w Zeit", "mediterranean"), ("Manoushe Street", "mediterranean"),
    ("Operation: Falafel", "mediterranean"), ("Shawarma House", "mediterranean"),
    ("Domino's", "pizza"), ("Pizza Hut", "pizza"), ("Papa Johns", "pizza"),
    ("Little Caesars", "pizza"), ("Papa Murphy's", "pizza"), ("California Pizza Kitchen", "pizza"),
    ("Starbucks", "coffee"), ("Dunkin'", "coffee"), ("Costa Coffee", "coffee"),
    ("Tim Hortons", "coffee"), ("Peet's Coffee", "coffee"), ("Caffè Nero", "coffee"),
    ("Chipotle Mexican Grill", "mexican"), ("Taco Bell", "mexican"),
    ("P.F. Chang's", "asian"), ("Panda Express", "asian"), ("Wagamama", "asian"),
    ("The Cheesecake Factory", "desserts"), ("Baskin-Robbins", "desserts"),
    ("Cinnabon", "desserts"),
]

MENUS = {
    "burgers": [
        ("Classic House Burger", "Grilled beef, lettuce, tomato, pickles, and house sauce.", 5.75, 610),
        ("Crispy Plant Burger", "Plant-based patty with greens and tangy vegan sauce.", 6.25, 520),
        ("Smoky BBQ Burger", "Beef patty, smoked barbecue sauce, and caramelized onion.", 6.50, 690),
        ("Golden Fries", "Crispy seasoned potato fries.", 2.25, 330),
    ],
    "chicken": [
        ("Crispy Chicken Box", "Crunchy seasoned chicken served with a fresh side.", 6.25, 640),
        ("Grilled Chicken Wrap", "Grilled chicken, crisp lettuce, and creamy herb dressing.", 5.75, 470),
        ("Spicy Chicken Sandwich", "Crispy chicken with slaw and a mild spicy sauce.", 5.50, 560),
        ("Seasoned Potato Wedges", "Oven-golden wedges with herbs and spices.", 2.50, 310),
    ],
    "sandwiches": [
        ("Garden Veggie Sub", "Seasonal vegetables, greens, and lemon herb dressing.", 5.25, 390),
        ("Roasted Chicken Club", "Roasted chicken, tomato, lettuce, and wholegrain bread.", 6.25, 510),
        ("Avocado Crunch Sandwich", "Avocado, cucumber, greens, and toasted seeds.", 5.75, 430),
        ("Tomato Basil Soup", "Slow-simmered tomato soup with fragrant basil.", 3.25, 210),
    ],
    "pizza": [
        ("Margherita Garden Pizza", "Tomato, mozzarella, basil, and olive oil.", 7.50, 720),
        ("Roasted Veggie Pizza", "Roasted peppers, mushrooms, olives, and mozzarella.", 8.25, 760),
        ("Classic Pepperoni Pizza", "Tomato sauce, mozzarella, and savory pepperoni.", 8.50, 840),
        ("Garlic Herb Bread", "Baked bread with garlic, herbs, and olive oil.", 3.25, 290),
    ],
    "coffee": [
        ("Oat Milk Latte", "Espresso with steamed oat milk.", 3.50, 180),
        ("Cold Brew Coffee", "Slow-steeped coffee served chilled.", 2.75, 10),
        ("Iced Matcha", "Ceremonial-style green tea with your choice of milk.", 3.75, 160),
        ("Banana Oat Muffin", "Soft-baked muffin with banana and rolled oats.", 2.50, 320),
    ],
    "asian": [
        ("Ginger Tofu Rice Bowl", "Crispy tofu, brown rice, vegetables, and ginger sauce.", 7.25, 540),
        ("Sesame Chicken Bowl", "Chicken, steamed rice, broccoli, and sesame glaze.", 7.75, 620),
        ("Vegetable Noodle Soup", "Noodles and seasonal vegetables in a light broth.", 6.50, 440),
        ("Fresh Spring Rolls", "Rice paper rolls with vegetables and dipping sauce.", 4.25, 250),
    ],
    "mexican": [
        ("Grilled Veggie Tacos", "Grilled vegetables, cabbage, salsa, and lime.", 5.75, 420),
        ("Black Bean Burrito Bowl", "Black beans, rice, corn salsa, and avocado.", 7.25, 610),
        ("Citrus Chicken Burrito", "Citrus-marinated chicken, rice, beans, and pico de gallo.", 7.75, 680),
        ("Guacamole & Chips", "Fresh avocado dip with crisp corn tortilla chips.", 3.75, 360),
    ],
    "mediterranean": [
        ("Falafel Garden Plate", "Herb falafel, greens, hummus, and warm flatbread.", 6.75, 560),
        ("Chicken Shawarma Wrap", "Spiced chicken, pickles, greens, and tahini sauce.", 6.50, 590),
        ("Roasted Cauliflower Bowl", "Roasted cauliflower, grains, herbs, and lemon tahini.", 6.25, 480),
        ("Classic Hummus & Pita", "Creamy chickpea hummus with warm pita bread.", 3.50, 330),
    ],
    "desserts": [
        ("New York Cheesecake Slice", "Creamy vanilla cheesecake with a crisp crumb base.", 4.75, 480),
        ("Chocolate Fudge Brownie", "Rich cocoa brownie with a soft center.", 3.25, 390),
        ("Strawberry Frozen Treat", "Chilled strawberry dessert made for sharing.", 3.50, 290),
        ("Cinnamon Roll", "Soft-baked roll with cinnamon and vanilla glaze.", 3.75, 420),
    ],
}


def write_artwork() -> None:
    for slug, (accent, pale, label, emoji) in ART.items():
        directory = STATIC / "menu"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{slug}.svg").write_text(
            f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 420" role="img" aria-label="FreshBite {label.lower()} illustration">
<rect width="640" height="420" rx="32" fill="{pale}"/><circle cx="500" cy="110" r="100" fill="{accent}" opacity=".12"/>
<circle cx="320" cy="200" r="112" fill="white"/><text x="320" y="244" text-anchor="middle" font-size="128">{emoji}</text>
<text x="320" y="365" text-anchor="middle" font-family="Arial,sans-serif" font-size="27" font-weight="700" letter-spacing="4" fill="{accent}">{label}</text>
</svg>''', encoding="utf-8")


async def seed() -> None:
    if len(BRANDS) != 50:
        raise RuntimeError(f"Expected 50 restaurants, got {len(BRANDS)}")
    write_artwork()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with SessionLocal() as db:
        created_restaurants = created_items = 0
        for brand, category in BRANDS:
            restaurant = await db.scalar(select(Restaurant).where(Restaurant.name == brand))
            if restaurant is None:
                restaurant = Restaurant(name=brand, rating=4.2 + (len(brand) % 8) / 10,
                    delivery_time="20-35 min", image_url=f"/static/menu/{category}.svg",
                    category_tags=[category.replace("-", " "), "popular"])
                db.add(restaurant)
                await db.flush()
                created_restaurants += 1
            for name, description, price, calories in MENUS[category]:
                existing = await db.scalar(select(MenuItem.id).where(
                    MenuItem.restaurant_id == restaurant.id, MenuItem.name == name))
                if existing is None:
                    db.add(MenuItem(restaurant_id=restaurant.id, name=name, description=description,
                        price=price, calories=calories, image_url=f"/static/menu/{category}.svg", category=category))
                    created_items += 1
        await db.commit()
    print(f"Seed complete: {len(BRANDS)} sample brands; added {created_restaurants} restaurants and {created_items} menu items.")
    print(f"Illustrations written to {STATIC / 'menu'}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())

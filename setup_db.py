"""Generate synthetic eCommerce data and compute ground-truth values for eval."""

import sqlite3
import random
import os
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REFERENCE_DATE = datetime(2025, 1, 15)
START_DATE = datetime(2024, 10, 1)
END_DATE = datetime(2025, 1, 14)  # inclusive
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "ecommerce.db")

random.seed(42)

# US states with weights (CA, TX, NY, FL more common)
STATES = [
    ("CA", 5), ("TX", 4), ("NY", 4), ("FL", 3),
    ("IL", 2), ("PA", 2), ("OH", 2), ("GA", 2),
    ("NC", 1), ("MI", 1), ("NJ", 1), ("VA", 1),
    ("WA", 1), ("AZ", 1), ("CO", 1),
]
STATE_NAMES = [s for s, _ in STATES]
STATE_WEIGHTS = [w for _, w in STATES]

# Products: (name, category, subcategory, price)
PRODUCTS = [
    # Electronics
    ("Wireless Earbuds", "Electronics", None, 49.99),
    ("USB-C Hub", "Electronics", None, 34.99),
    ("Mechanical Keyboard", "Electronics", None, 89.99),
    ("Webcam HD", "Electronics", None, 59.99),
    ("Portable Charger", "Electronics", None, 29.99),
    ("Smart Watch", "Electronics", None, 199.99),
    # Clothing
    ("Cotton T-Shirt", "Clothing", None, 19.99),
    ("Denim Jeans", "Clothing", None, 49.99),
    ("Running Shoes", "Clothing", None, 79.99),
    ("Winter Jacket", "Clothing", None, 129.99),
    ("Baseball Cap", "Clothing", None, 14.99),
    ("Wool Sweater", "Clothing", None, 59.99),
    # Home & Kitchen
    ("Coffee Maker", "Home & Kitchen", None, 69.99),
    ("Blender", "Home & Kitchen", None, 39.99),
    ("Cutting Board Set", "Home & Kitchen", None, 24.99),
    ("Cast Iron Skillet", "Home & Kitchen", None, 34.99),
    ("Kitchen Scale", "Home & Kitchen", None, 19.99),
    ("French Press", "Home & Kitchen", None, 29.99),
    # Books (with genre subcategories)
    ("The Last Journey", "Books", "Fiction", 14.99),
    ("Dark Alley", "Books", "Mystery", 12.99),
    ("Star Wanderer", "Books", "Sci-Fi", 15.99),
    ("Love in Paris", "Books", "Romance", 11.99),
    ("Life of Tesla", "Books", "Biography", 16.99),
    ("Atomic Habits", "Books", "Self-Help", 13.99),
    ("The Great Novel", "Books", "Fiction", 12.99),
    ("Ocean Mysteries", "Books", "Mystery", 14.99),
    # Sports & Outdoors
    ("Yoga Mat", "Sports & Outdoors", None, 29.99),
    ("Water Bottle", "Sports & Outdoors", None, 14.99),
    ("Resistance Bands", "Sports & Outdoors", None, 19.99),
    ("Camping Lantern", "Sports & Outdoors", None, 24.99),
    ("Jump Rope", "Sports & Outdoors", None, 9.99),
]

# Promo codes: (code, type, value)
PROMO_CODES = [
    ("SUMMER20", "percent", 20),
    ("WELCOME10", "percent", 10),
    ("HOLIDAY15", "percent", 15),
    ("FLASH25", "percent", 25),
    ("LOYALTY5", "flat", 5),
]


def create_tables(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            state TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT,
            price REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS purchases (
            purchase_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            promo_code TEXT,
            discount_amount REAL DEFAULT 0,
            purchase_date TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );

        CREATE TABLE IF NOT EXISTS customer_segments (
            segment_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            week_start TEXT NOT NULL,
            total_spend REAL NOT NULL,
            segment TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        );
    """)
    conn.commit()


def generate_customers(conn: sqlite3.Connection, n: int = 200):
    first_names = [
        "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael",
        "Linda", "David", "Elizabeth", "William", "Barbara", "Richard", "Susan",
        "Joseph", "Jessica", "Thomas", "Sarah", "Christopher", "Karen",
        "Daniel", "Lisa", "Matthew", "Nancy", "Anthony", "Betty", "Mark",
        "Margaret", "Donald", "Sandra", "Steven", "Ashley", "Andrew", "Emily",
        "Paul", "Donna", "Joshua", "Michelle", "Kenneth", "Carol",
    ]
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
        "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
        "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
        "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
        "Ramirez", "Lewis", "Robinson",
    ]

    customers = []
    for i in range(1, n + 1):
        first = random.choice(first_names)
        last = random.choice(last_names)
        name = f"{first} {last}"
        email = f"{first.lower()}.{last.lower()}{i}@example.com"
        state = random.choices(STATE_NAMES, weights=STATE_WEIGHTS, k=1)[0]
        # Created sometime before the data window
        created = START_DATE - timedelta(days=random.randint(30, 365))
        customers.append((i, name, email, state, created.strftime("%Y-%m-%d")))

    conn.executemany(
        "INSERT INTO customers VALUES (?, ?, ?, ?, ?)", customers
    )
    conn.commit()
    return customers


def generate_products(conn: sqlite3.Connection):
    products = []
    for i, (name, cat, subcat, price) in enumerate(PRODUCTS, 1):
        products.append((i, name, cat, subcat, price))
    conn.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?)", products)
    conn.commit()
    return products


def generate_purchases(conn: sqlite3.Connection, customers, products):
    """Generate ~2500 purchases with realistic patterns."""
    purchases = []
    purchase_id = 1
    current = START_DATE

    while current <= END_DATE:
        # Higher volume on weekends
        is_weekend = current.weekday() >= 5
        # Higher volume in late Nov / December
        is_holiday_season = (
            (current.month == 11 and current.day >= 20) or current.month == 12
        )

        base_count = 20
        if is_weekend:
            base_count += 5
        if is_holiday_season:
            base_count += 8

        daily_count = random.randint(base_count - 5, base_count + 5)

        for _ in range(daily_count):
            cust = random.choice(customers)
            customer_id = cust[0]
            prod = random.choice(products)
            product_id, _, _, _, price = prod
            quantity = random.choices([1, 2, 3], weights=[70, 25, 5], k=1)[0]

            # Promo code logic
            promo_code = None
            discount_amount = 0.0
            if random.random() < 0.30:
                if is_holiday_season and random.random() < 0.4:
                    promo_code = "HOLIDAY15"
                    promo_type, promo_val = "percent", 15
                else:
                    pc = random.choice(PROMO_CODES)
                    promo_code, promo_type, promo_val = pc

                subtotal = price * quantity
                if promo_type == "percent":
                    discount_amount = round(subtotal * promo_val / 100, 2)
                else:
                    discount_amount = min(promo_val, subtotal)

            total_price = round(price * quantity - discount_amount, 2)
            total_price = max(total_price, 0)

            purchases.append((
                purchase_id, customer_id, product_id, quantity,
                price, total_price, promo_code, discount_amount,
                current.strftime("%Y-%m-%d"),
            ))
            purchase_id += 1

        current += timedelta(days=1)

    conn.executemany("INSERT INTO purchases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", purchases)
    conn.commit()
    print(f"Generated {len(purchases)} purchases")
    return purchases


def generate_segments(conn: sqlite3.Connection):
    """Compute weekly customer segments based on spend."""
    cur = conn.cursor()

    # Get all distinct weeks
    cur.execute("""
        SELECT DISTINCT date(purchase_date, 'weekday 0', '-6 days') as week_start
        FROM purchases
        ORDER BY week_start
    """)
    weeks = [row[0] for row in cur.fetchall()]

    segment_id = 1
    all_segments = []

    for week_start in weeks:
        week_end_dt = datetime.strptime(week_start, "%Y-%m-%d") + timedelta(days=6)
        week_end = week_end_dt.strftime("%Y-%m-%d")

        # Get spend per customer for this week
        cur.execute("""
            SELECT customer_id, SUM(total_price) as total_spend
            FROM purchases
            WHERE purchase_date >= ? AND purchase_date <= ?
            GROUP BY customer_id
            ORDER BY total_spend DESC
        """, (week_start, week_end))
        spenders = cur.fetchall()

        if not spenders:
            continue

        n = len(spenders)
        top20 = max(1, int(n * 0.2))
        top60 = max(top20 + 1, int(n * 0.6))

        for i, (customer_id, total_spend) in enumerate(spenders):
            if i < top20:
                segment = "high"
            elif i < top60:
                segment = "medium"
            else:
                segment = "low"
            all_segments.append((segment_id, customer_id, week_start, round(total_spend, 2), segment))
            segment_id += 1

    conn.executemany("INSERT INTO customer_segments VALUES (?, ?, ?, ?, ?)", all_segments)
    conn.commit()
    print(f"Generated {len(all_segments)} customer segment records")


def compute_ground_truth(conn: sqlite3.Connection):
    """Run reference SQL queries and print ground-truth values."""
    cur = conn.cursor()

    print("\n" + "=" * 60)
    print("GROUND TRUTH VALUES (for eval dataset)")
    print("=" * 60)

    # 1. Revenue last week (2025-01-06 to 2025-01-12)
    cur.execute("""
        SELECT ROUND(SUM(total_price), 2)
        FROM purchases
        WHERE purchase_date >= '2025-01-06' AND purchase_date <= '2025-01-12'
    """)
    revenue_last_week = cur.fetchone()[0]
    print(f"\n1. Revenue last week (Jan 6-12): ${revenue_last_week}")

    # 2. Top 3 product categories by revenue last month (Dec 2024)
    cur.execute("""
        SELECT p.category, ROUND(SUM(pu.total_price), 2) as revenue
        FROM purchases pu
        JOIN products p ON pu.product_id = p.product_id
        WHERE pu.purchase_date >= '2024-12-01' AND pu.purchase_date <= '2024-12-31'
        GROUP BY p.category
        ORDER BY revenue DESC
        LIMIT 3
    """)
    top_categories = cur.fetchall()
    print("\n2. Top 3 categories by revenue (Dec 2024):")
    for cat, rev in top_categories:
        print(f"   {cat}: ${rev}")

    # 3. How many customers used promo code HOLIDAY15?
    cur.execute("""
        SELECT COUNT(DISTINCT customer_id)
        FROM purchases
        WHERE promo_code = 'HOLIDAY15'
    """)
    holiday15_customers = cur.fetchone()[0]
    print(f"\n3. Customers who used HOLIDAY15: {holiday15_customers}")

    # 4. Average order value last month (Dec 2024)
    cur.execute("""
        SELECT ROUND(AVG(total_price), 2)
        FROM purchases
        WHERE purchase_date >= '2024-12-01' AND purchase_date <= '2024-12-31'
    """)
    avg_order_dec = cur.fetchone()[0]
    print(f"\n4. Average order value (Dec 2024): ${avg_order_dec}")

    # 5. Best-selling book genre (all time)
    cur.execute("""
        SELECT p.subcategory, SUM(pu.quantity) as total_sold
        FROM purchases pu
        JOIN products p ON pu.product_id = p.product_id
        WHERE p.category = 'Books'
        GROUP BY p.subcategory
        ORDER BY total_sold DESC
        LIMIT 1
    """)
    best_genre = cur.fetchone()
    print(f"\n5. Best-selling book genre: {best_genre[0]} ({best_genre[1]} units)")

    # 6. Total discount amount from all promo codes
    cur.execute("""
        SELECT ROUND(SUM(discount_amount), 2)
        FROM purchases
        WHERE promo_code IS NOT NULL
    """)
    total_discounts = cur.fetchone()[0]
    print(f"\n6. Total discount amount: ${total_discounts}")

    # 7. Revenue by state (top 5)
    cur.execute("""
        SELECT c.state, ROUND(SUM(pu.total_price), 2) as revenue
        FROM purchases pu
        JOIN customers c ON pu.customer_id = c.customer_id
        GROUP BY c.state
        ORDER BY revenue DESC
        LIMIT 5
    """)
    top_states = cur.fetchall()
    print("\n7. Revenue by state (top 5):")
    for state, rev in top_states:
        print(f"   {state}: ${rev}")

    print("\n" + "=" * 60)

    return {
        "revenue_last_week": revenue_last_week,
        "top_categories": top_categories,
        "holiday15_customers": holiday15_customers,
        "avg_order_dec": avg_order_dec,
        "best_genre": best_genre,
        "total_discounts": total_discounts,
        "top_states": top_states,
    }


def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)
    customers = generate_customers(conn)
    products = generate_products(conn)
    generate_purchases(conn, customers, products)
    generate_segments(conn)
    ground_truth = compute_ground_truth(conn)
    conn.close()

    print(f"\nDatabase created at: {DB_PATH}")
    return ground_truth


if __name__ == "__main__":
    main()

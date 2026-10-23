"""Creates a sample SQLite sales database + a metadata layer that
describes every table and column, so Claude can write schema-aware SQL."""
import random
import sqlite3
from datetime import date, timedelta

DB_PATH = "sales.db"
random.seed(42)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.executescript("""
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS schema_metadata;

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name        TEXT,
    region      TEXT,
    segment     TEXT
);
CREATE TABLE products (
    product_id  INTEGER PRIMARY KEY,
    name        TEXT,
    category    TEXT,
    unit_price  REAL
);
CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    product_id  INTEGER REFERENCES products(product_id),
    order_date  TEXT,
    quantity    INTEGER,
    discount    REAL,
    status      TEXT
);
-- Metadata layer: business context for every table/column
CREATE TABLE schema_metadata (
    table_name  TEXT,
    column_name TEXT,
    description TEXT
);
""")

regions = ["North", "South", "East", "West"]
segments = ["Retail", "Wholesale", "Online"]
cur.executemany("INSERT INTO customers VALUES (?,?,?,?)",
    [(i, f"Customer {i}", random.choice(regions), random.choice(segments))
     for i in range(1, 101)])

catalog = [("Notebook", "Stationery", 40), ("Pen Pack", "Stationery", 120),
           ("Backpack", "Bags", 900), ("Calculator", "Electronics", 650),
           ("Headphones", "Electronics", 1500), ("Desk Lamp", "Home", 800)]
cur.executemany("INSERT INTO products VALUES (?,?,?,?)",
    [(i, n, c, p) for i, (n, c, p) in enumerate(catalog, 1)])

start = date(2025, 1, 1)
orders = []
for oid in range(1, 2001):
    orders.append((
        oid, random.randint(1, 100), random.randint(1, len(catalog)),
        (start + timedelta(days=random.randint(0, 299))).isoformat(),
        random.randint(1, 10), random.choice([0, 0, 0.05, 0.1, 0.2]),
        random.choices(["Delivered", "Returned", "Cancelled"], [85, 10, 5])[0]))
cur.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?,?)", orders)

meta = [
 ("customers", "customer_id", "Unique customer identifier (primary key)"),
 ("customers", "name", "Customer display name"),
 ("customers", "region", "Sales region: North, South, East, West"),
 ("customers", "segment", "Customer segment: Retail, Wholesale, Online"),
 ("products", "product_id", "Unique product identifier (primary key)"),
 ("products", "name", "Product name"),
 ("products", "category", "Product category"),
 ("products", "unit_price", "List price per unit in INR"),
 ("orders", "order_id", "Unique order identifier (primary key)"),
 ("orders", "customer_id", "FK -> customers.customer_id"),
 ("orders", "product_id", "FK -> products.product_id"),
 ("orders", "order_date", "Order date, ISO format YYYY-MM-DD"),
 ("orders", "quantity", "Units ordered"),
 ("orders", "discount", "Discount fraction (0.1 = 10%)"),
 ("orders", "status", "Delivered, Returned or Cancelled. Revenue should count Delivered only"),
]
cur.executemany("INSERT INTO schema_metadata VALUES (?,?,?)", meta)
conn.commit()
conn.close()
print(f"Created {DB_PATH} with sample data and metadata layer.")

# ElectroMart

ElectroMart is a database systems course project that simulates an electronics retailer. I built a Flask storefront for browsing products and placing orders, along with command-line tools for customer service, call center orders, and warehouse inventory.

## Database design

The MySQL schema uses 12 tables to model customers, products, orders, shipments, and inventory across stores and warehouses. Each order item stores the unit price at the time of purchase, so changes to the product catalog don’t change past orders.

- [`database/schema.sql`](database/schema.sql) creates the tables and their relationships.
- [`database/populate.sql`](database/populate.sql) loads sample data.
- [`database/queries.sql`](database/queries.sql) contains example SQL queries.

## Testing concurrent orders

I wrote a [five-thread test](src/python/test_concurrency.py) to see what happens when several orders compete for the same stock. Each thread tries to buy one unit of the same product at the same store. The script uses `READ COMMITTED` and `SELECT ... FOR UPDATE` to lock the product and inventory rows while it checks stock and records the order. If there’s enough stock, the order and inventory update are committed together. If stock is insufficient, the transaction rolls back. The script prints the number of successful and failed orders and the remaining stock.

## Run locally

1. In MySQL, run `database/schema.sql`, then `database/populate.sql`. These scripts use the `electronics_vendor` database.
2. From the repository root, run `python -m pip install -r requirements.txt`.
3. In PowerShell, set `$env:DB_PASSWORD = "your-local-mysql-password"`. The scripts connect to MySQL on `localhost` as `root`.
4. In the same PowerShell window, run `python src/python/web_app.py` and open `http://localhost:5000`.

To run the concurrency test, use a disposable copy of the sample database. Add an `Inventory_Store` row for `store_id = 1` and `product_id = 1` with at least five units in stock, then run `python src/python/test_concurrency.py`. Successful attempts create orders and reduce stock.

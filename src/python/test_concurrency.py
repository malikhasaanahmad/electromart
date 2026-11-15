#!/usr/bin/env python3
"""
Concurrency Test
Tests if multiple orders can happen at the same time without messing up the database
"""

import mysql.connector
from mysql.connector import Error
import threading
import time
import random
import os
import sys

# Add parent directory so we can import db_config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Get the password
try:
    from db_config import DB_CONFIG
    DB_PASSWORD = DB_CONFIG.get('password', 'Malik123')
except ImportError:
    DB_PASSWORD = 'Malik123'

# Make sure we have a password
if not DB_PASSWORD:
    DB_PASSWORD = 'Malik123'

# Database connection settings
DB_CONFIG_FULL = {
    'host': 'localhost',
    'port': 3306,
    'database': 'electronics_vendor',
    'user': 'root',
    'password': 'Malik123',  # The password
    'autocommit': False  # We'll handle commits manually
}

def simulate_order(customer_id, product_id, quantity, thread_id):
    """Simulate one person placing an order"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG_FULL)
        cursor = connection.cursor()
        
        print(f"[Thread {thread_id}] Starting order...")
        
        # Start a transaction so everything happens together
        connection.start_transaction(isolation_level='READ COMMITTED')
        
        # Get the product price and lock it so no one else can change it
        cursor.execute("SELECT price FROM Product WHERE product_id = %s FOR UPDATE", (product_id,))
        product = cursor.fetchone()
        
        if not product:
            print(f"[Thread {thread_id}] Product not found")
            connection.rollback()
            cursor.close()
            connection.close()
            return False
        
        price = float(product[0])
        total = price * quantity
        
        # Check if we have enough in stock (lock the inventory row)
        cursor.execute(
            "SELECT quantity FROM Inventory_Store WHERE store_id = 1 AND product_id = %s FOR UPDATE",
            (product_id,)
        )
        inventory = cursor.fetchone()
        
        # If we have enough, create the order
        if inventory and inventory[0] >= quantity:
            # Create the order
            cursor.execute(
                """INSERT INTO `Order` (customer_id, order_date, order_type, store_id, total_amount, status, payment_method)
                   VALUES (%s, CURDATE(), 'in-store', 1, %s, 'processing', 'test')""",
                (customer_id, total)
            )
            order_id = cursor.lastrowid
            
            # Add the item to the order
            cursor.execute(
                """INSERT INTO OrderItem (order_id, product_id, quantity, unit_price, subtotal)
                   VALUES (%s, %s, %s, %s, %s)""",
                (order_id, product_id, quantity, price, total)
            )
            
            # Update the inventory (reduce it by the quantity ordered)
            cursor.execute(
                """UPDATE Inventory_Store 
                   SET quantity = quantity - %s 
                   WHERE store_id = 1 AND product_id = %s""",
                (quantity, product_id)
            )
            
            # Wait a random amount of time to simulate real conditions
            time.sleep(random.uniform(0.1, 0.5))
            
            # Save everything to the database
            connection.commit()
            print(f"[Thread {thread_id}] Order {order_id} created! Total: ${total:.2f}")
            
            cursor.close()
            connection.close()
            return True
        else:
            # Not enough in stock
            print(f"[Thread {thread_id}] Not enough inventory")
            connection.rollback()
            cursor.close()
            connection.close()
            return False
    
    except Error as e:
        print(f"[Thread {thread_id}] Error: {e}")
        try:
            connection.rollback()
            cursor.close()
            connection.close()
        except:
            pass
        return False

def test_concurrent_orders():
    """Test if multiple orders at the same time work correctly"""
    print("="*80)
    print("CONCURRENCY TEST - Multiple Orders at the Same Time")
    print("="*80)
    
    num_threads = 5  # How many orders to try at once
    customer_id = 1  # Use customer ID 1
    product_id = 1   # Use product ID 1
    quantity_per_order = 1  # Each order is for 1 item
    
    threads = []
    results = []
    
    def worker(thread_id):
        # Each thread tries to place an order
        result = simulate_order(customer_id, product_id, quantity_per_order, thread_id)
        results.append((thread_id, result))
    
    print(f"\nStarting {num_threads} orders at the same time...")
    print(f"Each one will try to order 1x Product ID {product_id}\n")
    
    # Start all the threads
    start_time = time.time()
    for i in range(num_threads):
        thread = threading.Thread(target=worker, args=(i+1,))
        threads.append(thread)
        thread.start()
        time.sleep(0.1)  # Small delay between starting threads
    
    # Wait for all threads to finish
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    # Show the results
    print("\n" + "="*80)
    print("TEST RESULTS")
    print("="*80)
    print(f"Total orders attempted: {num_threads}")
    print(f"Time taken: {elapsed:.2f} seconds")
    print(f"Successful orders: {sum(1 for _, success in results if success)}")
    print(f"Failed orders: {sum(1 for _, success in results if not success)}")
    
    # Check the final inventory to make sure it's correct
    try:
        connection = mysql.connector.connect(**DB_CONFIG_FULL)
        cursor = connection.cursor()
        cursor.execute(
            "SELECT quantity FROM Inventory_Store WHERE store_id = 1 AND product_id = %s",
            (product_id,)
        )
        final_inventory = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if final_inventory:
            print(f"\nFinal inventory for product {product_id}: {final_inventory[0]}")
            print("✓ Database is still consistent!")
    except Error as e:
        print(f"Error checking final inventory: {e}")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    print("\n" + "="*80)
    print("DATABASE CONCURRENCY TESTING")
    print("="*80)
    
    test_concurrent_orders()
    
    print("\n" + "="*80)
    print("All concurrency tests completed!")
    print("="*80)


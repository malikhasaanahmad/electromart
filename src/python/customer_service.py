#!/usr/bin/env python3
"""
Customer Service Tool
For customer service people to check if products are in stock at stores or warehouses
"""

import mysql.connector
from mysql.connector import Error
import os
import sys

DB_PASSWORD = os.getenv("DB_PASSWORD", "")

class CustomerServiceApp:
    def __init__(self):
        self.connection = None
        self.connect_db()
    
    def connect_db(self):
        """Connect to the MySQL database"""
        try:
            # Connect to the database with the password
            self.connection = mysql.connector.connect(
                host='localhost',
                port=3306,
                database='electronics_vendor',
                user='root',
              password=DB_PASSWORD
            )
            if self.connection.is_connected():
                print("Connected to database successfully!")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            self.connection = None
    
    def check_inventory(self, product_name=None, store_id=None, state=None):
        """Check inventory for a product"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            if product_name:
                query = """
                    SELECT p.product_id, p.product_name, p.manufacturer, p.price,
                           s.store_id, s.store_name, s.city, s.state,
                           inv.quantity, inv.reorder_level
                    FROM Product p
                    JOIN Inventory_Store inv ON p.product_id = inv.product_id
                    JOIN Store s ON inv.store_id = s.store_id
                    WHERE p.product_name LIKE %s
                """
                params = [f'%{product_name}%']
                
                if state:
                    query += " AND s.state = %s"
                    params.append(state)
                
                query += " ORDER BY s.state, s.city, p.product_name"
                cursor.execute(query, params)
                
            elif store_id:
                query = """
                    SELECT p.product_id, p.product_name, p.manufacturer, p.price,
                           inv.quantity, inv.reorder_level
                    FROM Product p
                    JOIN Inventory_Store inv ON p.product_id = inv.product_id
                    WHERE inv.store_id = %s
                    ORDER BY p.product_name
                """
                cursor.execute(query, (store_id,))
            
            else:
                print("Please provide either product name or store ID")
                return
            
            results = cursor.fetchall()
            cursor.close()
            
            if not results:
                print("No inventory found.")
                return
            
            print("\n" + "="*80)
            print("INVENTORY RESULTS")
            print("="*80)
            
            for row in results:
                print(f"\nProduct: {row['product_name']}")
                print(f"Manufacturer: {row.get('manufacturer', 'N/A')}")
                print(f"Price: ${row['price']:.2f}")
                if 'store_name' in row:
                    print(f"Store: {row['store_name']} ({row['city']}, {row['state']})")
                print(f"Quantity: {row['quantity']}")
                if 'reorder_level' in row:
                    print(f"Reorder Level: {row['reorder_level']}")
                    if row['quantity'] <= row['reorder_level']:
                        print("⚠️  LOW STOCK - Reorder needed!")
                print("-"*80)
        
        except Error as e:
            print(f"Error checking inventory: {e}")
    
    def check_warehouse_inventory(self, product_name=None):
        """Check warehouse inventory"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
                SELECT p.product_id, p.product_name, p.manufacturer, p.price,
                       w.warehouse_id, w.warehouse_name, w.city, w.state,
                       inv.quantity
                FROM Product p
                JOIN Inventory_Warehouse inv ON p.product_id = inv.product_id
                JOIN Warehouse w ON inv.warehouse_id = w.warehouse_id
            """
            params = []
            
            if product_name:
                query += " WHERE p.product_name LIKE %s"
                params.append(f'%{product_name}%')
            
            query += " ORDER BY w.state, w.city, p.product_name"
            cursor.execute(query, params)
            
            results = cursor.fetchall()
            cursor.close()
            
            if not results:
                print("No warehouse inventory found.")
                return
            
            print("\n" + "="*80)
            print("WAREHOUSE INVENTORY")
            print("="*80)
            
            for row in results:
                print(f"\nProduct: {row['product_name']}")
                print(f"Manufacturer: {row.get('manufacturer', 'N/A')}")
                print(f"Warehouse: {row['warehouse_name']} ({row['city']}, {row['state']})")
                print(f"Quantity: {row['quantity']}")
                print("-"*80)
        
        except Error as e:
            print(f"Error checking warehouse inventory: {e}")
    
    def list_stores(self):
        """List all stores"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT store_id, store_name, city, state FROM Store ORDER BY state, city")
            stores = cursor.fetchall()
            cursor.close()
            
            print("\n" + "="*80)
            print("STORES")
            print("="*80)
            for store in stores:
                print(f"ID: {store['store_id']} - {store['store_name']} ({store['city']}, {store['state']})")
        
        except Error as e:
            print(f"Error listing stores: {e}")
    
    def run(self):
        """Main application loop"""
        if not self.connection:
            print("Cannot connect to database. Exiting.")
            return
        
        print("\n" + "="*80)
        print("CUSTOMER SERVICE INVENTORY LOOKUP SYSTEM")
        print("="*80)
        
        while True:
            print("\nOptions:")
            print("1. Check store inventory by product name")
            print("2. Check store inventory by store ID")
            print("3. Check warehouse inventory")
            print("4. List all stores")
            print("5. Exit")
            
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == '1':
                product = input("Enter product name (or part of it): ").strip()
                state = input("Enter state (optional, press Enter to skip): ").strip()
                self.check_inventory(product_name=product, state=state if state else None)
            
            elif choice == '2':
                self.list_stores()
                store_id = input("\nEnter store ID: ").strip()
                try:
                    self.check_inventory(store_id=int(store_id))
                except ValueError:
                    print("Invalid store ID")
            
            elif choice == '3':
                product = input("Enter product name (or part of it, press Enter for all): ").strip()
                self.check_warehouse_inventory(product_name=product if product else None)
            
            elif choice == '4':
                self.list_stores()
            
            elif choice == '5':
                print("Exiting...")
                break
            
            else:
                print("Invalid choice. Please try again.")
        
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed.")

if __name__ == '__main__':
    app = CustomerServiceApp()
    app.run()


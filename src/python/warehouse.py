#!/usr/bin/env python3
"""
Warehouse Tool
For warehouse workers to record shipments and update inventory
"""

import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os
import sys

# Add parent directory so we can import db_config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Get the password from db_config.py
try:
    from db_config import DB_CONFIG
    DB_PASSWORD = DB_CONFIG.get('password', 'Malik123')
except ImportError:
    DB_PASSWORD = 'Malik123'

# Make sure we have a password
if not DB_PASSWORD:
    DB_PASSWORD = 'Malik123'

class WarehouseApp:
    def __init__(self):
        self.connection = None
        self.connect_db()
    
    def connect_db(self):
        """Connect to the database"""
        try:
            # Connect with the password
            self.connection = mysql.connector.connect(
                host='localhost',
                port=3306,
                database='electronics_vendor',
                user='root',
                password='Malik123'  # The password
            )
            if self.connection.is_connected():
                print("Connected to database successfully!")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            self.connection = None
    
    def list_warehouses(self):
        """List all warehouses"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Warehouse ORDER BY warehouse_name")
            warehouses = cursor.fetchall()
            cursor.close()
            
            print("\n" + "="*80)
            print("WAREHOUSES")
            print("="*80)
            for warehouse in warehouses:
                print(f"ID: {warehouse['warehouse_id']} - {warehouse['warehouse_name']} "
                      f"({warehouse['city']}, {warehouse['state']})")
        
        except Error as e:
            print(f"Error listing warehouses: {e}")
    
    def view_pending_reorders(self, warehouse_id=None):
        """View pending reorders"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            if warehouse_id:
                query = """
                    SELECT r.*, p.product_name, p.manufacturer
                    FROM Reorder r
                    JOIN Product p ON r.product_id = p.product_id
                    WHERE r.warehouse_id = %s AND r.status = 'pending'
                    ORDER BY r.reorder_date
                """
                cursor.execute(query, (warehouse_id,))
            else:
                query = """
                    SELECT r.*, p.product_name, p.manufacturer, w.warehouse_name
                    FROM Reorder r
                    JOIN Product p ON r.product_id = p.product_id
                    LEFT JOIN Warehouse w ON r.warehouse_id = w.warehouse_id
                    WHERE r.warehouse_id IS NOT NULL AND r.status = 'pending'
                    ORDER BY r.reorder_date
                """
                cursor.execute(query)
            
            reorders = cursor.fetchall()
            cursor.close()
            
            if reorders:
                print("\n" + "="*80)
                print("PENDING REORDERS")
                print("="*80)
                for reorder in reorders:
                    print(f"\nReorder ID: {reorder['reorder_id']}")
                    print(f"Product: {reorder['product_name']} ({reorder.get('manufacturer', 'N/A')})")
                    if 'warehouse_name' in reorder:
                        print(f"Warehouse: {reorder['warehouse_name']}")
                    print(f"Order Date: {reorder['reorder_date']}")
                    print(f"Status: {reorder['status']}")
                    print("-"*80)
            else:
                print("No pending reorders found.")
        
        except Error as e:
            print(f"Error viewing reorders: {e}")
    
    def receive_shipment(self, reorder_id, warehouse_id):
        """Record receipt of a shipment and update inventory"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            connection = self.connection
            
            connection.start_transaction()
            
            try:
                # Get reorder details
                cursor.execute(
                    """SELECT * FROM Reorder WHERE reorder_id = %s AND warehouse_id = %s""",
                    (reorder_id, warehouse_id)
                )
                reorder = cursor.fetchone()
                
                if not reorder:
                    print("Reorder not found or doesn't belong to this warehouse.")
                    connection.rollback()
                    cursor.close()
                    return False
                
                if reorder['status'] == 'completed':
                    print("This reorder has already been completed.")
                    connection.rollback()
                    cursor.close()
                    return False
                
                # Update reorder status
                cursor.execute(
                    """UPDATE Reorder SET status = 'completed' WHERE reorder_id = %s""",
                    (reorder_id,)
                )
                
                # Update inventory
                cursor.execute(
                    """SELECT quantity FROM Inventory_Warehouse
                       WHERE warehouse_id = %s AND product_id = %s""",
                    (warehouse_id, reorder['product_id'])
                )
                inventory = cursor.fetchone()
                
                if inventory:
                    # Update existing inventory
                    new_quantity = inventory['quantity'] + 10  # Assume 10 units received
                    cursor.execute(
                        """UPDATE Inventory_Warehouse
                           SET quantity = %s
                           WHERE warehouse_id = %s AND product_id = %s""",
                        (new_quantity, warehouse_id, reorder['product_id'])
                    )
                else:
                    # Create new inventory record
                    cursor.execute(
                        """INSERT INTO Inventory_Warehouse (warehouse_id, product_id, quantity)
                           VALUES (%s, %s, %s)""",
                        (warehouse_id, reorder['product_id'], 10)
                    )
                
                connection.commit()
                
                print(f"\n✅ Shipment received successfully!")
                print(f"Product ID: {reorder['product_id']}")
                print(f"Quantity received: 10 units")
                
                cursor.close()
                return True
            
            except Error as e:
                connection.rollback()
                cursor.close()
                print(f"Error receiving shipment: {e}")
                return False
        
        except Error as e:
            print(f"Error receiving shipment: {e}")
            return False
    
    def update_inventory(self, warehouse_id, product_id, quantity_change):
        """Manually update inventory quantity"""
        try:
            cursor = self.connection.cursor()
            connection = self.connection
            
            connection.start_transaction()
            
            try:
                # Check current inventory
                cursor.execute(
                    """SELECT quantity FROM Inventory_Warehouse
                       WHERE warehouse_id = %s AND product_id = %s""",
                    (warehouse_id, product_id)
                )
                inventory = cursor.fetchone()
                
                if inventory:
                    new_quantity = inventory[0] + quantity_change
                    if new_quantity < 0:
                        print("Error: Cannot reduce inventory below 0.")
                        connection.rollback()
                        cursor.close()
                        return False
                    
                    cursor.execute(
                        """UPDATE Inventory_Warehouse
                           SET quantity = %s
                           WHERE warehouse_id = %s AND product_id = %s""",
                        (new_quantity, warehouse_id, product_id)
                    )
                else:
                    if quantity_change < 0:
                        print("Error: No inventory to reduce.")
                        connection.rollback()
                        cursor.close()
                        return False
                    
                    cursor.execute(
                        """INSERT INTO Inventory_Warehouse (warehouse_id, product_id, quantity)
                           VALUES (%s, %s, %s)""",
                        (warehouse_id, product_id, quantity_change)
                    )
                
                connection.commit()
                print(f"\n✅ Inventory updated successfully!")
                
                cursor.close()
                return True
            
            except Error as e:
                connection.rollback()
                cursor.close()
                print(f"Error updating inventory: {e}")
                return False
        
        except Error as e:
            print(f"Error updating inventory: {e}")
            return False
    
    def view_inventory(self, warehouse_id, product_name=None):
        """View warehouse inventory"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
                SELECT p.product_id, p.product_name, p.manufacturer, inv.quantity
                FROM Inventory_Warehouse inv
                JOIN Product p ON inv.product_id = p.product_id
                WHERE inv.warehouse_id = %s
            """
            params = [warehouse_id]
            
            if product_name:
                query += " AND p.product_name LIKE %s"
                params.append(f'%{product_name}%')
            
            query += " ORDER BY p.product_name"
            cursor.execute(query, params)
            
            inventory = cursor.fetchall()
            cursor.close()
            
            if inventory:
                print("\n" + "="*80)
                print("WAREHOUSE INVENTORY")
                print("="*80)
                for item in inventory:
                    print(f"{item['product_id']:3d} | {item['product_name']:40s} | "
                          f"Qty: {item['quantity']:4d}")
            else:
                print("No inventory found.")
        
        except Error as e:
            print(f"Error viewing inventory: {e}")
    
    def run(self):
        """Main application loop"""
        if not self.connection:
            print("Cannot connect to database. Exiting.")
            return
        
        print("\n" + "="*80)
        print("WAREHOUSE INVENTORY MANAGEMENT SYSTEM")
        print("="*80)
        
        while True:
            print("\nOptions:")
            print("1. List warehouses")
            print("2. View pending reorders")
            print("3. Receive shipment (mark reorder as completed)")
            print("4. Update inventory manually")
            print("5. View warehouse inventory")
            print("6. Exit")
            
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == '1':
                self.list_warehouses()
            
            elif choice == '2':
                warehouse_id = input("Enter warehouse ID (or press Enter for all): ").strip()
                try:
                    self.view_pending_reorders(int(warehouse_id) if warehouse_id else None)
                except ValueError:
                    print("Invalid warehouse ID")
            
            elif choice == '3':
                warehouse_id = input("Enter warehouse ID: ").strip()
                reorder_id = input("Enter reorder ID: ").strip()
                try:
                    self.receive_shipment(int(reorder_id), int(warehouse_id))
                except ValueError:
                    print("Invalid input")
            
            elif choice == '4':
                warehouse_id = input("Enter warehouse ID: ").strip()
                product_id = input("Enter product ID: ").strip()
                quantity_change = input("Enter quantity change (+ for increase, - for decrease): ").strip()
                try:
                    self.update_inventory(int(warehouse_id), int(product_id), int(quantity_change))
                except ValueError:
                    print("Invalid input")
            
            elif choice == '5':
                warehouse_id = input("Enter warehouse ID: ").strip()
                product_name = input("Enter product name filter (optional): ").strip()
                try:
                    self.view_inventory(int(warehouse_id), product_name if product_name else None)
                except ValueError:
                    print("Invalid warehouse ID")
            
            elif choice == '6':
                print("Exiting...")
                break
            
            else:
                print("Invalid choice. Please try again.")
        
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed.")

if __name__ == '__main__':
    app = WarehouseApp()
    app.run()


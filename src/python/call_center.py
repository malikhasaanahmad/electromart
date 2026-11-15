#!/usr/bin/env python3
"""
Call Center Tool
For call center staff to look up customers and create orders over the phone
"""

import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os
import sys

DB_PASSWORD = os.getenv("DB_PASSWORD", "")

class CallCenterApp:
    def __init__(self):
        self.connection = None
        self.connect_db()
    
    def connect_db(self):
        """Connect to the database"""
        try:
            # Set up connection parameters with the password
            conn_params = {
                'host': 'localhost',
                'port': 3306,
                'database': 'electronics_vendor',
                'user': 'root',
                  'password': DB_PASSWORD,
            }
            
            # Make sure password isn't empty (shouldn't happen but just in case)
            if not conn_params['password'] or conn_params['password'] == '':
                raise ValueError("Password is empty or None!")
            
            self.connection = mysql.connector.connect(**conn_params)
            if self.connection.is_connected():
                print("Connected to database successfully!")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            print("Connection parameters used:")
            print("  Host: localhost")
            print("  Port: 3306")
            print("  User: root")
            self.connection = None
    
    def lookup_customer(self, email=None, phone=None, account_number=None):
        """Look up customer information"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            if email:
                cursor.execute("SELECT * FROM Customer WHERE email = %s", (email,))
            elif phone:
                cursor.execute("SELECT * FROM Customer WHERE phone = %s", (phone,))
            elif account_number:
                cursor.execute("SELECT * FROM Customer WHERE account_number = %s", (account_number,))
            else:
                print("Please provide email, phone, or account number")
                return None
            
            customer = cursor.fetchone()
            cursor.close()
            
            if customer:
                print("\n" + "="*80)
                print("CUSTOMER INFORMATION")
                print("="*80)
                print(f"ID: {customer['customer_id']}")
                print(f"Name: {customer['first_name']} {customer['last_name']}")
                print(f"Email: {customer['email']}")
                print(f"Phone: {customer.get('phone', 'N/A')}")
                print(f"Address: {customer.get('address', 'N/A')}")
                print(f"City: {customer.get('city', 'N/A')}, {customer.get('state', 'N/A')} {customer.get('zip_code', 'N/A')}")
                print(f"Customer Type: {customer['customer_type']}")
                if customer.get('account_number'):
                    print(f"Account Number: {customer['account_number']}")
                print("="*80)
                return customer
            else:
                print("Customer not found.")
                return None
        
        except Error as e:
            print(f"Error looking up customer: {e}")
            return None
    
    def get_customer_orders(self, customer_id):
        """Get recent orders for a customer"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                """SELECT o.*, COUNT(oi.order_item_id) as item_count
                   FROM `Order` o
                   LEFT JOIN OrderItem oi ON o.order_id = oi.order_id
                   WHERE o.customer_id = %s
                   GROUP BY o.order_id
                   ORDER BY o.order_date DESC
                   LIMIT 10""",
                (customer_id,)
            )
            orders = cursor.fetchall()
            cursor.close()
            
            if orders:
                print("\n" + "="*80)
                print("RECENT ORDERS")
                print("="*80)
                for order in orders:
                    print(f"\nOrder ID: {order['order_id']}")
                    print(f"Date: {order['order_date']}")
                    print(f"Type: {order['order_type']}")
                    print(f"Status: {order['status']}")
                    print(f"Total: ${order['total_amount']:.2f}")
                    print(f"Items: {order['item_count']}")
                    print("-"*80)
            else:
                print("No orders found for this customer.")
        
        except Error as e:
            print(f"Error getting customer orders: {e}")
    
    def list_products(self, search_term=None):
        """List available products"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            if search_term:
                cursor.execute(
                    """SELECT product_id, product_name, manufacturer, price
                       FROM Product
                       WHERE product_name LIKE %s OR manufacturer LIKE %s
                       ORDER BY product_name
                       LIMIT 20""",
                    (f'%{search_term}%', f'%{search_term}%')
                )
            else:
                cursor.execute(
                    """SELECT product_id, product_name, manufacturer, price
                       FROM Product
                       ORDER BY product_name
                       LIMIT 20"""
                )
            
            products = cursor.fetchall()
            cursor.close()
            
            if products:
                print("\n" + "="*80)
                print("PRODUCTS")
                print("="*80)
                for product in products:
                    print(f"ID: {product['product_id']:3d} | {product['product_name']:40s} | "
                          f"{product.get('manufacturer', 'N/A'):20s} | ${product['price']:.2f}")
            else:
                print("No products found.")
        
        except Error as e:
            print(f"Error listing products: {e}")
    
    def create_phone_order(self, customer_id, store_id, items):
        """Create a phone order"""
        try:
            cursor = self.connection.cursor()
            connection = self.connection
            
            connection.start_transaction()
            
            try:
                # Calculate total
                total = sum(item['price'] * item['quantity'] for item in items)
                
                # Create order
                cursor.execute(
                    """INSERT INTO `Order` (customer_id, order_date, order_type, store_id, total_amount, status, payment_method)
                       VALUES (%s, CURDATE(), 'in-store', %s, %s, 'processing', 'phone_order')""",
                    (customer_id, store_id, total)
                )
                order_id = cursor.lastrowid
                
                # Create order items
                for item in items:
                    cursor.execute(
                        """INSERT INTO OrderItem (order_id, product_id, quantity, unit_price, subtotal)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (order_id, item['product_id'], item['quantity'], item['price'],
                         item['price'] * item['quantity'])
                    )
                
                connection.commit()
                
                print(f"\n✅ Order created successfully!")
                print(f"Order ID: {order_id}")
                print(f"Total: ${total:.2f}")
                
                cursor.close()
                return order_id
            
            except Error as e:
                connection.rollback()
                cursor.close()
                print(f"Error creating order: {e}")
                return None
        
        except Error as e:
            print(f"Error creating phone order: {e}")
            return None
    
    def run(self):
        """Main application loop"""
        if not self.connection:
            print("Cannot connect to database. Exiting.")
            return
        
        print("\n" + "="*80)
        print("CALL CENTER ORDER SYSTEM")
        print("="*80)
        
        while True:
            print("\nOptions:")
            print("1. Look up customer")
            print("2. View customer orders")
            print("3. Search products")
            print("4. Create phone order")
            print("5. Exit")
            
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == '1':
                print("\nLook up by:")
                print("1. Email")
                print("2. Phone")
                print("3. Account Number")
                lookup_type = input("Choice (1-3): ").strip()
                
                if lookup_type == '1':
                    email = input("Enter email: ").strip()
                    customer = self.lookup_customer(email=email)
                elif lookup_type == '2':
                    phone = input("Enter phone: ").strip()
                    customer = self.lookup_customer(phone=phone)
                elif lookup_type == '3':
                    account = input("Enter account number: ").strip()
                    customer = self.lookup_customer(account_number=account)
                else:
                    print("Invalid choice")
                    customer = None
                
                if customer:
                    view_orders = input("\nView recent orders? (y/n): ").strip().lower()
                    if view_orders == 'y':
                        self.get_customer_orders(customer['customer_id'])
            
            elif choice == '2':
                customer_id = input("Enter customer ID: ").strip()
                try:
                    self.get_customer_orders(int(customer_id))
                except ValueError:
                    print("Invalid customer ID")
            
            elif choice == '3':
                search = input("Enter search term (or press Enter for all): ").strip()
                self.list_products(search_term=search if search else None)
            
            elif choice == '4':
                customer_id = input("Enter customer ID: ").strip()
                store_id = input("Enter store ID: ").strip()
                
                try:
                    customer_id = int(customer_id)
                    store_id = int(store_id)
                    
                    items = []
                    print("\nAdd items to order (enter 'done' when finished):")
                    while True:
                        product_id = input("Product ID: ").strip()
                        if product_id.lower() == 'done':
                            break
                        
                        try:
                            product_id = int(product_id)
                            quantity = int(input("Quantity: ").strip())
                            
                            # Get product price
                            cursor = self.connection.cursor(dictionary=True)
                            cursor.execute("SELECT price FROM Product WHERE product_id = %s", (product_id,))
                            product = cursor.fetchone()
                            cursor.close()
                            
                            if product:
                                items.append({
                                    'product_id': product_id,
                                    'quantity': quantity,
                                    'price': float(product['price'])
                                })
                                print(f"Added: {quantity}x Product {product_id} @ ${product['price']:.2f}")
                            else:
                                print("Product not found")
                        except ValueError:
                            print("Invalid input")
                    
                    if items:
                        self.create_phone_order(customer_id, store_id, items)
                    else:
                        print("No items to order")
                
                except ValueError:
                    print("Invalid customer ID or store ID")
            
            elif choice == '5':
                print("Exiting...")
                break
            
            else:
                print("Invalid choice. Please try again.")
        
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed.")

if __name__ == '__main__':
    app = CallCenterApp()
    app.run()

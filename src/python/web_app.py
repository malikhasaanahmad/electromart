#!/usr/bin/env python3
"""
Web App Backend - Flask Server
This is the backend API for the website. It handles all the database stuff
and serves the web pages.
"""

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os
import sys

# Need to add the parent directory so we can import db_config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Figure out where the web files are
# This file is in src/python/web_app.py
# So we go up one level to src, then into web folder
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # src/python
SRC_DIR = os.path.dirname(SCRIPT_DIR)  # src
WEB_DIR = os.path.join(SRC_DIR, 'web')  # src/web

# Create the Flask app and tell it where to find web files
app = Flask(__name__, static_folder=WEB_DIR, static_url_path='')
CORS(app)  # This lets the website talk to the server (CORS stuff)

DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_CONFIG_FULL = {
    'host': 'localhost',
    'port': 3306,
    'database': 'electronics_vendor',
    'user': 'root',
        'password': DB_PASSWORD,
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

def get_db_connection():
    """Connect to the database and return the connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG_FULL)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

@app.route('/')
def index():
    """Serve the main web interface"""
    return send_file(os.path.join(WEB_DIR, 'index.html'))

@app.route('/css/<path:filename>')
def css(filename):
    """Serve CSS files"""
    return send_from_directory(os.path.join(WEB_DIR, 'css'), filename)

@app.route('/js/<path:filename>')
def js(filename):
    """Serve JavaScript files"""
    return send_from_directory(os.path.join(WEB_DIR, 'js'), filename)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'API is running'})

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products, with optional filters for manufacturer or search"""
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Start building the SQL query
        # WHERE 1=1 is a trick so we can easily add AND clauses
        query = "SELECT * FROM Product WHERE 1=1"
        params = []
        
        # Get filter parameters from the URL
        category = request.args.get('category')
        manufacturer = request.args.get('manufacturer')
        search = request.args.get('search')
        
        # Add manufacturer filter if they specified one
        if manufacturer:
            query += " AND manufacturer = %s"
            params.append(manufacturer)
        
        # Add search filter if they're searching
        if search:
            query += " AND (product_name LIKE %s OR description LIKE %s)"
            params.extend([f'%{search}%', f'%{search}%'])
        
        # Sort by product name
        query += " ORDER BY product_name"
        
        cursor.execute(query, params)
        products = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return jsonify(products)
    
    except Error as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all categories - we use manufacturers as categories"""
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = connection.cursor(dictionary=True)
        # Get all unique manufacturers and use them as categories
        cursor.execute("SELECT DISTINCT manufacturer as category_name FROM Product WHERE manufacturer IS NOT NULL ORDER BY manufacturer")
        categories = cursor.fetchall()
        
        # Make it look like a proper category list with IDs
        result = [{'category_id': i+1, 'category_name': cat['category_name']} for i, cat in enumerate(categories)]
        
        cursor.close()
        connection.close()
        
        return jsonify(result)
    
    except Error as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/manufacturers', methods=['GET'])
def get_manufacturers():
    """Get all unique manufacturers"""
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT manufacturer FROM Product WHERE manufacturer IS NOT NULL ORDER BY manufacturer")
        manufacturers = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        connection.close()
        
        return jsonify(manufacturers)
    
    except Error as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create a new order when someone checks out"""
    try:
        data = request.json
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = connection.cursor()
        connection.start_transaction()  # Start a transaction so everything happens together
        
        try:
            # See if this customer already exists
            cursor.execute("SELECT customer_id FROM Customer WHERE email = %s", (data['customer']['email'],))
            customer_result = cursor.fetchone()
            
            if customer_result:
                # They're already a customer, use their ID
                customer_id = customer_result[0]
            else:
                # New customer, create them in the database
                cursor.execute(
                    """INSERT INTO Customer (first_name, last_name, email, phone, address, city, state, zip_code, customer_type)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (data['customer']['first_name'], data['customer']['last_name'],
                     data['customer']['email'], data['customer'].get('phone'),
                     data['shipping_address']['address'], data['shipping_address']['city'],
                     data['shipping_address']['state'], data['shipping_address']['zip_code'],
                     'regular')
                )
                customer_id = cursor.lastrowid
            
            # Add up the total cost
            total_amount = sum(item['price'] * item['quantity'] for item in data['items'])
            
            # Create the order record
            cursor.execute(
                """INSERT INTO `Order` (customer_id, order_date, order_type, total_amount, status, payment_method)
                   VALUES (%s, CURDATE(), 'online', %s, 'processing', %s)""",
                (customer_id, total_amount, 'credit_card')
            )
            order_id = cursor.lastrowid  # Get the ID of the order we just created
            
            # Add each item in the cart to the order
            for item in data['items']:
                cursor.execute(
                    """INSERT INTO OrderItem (order_id, product_id, quantity, unit_price, subtotal)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (order_id, item['product_id'], item['quantity'], item['price'],
                     item['price'] * item['quantity'])
                )
            
            # Create a shipment record so they can track it
            shipping_address = f"{data['shipping_address']['address']}, {data['shipping_address']['city']}, {data['shipping_address']['state']} {data['shipping_address']['zip_code']}"
            tracking_number = f"TRACK{order_id:06d}"  # Make a tracking number
            
            cursor.execute(
                """INSERT INTO Shipment (order_id, tracking_number, shipper, ship_date, estimated_delivery_date, status, shipping_address)
                   VALUES (%s, %s, 'USPS', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 5 DAY), 'pending', %s)""",
                (order_id, tracking_number, shipping_address)
            )
            
            connection.commit()
            
            cursor.close()
            connection.close()
            
            return jsonify({
                'order_id': order_id,
                'tracking_number': tracking_number,
                'message': 'Order created successfully'
            }), 201
        
        except Error as e:
            connection.rollback()
            cursor.close()
            connection.close()
            return jsonify({'error': str(e)}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Get orders for a customer by email"""
    try:
        email = request.args.get('email')
        if not email:
            return jsonify({'error': 'Email parameter required'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """SELECT o.* FROM `Order` o
               JOIN Customer c ON o.customer_id = c.customer_id
               WHERE c.email = %s
               ORDER BY o.order_date DESC""",
            (email,)
        )
        orders = cursor.fetchall()
        
        # Convert dates to strings so JSON can handle them
        for order in orders:
            if order['order_date']:
                order['order_date'] = order['order_date'].isoformat() if hasattr(order['order_date'], 'isoformat') else str(order['order_date'])
        
        cursor.close()
        connection.close()
        
        return jsonify(orders)
    
    except Error as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Electronics Vendor Web API...")
    print(f"Database: {DB_CONFIG_FULL['database']} on {DB_CONFIG_FULL['host']}")
    app.run(debug=True, host='0.0.0.0', port=5000)


-- Electronics Vendor Database Schema
-- CSC 411/511 DBMS Project

CREATE DATABASE IF NOT EXISTS electronics_vendor;
USE electronics_vendor;

-- ============================================
-- Customer Table
-- ============================================
CREATE TABLE Customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    customer_type ENUM('contract','regular') DEFAULT 'regular',
    account_number VARCHAR(20) NULL,
    address VARCHAR(100),
    city VARCHAR(50),
    state VARCHAR(50),
    zip_code VARCHAR(10)
);

-- ============================================
-- Product Table
-- ============================================
CREATE TABLE Product (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    description TEXT,
    manufacturer VARCHAR(50),
    price DECIMAL(10,2),
    weight DECIMAL(5,3),
    dimensions VARCHAR(50)
);

-- ============================================
-- Store Table
-- ============================================
CREATE TABLE Store (
    store_id INT AUTO_INCREMENT PRIMARY KEY,
    store_name VARCHAR(100),
    city VARCHAR(50),
    state VARCHAR(50)
);

-- ============================================
-- Warehouse Table
-- ============================================
CREATE TABLE Warehouse (
    warehouse_id INT AUTO_INCREMENT PRIMARY KEY,
    warehouse_name VARCHAR(100),
    city VARCHAR(50),
    state VARCHAR(50)
);

-- ============================================
-- Order Table
-- ============================================
CREATE TABLE `Order` (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    order_date DATE,
    order_type ENUM('online','in-store'),
    store_id INT NULL,
    total_amount DECIMAL(10,2),
    status ENUM('processing','shipped','delivered','cancelled'),
    payment_method VARCHAR(50),
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id),
    FOREIGN KEY (store_id) REFERENCES Store(store_id)
);

-- ============================================
-- OrderItem Table
-- ============================================
CREATE TABLE OrderItem (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    product_id INT,
    quantity INT,
    unit_price DECIMAL(10,2),
    subtotal DECIMAL(10,2),
    FOREIGN KEY (order_id) REFERENCES `Order`(order_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

-- ============================================
-- Shipment Table
-- ============================================
CREATE TABLE Shipment (
    shipment_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT UNIQUE,
    tracking_number VARCHAR(50),
    shipper VARCHAR(50),
    ship_date DATE,
    estimated_delivery_date DATE,
    actual_delivery_date DATE NULL,
    status ENUM('pending','shipped','delivered','cancelled'),
    shipping_address VARCHAR(200),
    FOREIGN KEY (order_id) REFERENCES `Order`(order_id)
);

-- ============================================
-- Inventory_Store Table
-- ============================================
CREATE TABLE Inventory_Store (
    inventory_store_id INT AUTO_INCREMENT PRIMARY KEY,
    store_id INT,
    product_id INT,
    quantity INT,
    reorder_level INT,
    FOREIGN KEY (store_id) REFERENCES Store(store_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

-- ============================================
-- Inventory_Warehouse Table
-- ============================================
CREATE TABLE Inventory_Warehouse (
    inventory_warehouse_id INT AUTO_INCREMENT PRIMARY KEY,
    warehouse_id INT,
    product_id INT,
    quantity INT,
    FOREIGN KEY (warehouse_id) REFERENCES Warehouse(warehouse_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

-- ============================================
-- Reorder Table
-- ============================================
CREATE TABLE Reorder (
    reorder_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    store_id INT NULL,
    warehouse_id INT NULL,
    reorder_date DATE,
    status ENUM('pending','completed'),
    FOREIGN KEY (product_id) REFERENCES Product(product_id),
    FOREIGN KEY (store_id) REFERENCES Store(store_id),
    FOREIGN KEY (warehouse_id) REFERENCES Warehouse(warehouse_id)
);

-- ============================================
-- Package Table
-- ============================================
CREATE TABLE Package (
    package_id INT AUTO_INCREMENT PRIMARY KEY,
    package_name VARCHAR(100)
);

-- ============================================
-- PackageItem Table
-- ============================================
CREATE TABLE PackageItem (
    package_item_id INT AUTO_INCREMENT PRIMARY KEY,
    package_id INT,
    product_id INT,
    FOREIGN KEY (package_id) REFERENCES Package(package_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);


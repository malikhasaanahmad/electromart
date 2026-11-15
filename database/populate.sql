USE electronics_vendor;

-- ============================================
-- Customers
-- ============================================
INSERT INTO Customer (first_name, last_name, email, phone, customer_type, account_number, address, city, state, zip_code)
VALUES
('John', 'Doe', 'john.doe@example.com', '555-1234', 'contract', 'ACCT1001', '123 Main St', 'Los Angeles', 'CA', '90001'),
('Jane', 'Smith', 'jane.smith@example.com', '555-5678', 'regular', NULL, '456 Oak Ave', 'San Francisco', 'CA', '94102'),
('Alice', 'Johnson', 'alice.johnson@example.com', '555-8765', 'contract', 'ACCT1002', '789 Pine Rd', 'New York', 'NY', '10001'),
('Bob', 'Brown', 'bob.brown@example.com', '555-4321', 'regular', NULL, '321 Maple St', 'Miami', 'FL', '33101');

-- ============================================
-- Products
-- ============================================
INSERT INTO Product (product_name, description, manufacturer, price, weight, dimensions)
VALUES
('iPhone 15 Pro', 'Latest iPhone with A17 Pro chip', 'Apple', 999.99, 0.187, '6.1" x 2.78" x 0.32"'),
('Samsung Galaxy S24', 'Flagship Android smartphone', 'Samsung', 899.99, 0.168, '5.79" x 2.78" x 0.30"'),
('MacBook Pro 16"', 'Professional laptop with M3 chip', 'Apple', 2499.99, 2.14, '14.01" x 9.77" x 0.66"'),
('Dell XPS 15', 'Premium Windows laptop', 'Dell', 1499.99, 1.92, '13.57" x 9.06" x 0.71"');

-- ============================================
-- Stores
-- ============================================
INSERT INTO Store (store_name, city, state)
VALUES
('LA Downtown', 'Los Angeles', 'CA'),
('SF Bay', 'San Francisco', 'CA'),
('Miami Central', 'Miami', 'FL');

-- ============================================
-- Warehouses
-- ============================================
INSERT INTO Warehouse (warehouse_name, city, state)
VALUES
('LA Warehouse', 'Los Angeles', 'CA'),
('NY Warehouse', 'New York', 'NY');

-- ============================================
-- Orders
-- ============================================
INSERT INTO `Order` (customer_id, order_date, order_type, store_id, total_amount, status, payment_method)
VALUES
(1, '2025-11-01', 'online', NULL, 1999.98, 'delivered', 'credit_card'),
(2, '2025-11-03', 'in-store', 2, 1499.99, 'delivered', 'cash');

-- ============================================
-- OrderItems
-- ============================================
INSERT INTO OrderItem (order_id, product_id, quantity, unit_price, subtotal)
VALUES
(1, 1, 1, 999.99, 999.99),
(1, 3, 1, 999.99, 999.99),
(2, 4, 1, 1499.99, 1499.99);

-- ============================================
-- Shipments
-- ============================================
INSERT INTO Shipment (order_id, tracking_number, shipper, ship_date, estimated_delivery_date, actual_delivery_date, status, shipping_address)
VALUES
(1, '123456', 'USPS', '2025-11-02', '2025-11-06', '2025-11-07', 'delivered', '123 Main St, Los Angeles, CA 90001'),
(2, '789012', 'FedEx', '2025-11-03', '2025-11-05', '2025-11-05', 'delivered', '456 Oak Ave, San Francisco, CA 94102');


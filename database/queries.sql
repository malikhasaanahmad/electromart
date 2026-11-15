-- Required Queries for Electronics Vendor Database
-- CSC 411/511 Database Management Systems Project

USE electronics_vendor;

-- ============================================
-- Query 1: Destroyed Shipment (Tracking #123456)
-- Find customer contact info, shipment contents, and create replacement
-- ============================================

-- Part A: Find customer contact information for destroyed shipment
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    c.phone,
    c.address,
    c.city,
    c.state,
    c.zip_code,
    s.tracking_number,
    s.shipper,
    s.ship_date,
    s.status
FROM Customer c
JOIN `Order` o ON c.customer_id = o.customer_id
JOIN Shipment s ON o.order_id = s.order_id
WHERE s.tracking_number = '123456';

-- Part B: Find contents of that shipment
SELECT 
    s.tracking_number,
    o.order_id,
    o.order_date,
    p.product_id,
    p.product_name,
    p.manufacturer,
    oi.quantity,
    oi.unit_price,
    oi.subtotal
FROM Shipment s
JOIN `Order` o ON s.order_id = o.order_id
JOIN OrderItem oi ON o.order_id = oi.order_id
JOIN Product p ON oi.product_id = p.product_id
WHERE s.tracking_number = '123456';

-- Part C: Create a new shipment of replacement items
-- First, create a new order for replacement
INSERT INTO `Order` (customer_id, order_date, order_type, store_id, total_amount, status, payment_method)
SELECT 
    o.customer_id,
    NOW() as order_date,
    'online' as order_type,
    NULL as store_id,
    o.total_amount,
    'processing' as status,
    'replacement' as payment_method
FROM `Order` o
JOIN Shipment s ON o.order_id = s.order_id
WHERE s.tracking_number = '123456';

-- Get the new order_id (assuming it's the last inserted)
SET @new_order_id = LAST_INSERT_ID();

-- Insert order items for replacement
INSERT INTO OrderItem (order_id, product_id, quantity, unit_price, subtotal)
SELECT 
    @new_order_id,
    oi.product_id,
    oi.quantity,
    oi.unit_price,
    oi.subtotal
FROM OrderItem oi
JOIN `Order` o ON oi.order_id = o.order_id
JOIN Shipment s ON o.order_id = s.order_id
WHERE s.tracking_number = '123456';

-- Create new shipment for replacement
INSERT INTO Shipment (order_id, tracking_number, shipper, ship_date, estimated_delivery_date, 
                      status, shipping_address)
SELECT 
    @new_order_id,
    CONCAT('REPLACE-', s.tracking_number) as tracking_number,
    s.shipper,
    CURDATE() as ship_date,
    DATE_ADD(CURDATE(), INTERVAL 5 DAY) as estimated_delivery_date,
    'pending' as status,
    s.shipping_address
FROM Shipment s
WHERE s.tracking_number = '123456';

-- Verify replacement order and shipment
SELECT 
    o.order_id,
    o.order_date,
    o.status,
    s.tracking_number,
    s.ship_date,
    s.estimated_delivery_date,
    s.status as shipment_status
FROM `Order` o
JOIN Shipment s ON o.order_id = s.order_id
WHERE o.order_id = @new_order_id;

-- ============================================
-- Query 2: Customer with Highest Purchases (Past Year)
-- ============================================
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    c.phone,
    c.customer_type,
    c.account_number,
    SUM(o.total_amount) as total_purchases,
    COUNT(o.order_id) as total_orders
FROM Customer c
JOIN `Order` o ON c.customer_id = o.customer_id
WHERE o.order_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
  AND o.status != 'cancelled'
GROUP BY c.customer_id, c.first_name, c.last_name, c.email, c.phone, c.customer_type, c.account_number
ORDER BY total_purchases DESC
LIMIT 1;

-- ============================================
-- Query 3: Top 2 Products by Dollar Amount Sold (Past Year)
-- ============================================
SELECT 
    p.product_id,
    p.product_name,
    p.manufacturer,
    SUM(oi.subtotal) as total_revenue,
    SUM(oi.quantity) as total_units_sold,
    COUNT(DISTINCT o.order_id) as number_of_orders
FROM Product p
JOIN OrderItem oi ON p.product_id = oi.product_id
JOIN `Order` o ON oi.order_id = o.order_id
WHERE o.order_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
  AND o.status != 'cancelled'
GROUP BY p.product_id, p.product_name, p.manufacturer
ORDER BY total_revenue DESC
LIMIT 2;

-- ============================================
-- Query 4: Top 2 Products by Unit Sales (Past Year)
-- ============================================
SELECT 
    p.product_id,
    p.product_name,
    p.manufacturer,
    SUM(oi.quantity) as total_units_sold,
    SUM(oi.subtotal) as total_revenue,
    COUNT(DISTINCT o.order_id) as number_of_orders
FROM Product p
JOIN OrderItem oi ON p.product_id = oi.product_id
JOIN `Order` o ON oi.order_id = o.order_id
WHERE o.order_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
  AND o.status != 'cancelled'
GROUP BY p.product_id, p.product_name, p.manufacturer
ORDER BY total_units_sold DESC
LIMIT 2;

-- ============================================
-- Query 5: Products Out-of-Stock at Every Store in California
-- ============================================
SELECT 
    p.product_id,
    p.product_name,
    p.manufacturer,
    p.price,
    COUNT(DISTINCT s.store_id) as california_stores,
    COUNT(DISTINCT CASE WHEN inv.quantity > 0 THEN inv.store_id END) as stores_with_stock,
    COUNT(DISTINCT CASE WHEN inv.quantity = 0 OR inv.quantity IS NULL THEN inv.store_id END) as stores_out_of_stock
FROM Product p
CROSS JOIN Store s
LEFT JOIN Inventory_Store inv ON p.product_id = inv.product_id AND s.store_id = inv.store_id
WHERE s.state = 'CA'
GROUP BY p.product_id, p.product_name, p.manufacturer, p.price
HAVING stores_with_stock = 0
   AND california_stores > 0
ORDER BY p.product_name;

-- Alternative query (more efficient):
SELECT 
    p.product_id,
    p.product_name,
    p.manufacturer,
    p.price
FROM Product p
WHERE NOT EXISTS (
    SELECT 1
    FROM Store s
    LEFT JOIN Inventory_Store inv ON s.store_id = inv.store_id AND p.product_id = inv.product_id
    WHERE s.state = 'CA'
      AND (inv.quantity IS NULL OR inv.quantity > 0)
)
AND EXISTS (
    SELECT 1
    FROM Store s
    WHERE s.state = 'CA'
)
ORDER BY p.product_name;

-- ============================================
-- Query 6: Packages Not Delivered Within Promised Time
-- ============================================
SELECT 
    s.shipment_id,
    s.tracking_number,
    s.shipper,
    s.ship_date,
    s.estimated_delivery_date,
    s.actual_delivery_date,
    s.status,
    DATEDIFF(s.actual_delivery_date, s.estimated_delivery_date) as days_late,
    o.order_id,
    o.order_date,
    c.first_name,
    c.last_name,
    c.email,
    c.phone
FROM Shipment s
JOIN `Order` o ON s.order_id = o.order_id
JOIN Customer c ON o.customer_id = c.customer_id
WHERE s.actual_delivery_date IS NOT NULL
  AND s.actual_delivery_date > s.estimated_delivery_date
ORDER BY days_late DESC;

-- Also include shipments that are past estimated delivery date but not yet delivered
SELECT 
    s.shipment_id,
    s.tracking_number,
    s.shipper,
    s.ship_date,
    s.estimated_delivery_date,
    s.actual_delivery_date,
    s.status,
    CASE 
        WHEN s.actual_delivery_date IS NOT NULL 
        THEN DATEDIFF(s.actual_delivery_date, s.estimated_delivery_date)
        ELSE DATEDIFF(CURDATE(), s.estimated_delivery_date)
    END as days_late_or_overdue,
    o.order_id,
    o.order_date,
    c.first_name,
    c.last_name,
    c.email,
    c.phone
FROM Shipment s
JOIN `Order` o ON s.order_id = o.order_id
JOIN Customer c ON o.customer_id = c.customer_id
WHERE (s.actual_delivery_date IS NOT NULL AND s.actual_delivery_date > s.estimated_delivery_date)
   OR (s.actual_delivery_date IS NULL AND CURDATE() > s.estimated_delivery_date)
ORDER BY days_late_or_overdue DESC;

-- ============================================
-- Query 7: Generate Monthly Bills for Contract Customers (Past Month)
-- ============================================
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    c.phone,
    c.account_number,
    c.address,
    c.city,
    c.state,
    c.zip_code,
    DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 1 MONTH), '%Y-%m-01') as billing_period_start,
    LAST_DAY(DATE_SUB(CURDATE(), INTERVAL 1 MONTH)) as billing_period_end,
    COUNT(o.order_id) as number_of_orders,
    SUM(o.total_amount) as total_amount,
    MIN(o.order_date) as first_order_date,
    MAX(o.order_date) as last_order_date,
    CONCAT('Bill for ', DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 1 MONTH), '%B %Y')) as bill_description
FROM Customer c
JOIN `Order` o ON c.customer_id = o.customer_id
WHERE c.customer_type = 'contract'
  AND o.order_date >= DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 1 MONTH), '%Y-%m-01')
  AND o.order_date <= LAST_DAY(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
  AND o.status != 'cancelled'
GROUP BY c.customer_id, c.first_name, c.last_name, c.email, c.phone, 
         c.account_number, c.address, c.city, c.state, c.zip_code
ORDER BY c.last_name, c.first_name;

-- Detailed bill with order breakdown
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    c.account_number,
    o.order_id,
    o.order_date,
    o.order_type,
    o.total_amount,
    o.status,
    GROUP_CONCAT(
        CONCAT(oi.quantity, 'x ', p.product_name, ' @ $', oi.unit_price, ' = $', oi.subtotal)
        SEPARATOR '; '
    ) as order_items
FROM Customer c
JOIN `Order` o ON c.customer_id = o.customer_id
JOIN OrderItem oi ON o.order_id = oi.order_id
JOIN Product p ON oi.product_id = p.product_id
WHERE c.customer_type = 'contract'
  AND o.order_date >= DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 1 MONTH), '%Y-%m-01')
  AND o.order_date <= LAST_DAY(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
  AND o.status != 'cancelled'
GROUP BY c.customer_id, c.first_name, c.last_name, c.account_number, 
         o.order_id, o.order_date, o.order_type, o.total_amount, o.status
ORDER BY c.last_name, c.first_name, o.order_date;

-- Summary bill per customer
SELECT 
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) as customer_name,
    c.account_number,
    c.email,
    c.address,
    CONCAT(c.city, ', ', c.state, ' ', c.zip_code) as city_state_zip,
    COUNT(DISTINCT o.order_id) as number_of_orders,
    SUM(o.total_amount) as monthly_total,
    DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 1 MONTH), '%B %Y') as billing_month
FROM Customer c
JOIN `Order` o ON c.customer_id = o.customer_id
WHERE c.customer_type = 'contract'
  AND o.order_date >= DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 1 MONTH), '%Y-%m-01')
  AND o.order_date <= LAST_DAY(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
  AND o.status != 'cancelled'
GROUP BY c.customer_id, c.first_name, c.last_name, c.account_number, 
         c.email, c.address, c.city, c.state, c.zip_code
ORDER BY monthly_total DESC;



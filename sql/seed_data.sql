
SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE orders;
TRUNCATE TABLE products;
TRUNCATE TABLE customers;

SET FOREIGN_KEY_CHECKS = 1;

-- Load customers
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/customers.csv'
INTO TABLE customers
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

-- Load products
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/products.csv'
INTO TABLE products
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

-- Load orders (with blank -> NULL handling for discount_pct and rating)
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/orders.csv'
INTO TABLE orders
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(order_id, customer_id, product_id, order_date, quantity, @discount_pct, payment_method, @rating, returned)
SET
  discount_pct = NULLIF(@discount_pct, ''),
  rating = NULLIF(@rating, '');



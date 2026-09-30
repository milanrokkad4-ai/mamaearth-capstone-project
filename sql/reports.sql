-- a) Order totals
-- Expected/actual output: total_orders = 180, total_revenue = 99860.20, avg_order_value = 554.78

select
    count(*) as total_orders,
    round(sum( quantity * price * (1 - coalesce(discount_pct, 0)/100) ), 2) as total_revenue,
    round(avg( quantity * price * (1 - coalesce(discount_pct, 0)/100) ), 2) as avg_order_value
from orders o
join products p on o.product_id = p.product_id;

-- b) COUNT(*) VS COUNT(column)
-- Expected/actual output: total_orders = 180, rated_orders = 165, missing_rating = 15

select 
  count(*) as total_orders, 
  count(rating) as rated_orders ,
  count(*) - count(rating) as missing_rating
from orders;

-- c) LEFT JOIN with a genuine zero-match row
-- Expected/actual output: C045, Vihaan

select C.customer_id, C.name from customers C
left join orders O on C.customer_id = O.customer_id
group by C.customer_id, C.name
having count(order_id) = 0;

select customer_id, name
from customers
where customer_id not in (
   select distinct customer_id from orders
);

-- d) GROUP BY + HAVING — join orders to customers, group by city, compute total_orders,
-- returned_orders, and return_rate_pct (rounded to 1 decimal), filter to return_rate_pct > 20,
-- ordered by return_rate_pct DESC
-- Output: Jaipur (19, 8, 42.1), Lucknow (49, 15, 30.6), Bangalore (33, 8, 24.2)

SELECT 
  C.city,
  count(*) as total_orders,
  sum(returned) as returned_orders,
  round(sum(returned) * 100.0 / count(*), 1) as return_rate_pct
  from orders O
  join customers C on C.customer_id = O.customer_id
  group by C.city
  having return_rate_pct > 20
  order by return_rate_pct desc;

-- e) Ranking with ORDER BY + LIMIT/OFFSET — join orders to products and customers, group by
-- customer, compute total_spend; order by total_spend DESC with customer_id ASC as a tiebreaker
-- (spend amounts could tie, so a secondary sort key keeps ranking deterministic).
-- Top 5 output: C043 Reyansh 12920.00, C026 Isha 8371.60, C008 Meera 4564.60,
-- C011 Arjun 4111.00, C042 Sanya 3785.00

select C.customer_id, C.name,
    round(sum(O.quantity * P.price * (1 - coalesce(O.discount_pct,0)/100)), 2) as total_spend
from orders O
join products P on O.product_id = P.product_id
join customers C on C.customer_id = O.customer_id
group by C.customer_id, C.name
order by total_spend desc, C.customer_id asc
limit 5;

-- Same query with LIMIT 3 OFFSET 2, to get ranks 3-5 without re-deriving the top 5.
-- Output: C008 Meera 4564.60, C011 Arjun 4111.00, C042 Sanya 3785.00 (last 3 of the top 5 above)
select C.customer_id, C.name,
    round(sum(O.quantity * P.price * (1 - coalesce(O.discount_pct,0)/100)), 2) as total_spend
from orders O
join products P on O.product_id = P.product_id
join customers C on C.customer_id = O.customer_id
group by C.customer_id, C.name
order by total_spend desc, C.customer_id asc
limit 3 offset 2;

-- f) three-table join — join orders to products and customers (customers not strictly
-- needed for this calc, but confirms the three-way join compiles cleanly for part 3);
-- group by category, compute order_count and category_revenue, ordered by revenue desc
-- output: haircare (54, 44956.10), skincare (60, 27346.00), babycare (30, 16805.00),
-- personalcare (36, 10753.10)

select p.category,
    count(*) as order_count,
    round(sum(o.quantity * p.price * (1 - coalesce(o.discount_pct,0)/100)), 2) as category_revenue
from orders o
join products p on o.product_id = p.product_id
join customers c on c.customer_id = o.customer_id
group by p.category
order by category_revenue desc;

-- g) LIKE pattern match — customers whose name starts with "A"
-- output: 10 rows (Aryan, Anika, Aditya, Aisha, Ayaan, Aria, and 4 more)

select customer_id, name
from customers
where name like 'A%';

-- h) DISTINCT — distinct acquisition_source values used across all customers
-- output: 4 values (Organic, Referral, Ad, Social)

select distinct acquisition_source
from customers;

-- i) ALTER + UPDATE with CASE — add loyalty_tier column, populate every row: Gold for
-- tier-1 cities, else Silver (no WHERE clause — every row gets a value)
-- Note: required disabling MySQL Workbench's safe update mode (set sql_safe_updates = 0)
-- since this UPDATE intentionally has no WHERE clause on a key column
-- output: Gold = 28, Silver = 17

alter table customers
add loyalty_tier varchar(10);

update customers
set loyalty_tier = case when city_tier = 1 then 'Gold' else 'Silver' end;

-- verification (not part of the required task, just confirms the UPDATE above worked):
select loyalty_tier, count(*)
from customers
group by loyalty_tier;



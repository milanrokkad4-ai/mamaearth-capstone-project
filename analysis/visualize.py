"""
Mamaearth Returns & Growth Intelligence Pipeline
Part 2, Task 11: Visualizations

Run this script from the repository root: python analysis/visualize.py
Independent pandas pipeline over the same raw source files, so this script
can be run on its own and still regenerate identical PNGs. Re-runs end to
end from the raw CSVs.
"""

import pandas as pd
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Recreate the cleaned, merged, outlier-flagged frame (mirrors clean_and_eda.py
# Tasks 1-6, so this script does not depend on clean_and_eda.py having been
# run first)
# ---------------------------------------------------------------------------
customers = pd.read_csv('data/customers.csv')
products = pd.read_csv('data/products.csv')
orders = pd.read_csv('data/orders.csv')

orders['payment_method'] = orders['payment_method'].str.strip().str.upper()

duplicate_mask = orders.duplicated(
    subset=['customer_id', 'product_id', 'order_date', 'quantity',
            'discount_pct', 'payment_method', 'rating', 'returned'],
    keep='first'
)
orders_clean = orders[~duplicate_mask].reset_index(drop=True)

rating_median = orders_clean['rating'].median()
orders_clean['discount_pct'] = orders_clean['discount_pct'].fillna(0)
orders_clean['rating'] = orders_clean['rating'].fillna(rating_median)

merged = orders_clean.merge(products, on='product_id').merge(customers, on='customer_id')
merged['order_value'] = merged['quantity'] * merged['price'] * (1 - merged['discount_pct'] / 100)

q1 = merged['quantity'].quantile(0.25)
q3 = merged['quantity'].quantile(0.75)
iqr = q3 - q1
lower = q1 - 1.5 * iqr
upper = q3 + 1.5 * iqr
merged['is_outlier'] = (merged['quantity'] < lower) | (merged['quantity'] > upper)

merged['order_date'] = pd.to_datetime(merged['order_date'])
merged['year_month'] = merged['order_date'].dt.to_period('M')
monthly_without_outliers = merged[~merged['is_outlier']].groupby('year_month')['order_value'].sum().round(2)


# ---------------------------------------------------------------------------
# Chart 1: Return rate by (cleaned) payment_method, descending
# ---------------------------------------------------------------------------
payment_rates = merged.groupby('payment_method')['returned'].mean().mul(100).round(1).sort_values(ascending=False)

plt.figure(figsize=(7, 5))
bars = plt.bar(payment_rates.index, payment_rates.values, color=['#d62728', '#1f77b4', '#2ca02c'])
for bar, rate in zip(bars, payment_rates.values):
    plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5, f"{rate}%", ha='center')
plt.title(f"COD Returns at {payment_rates.max()}% — "
          f"{round(payment_rates.max() / payment_rates.min(), 1)}x Card")
plt.xlabel("Payment Method")
plt.ylabel("Return Rate (%)")
plt.tight_layout()
plt.savefig('visualizations/return_rate_by_payment.png')
plt.close()


# ---------------------------------------------------------------------------
# Chart 2: Outlier-corrected monthly revenue trend
# ---------------------------------------------------------------------------
plt.figure(figsize=(8, 5))
plt.plot(monthly_without_outliers.index.astype(str), monthly_without_outliers.values,
          marker='o', color='#2ca02c')
peak_month = monthly_without_outliers.idxmax()
plt.title(f"Monthly Revenue Trend (Outlier-Corrected) — Peak: {peak_month}")
plt.xlabel("Month")
plt.ylabel("Revenue (INR)")
plt.tight_layout()
plt.savefig('visualizations/monthly_revenue_trend.png')
plt.close()

print("Saved visualizations/return_rate_by_payment.png and visualizations/monthly_revenue_trend.png")

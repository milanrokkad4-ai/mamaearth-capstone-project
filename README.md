# Mamaearth Returns & Growth Intelligence Pipeline

**Program:** Data Analytics with AI & Gen AI · E&ICT Academy IIT Roorkee

## Scenario

Mamaearth's Growth Analytics team suspects that returns are eating into margins on a
subset of orders, but nobody has built the pipeline to prove it end to end. This repo
builds all three layers, wired into one connected pipeline — the SQL layer feeds the
Python analysis layer, and the analysis layer's verified numbers feed the GenAI
narrative layer. No layer reports a number it did not itself compute or receive from
the layer before it.

## Repo structure

```
.
├── README.md
├── sql/
│   ├── schema.sql        Part 1, Task 1 — table definitions
│   ├── seed_data.sql     Part 1, Task 2 — loads data/*.csv via INSERT statements
│   └── reports.sql       Part 1, Task 3 — nine business reports (a–i)
├── data/
│   ├── customers.csv
│   ├── products.csv
│   └── orders.csv
├── analysis/
│   ├── clean_and_eda.py  Part 2, Tasks 1–10 — cleaning, reconciliation, EDA;
│   │                     also writes narrator/findings.json (Part 3, Task 1)
│   └── visualize.py      Part 2, Task 11 — two charts, independently runnable
├── visualizations/
│   ├── return_rate_by_payment.png
│   └── monthly_revenue_trend.png
└── narrator/
    ├── findings.json       verified figures from Parts 1–2, written by code
    ├── generate_narrative.py  Part 3, Tasks 2–5 — online + offline SCR narrative,
    │                          plus the numeric accuracy checker
    └── sample_output.txt   a saved, genuine online Gemini run (for grading
                             without needing a live API call or key)
```

## A note on SQL engine

The brief allows "SQLite or any SQL engine that supports the exact syntax below."
This project uses **MySQL (MySQL Workbench)** instead of SQLite, since MySQL is what
was taught in this course. All queries and the schema use standard SQL syntax that
runs correctly in MySQL. The one place this matters practically: `seed_data.sql`
loads data via self-contained `INSERT` statements (not SQLite's `.import` or
MySQL's `LOAD DATA INFILE`), specifically so the script runs on any machine with no
local file-path setup required.

---

## How to run the pipeline, step by step

### 1. SQL layer (`sql/`)

Requires MySQL (e.g. MySQL Workbench) connected to a local server.

1. Create and select a database, e.g.:
   ```sql
   CREATE DATABASE mamaearth_capstone;
   USE mamaearth_capstone;
   ```
2. Run **`sql/schema.sql`** — creates the `customers`, `products`, and `orders`
   tables with the correct types, constraints, and foreign keys.
3. Run **`sql/seed_data.sql`** — truncates and reloads all three tables via
   `INSERT` statements generated directly from `data/*.csv`. Verification
   queries at the end of the script confirm the load:
   - `customers`: 45 rows
   - `products`: 16 rows
   - `orders`: 180 rows, with 12 NULL `discount_pct` and 15 NULL `rating`
     (genuine missing values, not zeros)
4. Run **`sql/reports.sql`** — nine business reports (a–i). Each query has its
   expected output pasted as a comment directly above it, so you can confirm
   your results match before moving on. Key figures: total revenue ₹99,860.20
   across 180 raw orders; Jaipur/Lucknow/Bangalore are the three cities with a
   return rate above 20%; customer C045 (Vihaan) is the one customer with zero
   orders; the `loyalty_tier` column added in query (i) ends with 28 Gold and
   17 Silver customers.

### 2. Python layer (`analysis/`)

Requires Python 3 with `pandas` and `matplotlib` installed (`pip install pandas
matplotlib`). These scripts read the raw CSVs directly from `data/` — they do
not depend on the SQL layer or database having been run first, so Part 1 and
Part 2 can be run in either order.

Run both scripts **from the repository root**:

```bash
python analysis/clean_and_eda.py
python analysis/visualize.py
```

- **`clean_and_eda.py`** runs all 11 tasks of Part 2 in order: loads the raw
  data, standardizes `payment_method` casing, removes 5 duplicate orders,
  imputes missing `discount_pct`/`rating`, merges and reconciles against
  Part 1's raw total (cleaned total ₹97,358.30 — a ₹2,501.90 difference
  explained entirely by the 5 duplicates removed), flags 2 quantity outliers
  via the IQR rule, tests and confirms the COD-returns hypothesis (COD 44.4%
  vs CARD 14.7% vs UPI 18.9%), segments return rate by payment method and
  city tier (COD + Tier-2 is the highest-risk segment at 54.5%), runs a
  correlation analysis (all pairs negligible), and builds the
  outlier-corrected monthly revenue trend (true peak: March 2026 at
  ₹20,318.90, once the two outlier orders are excluded).

  At the end, this script also writes **`narrator/findings.json`** — the
  verified figures above, written by code so they can never drift from the
  numbers actually computed in this script.

- **`visualize.py`** independently re-derives the cleaned, merged data (so it
  can be run on its own) and saves two PNGs to `visualizations/`:
  `return_rate_by_payment.png` (bar chart, COD/UPI/CARD) and
  `monthly_revenue_trend.png` (line chart, outlier-corrected, March peak).

### 3. GenAI layer (`narrator/`)

Requires the `google-genai` Python package (`pip install google-genai`) and,
for the live API path, a **free** Gemini API key from
[Google AI Studio](https://aistudio.google.com).

**To use the live Gemini API**, set your key as an environment variable before
running:

```bash
export GEMINI_API_KEY="your-key-here"   # macOS/Linux
set GEMINI_API_KEY=your-key-here        # Windows (cmd)
python narrator/generate_narrative.py
```

**To run with no API key at all** (zero cost, zero network access, zero
setup), simply don't set the environment variable:

```bash
python narrator/generate_narrative.py
```

Either way, running the script:
1. Reads the verified figures from `narrator/findings.json`
2. Calls `generate_scr_narrative(findings)`, which uses the live Gemini API
   if a key is set, and automatically falls back to
   `generate_scr_narrative_offline(findings)` — a deterministic,
   template-based narrative requiring no network access — if no key is set,
   or if the live call fails for any reason (the function always returns the
   same dict shape either way: `status`, `narrative`, `tokens`, `source`)
3. Prints the resulting Situation–Complication–Resolution narrative
4. If the narrative came from a genuine live API call, saves it to
   `narrator/sample_output.txt` (an offline fallback result never overwrites
   this file, so a known-good, already-graded sample is preserved)
5. Runs `check_numeric_accuracy()`, which confirms five key figures — the
   cleaned total revenue, the COD return rate, the highest-risk segment's
   return rate, the reconciliation delta, and the true peak month (name and
   revenue) — are all present in the narrative text, and prints a pass/fail
   line for each

`narrator/sample_output.txt` is a saved, genuine output from a successful live
Gemini run, included so the numeric accuracy check can be verified by a reader
without needing their own API key.

---

## Reproducing every number in this brief

Running the three layers in the order above (SQL → Python → GenAI) reproduces
every figure referenced throughout this README: the 180 raw orders, the
₹99,860.20 raw and ₹97,358.30 cleaned revenue totals, the 44.4% COD return
rate and 54.5% COD/Tier-2 segment rate, and the March 2026 true peak month —
each number computed once, in one layer, and passed forward rather than
recalculated or restated independently in the layers after it.

"""
# DATA FOR TRADERS
# https://datafortraders.io/
https://x.com/datafortraders

S&P 500 Monday/3rd‑Friday Analysis
---------------------------------
1.  Up vs Down **Mondays** (close vs previous‑close)  
2.  Up vs Down **Monday after the 3 rd Friday** of each month  
   (Monday‑close vs that Friday‑close)

# BE SURE TO CHANGE FILE PATH CSV TO YOUR LOCAL HISTORICAL DATA FILE.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# ──────────────────────────────────────────────────────────────────────────────
#  LOAD & PREP
# ──────────────────────────────────────────────────────────────────────────────
FILE = Path("YOUR CSV FILE HERE")  # change if needed

df = pd.read_csv(FILE)
df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values("Date").reset_index(drop=True)

# prices are strings like "$5,512.35" → strip "$" / "," and convert to float
df["Close"] = (
    df["Close/Last"]
    .replace({r"[\$,]": ""}, regex=True)
    .astype(float)
)

# handy calendar columns
df["Weekday"] = df["Date"].dt.day_name()
df["Year"] = df["Date"].dt.year
df["Month"] = df["Date"].dt.month


# ──────────────────────────────────────────────────────────────────────────────
#  (A) ORDINARY MONDAYS  ─ compare Monday‑close to previous‑close
# ──────────────────────────────────────────────────────────────────────────────
def count_up_down_mondays(start: datetime | None, end: datetime | None):
    """Return (#up, #down, #mondays) between start & end (inclusive)."""
    subset = df
    if start:
        subset = subset[subset["Date"] >= start]
    if end:
        subset = subset[subset["Date"] <= end]

    # filter Mondays & join with previous trading‑day close
    mondays = subset[subset["Weekday"] == "Monday"].copy()
    mondays["Prev_Close"] = mondays["Close"].shift()
    mondays = mondays.dropna(subset=["Prev_Close"])

    up = (mondays["Close"] > mondays["Prev_Close"]).sum()
    down = (mondays["Close"] < mondays["Prev_Close"]).sum()
    total = len(mondays)

    return up, down, total


# ──────────────────────────────────────────────────────────────────────────────
#  (B) 3RD‑FRIDAY ➜ NEXT MONDAY  ─ compare Monday‑close to that Friday‑close
# ──────────────────────────────────────────────────────────────────────────────
def count_thirdfriday_pairs(start: datetime | None, end: datetime | None):
    """Return (#up, #down, #pairs) between start & end (inclusive)."""
    subset = df
    if start:
        subset = subset[subset["Date"] >= start]
    if end:
        subset = subset[subset["Date"] <= end]

    pairs = []

    # iterate month‑by‑month
    for (yr, mo), group in subset.groupby(["Year", "Month"]):
        fridays = group[group["Weekday"] == "Friday"].sort_values("Date")
        if len(fridays) < 3:
            continue  # no 3rd Friday in truncated months

        third_friday = fridays.iloc[2]

        # the following calendar Monday
        monday_date = third_friday["Date"] + timedelta(days=3)
        mon_row = subset[subset["Date"] == monday_date]
        if mon_row.empty:
            continue  # holiday Monday → skip this month

        friday_close = third_friday["Close"]
        monday_close = mon_row.iloc[0]["Close"]

        pairs.append(monday_close > friday_close)

    up = sum(pairs)
    down = len(pairs) - up
    return up, down, len(pairs)


# ──────────────────────────────────────────────────────────────────────────────
#  RUN COUNTS
# ──────────────────────────────────────────────────────────────────────────────
TODAY = datetime(2025, 5, 16)  # adjust if you run later
one_year_ago = TODAY - timedelta(days=365)
five_years_ago = TODAY - timedelta(days=365 * 5)

windows = {
    "1 year":  (one_year_ago, TODAY),
    "5 years": (five_years_ago, TODAY),
    "10 years (full file)": (df["Date"].min(), TODAY),
}

print("A)  ORDINARY MONDAYS (close vs prev close)")
for label, (start, end) in windows.items():
    up, down, total = count_up_down_mondays(start, end)
    print(f"{label:20s}:  up={up:<3}  down={down:<3}  total={total}")

print("\nB)  3rd‑FRIDAY ➜ NEXT MONDAY (Mon close vs Fri close)")
for label, (start, end) in windows.items():
    up, down, total = count_thirdfriday_pairs(start, end)
    print(f"{label:20s}:  up={up:<3}  down={down:<3}  total={total}")

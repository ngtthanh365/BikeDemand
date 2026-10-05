import os
import sys

import pandas as pd


# =========================
# 0. PROJECT PATH
# =========================

# Cho phép import module database từ project root
PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.postgres import load_hourly_demand


# =========================
# 1. CONFIG
# =========================

OUTPUT_DIR = "analysis/outputs/ml"
OUTPUT_FILE = f"{OUTPUT_DIR}/citibike_ml_dataset.csv"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# =========================
# 2. LOAD DATA
#    FROM POSTGRESQL
# =========================

print("=" * 70)
print("FEATURE ENGINEERING 01 - CREATE ML DATASET")
print("=" * 70)

df = load_hourly_demand()

print(f"\nPostgreSQL hourly rows: {len(df):,}")


# =========================
# 3. PREPARE HOURLY DEMAND
# =========================

# Đảm bảo timestamp đúng kiểu datetime
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Chỉ lấy dữ liệu cần thiết cho ML
hourly = df[
    [
        "timestamp",
        "demand"
    ]
].copy()

# Đổi tên để tương thích với pipeline ML hiện tại
hourly = hourly.rename(
    columns={
        "timestamp": "datetime",
        "demand": "total_trips"
    }
)

hourly["date"] = hourly["datetime"].dt.date
hourly["hour"] = hourly["datetime"].dt.hour

hourly = hourly[
    [
        "date",
        "hour",
        "total_trips"
    ]
]


# =========================
# 4. CREATE COMPLETE
#    DATE-HOUR TIMELINE
# =========================

start_date = pd.Timestamp("2026-01-01")
end_date = pd.Timestamp("2026-06-30 23:00:00")

full_datetime = pd.date_range(
    start=start_date,
    end=end_date,
    freq="h"
)

calendar = pd.DataFrame({
    "datetime": full_datetime
})

calendar["date"] = calendar["datetime"].dt.date
calendar["hour"] = calendar["datetime"].dt.hour

# Pandas:
# Monday = 0
# Tuesday = 1
# ...
# Sunday = 6
calendar["day_of_week"] = (
    calendar["datetime"].dt.dayofweek
)

calendar["month"] = (
    calendar["datetime"].dt.month
)


# =========================
# 5. MERGE DEMAND
# =========================

ml_df = calendar.merge(
    hourly,
    on=["date", "hour"],
    how="left"
)

# Những giờ không có chuyến đi không xuất hiện
# trong hourly_demand của PostgreSQL.
# Vì vậy demand của các giờ này = 0.
ml_df["total_trips"] = (
    ml_df["total_trips"]
    .fillna(0)
    .astype(int)
)


# =========================
# 6. HISTORICAL FEATURES
# =========================

# Demand from previous hour
ml_df["lag_1"] = (
    ml_df["total_trips"]
    .shift(1)
)

# Demand from 24 hours ago
ml_df["lag_24"] = (
    ml_df["total_trips"]
    .shift(24)
)

# Demand from 168 hours ago
# Same hour, previous week
ml_df["lag_168"] = (
    ml_df["total_trips"]
    .shift(168)
)


# =========================
# 7. ROLLING FEATURES
# =========================

# Average demand over previous 24 hours
ml_df["rolling_24h"] = (
    ml_df["total_trips"]
    .shift(1)
    .rolling(window=24)
    .mean()
)

# Average demand over previous 7 days
ml_df["rolling_7d"] = (
    ml_df["total_trips"]
    .shift(1)
    .rolling(window=168)
    .mean()
)


# =========================
# 8. COLUMN ORDER
# =========================

ml_df = ml_df[
    [
        "datetime",
        "date",
        "hour",
        "day_of_week",
        "month",
        "total_trips",
        "lag_1",
        "lag_24",
        "lag_168",
        "rolling_24h",
        "rolling_7d"
    ]
]


# =========================
# 9. REMOVE ROWS
#    WITHOUT HISTORY
# =========================

before = len(ml_df)

ml_df = ml_df.dropna(
    subset=[
        "lag_1",
        "lag_24",
        "lag_168",
        "rolling_24h",
        "rolling_7d"
    ]
).reset_index(drop=True)

removed = before - len(ml_df)


# =========================
# 10. SAVE
# =========================

ml_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================
# 11. VALIDATION
# =========================

print("\n" + "=" * 70)
print("ML DATASET SUMMARY")
print("=" * 70)

print(f"Original hourly rows: {before:,}")
print(f"Rows removed: {removed:,}")
print(f"Final ML rows: {len(ml_df):,}")

print(
    f"\nDatetime range:"
    f"\n  MIN: {ml_df['datetime'].min()}"
    f"\n  MAX: {ml_df['datetime'].max()}"
)

print("\nColumns:")
print(ml_df.columns.tolist())

print("\nMissing values:")
print(ml_df.isnull().sum())

print("\nFirst 10 rows:")
print(
    ml_df.head(10).to_string(
        index=False
    )
)

print("\nLast 10 rows:")
print(
    ml_df.tail(10).to_string(
        index=False
    )
)

print("\nTarget statistics:")
print(
    ml_df["total_trips"].describe()
)

print("\nOutput:")
print(f"  {OUTPUT_FILE}")

print(
    "\nFeature Engineering 01 "
    "completed successfully."
)
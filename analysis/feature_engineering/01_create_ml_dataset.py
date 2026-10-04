import os
import pandas as pd


# =========================
# 1. CONFIG
# =========================

INPUT_FILE = "data/processed/citibike_2026_H1.csv"

OUTPUT_DIR = "analysis/outputs/ml"
OUTPUT_FILE = f"{OUTPUT_DIR}/citibike_ml_dataset.csv"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# =========================
# 2. LOAD DATA
# =========================

print("=" * 70)
print("FEATURE ENGINEERING 01 - CREATE ML DATASET")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

print(f"\nRaw rows: {len(df):,}")


# =========================
# 3. DATETIME
# =========================

df["started_at"] = pd.to_datetime(df["started_at"])

df["date"] = df["started_at"].dt.date
df["hour"] = df["started_at"].dt.hour
df["day_of_week"] = df["started_at"].dt.dayofweek
df["month"] = df["started_at"].dt.month


# =========================
# 4. HOURLY DEMAND
# =========================

hourly = (
    df.groupby(
        ["date", "hour"],
        as_index=False
    )
    .size()
    .rename(columns={"size": "total_trips"})
)


# =========================
# 5. CREATE COMPLETE
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
calendar["day_of_week"] = calendar["datetime"].dt.dayofweek
calendar["month"] = calendar["datetime"].dt.month


# =========================
# 6. MERGE DEMAND
# =========================

ml_df = calendar.merge(
    hourly,
    on=["date", "hour"],
    how="left"
)

ml_df["total_trips"] = (
    ml_df["total_trips"]
    .fillna(0)
    .astype(int)
)


# =========================
# 7. HISTORICAL FEATURES
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
# 8. ROLLING FEATURES
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
# 9. DATETIME STRING
# =========================

ml_df["datetime"] = pd.to_datetime(
    ml_df["date"].astype(str)
    + " "
    + ml_df["hour"].astype(str)
    + ":00:00"
)


# =========================
# 10. COLUMN ORDER
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
# 11. REMOVE ROWS
#     WITHOUT HISTORY
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
# 12. SAVE
# =========================

ml_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================
# 13. VALIDATION
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
print(ml_df.head(10).to_string(index=False))

print("\nLast 10 rows:")
print(ml_df.tail(10).to_string(index=False))

print("\nTarget statistics:")
print(ml_df["total_trips"].describe())

print("\nOutput:")
print(f"  {OUTPUT_FILE}")

print("\nFeature Engineering 01 completed successfully.")
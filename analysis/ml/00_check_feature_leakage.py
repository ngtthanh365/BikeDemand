import pandas as pd


# =========================
# 1. CONFIG
# =========================

RAW_FILE = "data/processed/citibike_2026_H1.csv"
ML_FILE = "analysis/outputs/ml/citibike_ml_dataset.csv"


# =========================
# 2. LOAD RAW DATA
# =========================

print("=" * 70)
print("ML 00 - FEATURE LEAKAGE CHECK")
print("=" * 70)

raw = pd.read_csv(RAW_FILE)

raw["started_at"] = pd.to_datetime(raw["started_at"])

raw["date"] = raw["started_at"].dt.date
raw["hour"] = raw["started_at"].dt.hour

print(f"\nRaw rows: {len(raw):,}")


# =========================
# 3. CREATE FULL HOURLY DATA
# =========================

hourly = (
    raw.groupby(
        ["date", "hour"],
        as_index=False
    )
    .size()
    .rename(columns={"size": "total_trips"})
)

full_datetime = pd.date_range(
    start="2026-01-01 00:00:00",
    end="2026-06-30 23:00:00",
    freq="h"
)

calendar = pd.DataFrame({
    "datetime": full_datetime
})

calendar["date"] = calendar["datetime"].dt.date
calendar["hour"] = calendar["datetime"].dt.hour

full = calendar.merge(
    hourly,
    on=["date", "hour"],
    how="left"
)

full["total_trips"] = (
    full["total_trips"]
    .fillna(0)
    .astype(int)
)


# =========================
# 4. RECREATE FEATURES
# =========================

full["lag_1_expected"] = (
    full["total_trips"].shift(1)
)

full["lag_24_expected"] = (
    full["total_trips"].shift(24)
)

full["lag_168_expected"] = (
    full["total_trips"].shift(168)
)

full["rolling_24h_expected"] = (
    full["total_trips"]
    .shift(1)
    .rolling(24)
    .mean()
)

full["rolling_7d_expected"] = (
    full["total_trips"]
    .shift(1)
    .rolling(168)
    .mean()
)


# =========================
# 5. LOAD ML DATASET
# =========================

ml = pd.read_csv(ML_FILE)

ml["datetime"] = pd.to_datetime(
    ml["datetime"]
)

ml = ml.sort_values(
    "datetime"
).reset_index(drop=True)


# =========================
# 6. MERGE EXPECTED VALUES
# =========================

expected = full[
    [
        "datetime",
        "lag_1_expected",
        "lag_24_expected",
        "lag_168_expected",
        "rolling_24h_expected",
        "rolling_7d_expected"
    ]
]

check = ml.merge(
    expected,
    on="datetime",
    how="left"
)


# =========================
# 7. CHECK LAGS
# =========================

print("\n" + "=" * 70)
print("CHECK LAG FEATURES")
print("=" * 70)


lag_1_error = (
    check["lag_1"]
    - check["lag_1_expected"]
).abs().dropna().max()

lag_24_error = (
    check["lag_24"]
    - check["lag_24_expected"]
).abs().dropna().max()

lag_168_error = (
    check["lag_168"]
    - check["lag_168_expected"]
).abs().dropna().max()


print(
    f"Maximum lag_1 difference:   "
    f"{lag_1_error}"
)

print(
    f"Maximum lag_24 difference:  "
    f"{lag_24_error}"
)

print(
    f"Maximum lag_168 difference: "
    f"{lag_168_error}"
)


lag_check = (
    lag_1_error < 0.000001
    and lag_24_error < 0.000001
    and lag_168_error < 0.000001
)

print(
    f"\nLag features correct: "
    f"{lag_check}"
)


# =========================
# 8. CHECK ROLLING FEATURES
# =========================

print("\n" + "=" * 70)
print("CHECK ROLLING FEATURES")
print("=" * 70)


rolling_24_error = (
    check["rolling_24h"]
    - check["rolling_24h_expected"]
).abs().dropna().max()

rolling_7_error = (
    check["rolling_7d"]
    - check["rolling_7d_expected"]
).abs().dropna().max()


print(
    f"Maximum rolling_24h difference: "
    f"{rolling_24_error}"
)

print(
    f"Maximum rolling_7d difference:  "
    f"{rolling_7_error}"
)


rolling_check = (
    rolling_24_error < 0.000001
    and rolling_7_error < 0.000001
)

print(
    f"\nRolling features correct: "
    f"{rolling_check}"
)


# =========================
# 9. CHECK TIME SPLIT
# =========================

print("\n" + "=" * 70)
print("CHECK TIME-BASED SPLIT")
print("=" * 70)

train = pd.read_csv(
    "analysis/outputs/ml/train.csv"
)

validation = pd.read_csv(
    "analysis/outputs/ml/validation.csv"
)

test = pd.read_csv(
    "analysis/outputs/ml/test.csv"
)

train["datetime"] = pd.to_datetime(
    train["datetime"]
)

validation["datetime"] = pd.to_datetime(
    validation["datetime"]
)

test["datetime"] = pd.to_datetime(
    test["datetime"]
)


train_end = train["datetime"].max()
validation_start = validation["datetime"].min()

validation_end = validation["datetime"].max()
test_start = test["datetime"].min()


print(
    f"Train end:        {train_end}"
)

print(
    f"Validation start: {validation_start}"
)

print(
    f"Validation end:   {validation_end}"
)

print(
    f"Test start:       {test_start}"
)


time_check = (
    train_end < validation_start
    and validation_end < test_start
)


print(
    f"\nTime order correct: "
    f"{time_check}"
)


# =========================
# 10. FINAL RESULT
# =========================

print("\n" + "=" * 70)
print("FINAL LEAKAGE CHECK")
print("=" * 70)


all_checks = (
    lag_check
    and rolling_check
    and time_check
)


if all_checks:
    print("RESULT: PASS")
    print("No feature leakage detected.")
else:
    print("RESULT: FAIL")
    print("Please inspect the feature engineering pipeline.")
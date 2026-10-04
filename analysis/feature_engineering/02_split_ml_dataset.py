import os
import pandas as pd


# =========================
# 1. CONFIG
# =========================

INPUT_FILE = "analysis/outputs/ml/citibike_ml_dataset.csv"

OUTPUT_DIR = "analysis/outputs/ml"

TRAIN_FILE = f"{OUTPUT_DIR}/train.csv"
VALIDATION_FILE = f"{OUTPUT_DIR}/validation.csv"
TEST_FILE = f"{OUTPUT_DIR}/test.csv"


# =========================
# 2. LOAD DATA
# =========================

print("=" * 70)
print("FEATURE ENGINEERING 02 - TRAIN / VALIDATION / TEST SPLIT")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

df["datetime"] = pd.to_datetime(df["datetime"])

df = df.sort_values("datetime").reset_index(drop=True)

print(f"\nTotal rows: {len(df):,}")


# =========================
# 3. DEFINE TIME PERIODS
# =========================

train_end = pd.Timestamp("2026-05-31 23:00:00")

validation_start = pd.Timestamp("2026-06-01 00:00:00")
validation_end = pd.Timestamp("2026-06-15 23:00:00")

test_start = pd.Timestamp("2026-06-16 00:00:00")
test_end = pd.Timestamp("2026-06-30 23:00:00")


# =========================
# 4. SPLIT
# =========================

train = df[
    df["datetime"] <= train_end
].copy()

validation = df[
    (df["datetime"] >= validation_start)
    & (df["datetime"] <= validation_end)
].copy()

test = df[
    (df["datetime"] >= test_start)
    & (df["datetime"] <= test_end)
].copy()


# =========================
# 5. SAVE
# =========================

train.to_csv(TRAIN_FILE, index=False)
validation.to_csv(VALIDATION_FILE, index=False)
test.to_csv(TEST_FILE, index=False)


# =========================
# 6. VALIDATION
# =========================

print("\n" + "=" * 70)
print("DATA SPLIT SUMMARY")
print("=" * 70)

print("\nTRAIN")
print(f"Rows: {len(train):,}")
print(f"From: {train['datetime'].min()}")
print(f"To:   {train['datetime'].max()}")

print("\nVALIDATION")
print(f"Rows: {len(validation):,}")
print(f"From: {validation['datetime'].min()}")
print(f"To:   {validation['datetime'].max()}")

print("\nTEST")
print(f"Rows: {len(test):,}")
print(f"From: {test['datetime'].min()}")
print(f"To:   {test['datetime'].max()}")


# =========================
# 7. CHECK OVERLAP
# =========================

train_max = train["datetime"].max()
validation_min = validation["datetime"].min()
validation_max = validation["datetime"].max()
test_min = test["datetime"].min()

print("\n" + "=" * 70)
print("TIME ORDER CHECK")
print("=" * 70)

print(
    f"Train ends before validation: "
    f"{train_max < validation_min}"
)

print(
    f"Validation ends before test: "
    f"{validation_max < test_min}"
)


# =========================
# 8. TARGET STATISTICS
# =========================

print("\n" + "=" * 70)
print("TARGET STATISTICS")
print("=" * 70)

print("\nTrain:")
print(train["total_trips"].describe())

print("\nValidation:")
print(validation["total_trips"].describe())

print("\nTest:")
print(test["total_trips"].describe())


# =========================
# 9. OUTPUT
# =========================

print("\n" + "=" * 70)
print("OUTPUT FILES")
print("=" * 70)

print(TRAIN_FILE)
print(VALIDATION_FILE)
print(TEST_FILE)

print("\nFeature Engineering 02 completed successfully.")
import os
import sys

import pandas as pd


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(
        0,
        PROJECT_ROOT
    )


from database.postgres import save_predictions


# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = (
    "analysis/outputs/ml/"
    "dashboard_prediction_full.csv"
)

MODEL_NAME = "Random Forest"
MODEL_VERSION = "1.0"


# ============================================================
# LOAD PREDICTIONS
# ============================================================

print("=" * 70)
print("ML 07 - SAVE PREDICTIONS TO POSTGRESQL")
print("=" * 70)

df = pd.read_csv(
    INPUT_FILE
)

df["datetime"] = pd.to_datetime(
    df["datetime"]
)

print(
    f"\nPrediction rows: "
    f"{len(df):,}"
)

print(
    f"From: "
    f"{df['datetime'].min()}"
)

print(
    f"To:   "
    f"{df['datetime'].max()}"
)


# ============================================================
# VALIDATION
# ============================================================

required_columns = [
    "datetime",
    "total_trips",
    "predicted_demand"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing columns: "
        f"{missing_columns}"
    )


# ============================================================
# SAVE TO POSTGRESQL
# ============================================================

print(
    "\nSaving predictions "
    "to PostgreSQL..."
)

save_predictions(
    df=df,
    model_name=MODEL_NAME,
    model_version=MODEL_VERSION
)


# ============================================================
# COMPLETED
# ============================================================

print(
    "\nML 07 completed successfully."
)
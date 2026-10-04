from pathlib import Path

import pandas as pd


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

ML_OUTPUT_DIR = (
    BASE_DIR
    / "analysis"
    / "outputs"
    / "ml"
)

INPUT_PREDICTIONS = (
    ML_OUTPUT_DIR
    / "random_forest_predictions.csv"
)

INPUT_COMPARISON = (
    ML_OUTPUT_DIR
    / "model_comparison.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 60)
print("ML 06 - PREPARE DASHBOARD DATA")
print("=" * 60)

df = pd.read_csv(INPUT_PREDICTIONS)

df["datetime"] = pd.to_datetime(df["datetime"])

print("\nInput:")
print(f"Rows: {len(df):,}")
print(f"Columns: {list(df.columns)}")


# ============================================================
# 1. PREPARE PREDICTION DATA
# ============================================================

dashboard_prediction = df[
    [
        "datetime",
        "date",
        "hour",
        "day_of_week",
        "month",
        "total_trips",
        "predicted_demand",
        "model_name",
        "error",
        "absolute_error",
    ]
].copy()


# Đổi tên để Dashboard dễ hiểu

dashboard_prediction = dashboard_prediction.rename(
    columns={
        "total_trips": "actual_demand",
        "error": "prediction_error",
    }
)


# Sắp xếp theo thời gian

dashboard_prediction = dashboard_prediction.sort_values(
    "datetime"
)


# ============================================================
# SAVE PREDICTION DATA
# ============================================================

prediction_output = (
    ML_OUTPUT_DIR
    / "dashboard_prediction.csv"
)

dashboard_prediction.to_csv(
    prediction_output,
    index=False,
)

print(
    f"\nSaved: {prediction_output}"
)


# ============================================================
# 2. HOURLY DEMAND
# ============================================================

hourly_demand = (
    dashboard_prediction
    .groupby("hour")
    .agg(
        total_actual_demand=(
            "actual_demand",
            "sum",
        ),
        total_predicted_demand=(
            "predicted_demand",
            "sum",
        ),
        average_actual_demand=(
            "actual_demand",
            "mean",
        ),
        average_predicted_demand=(
            "predicted_demand",
            "mean",
        ),
    )
    .reset_index()
)


hourly_output = (
    ML_OUTPUT_DIR
    / "dashboard_hourly_demand.csv"
)

hourly_demand.to_csv(
    hourly_output,
    index=False,
)

print(
    f"Saved: {hourly_output}"
)


# ============================================================
# 3. DAILY DEMAND
# ============================================================

daily_demand = (
    dashboard_prediction
    .groupby("date")
    .agg(
        actual_demand=(
            "actual_demand",
            "sum",
        ),
        predicted_demand=(
            "predicted_demand",
            "sum",
        ),
    )
    .reset_index()
)


daily_demand["prediction_error"] = (
    daily_demand["actual_demand"]
    - daily_demand["predicted_demand"]
)

daily_demand["absolute_error"] = (
    daily_demand["prediction_error"]
    .abs()
)


daily_output = (
    ML_OUTPUT_DIR
    / "dashboard_daily_demand.csv"
)

daily_demand.to_csv(
    daily_output,
    index=False,
)

print(
    f"Saved: {daily_output}"
)


# ============================================================
# 4. MODEL METRICS
# ============================================================

if INPUT_COMPARISON.exists():

    model_metrics = pd.read_csv(
        INPUT_COMPARISON
    )

    metrics_output = (
        ML_OUTPUT_DIR
        / "dashboard_model_metrics.csv"
    )

    model_metrics.to_csv(
        metrics_output,
        index=False,
    )

    print(
        f"Saved: {metrics_output}"
    )

else:

    print(
        "\nWarning: model_comparison.csv "
        "was not found."
    )


# ============================================================
# 5. SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("DASHBOARD DATA SUMMARY")
print("=" * 60)

print(
    f"Prediction rows: {len(dashboard_prediction):,}"
)

print(
    f"Hourly rows:     {len(hourly_demand):,}"
)

print(
    f"Daily rows:      {len(daily_demand):,}"
)


print("\nPrediction columns:")

for column in dashboard_prediction.columns:
    print(f"- {column}")


# ============================================================
# 6. SAMPLE DATA
# ============================================================

print("\n" + "=" * 60)
print("SAMPLE PREDICTION DATA")
print("=" * 60)

print(
    dashboard_prediction.head(10).to_string(
        index=False
    )
)


print("\n" + "=" * 60)
print("ML 06 COMPLETED SUCCESSFULLY")
print("=" * 60)
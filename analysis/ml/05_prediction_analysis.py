from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    BASE_DIR
    / "analysis"
    / "outputs"
    / "ml"
    / "random_forest_predictions.csv"
)

OUTPUT_FIGURES = (
    BASE_DIR
    / "analysis"
    / "outputs"
    / "figures"
)

OUTPUT_ML = (
    BASE_DIR
    / "analysis"
    / "outputs"
    / "ml"
)

OUTPUT_FIGURES.mkdir(parents=True, exist_ok=True)
OUTPUT_ML.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 60)
print("ML 05 - RANDOM FOREST PREDICTION ANALYSIS")
print("=" * 60)

df = pd.read_csv(INPUT_FILE)

df["datetime"] = pd.to_datetime(df["datetime"])

print(f"\nInput file: {INPUT_FILE}")
print(f"Rows: {len(df):,}")
print(f"Columns: {list(df.columns)}")


# ============================================================
# CHECK REQUIRED COLUMNS
# ============================================================

required_columns = [
    "datetime",
    "total_trips",
    "predicted_demand",
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )


# ============================================================
# STANDARDIZE COLUMN NAMES FOR ANALYSIS
# ============================================================

# total_trips = Actual demand
# predicted_demand = Predicted demand

df["actual"] = df["total_trips"]

df["predicted"] = df["predicted_demand"]


# ============================================================
# CALCULATE ERROR
# ============================================================

df["error"] = df["actual"] - df["predicted"]

df["absolute_error"] = df["error"].abs()

df["squared_error"] = df["error"] ** 2


# ============================================================
# BASIC STATISTICS
# ============================================================

mae = df["absolute_error"].mean()

rmse = (df["squared_error"].mean()) ** 0.5

mean_error = df["error"].mean()

max_absolute_error = df["absolute_error"].max()


print("\n" + "=" * 60)
print("PREDICTION ERROR SUMMARY")
print("=" * 60)

print(f"MAE:                    {mae:.4f}")
print(f"RMSE:                   {rmse:.4f}")
print(f"Mean Error:             {mean_error:.4f}")
print(f"Maximum Absolute Error: {max_absolute_error:.4f}")


# ============================================================
# 1. ACTUAL VS PREDICTED - TIME SERIES
# ============================================================

plt.figure(figsize=(14, 6))

plt.plot(
    df["datetime"],
    df["actual"],
    label="Actual",
    linewidth=1.5,
)

plt.plot(
    df["datetime"],
    df["predicted"],
    label="Predicted",
    linewidth=1.2,
)

plt.title(
    "Random Forest - Actual vs Predicted Demand"
)

plt.xlabel("Datetime")

plt.ylabel("Trips per Hour")

plt.legend()

plt.grid(True, alpha=0.3)

plt.tight_layout()

output_file = (
    OUTPUT_FIGURES
    / "random_forest_actual_vs_predicted.png"
)

plt.savefig(
    output_file,
    dpi=150,
)

plt.close()

print(
    f"\nSaved: {output_file}"
)


# ============================================================
# 2. ACTUAL VS PREDICTED SCATTER
# ============================================================

plt.figure(figsize=(8, 8))

plt.scatter(
    df["actual"],
    df["predicted"],
    alpha=0.5,
)

min_value = min(
    df["actual"].min(),
    df["predicted"].min(),
)

max_value = max(
    df["actual"].max(),
    df["predicted"].max(),
)

plt.plot(
    [min_value, max_value],
    [min_value, max_value],
    linestyle="--",
    linewidth=1.5,
)

plt.title(
    "Random Forest - Actual vs Predicted"
)

plt.xlabel("Actual Demand")

plt.ylabel("Predicted Demand")

plt.grid(True, alpha=0.3)

plt.tight_layout()

output_file = (
    OUTPUT_FIGURES
    / "random_forest_scatter.png"
)

plt.savefig(
    output_file,
    dpi=150,
)

plt.close()

print(
    f"Saved: {output_file}"
)


# ============================================================
# 3. PREDICTION ERROR OVER TIME
# ============================================================

plt.figure(figsize=(14, 6))

plt.plot(
    df["datetime"],
    df["error"],
    linewidth=1.2,
)

plt.axhline(
    y=0,
    linestyle="--",
    linewidth=1,
)

plt.title(
    "Random Forest - Prediction Error Over Time"
)

plt.xlabel("Datetime")

plt.ylabel("Error (Actual - Predicted)")

plt.grid(True, alpha=0.3)

plt.tight_layout()

output_file = (
    OUTPUT_FIGURES
    / "random_forest_error.png"
)

plt.savefig(
    output_file,
    dpi=150,
)

plt.close()

print(
    f"Saved: {output_file}"
)


# ============================================================
# 4. TOP 20 LARGEST PREDICTION ERRORS
# ============================================================

top_errors = (
    df[
        [
            "datetime",
            "actual",
            "predicted",
            "error",
            "absolute_error",
        ]
    ]
    .sort_values(
        by="absolute_error",
        ascending=False,
    )
    .head(20)
)

output_file = (
    OUTPUT_ML
    / "random_forest_error_summary.csv"
)

top_errors.to_csv(
    output_file,
    index=False,
)

print(
    f"\nSaved: {output_file}"
)


# ============================================================
# 5. ERROR BY HOUR
# ============================================================

error_by_hour = (
    df.groupby("hour")
    .agg(
        mean_absolute_error=(
            "absolute_error",
            "mean",
        ),
        mean_error=(
            "error",
            "mean",
        ),
        max_absolute_error=(
            "absolute_error",
            "max",
        ),
    )
    .reset_index()
)

print("\n" + "=" * 60)
print("ERROR BY HOUR")
print("=" * 60)

print(
    error_by_hour.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}",
    )
)


# ============================================================
# 6. ERROR BY DAY OF WEEK
# ============================================================

error_by_day = (
    df.groupby("day_of_week")
    .agg(
        mean_absolute_error=(
            "absolute_error",
            "mean",
        ),
        mean_error=(
            "error",
            "mean",
        ),
        max_absolute_error=(
            "absolute_error",
            "max",
        ),
    )
    .reset_index()
)

print("\n" + "=" * 60)
print("ERROR BY DAY OF WEEK")
print("=" * 60)

print(
    error_by_day.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}",
    )
)


# ============================================================
# 7. SAVE ERROR BY HOUR
# ============================================================

error_by_hour_file = (
    OUTPUT_ML
    / "random_forest_error_by_hour.csv"
)

error_by_hour.to_csv(
    error_by_hour_file,
    index=False,
)

print(
    f"\nSaved: {error_by_hour_file}"
)


# ============================================================
# 8. SAVE ERROR BY DAY
# ============================================================

error_by_day_file = (
    OUTPUT_ML
    / "random_forest_error_by_day.csv"
)

error_by_day.to_csv(
    error_by_day_file,
    index=False,
)

print(
    f"Saved: {error_by_day_file}"
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("FINAL RESULT")
print("=" * 60)

print(
    f"Number of predictions:     {len(df):,}"
)

print(
    f"MAE:                       {mae:.4f}"
)

print(
    f"RMSE:                      {rmse:.4f}"
)

print(
    f"Mean Error:                {mean_error:.4f}"
)

print(
    f"Maximum Absolute Error:    {max_absolute_error:.4f}"
)

print("\nML 05 completed successfully.")
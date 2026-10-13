import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

# ============================================================
# 0. PROJECT PATH CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.postgres import get_connection, save_predictions

# ============================================================
# 1. CONSTANTS & CONFIG
# ============================================================

OUTPUT_DIR = PROJECT_ROOT / "analysis" / "outputs" / "ml"
OUTPUT_FILE = OUTPUT_DIR / "future_forecast.csv"

MODEL_NAME = "Random Forest"
MODEL_VERSION = "future-v1"
FORECAST_HORIZON_HOURS = 168  # 7 days continuous

FEATURES = [
    "hour",
    "day_of_week",
    "month",
    "lag_1",
    "lag_24",
    "lag_168",
    "rolling_24h",
    "rolling_7d",
]
TARGET = "total_trips"


def validate_training_pipeline(raw_df, merged, train_df, earliest_actual, latest_actual, train_start, train_end):
    """
    Automated test suite verifying:
    1. Training data scope and sample count.
    2. Dynamic determination of train_end vs latest_actual.
    3. Correctness of all 5 lag and rolling features.
    4. Absence of future data leakage.
    """
    print("\n" + "-" * 70)
    print("[TEST] VALIDATING TRAINING DATA PIPELINE & FEATURE ENGINEERING")
    print("-" * 70)

    # 1. Check timeline continuity
    expected_total_hours = len(pd.date_range(start=earliest_actual, end=latest_actual, freq="h"))
    assert len(merged) == expected_total_hours, (
        f"Timeline length mismatch: expected {expected_total_hours}, got {len(merged)}"
    )
    print(f"[TEST PASS] Full timeline continuity: {len(merged):,} continuous hours.")

    # 2. Check training sample count (dropped exactly 168 initial hours)
    expected_samples = len(merged) - 168
    assert len(train_df) == expected_samples, (
        f"Training sample count mismatch: expected {expected_samples}, got {len(train_df)}"
    )
    print(f"[TEST PASS] Valid training samples after dropna: {len(train_df):,} samples.")

    # 3. Check train_start offset
    expected_train_start = earliest_actual + pd.Timedelta(hours=168)
    assert train_start == expected_train_start, (
        f"train_start mismatch: expected {expected_train_start}, got {train_start}"
    )
    print(f"[TEST PASS] Training start offset: {train_start} (exactly 168h after {earliest_actual}).")

    # 4. Explicit verification of train_end vs latest_actual
    # Note: latest_actual is the boundary of raw records in hourly_demand.
    # train_end is the latest timestamp in train_df after feature generation.
    # Because target is demand at time t (y_t) and all features are backward-looking (<= t-1),
    # the sample at latest_actual has complete features and known target y_t.
    # Thus train_end equals latest_actual in this design, but it is verified dynamically.
    assert train_end == latest_actual, (
        f"train_end {train_end} unexpected relative to latest_actual {latest_actual}"
    )
    print(f"[TEST PASS] Training end ({train_end}) verified dynamically against latest actual ({latest_actual}).")

    # 5. Check no NaN / Inf in train_df features or target
    assert train_df[FEATURES].isnull().sum().sum() == 0, "Nulls detected in training features!"
    assert not np.isinf(train_df[FEATURES].to_numpy()).any(), "Inf detected in training features!"
    assert train_df[TARGET].isnull().sum() == 0, "Nulls detected in training target!"
    print("[TEST PASS] Zero NaN / Inf in training features and target.")

    # 6. Spot-check 5 lag / rolling features for mathematical correctness & no leakage
    # We test on multiple anchor points (first row, middle row, last row)
    test_indices = [0, len(train_df) // 2, len(train_df) - 1]
    for idx in test_indices:
        sample_row = train_df.iloc[idx]
        sample_time = sample_row["timestamp"]
        
        # Find corresponding index in the continuous merged dataframe
        merged_idx = merged[merged["timestamp"] == sample_time].index[0]
        
        # Verify lag_1
        expected_lag_1 = merged.loc[merged_idx - 1, "total_trips"]
        assert sample_row["lag_1"] == expected_lag_1, (
            f"lag_1 mismatch at {sample_time}: {sample_row['lag_1']} != {expected_lag_1}"
        )

        # Verify lag_24
        expected_lag_24 = merged.loc[merged_idx - 24, "total_trips"]
        assert sample_row["lag_24"] == expected_lag_24, (
            f"lag_24 mismatch at {sample_time}: {sample_row['lag_24']} != {expected_lag_24}"
        )

        # Verify lag_168
        expected_lag_168 = merged.loc[merged_idx - 168, "total_trips"]
        assert sample_row["lag_168"] == expected_lag_168, (
            f"lag_168 mismatch at {sample_time}: {sample_row['lag_168']} != {expected_lag_168}"
        )

        # Verify rolling_24h (mean of trips from merged_idx - 24 to merged_idx - 1)
        expected_rolling_24h = merged.loc[merged_idx - 24 : merged_idx - 1, "total_trips"].mean()
        assert np.isclose(sample_row["rolling_24h"], expected_rolling_24h), (
            f"rolling_24h mismatch at {sample_time}: {sample_row['rolling_24h']} != {expected_rolling_24h}"
        )

        # Verify rolling_7d (mean of trips from merged_idx - 168 to merged_idx - 1)
        expected_rolling_7d = merged.loc[merged_idx - 168 : merged_idx - 1, "total_trips"].mean()
        assert np.isclose(sample_row["rolling_7d"], expected_rolling_7d), (
            f"rolling_7d mismatch at {sample_time}: {sample_row['rolling_7d']} != {expected_rolling_7d}"
        )

    print("[TEST PASS] 5 lag/rolling features verified mathematically across sample points.")
    print("[TEST PASS] Strict no-leakage rule: all features at time t depend strictly on observations <= t-1.")
    print("-" * 70)


def prepare_full_training_data():
    """
    Extract all hourly_demand records from PostgreSQL,
    create a continuous timeline from earliest to latest actual timestamp,
    fill missing hours with 0, and compute 8 standard features.
    
    Note: Training period start is shifted by 168 hours relative to earliest actual
    to allow full computation of lag_168 and rolling_7d.
    """
    print("\n" + "=" * 70)
    print("[1/5] PREPARING IN-MEMORY TRAINING DATASET FROM POSTGRESQL")
    print("=" * 70)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, demand FROM hourly_demand ORDER BY timestamp;")
        records = cursor.fetchall()
    finally:
        conn.close()

    if not records:
        raise ValueError("No records found in hourly_demand table in PostgreSQL.")

    raw_df = pd.DataFrame(records, columns=["timestamp", "demand"])
    raw_df["timestamp"] = pd.to_datetime(raw_df["timestamp"])

    earliest_actual = raw_df["timestamp"].min()
    latest_actual = raw_df["timestamp"].max()

    print(f"[DATA] Actual records in DB:       {len(raw_df):,} rows")
    print(f"[DATA] Earliest actual timestamp:  {earliest_actual}")
    print(f"[DATA] Latest actual timestamp:    {latest_actual}")

    # Create continuous timeline from earliest to latest
    full_timeline = pd.date_range(start=earliest_actual, end=latest_actual, freq="h")
    expected_total_hours = len(full_timeline)

    merged = pd.DataFrame({"timestamp": full_timeline}).merge(
        raw_df, on="timestamp", how="left"
    )
    missing_hours = merged["demand"].isnull().sum()
    merged["total_trips"] = merged["demand"].fillna(0).astype(int)

    print(f"[PROCESS] Expected continuous timeline: {expected_total_hours:,} hours")
    print(f"[PROCESS] Missing hours (filled with 0): {missing_hours:,} hours")

    # Calendar features
    merged["hour"] = merged["timestamp"].dt.hour
    merged["day_of_week"] = merged["timestamp"].dt.dayofweek
    merged["month"] = merged["timestamp"].dt.month

    # Lag & rolling features (strict no-leakage rules)
    merged["lag_1"] = merged["total_trips"].shift(1)
    merged["lag_24"] = merged["total_trips"].shift(24)
    merged["lag_168"] = merged["total_trips"].shift(168)
    merged["rolling_24h"] = merged["total_trips"].shift(1).rolling(24).mean()
    merged["rolling_7d"] = merged["total_trips"].shift(1).rolling(168).mean()

    # Drop first 168 hours due to lag requirements
    train_df = merged.dropna(subset=FEATURES + [TARGET]).reset_index(drop=True)

    train_start = train_df["timestamp"].min()
    train_end = train_df["timestamp"].max()

    print(f"[FEATURE] Total valid training samples: {len(train_df):,} rows")
    print(f"[FEATURE] Training period start:        {train_start} (168h after earliest actual)")
    print(f"[FEATURE] Training period end:          {train_end}")
    print(f"[FEATURE] Latest actual timestamp:      {latest_actual}")

    # Run automated assertions on training dataset pipeline
    validate_training_pipeline(
        raw_df, merged, train_df, earliest_actual, latest_actual, train_start, train_end
    )

    return train_df, merged, latest_actual


def train_in_memory_model(train_df):
    """
    Train Random Forest Regressor on the prepared dataset
    using standard hyperparameters from Phase 1.
    """
    print("\n" + "=" * 70)
    print("[2/5] TRAINING RANDOM FOREST REGRESSOR IN MEMORY")
    print("=" * 70)

    X_train = train_df[FEATURES]
    y_train = train_df[TARGET]

    print(f"[PROCESS] Features: {FEATURES}")
    print(f"[PROCESS] Fitting Random Forest (n_estimators=200, max_depth=15, random_state=42)...")

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    print("[SUCCESS] In-memory Random Forest model trained successfully.")

    return model


def get_history_buffer(merged_timeline, latest_actual):
    """
    Extract the 168 continuous hours ending at latest_actual
    to serve as the initial buffer for Recursive Forecasting.
    """
    history_end = latest_actual
    history_start = latest_actual - pd.Timedelta(hours=FORECAST_HORIZON_HOURS - 1)

    sub_df = merged_timeline[
        (merged_timeline["timestamp"] >= history_start)
        & (merged_timeline["timestamp"] <= history_end)
    ].sort_values("timestamp")

    if len(sub_df) != FORECAST_HORIZON_HOURS:
        raise ValueError(
            f"Expected {FORECAST_HORIZON_HOURS} history buffer points, got {len(sub_df)}"
        )

    history_demand = list(sub_df["total_trips"].values)
    print(f"\n[INFO] Initial history buffer: 168 hours ({history_start} -> {history_end})")

    return history_demand


def run_recursive_forecast(model, latest_actual, history_demand):
    """
    Run 168 continuous recursive forecast steps.
    Only uses historical actuals and previous predictions to compute lag/rolling features.
    Strictly NO future actual data is accessed or leaked.
    """
    print("\n" + "=" * 70)
    print("[3/5] RUNNING RECURSIVE FORECASTING (168 HOURS / 7 DAYS)")
    print("=" * 70)

    forecast_start = latest_actual + pd.Timedelta(hours=1)
    forecast_timeline = pd.date_range(
        start=forecast_start, periods=FORECAST_HORIZON_HOURS, freq="h"
    )

    print(f"[PLAN] Forecast start: {forecast_timeline[0]}")
    print(f"[PLAN] Forecast end:   {forecast_timeline[-1]}")
    print(f"[PLAN] Total steps:    {len(forecast_timeline)} hours")

    prediction_run_time = datetime.now()
    current_history = list(history_demand)
    predictions_list = []

    for step, target_time in enumerate(forecast_timeline, start=1):
        # 1. Calendar features
        hour = target_time.hour
        day_of_week = target_time.dayofweek
        month = target_time.month

        # 2. Lag features from current buffer
        lag_1 = current_history[-1]
        lag_24 = current_history[-24]
        lag_168 = current_history[-168]

        # 3. Rolling features from current buffer
        rolling_24h = float(np.mean(current_history[-24:]))
        rolling_7d = float(np.mean(current_history[-168:]))

        row_features = pd.DataFrame(
            [
                {
                    "hour": hour,
                    "day_of_week": day_of_week,
                    "month": month,
                    "lag_1": lag_1,
                    "lag_24": lag_24,
                    "lag_168": lag_168,
                    "rolling_24h": rolling_24h,
                    "rolling_7d": rolling_7d,
                }
            ]
        )

        # 4. Predict demand
        pred = model.predict(row_features)[0]
        pred_val = max(0.0, float(pred))  # Non-negative demand

        # 5. Append prediction to buffer for subsequent steps
        current_history.append(pred_val)

        # 6. Record prediction
        predictions_list.append(
            {
                "target_time": target_time.strftime("%Y-%m-%d %H:%M:%S"),
                "datetime": target_time.strftime("%Y-%m-%d %H:%M:%S"),
                "date": target_time.strftime("%Y-%m-%d"),
                "hour": hour,
                "day_of_week": day_of_week,
                "month": month,
                "predicted_demand": round(pred_val, 4),
                "actual_demand": None,
                "model_name": MODEL_NAME,
                "model_version": MODEL_VERSION,
                "prediction_time": prediction_run_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    forecast_df = pd.DataFrame(predictions_list)
    print(f"[SUCCESS] Recursive forecasting completed: {len(forecast_df)} steps.")

    return forecast_df, forecast_start, forecast_timeline[-1]


def validate_and_save_forecast(forecast_df, forecast_start, forecast_end):
    """
    Validate forecast assertions and export to CSV.
    """
    print("\n" + "=" * 70)
    print("[4/5] VALIDATING FORECAST RESULTS")
    print("=" * 70)

    # 1. Total row count
    assert len(forecast_df) == 168, f"Expected 168 rows, got {len(forecast_df)}"
    print("[CHECK] Total rows: 168 (PASS)")

    # 2. Distinct timestamps count
    unique_timestamps = forecast_df["target_time"].nunique()
    assert unique_timestamps == 168, f"Expected 168 unique timestamps, got {unique_timestamps}"
    print("[CHECK] Unique timestamps: 168 (PASS)")

    # 3. Start and End time
    dt_series = pd.to_datetime(forecast_df["target_time"])
    assert dt_series.min() == forecast_start, f"Start mismatch: {dt_series.min()} != {forecast_start}"
    assert dt_series.max() == forecast_end, f"End mismatch: {dt_series.max()} != {forecast_end}"
    print(f"[CHECK] Time range: {forecast_start} -> {forecast_end} (PASS)")

    # 4. Strict 1-hour interval
    diffs = dt_series.diff().dropna()
    expected_step = pd.Timedelta(hours=1)
    assert (diffs == expected_step).all(), "Timestamps are not strictly 1 hour apart!"
    print("[CHECK] Timestamp step: strictly 1 hour apart (PASS)")

    # 5. No missing, NaN or Inf in predicted_demand
    assert forecast_df["predicted_demand"].isnull().sum() == 0, "predicted_demand contains nulls"
    assert not np.isinf(forecast_df["predicted_demand"]).any(), "predicted_demand contains inf"
    print("[CHECK] Missing / NaN / Inf values in predicted_demand: 0 (PASS)")

    # 6. Non-negative demand bounds
    min_demand = forecast_df["predicted_demand"].min()
    max_demand = forecast_df["predicted_demand"].max()
    mean_demand = forecast_df["predicted_demand"].mean()
    assert min_demand >= 0, f"Negative predicted_demand detected: {min_demand}"
    print(
        f"[CHECK] Demand bounds: Min={min_demand:.2f}, Max={max_demand:.2f}, Mean={mean_demand:.2f} (PASS)"
    )

    # 7. Model version & Actual demand
    assert (forecast_df["model_version"] == "future-v1").all(), "model_version must be future-v1"
    assert forecast_df["actual_demand"].isnull().all(), "actual_demand must be NULL for future"
    print("[CHECK] Model version: future-v1, actual_demand: NULL (PASS)")

    # Export to CSV
    print("\n" + "=" * 70)
    print("[5/5] EXPORTING TO CSV")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    forecast_df.to_csv(OUTPUT_FILE, index=False)
    print(f"[EXPORT] Saved Future Forecast to: {OUTPUT_FILE}")
    print(f"[EXPORT] File size: {OUTPUT_FILE.stat().st_size:,} bytes")


def save_forecast_to_postgres(forecast_df):
    """
    Save the validated future forecast into PostgreSQL predictions table.
    Uses model_name='Random Forest' and model_version='future-v1'.
    actual_demand is saved as NULL.
    Strictly preserves Historical Prediction (1.0).
    """
    print("\n" + "=" * 70)
    print("[6/6] SAVING FUTURE FORECAST TO POSTGRESQL")
    print("=" * 70)

    save_predictions(
        df=forecast_df,
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
    )
    print(f"[SUCCESS] Saved {len(forecast_df)} rows to PostgreSQL table 'predictions'.")
    print(f"[SUCCESS] model_name='{MODEL_NAME}', model_version='{MODEL_VERSION}', actual_demand=NULL.")


def main():
    print("=" * 70)
    print("BIKEDEMAND v2.0 -- FUTURE DEMAND FORECAST (PROPOSAL B ENGINE)")
    print("=" * 70)

    # 1. Prepare full in-memory training dataset from DB
    train_df, merged_timeline, latest_actual = prepare_full_training_data()

    # 2. Train model in memory
    model = train_in_memory_model(train_df)

    # 3. Get history buffer
    history_demand = get_history_buffer(merged_timeline, latest_actual)

    # 4. Run recursive forecast
    forecast_df, forecast_start, forecast_end = run_recursive_forecast(
        model, latest_actual, history_demand
    )

    # 5. Validate and export CSV
    validate_and_save_forecast(forecast_df, forecast_start, forecast_end)

    # 6. Save Future Forecast to PostgreSQL
    save_forecast_to_postgres(forecast_df)

    print("\n" + "=" * 70)
    print("[SUCCESS] TASK 4 -- FUTURE FORECAST SAVED TO POSTGRESQL SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()

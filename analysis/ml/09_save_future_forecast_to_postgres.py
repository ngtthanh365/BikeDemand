"""
Save Future Forecast to PostgreSQL (Task 4)
--------------------------------------------
Reads analysis/outputs/ml/future_forecast.csv and saves the 168 rows
into the PostgreSQL 'predictions' table under model_name='Random Forest'
and model_version='future-v1'.

Strictly preserves Historical Prediction ('Random Forest' / '1.0', 4,176 rows).
"""

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.postgres import get_connection, save_predictions

CSV_FILE = PROJECT_ROOT / "analysis" / "outputs" / "ml" / "future_forecast.csv"
MODEL_NAME = "Random Forest"
MODEL_VERSION = "future-v1"


def get_predictions_summary():
    """
    Query summary counts grouped by model_name and model_version from PostgreSQL.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                model_name,
                model_version,
                COUNT(*) as total_rows,
                COUNT(actual_demand) as non_null_actual,
                MIN(target_time) as min_target,
                MAX(target_time) as max_target
            FROM predictions
            GROUP BY model_name, model_version
            ORDER BY model_name, model_version;
            """
        )
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
        return pd.DataFrame(rows, columns=cols)
    finally:
        conn.close()


def main():
    print("=" * 70)
    print("BIKEDEMAND v2.0 -- TASK 4: SAVE FUTURE FORECAST TO POSTGRESQL")
    print("=" * 70)

    # 1. Validate CSV file existence
    if not CSV_FILE.exists():
        raise FileNotFoundError(f"Future forecast CSV not found: {CSV_FILE}")

    df = pd.read_csv(CSV_FILE)
    print(f"\n[1/4] Loaded forecast CSV: {len(df)} rows from {CSV_FILE}")

    # 2. Validate forecast structure
    assert len(df) == 168, f"Expected 168 rows, got {len(df)}"
    assert "target_time" in df.columns, "Missing 'target_time' column"
    assert "predicted_demand" in df.columns, "Missing 'predicted_demand' column"
    assert df["actual_demand"].isnull().all(), "actual_demand must be all NULL/NaN for future forecast"
    print("[CHECK] Forecast validation: 168 rows, actual_demand=NULL (PASS)")

    # 3. Check DB baseline before save
    print("\n[2/4] Database state BEFORE saving:")
    before_summary = get_predictions_summary()
    print(before_summary.to_string(index=False))

    # Verify Historical Prediction exists
    hist_before = before_summary[
        (before_summary["model_name"] == MODEL_NAME)
        & (before_summary["model_version"] == "1.0")
    ]
    if not hist_before.empty:
        hist_rows_before = int(hist_before["total_rows"].iloc[0])
        print(f"[CHECK] Historical Prediction ('1.0') before save: {hist_rows_before:,} rows")
    else:
        hist_rows_before = 0
        print("[WARNING] No Historical Prediction ('1.0') found before save.")

    # 4. Save future forecast to PostgreSQL
    print(f"\n[3/4] Saving to PostgreSQL (model_name='{MODEL_NAME}', model_version='{MODEL_VERSION}')...")
    save_predictions(
        df=df,
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
    )

    # 5. Verify DB state after save
    print("\n[4/4] Database state AFTER saving:")
    after_summary = get_predictions_summary()
    print(after_summary.to_string(index=False))

    # Assert Historical Prediction (1.0) is unchanged
    hist_after = after_summary[
        (after_summary["model_name"] == MODEL_NAME)
        & (after_summary["model_version"] == "1.0")
    ]
    assert not hist_after.empty, "Historical Prediction ('1.0') was deleted!"
    hist_rows_after = int(hist_after["total_rows"].iloc[0])
    assert hist_rows_after == hist_rows_before, (
        f"Historical Prediction count altered! Before: {hist_rows_before}, After: {hist_rows_after}"
    )
    print(f"[VERIFY] Historical Prediction ('1.0') completely preserved: {hist_rows_after:,} rows (PASS)")

    # Assert Future Forecast (future-v1) is exactly 168 rows
    future_after = after_summary[
        (after_summary["model_name"] == MODEL_NAME)
        & (after_summary["model_version"] == MODEL_VERSION)
    ]
    assert not future_after.empty, f"Future Forecast ('{MODEL_VERSION}') not found in DB!"
    future_rows_after = int(future_after["total_rows"].iloc[0])
    assert future_rows_after == 168, f"Expected 168 future rows, got {future_rows_after}"
    print(f"[VERIFY] Future Forecast ('{MODEL_VERSION}') in DB: {future_rows_after} rows (PASS)")

    # Assert actual_demand is strictly NULL for future-v1
    non_null_actual = int(future_after["non_null_actual"].iloc[0])
    assert non_null_actual == 0, f"Future actual_demand contains non-null values: {non_null_actual}"
    print(f"[VERIFY] Future Forecast actual_demand: strictly NULL (PASS)")

    print("\n" + "=" * 70)
    print("[SUCCESS] TASK 4 COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()

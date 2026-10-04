import os
import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)


# =========================
# 1. CONFIG
# =========================

TRAIN_FILE = "analysis/outputs/ml/train.csv"
VALIDATION_FILE = "analysis/outputs/ml/validation.csv"
TEST_FILE = "analysis/outputs/ml/test.csv"

OUTPUT_DIR = "analysis/outputs/ml"

MODEL_NAME = "Linear Regression"


# =========================
# 2. LOAD DATA
# =========================

print("=" * 70)
print("ML 01 - LINEAR REGRESSION")
print("=" * 70)

train = pd.read_csv(TRAIN_FILE)
validation = pd.read_csv(VALIDATION_FILE)
test = pd.read_csv(TEST_FILE)


# =========================
# 3. DEFINE FEATURES
# =========================

FEATURES = [
    "hour",
    "day_of_week",
    "month",
    "lag_1",
    "lag_24",
    "lag_168",
    "rolling_24h",
    "rolling_7d"
]

TARGET = "total_trips"


print("\nFeatures:")
for feature in FEATURES:
    print(f"  - {feature}")

print(f"\nTarget:")
print(f"  - {TARGET}")


# =========================
# 4. PREPARE X / Y
# =========================

X_train = train[FEATURES]
y_train = train[TARGET]

X_validation = validation[FEATURES]
y_validation = validation[TARGET]

X_test = test[FEATURES]
y_test = test[TARGET]


print("\nDataset sizes:")
print(f"Train:      {len(X_train):,}")
print(f"Validation: {len(X_validation):,}")
print(f"Test:       {len(X_test):,}")


# =========================
# 5. TRAIN MODEL
# =========================

print("\n" + "=" * 70)
print("TRAINING")
print("=" * 70)

model = LinearRegression()

model.fit(
    X_train,
    y_train
)

print("Linear Regression training completed.")


# =========================
# 6. VALIDATION PREDICTION
# =========================

validation_prediction = model.predict(
    X_validation
)


# =========================
# 7. TEST PREDICTION
# =========================

test_prediction = model.predict(
    X_test
)


# =========================
# 8. METRIC FUNCTION
# =========================

def evaluate_model(y_true, y_pred):

    mae = mean_absolute_error(
        y_true,
        y_pred
    )

    rmse = mean_squared_error(
        y_true,
        y_pred
    ) ** 0.5

    r2 = r2_score(
        y_true,
        y_pred
    )

    return mae, rmse, r2


# =========================
# 9. VALIDATION METRICS
# =========================

validation_mae, validation_rmse, validation_r2 = (
    evaluate_model(
        y_validation,
        validation_prediction
    )
)


# =========================
# 10. TEST METRICS
# =========================

test_mae, test_rmse, test_r2 = (
    evaluate_model(
        y_test,
        test_prediction
    )
)


# =========================
# 11. PRINT RESULTS
# =========================

print("\n" + "=" * 70)
print("VALIDATION RESULTS")
print("=" * 70)

print(f"MAE:  {validation_mae:.4f}")
print(f"RMSE: {validation_rmse:.4f}")
print(f"R²:   {validation_r2:.4f}")


print("\n" + "=" * 70)
print("TEST RESULTS")
print("=" * 70)

print(f"MAE:  {test_mae:.4f}")
print(f"RMSE: {test_rmse:.4f}")
print(f"R²:   {test_r2:.4f}")


# =========================
# 12. FEATURE COEFFICIENTS
# =========================

coefficients = pd.DataFrame({
    "feature": FEATURES,
    "coefficient": model.coef_
})

coefficients["abs_coefficient"] = (
    coefficients["coefficient"].abs()
)

coefficients = coefficients.sort_values(
    "abs_coefficient",
    ascending=False
)


print("\n" + "=" * 70)
print("MODEL COEFFICIENTS")
print("=" * 70)

print(
    coefficients[
        ["feature", "coefficient"]
    ].to_string(index=False)
)


# =========================
# 13. SAVE PREDICTIONS
# =========================

test_results = test[
    [
        "datetime",
        "date",
        "hour",
        "day_of_week",
        "month",
        "total_trips"
    ]
].copy()

test_results["predicted_demand"] = test_prediction

test_results["model_name"] = MODEL_NAME

test_results["error"] = (
    test_results["total_trips"]
    - test_results["predicted_demand"]
)

test_results["absolute_error"] = (
    test_results["error"].abs()
)


prediction_file = (
    f"{OUTPUT_DIR}/"
    "linear_regression_predictions.csv"
)

test_results.to_csv(
    prediction_file,
    index=False
)


# =========================
# 14. SAVE METRICS
# =========================

metrics = pd.DataFrame([
    {
        "model": MODEL_NAME,
        "dataset": "validation",
        "mae": validation_mae,
        "rmse": validation_rmse,
        "r2": validation_r2
    },
    {
        "model": MODEL_NAME,
        "dataset": "test",
        "mae": test_mae,
        "rmse": test_rmse,
        "r2": test_r2
    }
])

metrics_file = (
    f"{OUTPUT_DIR}/"
    "linear_regression_metrics.csv"
)

metrics.to_csv(
    metrics_file,
    index=False
)


# =========================
# 15. FINAL SUMMARY
# =========================

print("\n" + "=" * 70)
print("OUTPUT")
print("=" * 70)

print(f"Predictions:")
print(f"  {prediction_file}")

print(f"\nMetrics:")
print(f"  {metrics_file}")

print("\nML 01 completed successfully.")
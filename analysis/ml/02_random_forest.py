import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

TRAIN_FILE = "analysis/outputs/ml/train.csv"
VALIDATION_FILE = "analysis/outputs/ml/validation.csv"
TEST_FILE = "analysis/outputs/ml/test.csv"

OUTPUT_DIR = "analysis/outputs/ml"
MODEL_NAME = "Random Forest"

print("=" * 70)
print("ML 02 - RANDOM FOREST")
print("=" * 70)

# ============================================================
# 1. LOAD DATA
# ============================================================

train = pd.read_csv(TRAIN_FILE)
validation = pd.read_csv(VALIDATION_FILE)
test = pd.read_csv(TEST_FILE)

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

print("\nTarget:")
print(f"  - {TARGET}")

# ============================================================
# 2. PREPARE DATA
# ============================================================

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

# ============================================================
# 3. TRAIN MODEL
# ============================================================

print("\n" + "=" * 70)
print("TRAINING")
print("=" * 70)

model = RandomForestRegressor(
    n_estimators=200,
    max_depth=15,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

print("Random Forest training completed.")

# ============================================================
# 4. PREDICTION
# ============================================================

validation_prediction = model.predict(X_validation)
test_prediction = model.predict(X_test)

# ============================================================
# 5. EVALUATION
# ============================================================

def evaluate_model(y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = mean_squared_error(y_true, y_pred) ** 0.5
    r2 = r2_score(y_true, y_pred)

    return mae, rmse, r2


validation_mae, validation_rmse, validation_r2 = evaluate_model(
    y_validation,
    validation_prediction
)

test_mae, test_rmse, test_r2 = evaluate_model(
    y_test,
    test_prediction
)

# ============================================================
# 6. PRINT RESULTS
# ============================================================

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

# ============================================================
# 7. FEATURE IMPORTANCE
# ============================================================

feature_importance = pd.DataFrame({
    "feature": FEATURES,
    "importance": model.feature_importances_
})

feature_importance = feature_importance.sort_values(
    "importance",
    ascending=False
)

print("\n" + "=" * 70)
print("FEATURE IMPORTANCE")
print("=" * 70)

print(
    feature_importance.to_string(index=False)
)

# ============================================================
# 8. SAVE PREDICTIONS
# ============================================================

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
    "random_forest_predictions.csv"
)

test_results.to_csv(
    prediction_file,
    index=False
)

# ============================================================
# 9. SAVE METRICS
# ============================================================

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
    "random_forest_metrics.csv"
)

metrics.to_csv(
    metrics_file,
    index=False
)

# ============================================================
# 10. OUTPUT
# ============================================================

print("\n" + "=" * 70)
print("OUTPUT")
print("=" * 70)

print("Predictions:")
print(f"  {prediction_file}")

print("\nMetrics:")
print(f"  {metrics_file}")

print("\nML 02 completed successfully.")
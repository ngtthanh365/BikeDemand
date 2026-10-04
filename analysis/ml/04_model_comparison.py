import os
import pandas as pd
import matplotlib.pyplot as plt

OUTPUT_DIR = "analysis/outputs/ml"

LINEAR_FILE = (
    f"{OUTPUT_DIR}/"
    "linear_regression_metrics.csv"
)

RANDOM_FOREST_FILE = (
    f"{OUTPUT_DIR}/"
    "random_forest_metrics.csv"
)

GRADIENT_BOOSTING_FILE = (
    f"{OUTPUT_DIR}/"
    "gradient_boosting_metrics.csv"
)

COMPARISON_FILE = (
    f"{OUTPUT_DIR}/"
    "model_comparison.csv"
)

FIGURE_DIR = "analysis/outputs/figures"

MAE_FIGURE = (
    f"{FIGURE_DIR}/"
    "model_comparison_mae.png"
)

RMSE_FIGURE = (
    f"{FIGURE_DIR}/"
    "model_comparison_rmse.png"
)

R2_FIGURE = (
    f"{FIGURE_DIR}/"
    "model_comparison_r2.png"
)

print("=" * 70)
print("ML 04 - MODEL COMPARISON")
print("=" * 70)

# ============================================================
# 1. LOAD METRICS
# ============================================================

linear = pd.read_csv(LINEAR_FILE)
random_forest = pd.read_csv(RANDOM_FOREST_FILE)
gradient_boosting = pd.read_csv(GRADIENT_BOOSTING_FILE)

metrics = pd.concat(
    [
        linear,
        random_forest,
        gradient_boosting
    ],
    ignore_index=True
)

print("\nAll model results:")
print(metrics.to_string(index=False))

# ============================================================
# 2. SAVE COMPARISON TABLE
# ============================================================

metrics.to_csv(
    COMPARISON_FILE,
    index=False
)

# ============================================================
# 3. TEST RESULTS
# ============================================================

test_results = metrics[
    metrics["dataset"] == "test"
].copy()

test_results = test_results.sort_values(
    "r2",
    ascending=False
)

print("\n" + "=" * 70)
print("TEST SET COMPARISON")
print("=" * 70)

print(
    test_results[
        [
            "model",
            "mae",
            "rmse",
            "r2"
        ]
    ].to_string(index=False)
)

# ============================================================
# 4. FIND BEST MODEL BY EACH METRIC
# ============================================================

best_mae = test_results.loc[
    test_results["mae"].idxmin()
]

best_rmse = test_results.loc[
    test_results["rmse"].idxmin()
]

best_r2 = test_results.loc[
    test_results["r2"].idxmax()
]

print("\n" + "=" * 70)
print("TEST SET METRIC RESULTS")
print("=" * 70)

print(
    f"Lowest MAE:  "
    f"{best_mae['model']} "
    f"({best_mae['mae']:.4f})"
)

print(
    f"Lowest RMSE: "
    f"{best_rmse['model']} "
    f"({best_rmse['rmse']:.4f})"
)

print(
    f"Highest R²:  "
    f"{best_r2['model']} "
    f"({best_r2['r2']:.4f})"
)

# ============================================================
# 5. PREPARE FIGURE DIRECTORY
# ============================================================

os.makedirs(
    FIGURE_DIR,
    exist_ok=True
)

# ============================================================
# 6. MAE COMPARISON
# ============================================================

plt.figure(figsize=(9, 6))

plt.bar(
    test_results["model"],
    test_results["mae"]
)

plt.title("Model Comparison - MAE")
plt.xlabel("Model")
plt.ylabel("MAE")

plt.xticks(
    rotation=15
)

plt.tight_layout()

plt.savefig(
    MAE_FIGURE,
    dpi=150
)

plt.close()

# ============================================================
# 7. RMSE COMPARISON
# ============================================================

plt.figure(figsize=(9, 6))

plt.bar(
    test_results["model"],
    test_results["rmse"]
)

plt.title("Model Comparison - RMSE")
plt.xlabel("Model")
plt.ylabel("RMSE")

plt.xticks(
    rotation=15
)

plt.tight_layout()

plt.savefig(
    RMSE_FIGURE,
    dpi=150
)

plt.close()

# ============================================================
# 8. R2 COMPARISON
# ============================================================

plt.figure(figsize=(9, 6))

plt.bar(
    test_results["model"],
    test_results["r2"]
)

plt.title("Model Comparison - R²")
plt.xlabel("Model")
plt.ylabel("R²")

plt.xticks(
    rotation=15
)

plt.tight_layout()

plt.savefig(
    R2_FIGURE,
    dpi=150
)

plt.close()

# ============================================================
# 9. OUTPUT
# ============================================================

print("\n" + "=" * 70)
print("OUTPUT")
print("=" * 70)

print("Comparison table:")
print(f"  {COMPARISON_FILE}")

print("\nFigures:")
print(f"  {MAE_FIGURE}")
print(f"  {RMSE_FIGURE}")
print(f"  {R2_FIGURE}")

print("\nML 04 completed successfully.")
from pathlib import Path


# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

ML_OUTPUT_DIR = (
    BASE_DIR
    / "analysis"
    / "outputs"
    / "ml"
)


# ============================================================
# MODEL METRICS
# ============================================================

MODEL_METRICS_FILE = (
    ML_OUTPUT_DIR
    / "dashboard_model_metrics.csv"
)
from pathlib import Path


# Thư mục gốc của project
BASE_DIR = Path(__file__).resolve().parent.parent


# Thư mục chứa kết quả ML
ML_OUTPUT_DIR = BASE_DIR / "analysis" / "outputs" / "ml"


# Các file dữ liệu Dashboard
PREDICTION_FILE = ML_OUTPUT_DIR / "dashboard_prediction_full.csv"

HOURLY_DEMAND_FILE = ML_OUTPUT_DIR / "dashboard_hourly_demand.csv"

DAILY_DEMAND_FILE = ML_OUTPUT_DIR / "dashboard_daily_demand.csv"

MODEL_METRICS_FILE = ML_OUTPUT_DIR / "dashboard_model_metrics.csv"
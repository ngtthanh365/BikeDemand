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


# ============================================================
# GEOSPATIAL INTELLIGENCE DESIGN SYSTEM TOKENS
# ============================================================

THEME_COLORS = {
    "bg_primary": "#0B1329",
    "bg_card": "#111D38",
    "bg_secondary": "#1E293B",
    "text_primary": "#F8FAFC",
    "text_muted": "#94A3B8",
    "accent_cyan": "#00F2FE",
    "accent_blue": "#38BDF8",
    "accent_orange": "#F97316",
    "accent_emerald": "#10B981",
    "border_subtle": "rgba(148, 163, 184, 0.18)",
}
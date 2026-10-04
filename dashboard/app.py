import sys
from pathlib import Path

import streamlit as st
import pandas as pd


# ============================================================
# IMPORT PATH
# ============================================================

DASHBOARD_DIR = Path(__file__).resolve().parent

if str(DASHBOARD_DIR) not in sys.path:
    sys.path.append(str(DASHBOARD_DIR))


from services.data_loader import (
    load_prediction_data,
    load_hourly_demand,
    load_daily_demand,
    load_model_metrics
)

from components.kpi import show_kpis

from components.charts import (
    show_prediction_chart,
    show_hourly_chart,
    show_daily_chart
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Citi Bike Demand Dashboard",
    page_icon="🚲",
    layout="wide"
)


# ============================================================
# TITLE
# ============================================================

st.title("🚲 Citi Bike Demand Analysis & Prediction")

st.caption(
    "Phân tích và dự báo nhu cầu sử dụng xe đạp Citi Bike — H1 2026"
)


# ============================================================
# LOAD DATA
# ============================================================

prediction_df = load_prediction_data()
hourly_df = load_hourly_demand()
daily_df = load_daily_demand()
metrics_df = load_model_metrics()


# ============================================================
# KPI
# ============================================================

# Tổng số chuyến thực tế trong H1 2026
total_trips = 415708

# H1 2026 có 181 ngày (01/01/2026 → 30/06/2026)
avg_daily_trips = total_trips / 181


# ------------------------------------------------------------
# Tìm giờ có nhu cầu cao nhất
# ------------------------------------------------------------

if "total_actual_demand" in hourly_df.columns:

    peak_hour_row = hourly_df.loc[
        hourly_df["total_actual_demand"].idxmax()
    ]

    peak_hour = f"{int(peak_hour_row['hour']):02d}:00"

    peak_hour_trips = int(
        peak_hour_row["total_actual_demand"]
    )

else:

    peak_hour = "N/A"
    peak_hour_trips = 0


# ------------------------------------------------------------
# Lấy MAE của Random Forest
# ------------------------------------------------------------

test_mae = 24.8594

if not metrics_df.empty and "model" in metrics_df.columns:

    rf_metrics = metrics_df[
        metrics_df["model"].str.contains(
            "Random Forest",
            case=False,
            na=False
        )
    ]

    if not rf_metrics.empty and "mae" in rf_metrics.columns:
        test_mae = float(rf_metrics.iloc[0]["mae"])


# ============================================================
# DISPLAY KPI
# ============================================================

show_kpis(
    total_trips=total_trips,
    avg_daily_trips=avg_daily_trips,
    peak_hour=peak_hour,
    peak_hour_trips=peak_hour_trips,
    model_mae=test_mae
)


st.divider()


# ============================================================
# ACTUAL VS PREDICTED
# ============================================================

st.subheader("📈 Actual vs Predicted Demand")

show_prediction_chart(prediction_df)


st.divider()


# ============================================================
# HOURLY + DAILY DEMAND
# ============================================================

col1, col2 = st.columns(2)


# ------------------------------------------------------------
# Demand by Hour
# ------------------------------------------------------------

with col1:

    st.subheader("🕐 Demand by Hour")

    show_hourly_chart(hourly_df)


# ------------------------------------------------------------
# Demand by Day
# ------------------------------------------------------------

with col2:

    st.subheader("📅 Demand by Day")

    show_daily_chart(daily_df)


st.divider()


# ============================================================
# DATA PREVIEW
# ============================================================

st.subheader("📋 Prediction Data")

st.dataframe(
    prediction_df,
    use_container_width=True
)

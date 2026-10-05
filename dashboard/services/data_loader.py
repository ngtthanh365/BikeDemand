import sys
from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORT DATABASE
# ============================================================

from database.postgres import (
    load_predictions,
    load_dashboard_trips
)


from config import (
    MODEL_METRICS_FILE
)


# ============================================================
# PREDICTION DATA
# ============================================================

@st.cache_data
def load_prediction_data():

    # --------------------------------------------------------
    # Đọc prediction từ PostgreSQL
    # --------------------------------------------------------

    df = load_predictions(
        model_name="Random Forest",
        model_version="1.0"
    )

    if df.empty:
        return df


    # --------------------------------------------------------
    # Đổi tên cột PostgreSQL về cấu trúc Dashboard cũ
    # --------------------------------------------------------

    df = df.rename(
        columns={
            "target_time": "datetime",
            "actual_demand": "total_trips"
        }
    )


    # --------------------------------------------------------
    # Chuyển thời gian
    # --------------------------------------------------------

    df["datetime"] = pd.to_datetime(
        df["datetime"]
    )


    # --------------------------------------------------------
    # Tạo các cột thời gian
    # --------------------------------------------------------

    df["date"] = (
        df["datetime"]
        .dt.normalize()
    )

    df["hour"] = (
        df["datetime"]
        .dt.hour
    )

    df["day_of_week"] = (
        df["datetime"]
        .dt.dayofweek
    )

    df["month"] = (
        df["datetime"]
        .dt.month
    )


    # --------------------------------------------------------
    # Tính sai số dự đoán
    # --------------------------------------------------------

    df["error"] = (
        df["total_trips"]
        - df["predicted_demand"]
    )

    df["absolute_error"] = (
        df["error"]
        .abs()
    )


    # --------------------------------------------------------
    # Giữ cấu trúc giống Dashboard cũ
    # --------------------------------------------------------

    df = df[
        [
            "datetime",
            "date",
            "hour",
            "day_of_week",
            "month",
            "total_trips",
            "predicted_demand",
            "model_name",
            "error",
            "absolute_error"
        ]
    ]


    return df


# ============================================================
# MODEL METRICS
# ============================================================

@st.cache_data
def load_model_metrics():

    df = pd.read_csv(
        MODEL_METRICS_FILE
    )

    return df


# ============================================================
# RAW DATA FOR FILTER
# ============================================================

@st.cache_data
def load_raw_data():

    # --------------------------------------------------------
    # Đọc dữ liệu từ PostgreSQL
    # --------------------------------------------------------

    df = load_dashboard_trips()


    # --------------------------------------------------------
    # Chuyển thời gian
    # --------------------------------------------------------

    df["started_at"] = pd.to_datetime(
        df["started_at"]
    )

    df["ended_at"] = pd.to_datetime(
        df["ended_at"]
    )


    return df
import pandas as pd
import streamlit as st

from config import (
    PREDICTION_FILE,
    HOURLY_DEMAND_FILE,
    DAILY_DEMAND_FILE,
    MODEL_METRICS_FILE
)


@st.cache_data
def load_prediction_data():
    df = pd.read_csv(PREDICTION_FILE)

    df["datetime"] = pd.to_datetime(df["datetime"])
    df["date"] = pd.to_datetime(df["date"])

    return df


@st.cache_data
def load_hourly_demand():
    df = pd.read_csv(HOURLY_DEMAND_FILE)

    return df


@st.cache_data
def load_daily_demand():
    df = pd.read_csv(DAILY_DEMAND_FILE)

    df["date"] = pd.to_datetime(df["date"])

    return df


@st.cache_data
def load_model_metrics():
    df = pd.read_csv(MODEL_METRICS_FILE)

    return df


# ============================================================
# MEMBER VS CASUAL
# ============================================================

@st.cache_data
def load_member_type():
    df = pd.read_csv(
        "data/processed/citibike_2026_H1.csv",
        usecols=["member_casual"]
    )

    result = (
        df["member_casual"]
        .value_counts()
        .reset_index()
    )

    result.columns = ["member_casual", "trips"]

    return result


# ============================================================
# ELECTRIC VS CLASSIC
# ============================================================

@st.cache_data
def load_bike_type():
    df = pd.read_csv(
        "data/processed/citibike_2026_H1.csv",
        usecols=["rideable_type"]
    )

    result = (
        df["rideable_type"]
        .value_counts()
        .reset_index()
    )

    result.columns = ["rideable_type", "trips"]

    return result


# ============================================================
# TOP START STATIONS
# ============================================================

@st.cache_data
def load_top_stations():
    df = pd.read_csv(
        "data/processed/citibike_2026_H1.csv",
        usecols=["start_station_id"]
    )

    result = (
        df["start_station_id"]
        .value_counts()
        .head(10)
        .reset_index()
    )

    result.columns = ["station_id", "trips"]

    return result

# ============================================================
# RAW DATA FOR FILTER
# ============================================================

@st.cache_data
def load_raw_data():

    df = pd.read_csv(
        "data/processed/citibike_2026_H1.csv",
        usecols=[
            "started_at",
            "ended_at",
            "member_casual",
            "rideable_type",
            "start_station_id"
        ]
    )

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
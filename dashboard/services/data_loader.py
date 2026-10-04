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
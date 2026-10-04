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
    load_model_metrics,
    load_member_type,
    load_bike_type,
    load_top_stations,
    load_raw_data
)

from components.kpi import show_kpis

from components.charts import (
    show_prediction_chart,
    show_hourly_chart,
    show_daily_chart,
    show_member_chart,
    show_bike_type_chart,
    show_top_station_chart,
    show_model_comparison_chart
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

member_df = load_member_type()
bike_df = load_bike_type()
top_station_df = load_top_stations()

raw_df = load_raw_data()


# ============================================================
# FILTER
# ============================================================

st.sidebar.header("🔎 Dashboard Filters")


# ------------------------------------------------------------
# DATE FILTER
# ------------------------------------------------------------

if not raw_df.empty and "started_at" in raw_df.columns:

    min_date = raw_df["started_at"].min().date()
    max_date = raw_df["started_at"].max().date()

else:

    min_date = pd.Timestamp("2026-01-01").date()
    max_date = pd.Timestamp("2026-06-30").date()


date_range = st.sidebar.date_input(
    "📅 Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)


# ------------------------------------------------------------
# USER TYPE FILTER
# ------------------------------------------------------------

user_options = [
    "All",
    "Member",
    "Casual"
]

selected_user = st.sidebar.selectbox(
    "👤 User Type",
    user_options
)


# ------------------------------------------------------------
# BIKE TYPE FILTER
# ------------------------------------------------------------

bike_options = [
    "All",
    "Electric",
    "Classic"
]

selected_bike = st.sidebar.selectbox(
    "🚲 Bike Type",
    bike_options
)


# ============================================================
# APPLY FILTER
# ============================================================

filtered_raw_df = raw_df.copy()


# ------------------------------------------------------------
# Date filter
# ------------------------------------------------------------

if len(date_range) == 2:

    start_date = pd.Timestamp(date_range[0])

    end_date = (
        pd.Timestamp(date_range[1])
        + pd.Timedelta(days=1)
    )

    filtered_raw_df = filtered_raw_df[
        (
            filtered_raw_df["started_at"] >= start_date
        )
        &
        (
            filtered_raw_df["started_at"] < end_date
        )
    ]


# ------------------------------------------------------------
# User Type filter
# ------------------------------------------------------------

if selected_user != "All":

    filtered_raw_df = filtered_raw_df[
        filtered_raw_df["member_casual"].str.lower()
        == selected_user.lower()
    ]


# ------------------------------------------------------------
# Bike Type filter
# ------------------------------------------------------------

if selected_bike != "All":

    bike_mapping = {
        "Electric": "electric_bike",
        "Classic": "classic_bike"
    }

    selected_bike_value = bike_mapping[
        selected_bike
    ]

    filtered_raw_df = filtered_raw_df[
        filtered_raw_df["rideable_type"].str.lower()
        == selected_bike_value
    ]


# ============================================================
# FILTERED DATA CHECK
# ============================================================

if filtered_raw_df.empty:

    st.warning(
        "Không có dữ liệu phù hợp với bộ lọc hiện tại."
    )

    st.stop()


# ============================================================
# CREATE FILTERED MEMBER DATA
# ============================================================

filtered_member_df = (
    filtered_raw_df["member_casual"]
    .value_counts()
    .reset_index()
)

filtered_member_df.columns = [
    "member_casual",
    "trips"
]


# ============================================================
# CREATE FILTERED BIKE DATA
# ============================================================

filtered_bike_df = (
    filtered_raw_df["rideable_type"]
    .value_counts()
    .reset_index()
)

filtered_bike_df.columns = [
    "rideable_type",
    "trips"
]


# ============================================================
# CREATE FILTERED TOP STATIONS
# ============================================================

filtered_top_station_df = (
    filtered_raw_df["start_station_id"]
    .value_counts()
    .head(10)
    .reset_index()
)

filtered_top_station_df.columns = [
    "station_id",
    "trips"
]


# ============================================================
# CREATE FILTERED HOURLY DATA
# ============================================================

filtered_raw_df["hour"] = (
    filtered_raw_df["started_at"].dt.hour
)

filtered_hourly_actual = (
    filtered_raw_df
    .groupby("hour")
    .size()
    .reset_index(name="total_actual_demand")
)


# ------------------------------------------------------------
# Merge prediction data theo hour
# ------------------------------------------------------------

if (
    not prediction_df.empty
    and "datetime" in prediction_df.columns
    and "predicted_demand" in prediction_df.columns
):

    prediction_hourly = prediction_df.copy()

    prediction_hourly["hour"] = (
        prediction_hourly["datetime"].dt.hour
    )

    prediction_hourly = (
        prediction_hourly
        .groupby("hour")["predicted_demand"]
        .sum()
        .reset_index()
    )

    prediction_hourly.columns = [
        "hour",
        "total_predicted_demand"
    ]

    filtered_hourly_df = filtered_hourly_actual.merge(
        prediction_hourly,
        on="hour",
        how="left"
    )

else:

    filtered_hourly_df = filtered_hourly_actual


# ============================================================
# CREATE FILTERED DAILY DATA
# ============================================================

filtered_raw_df["date"] = (
    filtered_raw_df["started_at"].dt.date
)

filtered_daily_df = (
    filtered_raw_df
    .groupby("date")
    .size()
    .reset_index(name="actual_demand")
)

filtered_daily_df["date"] = pd.to_datetime(
    filtered_daily_df["date"]
)


# ------------------------------------------------------------
# Merge daily prediction
# ------------------------------------------------------------

if (
    not prediction_df.empty
    and "date" in prediction_df.columns
    and "predicted_demand" in prediction_df.columns
):

    prediction_daily = prediction_df.copy()

    prediction_daily["date"] = pd.to_datetime(
        prediction_daily["date"]
    )

    prediction_daily = (
        prediction_daily
        .groupby("date")["predicted_demand"]
        .sum()
        .reset_index()
    )

    filtered_daily_df = filtered_daily_df.merge(
        prediction_daily,
        on="date",
        how="left"
    )


# ============================================================
# FILTER PREDICTION DATA BY DATE
# ============================================================

filtered_prediction_df = prediction_df.copy()


if len(date_range) == 2:

    prediction_start = pd.Timestamp(date_range[0])

    prediction_end = (
        pd.Timestamp(date_range[1])
        + pd.Timedelta(days=1)
    )

    filtered_prediction_df = filtered_prediction_df[
        (
            filtered_prediction_df["datetime"]
            >= prediction_start
        )
        &
        (
            filtered_prediction_df["datetime"]
            < prediction_end
        )
    ]


# ============================================================
# KPI
# ============================================================

# ------------------------------------------------------------
# Tổng số chuyến sau Filter
# ------------------------------------------------------------

total_trips = len(filtered_raw_df)


# ------------------------------------------------------------
# Số ngày thực tế sau Filter
# ------------------------------------------------------------

if not filtered_raw_df.empty:

    total_days = (
        filtered_raw_df["started_at"]
        .dt.date
        .nunique()
    )

else:

    total_days = 1


avg_daily_trips = (
    total_trips / total_days
)


# ------------------------------------------------------------
# Tìm giờ có nhu cầu cao nhất
# ------------------------------------------------------------

if (
    not filtered_hourly_df.empty
    and "total_actual_demand"
    in filtered_hourly_df.columns
    and "hour"
    in filtered_hourly_df.columns
):

    peak_hour_row = filtered_hourly_df.loc[
        filtered_hourly_df[
            "total_actual_demand"
        ].idxmax()
    ]

    peak_hour = (
        f"{int(peak_hour_row['hour']):02d}:00"
    )

    peak_hour_trips = int(
        peak_hour_row["total_actual_demand"]
    )

else:

    peak_hour = "N/A"
    peak_hour_trips = 0


# ------------------------------------------------------------
# Lấy Test MAE của Random Forest
# ------------------------------------------------------------

test_mae = 24.8594

if (
    not metrics_df.empty
    and "model" in metrics_df.columns
    and "dataset" in metrics_df.columns
):

    rf_metrics = metrics_df[
        (
            metrics_df["model"].str.contains(
                "Random Forest",
                case=False,
                na=False
            )
        )
        &
        (
            metrics_df["dataset"]
            .astype(str)
            .str.lower()
            == "test"
        )
    ]

    if (
        not rf_metrics.empty
        and "mae" in rf_metrics.columns
    ):

        test_mae = float(
            rf_metrics.iloc[0]["mae"]
        )


# ============================================================
# DISPLAY KPI
# ============================================================

show_kpis(
    total_trips=total_trips,
    avg_daily_trips=avg_daily_trips,
    peak_hour=peak_hour,
    peak_hour_trips=peak_hour_trips,
    test_mae=test_mae
)


# ============================================================
# FILTER INFORMATION
# ============================================================

st.caption(
    f"Đang hiển thị {total_trips:,} chuyến "
    f"({total_days:,} ngày) "
    f"• User: {selected_user} "
    f"• Bike: {selected_bike}"
)


# ============================================================
# ACTUAL VS PREDICTED
# ============================================================

st.divider()

st.subheader("📈 Actual vs Predicted Demand")

show_prediction_chart(
    filtered_prediction_df
)


# ============================================================
# HOURLY + DAILY DEMAND
# ============================================================

st.divider()

col1, col2 = st.columns(2)


# ------------------------------------------------------------
# Demand by Hour
# ------------------------------------------------------------

with col1:

    st.subheader("🕐 Demand by Hour")

    show_hourly_chart(
        filtered_hourly_df
    )


# ------------------------------------------------------------
# Demand by Day
# ------------------------------------------------------------

with col2:

    st.subheader("📅 Demand by Day")

    show_daily_chart(
        filtered_daily_df
    )


# ============================================================
# MEMBER VS CASUAL
# ============================================================

st.divider()

st.subheader("👤 Member vs Casual")

if not filtered_member_df.empty:

    col1, col2 = st.columns(2)

    with col1:

        show_member_chart(
            filtered_member_df
        )

    with col2:

        st.dataframe(
            filtered_member_df,
            width="stretch"
        )

else:

    st.warning(
        "Không có dữ liệu Member vs Casual."
    )


# ============================================================
# ELECTRIC VS CLASSIC
# ============================================================

st.divider()

st.subheader("🚲 Bike Type")

if not filtered_bike_df.empty:

    col1, col2 = st.columns(2)

    with col1:

        show_bike_type_chart(
            filtered_bike_df
        )

    with col2:

        st.dataframe(
            filtered_bike_df,
            width="stretch"
        )

else:

    st.warning(
        "Không có dữ liệu loại xe."
    )


# ============================================================
# TOP 10 START STATIONS
# ============================================================

st.divider()

st.subheader("📍 Top 10 Start Stations")

if not filtered_top_station_df.empty:

    show_top_station_chart(
        filtered_top_station_df
    )

    st.dataframe(
        filtered_top_station_df,
        width="stretch"
    )

else:

    st.warning(
        "Không có dữ liệu Top Stations."
    )


# ============================================================
# MODEL COMPARISON
# ============================================================

st.divider()

st.subheader("🤖 Model Comparison")

show_model_comparison_chart(
    metrics_df
)


# ============================================================
# DATA PREVIEW
# ============================================================

st.divider()

st.subheader("📋 Prediction Data")

st.dataframe(
    filtered_prediction_df,
    width="stretch"
)
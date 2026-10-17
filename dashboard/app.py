import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import pydeck as pdk


# ============================================================
# IMPORT PATH
# ============================================================

DASHBOARD_DIR = Path(__file__).resolve().parent

if str(DASHBOARD_DIR) not in sys.path:
    sys.path.append(str(DASHBOARD_DIR))


from services.data_loader import (
    load_prediction_data,
    load_future_forecast_data,
    load_model_metrics,
    load_raw_data,
    load_station_activity,
    format_date_range_label
)

from components.kpi import show_kpis

import importlib
import components.charts
importlib.reload(components.charts)

from components.charts import (
    show_prediction_chart,
    show_hourly_chart,
    show_daily_chart,
    show_member_chart,
    show_bike_type_chart,
    show_top_station_chart,
    show_model_comparison_chart,
    show_future_forecast_chart,
    show_station_symbol_map
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="BikeDemand — Geospatial Intelligence",
    page_icon="🚲",
    layout="wide"
)


# ============================================================
# LOAD CUSTOM CSS (GEOSPATIAL INTELLIGENCE DESIGN SYSTEM)
# ============================================================

CSS_FILE = DASHBOARD_DIR / "static" / "style.css"
if CSS_FILE.exists():
    st.markdown(
        f"<style>{CSS_FILE.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True
    )


# ============================================================
# LOAD DATA
# ============================================================

prediction_df = load_prediction_data()

future_forecast_df = load_future_forecast_data()

metrics_df = load_model_metrics()

raw_df = load_raw_data()


# ============================================================
# SIDEBAR FILTER
# ============================================================

st.sidebar.title("🔎 Filters")

st.sidebar.caption(
    "Lọc dữ liệu để xem nhu cầu sử dụng Citi Bike."
)


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
    end_date = pd.Timestamp(date_range[1]) + pd.Timedelta(days=1)

    filtered_raw_df = filtered_raw_df[
        (filtered_raw_df["started_at"] >= start_date)
        & (filtered_raw_df["started_at"] < end_date)
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

    selected_bike_value = bike_mapping[selected_bike]

    filtered_raw_df = filtered_raw_df[
        filtered_raw_df["rideable_type"].str.lower()
        == selected_bike_value
    ]


# ============================================================
# PREDICTION FILTER CONTROL
# ============================================================

show_prediction = (
    selected_user == "All"
    and selected_bike == "All"
)


# ============================================================
# FILTERED DATA CHECK
# ============================================================

if filtered_raw_df.empty:
    st.warning("Không có dữ liệu phù hợp với bộ lọc hiện tại.")
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

filtered_raw_df["hour"] = filtered_raw_df["started_at"].dt.hour

filtered_hourly_actual = (
    filtered_raw_df
    .groupby("hour")
    .size()
    .reset_index(name="total_actual_demand")
)


# Merge prediction data theo hour
if (
    show_prediction
    and not prediction_df.empty
    and "datetime" in prediction_df.columns
    and "predicted_demand" in prediction_df.columns
):
    prediction_hourly = prediction_df.copy()
    prediction_hourly["hour"] = prediction_hourly["datetime"].dt.hour
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

filtered_raw_df["date"] = filtered_raw_df["started_at"].dt.date

filtered_daily_df = (
    filtered_raw_df
    .groupby("date")
    .size()
    .reset_index(name="actual_demand")
)

filtered_daily_df["date"] = pd.to_datetime(filtered_daily_df["date"])


# Merge daily prediction
prediction_daily = pd.DataFrame(
    columns=["date", "predicted_demand"]
)

if (
    show_prediction
    and not prediction_df.empty
    and "date" in prediction_df.columns
    and "predicted_demand" in prediction_df.columns
):
    prediction_daily = prediction_df.copy()
    prediction_daily["date"] = pd.to_datetime(prediction_daily["date"])
    prediction_daily = (
        prediction_daily
        .groupby("date")["predicted_demand"]
        .sum()
        .reset_index()
    )

filtered_actual_prediction_df = (
    filtered_daily_df
    .merge(
        prediction_daily,
        on="date",
        how="left"
    )
    .sort_values("date")
    .reset_index(drop=True)
)


# ============================================================
# FILTER PREDICTION DATA BY DATE
# ============================================================

filtered_prediction_df = prediction_df.copy()

if len(date_range) == 2:
    prediction_start = pd.Timestamp(date_range[0])
    prediction_end = pd.Timestamp(date_range[1]) + pd.Timedelta(days=1)

    filtered_prediction_df = filtered_prediction_df[
        (filtered_prediction_df["datetime"] >= prediction_start)
        & (filtered_prediction_df["datetime"] < prediction_end)
    ]


# ============================================================
# KPI CALCULATIONS
# ============================================================

total_trips = len(filtered_raw_df)

if len(date_range) == 2:
    selected_start_date = pd.Timestamp(date_range[0])
    selected_end_date = pd.Timestamp(date_range[1])
    total_days = (selected_end_date - selected_start_date).days + 1
else:
    total_days = 1

avg_daily_trips = total_trips / total_days

if (
    not filtered_hourly_df.empty
    and "total_actual_demand" in filtered_hourly_df.columns
    and "hour" in filtered_hourly_df.columns
):
    peak_hour_row = filtered_hourly_df.loc[
        filtered_hourly_df["total_actual_demand"].idxmax()
    ]
    peak_hour = f"{int(peak_hour_row['hour']):02d}:00"
    peak_hour_trips = int(peak_hour_row["total_actual_demand"])
else:
    peak_hour = "N/A"
    peak_hour_trips = 0

test_mae = 24.8594
if (
    not metrics_df.empty
    and "model" in metrics_df.columns
    and "dataset" in metrics_df.columns
):
    rf_metrics = metrics_df[
        (metrics_df["model"].str.contains("Random Forest", case=False, na=False))
        & (metrics_df["dataset"].astype(str).str.lower() == "test")
    ]
    if not rf_metrics.empty and "mae" in rf_metrics.columns:
        test_mae = float(rf_metrics.iloc[0]["mae"])


# ============================================================
# PREPARE STATION MAP DATA (PHASE 3)
# ============================================================

start_map_date = date_range[0] if len(date_range) >= 1 else None
end_map_date = date_range[1] if len(date_range) == 2 else None

is_full_range = (
    len(date_range) == 2
    and date_range[0] == min_date
    and date_range[1] == max_date
)

if is_full_range:
    station_df = load_station_activity(None, None)
    map_date_label = f"Toàn bộ dữ liệu ({min_date.strftime('%d/%m/%Y')} — {max_date.strftime('%d/%m/%Y')})"
else:
    station_df = load_station_activity(start_map_date, end_map_date)
    map_date_label = format_date_range_label(start_map_date, end_map_date)


# ============================================================
# 6 TABS NAVIGATION (DESKTOP: LOGO + 6 TABS ON ONE ROW)
# ============================================================

tab_overview, tab_map, tab_forecast, tab_user_bike, tab_demand, tab_model = st.tabs([
    "Tổng quan",
    "Bản đồ trạm",
    "Dự báo",
    "Người dùng & xe",
    "Phân tích nhu cầu",
    "Machine Learning"
])


# ============================================================
# TAB 1: TỔNG QUAN
# ============================================================

with tab_overview:
    # 1. 5 KPI Cards Tổng quan
    show_kpis(
        total_trips=total_trips,
        avg_daily_trips=avg_daily_trips,
        peak_hour=peak_hour,
        peak_hour_trips=peak_hour_trips,
        test_mae=test_mae
    )

    # 2. Thông tin tóm tắt trạng thái bộ lọc
    st.info(
        f"📊 Đang hiển thị **{total_trips:,} chuyến** "
        f"trong **{total_days:,} ngày** "
        f"• User: **{selected_user}** "
        f"• Bike: **{selected_bike}**"
    )

    # 3. Lưới 2 cột cho các biểu đồ chính
    col_ov1, col_ov2 = st.columns(2)

    with col_ov1:
        st.subheader("📈 Xu hướng Nhu cầu Theo Ngày (Actual vs Predicted)")
        show_prediction_chart(
            filtered_actual_prediction_df,
            key="overview_daily_demand"
        )

    with col_ov2:
        st.subheader("🕐 Phân bố Nhu cầu theo Giờ")
        show_hourly_chart(
            filtered_hourly_df,
            key="overview_hourly_demand"
        )


# ============================================================
# TAB 2: BẢN ĐỒ TRẠM (STATION COMPOSITE MAP)
# ============================================================

with tab_map:
    st.header("🗺️ Bản đồ trạm (Station Composite Map)")
    st.caption(
        "Bản đồ hoạt động các trạm xe đạp Citi Bike kết hợp Point/Proportional Symbol Map "
        "và lớp nhiệt nền (Heatmap) thể hiện mật độ tập trung nhu cầu."
    )

    # 1. Các bộ điều khiển nằm phía trên bản đồ
    col_map_ctrl1, col_map_ctrl2, col_map_ctrl3 = st.columns([2, 1, 1])

    with col_map_ctrl1:
        st.markdown(f"📅 **Phạm vi ngày:** `{map_date_label}`")

    with col_map_ctrl2:
        selected_style_name = st.selectbox(
            "🗺️ Nền bản đồ",
            options=[
                "CARTO Dark Matter (Tối)",
                "CARTO Positron (Sáng)",
                "CARTO Voyager (Chi tiết)"
            ],
            index=0,
            help="Lớp nền bản đồ địa lý thực tế (vector tiles: đường phố, công viên, địa danh)"
        )

    with col_map_ctrl3:
        toggle_heatmap = st.checkbox(
            "🔥 Bật Heatmap nền",
            value=True,
            help="Bật/tắt lớp nhiệt mật độ tập trung nhu cầu bên dưới các marker trạm"
        )

    STYLE_MAPPING = {
        "CARTO Dark Matter (Tối)": pdk.map_styles.CARTO_DARK,
        "CARTO Positron (Sáng)": pdk.map_styles.CARTO_LIGHT,
        "CARTO Voyager (Chi tiết)": pdk.map_styles.CARTO_ROAD,
    }
    chosen_map_style = STYLE_MAPPING.get(selected_style_name, pdk.map_styles.CARTO_DARK)

    # 2. 5 Station Metrics cards
    if not station_df.empty:
        st_active_count = len(station_df)
        st_total_activity = int(station_df["activity_count"].sum())
        st_total_starts = int(station_df["start_count"].sum())
        st_total_ends = int(station_df["end_count"].sum())
        top_station_row = station_df.iloc[0]
        top_station_name = top_station_row["station_name"]
        top_station_activity = int(top_station_row["activity_count"])

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.metric("📍 Số trạm hoạt động", f"{st_active_count:,}")
        with m2:
            st.metric("🔄 Tổng hoạt động", f"{st_total_activity:,}")
        with m3:
            st.metric("🟢 Lượt bắt đầu", f"{st_total_starts:,}")
        with m4:
            st.metric("🔴 Lượt kết thúc", f"{st_total_ends:,}")
        with m5:
            st.metric(
                "🏆 Trạm sôi động nhất",
                f"{top_station_activity:,}",
                help=f"{top_station_name} (ID: {top_station_row['station_id']})"
            )

    # 3. Bản đồ PyDeck chiếm gần hết chiều rộng vùng nội dung (kèm Legend 4 cấp)
    try:
        show_station_symbol_map(
            station_df,
            show_heatmap=toggle_heatmap,
            date_label=map_date_label,
            map_style=chosen_map_style,
        )
    except Exception as e:
        st.error(f"⚠️ Có lỗi xảy ra khi hiển thị bản đồ trạm: {e}")

    # 4. Bảng danh sách và xếp hạng hoạt động các trạm trong expander
    if not station_df.empty:
        with st.expander("📋 Xem danh sách & xếp hạng hoạt động các trạm"):
            st.caption(
                "Dữ liệu tổng hợp trực tiếp từ PostgreSQL theo các trạm có hoạt động trong phạm vi lọc."
            )
            table_cols = [
                "station_id",
                "station_name",
                "start_count",
                "end_count",
                "activity_count",
                "latitude",
                "longitude",
            ]
            display_table = station_df[[c for c in table_cols if c in station_df.columns]].copy()
            display_table.rename(
                columns={
                    "station_id": "Mã trạm",
                    "station_name": "Tên trạm",
                    "start_count": "Lượt bắt đầu",
                    "end_count": "Lượt kết thúc",
                    "activity_count": "Tổng hoạt động",
                    "latitude": "Vĩ độ",
                    "longitude": "Kinh độ",
                },
                inplace=True
            )
            st.dataframe(display_table, width="stretch", hide_index=True)


# ============================================================
# TAB 3: DỰ BÁO (FUTURE DEMAND FORECAST — 168 HOURS)
# ============================================================

with tab_forecast:
    st.header("🔮 Dự báo (Future Demand Forecast)")
    st.caption(
        "Dự báo nhu cầu sử dụng Citi Bike trong 7 ngày (168 giờ tiếp theo) "
        "sử dụng mô hình **Random Forest (future-v1)** với thuật toán Recursive Forecasting."
    )

    if future_forecast_df.empty:
        st.info(
            "ℹ️ Chưa có dữ liệu dự báo tương lai (`future-v1`) trong cơ sở dữ liệu. "
            "Vui lòng chạy module dự báo: `python analysis/ml/08_future_forecast.py`."
        )
    else:
        # Thống kê cơ bản
        total_points = len(future_forecast_df)
        start_time = future_forecast_df["target_time"].min()
        end_time = future_forecast_df["target_time"].max()
        mean_demand = future_forecast_df["predicted_demand"].mean()
        min_demand = future_forecast_df["predicted_demand"].min()
        max_demand = future_forecast_df["predicted_demand"].max()
        total_forecast_demand = future_forecast_df["predicted_demand"].sum()

        # 5 KPI cards dự báo
        col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5 = st.columns(5)

        with col_kpi1:
            st.metric(
                label="⏱️ Chu kỳ dự báo",
                value=f"{total_points} giờ",
                help="7 ngày liên tục (168 giờ)",
            )
        with col_kpi2:
            st.metric(
                label="📅 Khoảng thời gian",
                value=f"{start_time.strftime('%d/%m')} → {end_time.strftime('%d/%m')}",
                help=f"{start_time} đến {end_time}",
            )
        with col_kpi3:
            st.metric(
                label="📊 TB / giờ (Mean)",
                value=f"{mean_demand:.1f}",
                help="Số chuyến trung bình mỗi giờ",
            )
        with col_kpi4:
            st.metric(
                label="⚡ Đỉnh tải (Max)",
                value=f"{max_demand:.1f}",
                help=f"Giờ cao điểm: {future_forecast_df.loc[future_forecast_df['predicted_demand'].idxmax()]['target_time'].strftime('%d/%m %H:00')}",
            )
        with col_kpi5:
            st.metric(
                label="🌙 Đáy đêm (Min)",
                value=f"{min_demand:.1f}",
                help=f"Giờ thấp điểm: {future_forecast_df.loc[future_forecast_df['predicted_demand'].idxmin()]['target_time'].strftime('%d/%m %H:00')}",
            )

        pred_time_str = "N/A"
        if "prediction_time" in future_forecast_df.columns and not future_forecast_df["prediction_time"].isnull().all():
            pred_time_str = str(future_forecast_df["prediction_time"].iloc[0])

        st.caption(
            f"**Mô hình:** Random Forest • **Phiên bản:** `future-v1` • **Tổng nhu cầu 7 ngày:** {total_forecast_demand:,.0f} chuyến • **Thời điểm chạy:** {pred_time_str}"
        )

        # Biểu đồ đường dự báo 168 giờ
        show_future_forecast_chart(
            future_forecast_df,
            key="forecast_168h_demand"
        )

        # Bảng dữ liệu chi tiết
        with st.expander("📋 Xem bảng dữ liệu Future Forecast (168 dòng)"):
            st.caption(
                "Dữ liệu chi tiết từng giờ được đọc trực tiếp từ PostgreSQL bảng `predictions`."
            )
            preview_df = future_forecast_df.copy()
            preview_df["target_time"] = preview_df["target_time"].dt.strftime("%Y-%m-%d %H:%M")
            st.dataframe(preview_df, width="stretch")


# ============================================================
# TAB 4: NGƯỜI DÙNG & XE (USER & BIKE ANALYSIS)
# ============================================================

with tab_user_bike:
    st.header("👥 Người dùng & xe")

    col_u1, col_u2 = st.columns(2)

    with col_u1:
        st.subheader("👤 User Type")
        if not filtered_member_df.empty:
            show_member_chart(
                filtered_member_df,
                key="user_member_casual"
            )
            st.dataframe(filtered_member_df, width="stretch")
        else:
            st.warning("Không có dữ liệu Member vs Casual.")

    with col_u2:
        st.subheader("🚲 Bike Type")
        if not filtered_bike_df.empty:
            show_bike_type_chart(
                filtered_bike_df,
                key="user_bike_type"
            )
            st.dataframe(filtered_bike_df, width="stretch")
        else:
            st.warning("Không có dữ liệu loại xe.")


# ============================================================
# TAB 5: PHÂN TÍCH NHU CẦU (DEMAND ANALYSIS)
# ============================================================

with tab_demand:
    st.header("📈 Phân tích nhu cầu")

    if not show_prediction:
        st.info(
            "ℹ️ Prediction chỉ áp dụng cho tổng nhu cầu "
            "và được ẩn khi lọc theo User Type hoặc Bike Type."
        )

    st.subheader("Actual vs Predicted Demand")
    show_prediction_chart(
        filtered_actual_prediction_df,
        key="demand_actual_vs_predicted"
    )

    col_d1, col_d2 = st.columns(2)

    with col_d1:
        st.subheader("🕐 Demand by Hour")
        show_hourly_chart(
            filtered_hourly_df,
            key="demand_by_hour"
        )

    with col_d2:
        st.subheader("📅 Demand by Day")
        show_daily_chart(
            filtered_actual_prediction_df,
            key="demand_by_day"
        )


# ============================================================
# TAB 6: MÔ HÌNH (MACHINE LEARNING & DATA PREVIEW)
# ============================================================

with tab_model:
    st.header("🤖 Machine Learning")

    st.subheader("Model Comparison")
    show_model_comparison_chart(
        metrics_df,
        key="model"
    )

    st.divider()

    with st.expander("📋 View Prediction Data"):
        if show_prediction:
            st.caption(
                "Dữ liệu dự báo được sử dụng cho biểu đồ Actual vs Predicted."
            )
            st.dataframe(filtered_prediction_df, width="stretch")
        else:
            st.info(
                "ℹ️ Prediction chỉ áp dụng cho tổng nhu cầu. "
                "Dữ liệu dự báo được ẩn khi lọc theo "
                "User Type hoặc Bike Type."
            )
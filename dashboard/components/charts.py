import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# ACTUAL VS PREDICTED
# ============================================================

def show_prediction_chart(df):

    # --------------------------------------------------------
    # Kiểm tra dữ liệu
    # --------------------------------------------------------

    if df.empty:

        st.warning(
            "Không có dữ liệu trong khoảng thời gian đã chọn."
        )

        return


    # --------------------------------------------------------
    # Copy dữ liệu
    # --------------------------------------------------------

    plot_df = df.copy()


    # --------------------------------------------------------
    # Kiểm tra cột date
    # --------------------------------------------------------

    if "date" not in plot_df.columns:

        st.warning(
            "Dữ liệu Actual vs Predicted không có cột 'date'."
        )

        return


    # --------------------------------------------------------
    # Chuẩn hóa date
    # --------------------------------------------------------

    plot_df["date"] = pd.to_datetime(
        plot_df["date"]
    )

    plot_df = (
        plot_df
        .sort_values("date")
        .reset_index(drop=True)
    )


    # ========================================================
    # KIỂM TRA DỮ LIỆU ACTUAL / PREDICTED
    # ========================================================

    has_actual = (
        "actual_demand"
        in plot_df.columns
    )

    has_predicted = (
        "predicted_demand"
        in plot_df.columns
    )


    if not has_actual and not has_predicted:

        st.warning(
            "Không tìm thấy dữ liệu Actual hoặc Predicted."
        )

        return


    # ========================================================
    # TẠO BIỂU ĐỒ
    # ========================================================

    fig = go.Figure()


    # --------------------------------------------------------
    # Actual
    # --------------------------------------------------------

    if has_actual:

        fig.add_trace(
            go.Scatter(
                x=plot_df["date"],
                y=plot_df["actual_demand"],
                mode="lines+markers",
                name="Actual"
            )
        )


    # --------------------------------------------------------
    # Predicted
    # --------------------------------------------------------

    if has_predicted:

        fig.add_trace(
            go.Scatter(
                x=plot_df["date"],
                y=plot_df["predicted_demand"],
                mode="lines+markers",
                name="Predicted"
            )
        )


    # ========================================================
    # LAYOUT
    # ========================================================

    fig.update_layout(
        title="Actual vs Predicted Demand — Daily",
        xaxis_title="Date",
        yaxis_title="Number of Trips",
        hovermode="x unified",
        legend_title="Demand Type",
        xaxis=dict(
            tickangle=0
        )
    )


    # ========================================================
    # DISPLAY
    # ========================================================

    st.plotly_chart(
        fig,
        width="stretch"
    )


# ============================================================
# DEMAND BY HOUR
# ============================================================

def show_hourly_chart(df):

    fig = go.Figure()

    # --------------------------------------------------------
    # Actual demand
    # --------------------------------------------------------

    if "total_actual_demand" in df.columns:

        fig.add_trace(
            go.Bar(
                x=df["hour"],
                y=df["total_actual_demand"],
                name="Actual"
            )
        )

    # --------------------------------------------------------
    # Predicted demand
    # --------------------------------------------------------

    if "total_predicted_demand" in df.columns:

        fig.add_trace(
            go.Bar(
                x=df["hour"],
                y=df["total_predicted_demand"],
                name="Predicted"
            )
        )

    fig.update_layout(
        title="Demand by Hour",
        xaxis_title="Hour",
        yaxis_title="Total Trips",
        barmode="group",
        hovermode="x unified",
        xaxis=dict(
            tickangle=0
        )
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )


# ============================================================
# DEMAND BY DAY
# ============================================================

def show_daily_chart(df):

    # --------------------------------------------------------
    # Kiểm tra cột ngày
    # --------------------------------------------------------

    if "date" not in df.columns:

        st.warning(
            "Daily data không có cột 'date'."
        )

        return


    # --------------------------------------------------------
    # Tạo biểu đồ
    # --------------------------------------------------------

    fig = go.Figure()


    # --------------------------------------------------------
    # Actual demand
    # --------------------------------------------------------

    if "actual_demand" in df.columns:

        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["actual_demand"],
                mode="lines+markers",
                name="Actual"
            )
        )


    # --------------------------------------------------------
    # Predicted demand
    # --------------------------------------------------------

    if "predicted_demand" in df.columns:

        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["predicted_demand"],
                mode="lines+markers",
                name="Predicted"
            )
        )


    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    fig.update_layout(
        title="Demand by Day",
        xaxis_title="Date",
        yaxis_title="Number of Trips",
        hovermode="x unified",
        legend_title="Demand Type",
        xaxis=dict(
            tickangle=0
        )
    )


    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    st.plotly_chart(
        fig,
        width="stretch"
    )


# ============================================================
# MEMBER VS CASUAL
# ============================================================

def show_member_chart(df):

    fig = go.Figure()

    # --------------------------------------------------------
    # Member / Casual
    # --------------------------------------------------------

    fig.add_trace(
        go.Bar(
            x=df["member_casual"],
            y=df["trips"],
            text=df["trips"],
            textposition="auto",
            name="Trips"
        )
    )

    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    fig.update_layout(
        title="Member vs Casual",
        xaxis_title="User Type",
        yaxis_title="Number of Trips",
        xaxis=dict(
            tickangle=0
        ),
        yaxis=dict(
            rangemode="tozero"
        )
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )


# ============================================================
# BIKE TYPE
# ============================================================

def show_bike_type_chart(df):

    fig = go.Figure()

    # --------------------------------------------------------
    # Bike type
    # --------------------------------------------------------

    fig.add_trace(
        go.Bar(
            x=df["rideable_type"],
            y=df["trips"],
            text=df["trips"],
            textposition="auto",
            name="Trips"
        )
    )

    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    fig.update_layout(
        title="Bike Type",
        xaxis_title="Bike Type",
        yaxis_title="Number of Trips",
        xaxis=dict(
            tickangle=0
        ),
        yaxis=dict(
            rangemode="tozero"
        )
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )


# ============================================================
# TOP 10 START STATIONS
# ============================================================

def show_top_station_chart(df):

    fig = go.Figure()

    # --------------------------------------------------------
    # Top stations
    # --------------------------------------------------------

    fig.add_trace(
        go.Bar(
            x=df["trips"],
            y=df["station_id"],
            orientation="h",
            text=df["trips"],
            textposition="auto",
            name="Trips"
        )
    )

    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    fig.update_layout(
        title="Top 10 Start Stations",
        xaxis_title="Number of Trips",
        yaxis_title="Station ID",
        xaxis=dict(
            rangemode="tozero"
        )
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )


# ============================================================
# MODEL COMPARISON
# ============================================================

def show_model_comparison_chart(df):

    # --------------------------------------------------------
    # Chỉ lấy kết quả TEST
    # --------------------------------------------------------

    test_df = df[
        df["dataset"].astype(str).str.lower() == "test"
    ].copy()

    if test_df.empty:

        st.warning(
            "Không có dữ liệu test để so sánh model."
        )

        return


    # ========================================================
    # MAE + RMSE
    # ========================================================

    fig = go.Figure()

    # --------------------------------------------------------
    # MAE
    # --------------------------------------------------------

    if "mae" in test_df.columns:

        fig.add_trace(
            go.Bar(
                x=test_df["model"],
                y=test_df["mae"],
                text=test_df["mae"].round(2),
                textposition="auto",
                name="MAE"
            )
        )


    # --------------------------------------------------------
    # RMSE
    # --------------------------------------------------------

    if "rmse" in test_df.columns:

        fig.add_trace(
            go.Bar(
                x=test_df["model"],
                y=test_df["rmse"],
                text=test_df["rmse"].round(2),
                textposition="auto",
                name="RMSE"
            )
        )


    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    fig.update_layout(
        title="Model Comparison — MAE & RMSE",
        xaxis_title="Model",
        yaxis_title="Error",
        barmode="group",
        hovermode="x unified",
        xaxis=dict(
            tickangle=0
        )
    )


    st.plotly_chart(
        fig,
        width="stretch"
    )


    # ========================================================
    # R²
    # ========================================================

    fig_r2 = go.Figure()

    # --------------------------------------------------------
    # R²
    # --------------------------------------------------------

    if "r2" in test_df.columns:

        fig_r2.add_trace(
            go.Bar(
                x=test_df["model"],
                y=test_df["r2"],
                text=test_df["r2"].round(3),
                textposition="auto",
                name="R²"
            )
        )


    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    fig_r2.update_layout(
        title="Model Comparison — R²",
        xaxis_title="Model",
        yaxis_title="R²",
        yaxis=dict(
            range=[0, 1]
        ),
        xaxis=dict(
            tickangle=0
        )
    )


    st.plotly_chart(
        fig_r2,
        width="stretch"
    )
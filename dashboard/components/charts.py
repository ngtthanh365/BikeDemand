import plotly.graph_objects as go
import streamlit as st


# ============================================================
# ACTUAL VS PREDICTED
# ============================================================

def show_prediction_chart(df):

    fig = go.Figure()

    # --------------------------------------------------------
    # Actual
    # --------------------------------------------------------

    if "actual_demand" in df.columns:

        fig.add_trace(
            go.Scatter(
                x=df["datetime"],
                y=df["actual_demand"],
                mode="lines",
                name="Actual"
            )
        )

    # --------------------------------------------------------
    # Predicted
    # --------------------------------------------------------

    if "predicted_demand" in df.columns:

        fig.add_trace(
            go.Scatter(
                x=df["datetime"],
                y=df["predicted_demand"],
                mode="lines",
                name="Predicted"
            )
        )

    fig.update_layout(
        title="Actual vs Predicted Demand",
        xaxis_title="Time",
        yaxis_title="Number of Trips",
        hovermode="x unified",
        legend_title="Demand Type"
    )

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
        hovermode="x unified"
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
        legend_title="Demand Type"
    )


    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    st.plotly_chart(
        fig,
        width="stretch"
    )


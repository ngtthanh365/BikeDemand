import streamlit as st


def show_kpis(
    total_trips,
    avg_daily_trips,
    peak_hour,
    peak_hour_trips,
    model_mae
):
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Total Trips",
            f"{total_trips:,}"
        )

    with col2:
        st.metric(
            "Avg Trips / Day",
            f"{avg_daily_trips:,.0f}"
        )

    with col3:
        st.metric(
            "Peak Hour",
            peak_hour
        )

    with col4:
        st.metric(
            "Peak Hour Trips",
            f"{peak_hour_trips:,}"
        )

    with col5:
        st.metric(
            "Prediction MAE",
            f"{model_mae:.2f}"
        )
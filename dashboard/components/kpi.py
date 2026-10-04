import streamlit as st


def show_kpis(
    total_trips,
    avg_daily_trips,
    peak_hour,
    peak_hour_trips,
    test_mae
):
    col1, col2, col3, col4, col5 = st.columns(
        5,
        gap="medium"
    )

    with col1:
        st.metric(
            label="🚲 Total Trips",
            value=f"{total_trips:,}",
            help="Tổng số chuyến xe trong khoảng thời gian đã chọn."
        )

    with col2:
        st.metric(
            label="📊 Avg Trips / Day",
            value=f"{avg_daily_trips:,.0f}",
            help="Số chuyến xe trung bình mỗi ngày."
        )

    with col3:
        st.metric(
            label="🕐 Peak Hour",
            value=peak_hour,
            help="Khung giờ có nhu cầu sử dụng xe cao nhất."
        )

    with col4:
        st.metric(
            label="🔥 Peak Hour Trips",
            value=f"{peak_hour_trips:,}",
            help="Số chuyến xe được ghi nhận trong giờ cao điểm."
        )

    with col5:
        st.metric(
            label="🤖 Test MAE",
            value=f"{test_mae:.2f}",
            help="Sai số tuyệt đối trung bình của mô hình Random Forest trên tập Test."
        )
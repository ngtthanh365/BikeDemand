import streamlit as st


def show_kpis(
    total_trips,
    avg_daily_trips,
    peak_hour,
    peak_hour_trips,
    test_mae
):
    """
    Hiển thị 5 thẻ KPI tổng quan chuẩn phong cách Geospatial Intelligence:
    Nền card #111D38, viền mỏng, bo góc, phân cấp chữ rõ ràng và hover nhẹ tối đa 2px.
    """
    col1, col2, col3, col4, col5 = st.columns(
        5,
        gap="medium"
    )

    kpi_items = [
        (
            col1,
            "🚲 TOTAL TRIPS",
            f"{total_trips:,}",
            "Tổng số chuyến xe trong khoảng thời gian đã chọn.",
            "#00F2FE",
            "kpi-cyan",
        ),
        (
            col2,
            "📊 AVG TRIPS / DAY",
            f"{avg_daily_trips:,.0f}",
            "Số chuyến xe trung bình mỗi ngày.",
            "#38BDF8",
            "kpi-blue",
        ),
        (
            col3,
            "🕐 PEAK HOUR",
            str(peak_hour),
            "Khung giờ có nhu cầu sử dụng xe cao nhất.",
            "#FBBF24",
            "kpi-amber",
        ),
        (
            col4,
            "🔥 PEAK HOUR TRIPS",
            f"{peak_hour_trips:,}",
            "Số chuyến ghi nhận trong giờ cao điểm.",
            "#F97316",
            "kpi-orange",
        ),
        (
            col5,
            "🤖 TEST MAE",
            f"{test_mae:.2f}",
            "Sai số tuyệt đối trung bình của Random Forest trên tập Test.",
            "#10B981",
            "kpi-emerald",
        ),
    ]

    for col, label, value, help_text, accent_color, css_class in kpi_items:
        with col:
            st.markdown(
                f"""
                <div class="kpi-card {css_class}">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value" style="color: {accent_color};">{value}</div>
                    <div class="kpi-help">{help_text}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st


# ============================================================
# PLOTLY DARK THEME HELPER (GEOSPATIAL INTELLIGENCE)
# ============================================================

def _apply_dark_theme(
    fig: go.Figure,
    title: str = "",
    xaxis_title: str | None = None,
    yaxis_title: str | None = None,
    barmode: str | None = None,
    hovermode: str = "x unified",
    legend_title: str | None = None,
    extra_layout: dict | None = None
) -> go.Figure:
    """
    Áp dụng Dark Theme chuẩn Geospatial Intelligence cho biểu đồ Plotly:
    - Nền tối #111D38 / trong suốt hòa nhập với giao diện.
    - Lưới tọa độ mờ nhẹ (rgba(148, 163, 184, 0.14)).
    - Typography rõ ràng, màu chữ sáng #F8FAFC và #94A3B8.
    - Legend có khung nền và viền kính nhẹ.
    """
    layout_args = dict(
        template="plotly_dark",
        paper_bgcolor="rgba(17, 29, 56, 0.4)",
        plot_bgcolor="rgba(11, 19, 41, 0.3)",
        font=dict(
            family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
            color="#E2E8F0",
            size=12
        ),
        hovermode=hovermode,
        xaxis=dict(
            gridcolor="rgba(148, 163, 184, 0.14)",
            zerolinecolor="rgba(148, 163, 184, 0.2)",
            tickfont=dict(color="#94A3B8"),
            title_font=dict(color="#CBD5E1"),
            tickangle=0
        ),
        yaxis=dict(
            gridcolor="rgba(148, 163, 184, 0.14)",
            zerolinecolor="rgba(148, 163, 184, 0.2)",
            tickfont=dict(color="#94A3B8"),
            title_font=dict(color="#CBD5E1")
        ),
        legend=dict(
            bgcolor="rgba(17, 29, 56, 0.8)",
            bordercolor="rgba(148, 163, 184, 0.2)",
            borderwidth=1,
            font=dict(color="#E2E8F0", size=11)
        ),
        margin=dict(l=45, r=30, t=50, b=45)
    )

    if title:
        layout_args["title"] = dict(
            text=title,
            font=dict(size=14, color="#F8FAFC"),
            x=0.01,
            xanchor="left"
        )
    if xaxis_title:
        layout_args["xaxis"]["title"] = xaxis_title
    if yaxis_title:
        layout_args["yaxis"]["title"] = yaxis_title
    if barmode:
        layout_args["barmode"] = barmode
    if legend_title:
        layout_args["legend"]["title"] = dict(text=legend_title, font=dict(color="#94A3B8", size=11))
    if extra_layout:
        layout_args.update(extra_layout)

    fig.update_layout(**layout_args)
    return fig


# ============================================================
# ACTUAL VS PREDICTED
# ============================================================

def show_prediction_chart(df, key: str | None = None):
    if df.empty:
        st.warning("Không có dữ liệu trong khoảng thời gian đã chọn.")
        return

    plot_df = df.copy()

    if "date" not in plot_df.columns:
        st.warning("Dữ liệu Actual vs Predicted không có cột 'date'.")
        return

    plot_df["date"] = pd.to_datetime(plot_df["date"])
    plot_df = plot_df.sort_values("date").reset_index(drop=True)

    has_actual = "actual_demand" in plot_df.columns
    has_predicted = "predicted_demand" in plot_df.columns

    if not has_actual and not has_predicted:
        st.warning("Không tìm thấy dữ liệu Actual hoặc Predicted.")
        return

    fig = go.Figure()

    if has_actual:
        fig.add_trace(
            go.Scatter(
                x=plot_df["date"],
                y=plot_df["actual_demand"],
                mode="lines+markers",
                name="Actual",
                line=dict(color="#00F2FE", width=2.5),
                marker=dict(size=5, color="#38BDF8"),
                hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Actual:</b> %{y:,} trips<extra></extra>"
            )
        )

    if has_predicted:
        fig.add_trace(
            go.Scatter(
                x=plot_df["date"],
                y=plot_df["predicted_demand"],
                mode="lines+markers",
                name="Predicted",
                line=dict(color="#F97316", width=2.5, dash="dash"),
                marker=dict(size=5, color="#FBBF24"),
                hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Predicted:</b> %{y:,.1f} trips<extra></extra>"
            )
        )

    _apply_dark_theme(
        fig,
        title="Actual vs Predicted Demand — Daily",
        xaxis_title="Date",
        yaxis_title="Number of Trips",
        legend_title="Demand Type"
    )

    st.plotly_chart(fig, width="stretch", key=key)


# ============================================================
# DEMAND BY HOUR
# ============================================================

def show_hourly_chart(df, key: str | None = None):
    fig = go.Figure()

    if "total_actual_demand" in df.columns:
        fig.add_trace(
            go.Bar(
                x=df["hour"],
                y=df["total_actual_demand"],
                name="Actual",
                marker=dict(
                    color="#00F2FE",
                    opacity=0.9,
                    line=dict(color="#38BDF8", width=1)
                ),
                hovertemplate="<b>Hour:</b> %{x}:00<br><b>Actual:</b> %{y:,} trips<extra></extra>"
            )
        )

    if "total_predicted_demand" in df.columns:
        fig.add_trace(
            go.Bar(
                x=df["hour"],
                y=df["total_predicted_demand"],
                name="Predicted",
                marker=dict(
                    color="#F97316",
                    opacity=0.9,
                    line=dict(color="#FBBF24", width=1)
                ),
                hovertemplate="<b>Hour:</b> %{x}:00<br><b>Predicted:</b> %{y:,.1f} trips<extra></extra>"
            )
        )

    _apply_dark_theme(
        fig,
        title="Demand by Hour",
        xaxis_title="Hour",
        yaxis_title="Total Trips",
        barmode="group",
        hovermode="x unified"
    )

    st.plotly_chart(fig, width="stretch", key=key)


# ============================================================
# DEMAND BY DAY
# ============================================================

def show_daily_chart(df, key: str | None = None):
    if "date" not in df.columns:
        st.warning("Daily data không có cột 'date'.")
        return

    fig = go.Figure()

    if "actual_demand" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["actual_demand"],
                mode="lines+markers",
                name="Actual",
                line=dict(color="#00F2FE", width=2),
                marker=dict(size=4, color="#38BDF8"),
                hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Actual:</b> %{y:,} trips<extra></extra>"
            )
        )

    if "predicted_demand" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["predicted_demand"],
                mode="lines+markers",
                name="Predicted",
                line=dict(color="#F97316", width=2, dash="dash"),
                marker=dict(size=4, color="#FBBF24"),
                hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Predicted:</b> %{y:,.1f} trips<extra></extra>"
            )
        )

    _apply_dark_theme(
        fig,
        title="Demand by Day",
        xaxis_title="Date",
        yaxis_title="Number of Trips",
        legend_title="Demand Type"
    )

    st.plotly_chart(fig, width="stretch", key=key)


# ============================================================
# MEMBER VS CASUAL
# ============================================================

def show_member_chart(df, key: str | None = None):
    fig = go.Figure()

    colors = ["#00F2FE", "#F97316"] if len(df) == 2 else ["#00F2FE"] * len(df)

    fig.add_trace(
        go.Bar(
            x=df["member_casual"],
            y=df["trips"],
            text=df["trips"],
            textposition="auto",
            texttemplate="%{text:,}",
            textfont=dict(color="#FFFFFF", weight=700),
            name="Trips",
            marker=dict(
                color=colors,
                opacity=0.9,
                line=dict(color="rgba(255, 255, 255, 0.2)", width=1)
            ),
            hovertemplate="<b>User Type:</b> %{x}<br><b>Trips:</b> %{y:,}<extra></extra>"
        )
    )

    _apply_dark_theme(
        fig,
        title="Member vs Casual",
        xaxis_title="User Type",
        yaxis_title="Number of Trips",
        hovermode="closest",
        extra_layout=dict(
            yaxis=dict(
                rangemode="tozero",
                gridcolor="rgba(148, 163, 184, 0.14)"
            )
        )
    )

    st.plotly_chart(fig, width="stretch", key=key)


# ============================================================
# BIKE TYPE
# ============================================================

def show_bike_type_chart(df, key: str | None = None):
    fig = go.Figure()

    colors = ["#00F2FE", "#38BDF8"] if len(df) == 2 else ["#00F2FE"] * len(df)

    fig.add_trace(
        go.Bar(
            x=df["rideable_type"],
            y=df["trips"],
            text=df["trips"],
            textposition="auto",
            texttemplate="%{text:,}",
            textfont=dict(color="#FFFFFF", weight=700),
            name="Trips",
            marker=dict(
                color=colors,
                opacity=0.9,
                line=dict(color="rgba(255, 255, 255, 0.2)", width=1)
            ),
            hovertemplate="<b>Bike Type:</b> %{x}<br><b>Trips:</b> %{y:,}<extra></extra>"
        )
    )

    _apply_dark_theme(
        fig,
        title="Bike Type",
        xaxis_title="Bike Type",
        yaxis_title="Number of Trips",
        hovermode="closest",
        extra_layout=dict(
            yaxis=dict(
                rangemode="tozero",
                gridcolor="rgba(148, 163, 184, 0.14)"
            )
        )
    )

    st.plotly_chart(fig, width="stretch", key=key)


# ============================================================
# TOP 10 START STATIONS
# ============================================================

def show_top_station_chart(df, key: str | None = None):
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df["trips"],
            y=df["station_id"],
            orientation="h",
            text=df["trips"],
            textposition="auto",
            texttemplate="%{text:,}",
            textfont=dict(color="#FFFFFF", weight=700),
            name="Trips",
            marker=dict(
                color="#38BDF8",
                opacity=0.9,
                line=dict(color="#00F2FE", width=1)
            ),
            hovertemplate="<b>Station ID:</b> %{y}<br><b>Trips:</b> %{x:,}<extra></extra>"
        )
    )

    _apply_dark_theme(
        fig,
        title="Top 10 Start Stations",
        xaxis_title="Number of Trips",
        yaxis_title="Station ID",
        hovermode="closest",
        extra_layout=dict(
            xaxis=dict(
                rangemode="tozero",
                gridcolor="rgba(148, 163, 184, 0.14)"
            )
        )
    )

    st.plotly_chart(fig, width="stretch", key=key)


# ============================================================
# MODEL COMPARISON
# ============================================================

def show_model_comparison_chart(df, key: str | None = None):
    test_df = df[
        df["dataset"].astype(str).str.lower() == "test"
    ].copy()

    if test_df.empty:
        st.warning("Không có dữ liệu test để so sánh model.")
        return

    # MAE + RMSE
    fig = go.Figure()

    if "mae" in test_df.columns:
        fig.add_trace(
            go.Bar(
                x=test_df["model"],
                y=test_df["mae"],
                text=test_df["mae"].round(2),
                textposition="auto",
                textfont=dict(color="#FFFFFF", weight=700),
                name="MAE",
                marker=dict(
                    color="#00F2FE",
                    opacity=0.9,
                    line=dict(color="#38BDF8", width=1)
                )
            )
        )

    if "rmse" in test_df.columns:
        fig.add_trace(
            go.Bar(
                x=test_df["model"],
                y=test_df["rmse"],
                text=test_df["rmse"].round(2),
                textposition="auto",
                textfont=dict(color="#FFFFFF", weight=700),
                name="RMSE",
                marker=dict(
                    color="#F97316",
                    opacity=0.9,
                    line=dict(color="#FBBF24", width=1)
                )
            )
        )

    _apply_dark_theme(
        fig,
        title="Model Comparison — MAE & RMSE",
        xaxis_title="Model",
        yaxis_title="Error",
        barmode="group",
        hovermode="x unified"
    )

    mae_rmse_key = f"{key}_mae_rmse" if key else None
    st.plotly_chart(fig, width="stretch", key=mae_rmse_key)

    # R²
    fig_r2 = go.Figure()

    if "r2" in test_df.columns:
        fig_r2.add_trace(
            go.Bar(
                x=test_df["model"],
                y=test_df["r2"],
                text=test_df["r2"].round(3),
                textposition="auto",
                textfont=dict(color="#FFFFFF", weight=700),
                name="R²",
                marker=dict(
                    color="#10B981",
                    opacity=0.9,
                    line=dict(color="#34D399", width=1)
                )
            )
        )

    _apply_dark_theme(
        fig_r2,
        title="Model Comparison — R²",
        xaxis_title="Model",
        yaxis_title="R²",
        hovermode="closest",
        extra_layout=dict(
            yaxis=dict(
                range=[0, 1],
                gridcolor="rgba(148, 163, 184, 0.14)"
            )
        )
    )

    r2_key = f"{key}_r2" if key else None
    st.plotly_chart(fig_r2, width="stretch", key=r2_key)


# ============================================================
# FUTURE DEMAND FORECAST (PHASE 2)
# ============================================================

def show_future_forecast_chart(df, key: str | None = None):
    """
    Hiển thị biểu đồ đường dự báo nhu cầu 7 ngày tiếp theo (168 giờ).
    Trục thời gian (target_time) sắp xếp tăng dần.
    Đồng bộ phong cách Geospatial Intelligence Dark Theme với line Cyan và fill mờ.
    """
    if df.empty:
        st.warning("⚠️ Không có dữ liệu Future Demand Forecast.")
        return

    plot_df = df.copy()
    plot_df["target_time"] = pd.to_datetime(plot_df["target_time"])
    plot_df = plot_df.sort_values("target_time").reset_index(drop=True)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=plot_df["target_time"],
            y=plot_df["predicted_demand"],
            mode="lines+markers",
            name="Forecast Demand",
            line=dict(color="#00F2FE", width=2.5),
            marker=dict(size=4, color="#38BDF8"),
            fill="tozeroy",
            fillcolor="rgba(0, 242, 254, 0.10)",
            hovertemplate="<b>Thời gian:</b> %{x|%Y-%m-%d %H:%M}<br><b>Dự báo:</b> %{y:.1f} chuyến<extra></extra>",
        )
    )

    _apply_dark_theme(
        fig,
        title="7-Day Future Demand Forecast (168 Continuous Hours)",
        xaxis_title="Thời gian (Giờ)",
        yaxis_title="Nhu cầu dự báo (Chuyến / Giờ)",
        hovermode="x unified",
        extra_layout=dict(
            xaxis=dict(
                tickformat="%b %d, %H:%M",
                dtick=24 * 3600 * 1000,
                gridcolor="rgba(148, 163, 184, 0.14)",
                tickangle=0
            ),
            yaxis=dict(
                rangemode="tozero",
                gridcolor="rgba(148, 163, 184, 0.14)"
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=45, r=35, t=60, b=45)
        )
    )

    st.plotly_chart(fig, width="stretch", key=key)



# ============================================================
# STATION POINT / PROPORTIONAL SYMBOL MAP (TASK 4 — PHASE 3)
# ============================================================

def compute_station_marker_sizes(
    df: pd.DataFrame,
    min_radius: float = 25.0,
    max_radius: float = 220.0
) -> pd.DataFrame:
    """
    Tính bán kính marker (mét) và màu sắc cho từng trạm:
    - Bán kính tỷ lệ theo căn bậc hai của activity_count (Area Proportional).
    - Có ngưỡng giới hạn [min_radius, max_radius] để tránh che lấp bản đồ.
    - Màu sắc phân cấp theo mức độ hoạt động: Xanh cyan -> Xanh dương -> Cam -> Đỏ cam.
    """
    if df.empty:
        return df.copy()

    plot_df = df.copy()

    min_act = plot_df["activity_count"].min()
    max_act = plot_df["activity_count"].max()

    sqrt_min = np.sqrt(max(min_act, 0))
    sqrt_max = np.sqrt(max(max_act, 0))
    sqrt_range = sqrt_max - sqrt_min if sqrt_max > sqrt_min else 1.0

    # Tính bán kính theo căn bậc hai (diện tích marker tỷ lệ với activity_count)
    plot_df["radius"] = min_radius + (max_radius - min_radius) * (
        (np.sqrt(plot_df["activity_count"].clip(lower=0)) - sqrt_min) / sqrt_range
    )

    # Phân cấp màu trực quan theo mức độ hoạt động
    def _get_color(act):
        if act >= 20000:
            return [255, 65, 54, 220]    # Đỏ cam (Rất cao: >= 20,000 lượt)
        elif act >= 10000:
            return [255, 140, 0, 200]   # Cam (Cao: 10,000 - 19,999 lượt)
        elif act >= 1000:
            return [0, 160, 255, 180]   # Xanh dương (Trung bình: 1,000 - 9,999 lượt)
        else:
            return [0, 210, 210, 160]   # Cyan / Ngọc lam (Thấp: < 1,000 lượt)

    plot_df["fill_color"] = plot_df["activity_count"].apply(_get_color)
    return plot_df


def format_station_tooltip_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Chuẩn hóa các trường hiển thị cho tooltip (Task 6 — Phase 3):
    - Bảo đảm đủ 7 trường: station_name, station_id, latitude, longitude,
      start_count, end_count, activity_count.
    - Xử lý an toàn các giá trị NaN/None/Inf thành 'N/A' hoặc fallback minh bạch.
    - Phân biệt rõ số 0 thực tế với giá trị bị thiếu (số 0 được giữ nguyên).
    - Không tự bịa thông tin trạm giả; nếu thiếu tên thì dùng fallback 'Station {station_id}'.
    """
    if df.empty:
        return df.copy()

    plot_df = df.copy()

    # station_id
    if "station_id" in plot_df.columns:
        plot_df["station_id"] = plot_df["station_id"].apply(
            lambda x: str(x).strip() if pd.notna(x) and str(x).strip().lower() not in ("", "none", "nan", "null") else "N/A"
        )
    else:
        plot_df["station_id"] = "N/A"

    # station_name
    if "station_name" in plot_df.columns:
        plot_df["station_name"] = plot_df.apply(
            lambda r: str(r["station_name"]).strip()
            if pd.notna(r["station_name"]) and str(r["station_name"]).strip().lower() not in ("", "none", "nan", "null")
            else (f"Station {r['station_id']}" if r["station_id"] != "N/A" else "Trạm không xác định"),
            axis=1,
        )
    else:
        plot_df["station_name"] = plot_df["station_id"].apply(
            lambda sid: f"Station {sid}" if sid != "N/A" else "Trạm không xác định"
        )

    # latitude & longitude (giữ float hợp lệ để vẽ marker và hiển thị tooltip)
    if "latitude" in plot_df.columns:
        plot_df["latitude"] = plot_df["latitude"].apply(
            lambda x: round(float(x), 5) if pd.notna(x) and np.isfinite(x) else "N/A"
        )
    else:
        plot_df["latitude"] = "N/A"

    if "longitude" in plot_df.columns:
        plot_df["longitude"] = plot_df["longitude"].apply(
            lambda x: round(float(x), 5) if pd.notna(x) and np.isfinite(x) else "N/A"
        )
    else:
        plot_df["longitude"] = "N/A"

    # start_count, end_count, activity_count (phân biệt số 0 thực tế với NaN/None)
    for col in ["start_count", "end_count", "activity_count"]:
        if col in plot_df.columns:
            plot_df[col] = plot_df[col].apply(
                lambda x: f"{int(x):,}" if pd.notna(x) and np.isfinite(x) else "N/A"
            )
        else:
            plot_df[col] = "N/A"

    return plot_df


def get_station_tooltip_config() -> dict:
    """
    Cấu hình HTML tooltip và CSS style hiển thị thông tin trạm khi hover (Task 6 — Phase 3).
    Đầy đủ 7 trường thông tin:
    - station_name: Tên trạm
    - station_id: Mã trạm
    - latitude, longitude: Tọa độ địa lý
    - start_count: Số lượt bắt đầu
    - end_count: Số lượt kết thúc
    - activity_count: Tổng lượt hoạt động

    Thiết kế gọn gàng, an toàn, hỗ trợ cuộn nội dung nếu dài, loại bỏ nhấp nháy (pointer-events: none)
    và sử dụng 100% cơ chế tooltip gốc của PyDeck/Deck.gl, không dùng JavaScript can thiệp DOM.
    """
    return {
        "html": (
            "<div style='font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, Helvetica, Arial, sans-serif; min-width: 190px; max-width: 270px; line-height: 1.4;'>"
            "<div style='display: flex; align-items: flex-start; gap: 4px; margin-bottom: 3px;'>"
            "<span style='font-size: 14px; line-height: 1.2;'>📍</span>"
            "<div style='font-size: 13px; font-weight: 700; color: #38bdf8; word-break: break-word;'>{station_name}</div>"
            "</div>"
            "<div style='font-size: 11px; color: #94a3b8; margin-bottom: 5px; padding-left: 18px;'>Mã trạm: <b style='color: #cbd5e1;'>{station_id}</b></div>"
            "<hr style='border: 0; border-top: 1px solid rgba(255,255,255,0.15); margin: 3px 0 5px 0;'/>"
            "<div style='font-size: 12px; line-height: 1.5; color: #f1f5f9; display: grid; grid-template-columns: auto 1fr; gap: 2px 10px; align-items: center;'>"
            "<span style='color: #94a3b8;'>Tọa độ:</span><span style='font-family: monospace; color: #e2e8f0;'>{latitude}, {longitude}</span>"
            "<span style='color: #94a3b8;'>Lượt bắt đầu:</span><span style='color: #4ade80; font-weight: 600;'>{start_count}</span>"
            "<span style='color: #94a3b8;'>Lượt kết thúc:</span><span style='color: #f87171; font-weight: 600;'>{end_count}</span>"
            "<span style='color: #fbbf24; font-weight: 600;'>Tổng hoạt động:</span><span style='color: #fbbf24; font-weight: 700;'>{activity_count}</span>"
            "</div>"
            "</div>"
        ),
        "style": {
            "backgroundColor": "rgba(15, 23, 42, 0.94)",
            "color": "#f8fafc",
            "fontSize": "12px",
            "borderRadius": "8px",
            "padding": "8px 12px",
            "border": "1px solid rgba(255, 255, 255, 0.18)",
            "boxShadow": "0 8px 24px -2px rgba(0, 0, 0, 0.6)",
            "zIndex": "1000",
            "pointerEvents": "none",
            "top": "500px",
            "maxWidth": "290px",
            "maxHeight": "240px",
            "overflowY": "auto",
            "overflowX": "hidden",
            "boxSizing": "border-box",
        },
    }


def create_station_symbol_layer(
    df: pd.DataFrame,
    min_radius: float = 20.0,
    max_radius: float = 160.0
) -> tuple[pdk.Layer, pd.DataFrame]:
    """
    Tạo ScatterplotLayer cho Point / Proportional Symbol Map.
    Trả về tuple (layer, plot_df đã gắn bán kính & màu sắc và chuẩn hóa tooltip).
    - Giới hạn pixel [3, 18] để giảm chồng lấn nhưng vẫn phân biệt rõ cấp độ hoạt động.
    """
    plot_df = compute_station_marker_sizes(df, min_radius=min_radius, max_radius=max_radius)
    plot_df = format_station_tooltip_data(plot_df)

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=plot_df,
        get_position=["longitude", "latitude"],
        get_radius="radius",
        get_fill_color="fill_color",
        get_line_color=[255, 255, 255, 220],
        line_width_min_pixels=1,
        pickable=True,
        auto_highlight=True,
        radius_min_pixels=3,
        radius_max_pixels=18,
    )

    return layer, plot_df


# Bảng màu Heatmap chuyển tiếp mượt mà: Vàng nhạt -> Vàng cam -> Cam -> Cam đỏ -> Đỏ -> Đỏ đậm
DEFAULT_HEATMAP_COLOR_RANGE = [
    [255, 255, 178],  # Vàng nhạt (mật độ bắt đầu)
    [254, 204, 92],   # Vàng cam
    [253, 141, 60],   # Cam sáng
    [240, 59, 32],    # Cam đỏ
    [189, 0, 38],     # Đỏ
    [128, 0, 38],     # Đỏ đậm (mật độ tập trung nhu cầu cao nhất)
]


def create_station_heatmap_layer(
    df: pd.DataFrame,
    radius_pixels: int = 45,
    opacity: float = 0.50,
    threshold: float = 0.05,
    intensity: float = 1.2,
    color_range: list | None = None,
) -> pdk.Layer:
    """
    Tạo HeatmapLayer làm lớp nền mật độ hoạt động cho bản đồ (Task 5 & Tối ưu Phase 3).
    - Sử dụng tọa độ trạm hợp lệ [longitude, latitude].
    - Trọng số phân bổ theo activity_count để phản ánh mật độ tập trung nhu cầu.
    - Cấu hình tối ưu: opacity=0.50, radius_pixels=45, threshold=0.05, intensity=1.2.
    - Dải màu chuyển tiếp từ vàng nhạt sang cam/đỏ giúp nhận diện vùng tập trung rõ rệt.
    - Không che khuất mạng lưới đường phố của bản đồ nền hay marker trạm nằm phía trên.
    - Lớp nhiệt nằm dưới ScatterplotLayer; không phản ánh số xe tồn kho.
    """
    chosen_color_range = color_range if color_range is not None else DEFAULT_HEATMAP_COLOR_RANGE

    if df.empty:
        return pdk.Layer(
            "HeatmapLayer",
            data=pd.DataFrame(columns=["longitude", "latitude", "activity_count"]),
            get_position=["longitude", "latitude"],
            get_weight="activity_count",
            radius_pixels=radius_pixels,
            opacity=opacity,
            threshold=threshold,
            intensity=intensity,
            color_range=chosen_color_range,
        )

    weight_col = "activity_count" if "activity_count" in df.columns else None

    return pdk.Layer(
        "HeatmapLayer",
        data=df,
        get_position=["longitude", "latitude"],
        get_weight=weight_col,
        radius_pixels=radius_pixels,
        opacity=opacity,
        threshold=threshold,
        intensity=intensity,
        color_range=chosen_color_range,
    )


def build_station_map_deck(
    df: pd.DataFrame,
    show_heatmap: bool = True,
    min_radius: float = 20.0,
    max_radius: float = 160.0,
    tooltip: dict | None = None,
    map_style: str | None = None,
    heatmap_radius_pixels: int = 45,
    heatmap_opacity: float = 0.50,
    heatmap_threshold: float = 0.05,
    heatmap_intensity: float = 1.2,
    heatmap_color_range: list | None = None,
) -> tuple[pdk.Deck, pd.DataFrame]:
    """
    Xây dựng PyDeck Deck đa lớp cho Station Map (Task 4-8).
    - Thứ tự xếp lớp: HeatmapLayer ở dưới, ScatterplotLayer ở trên.
    - Cấu hình Tooltip hiển thị đầy đủ thông tin trạm khi tương tác hover.
    - map_style: URL hoặc identifier style bản đồ nền địa lý (mặc định CARTO Positron vector tiles).
    - Zoom 11.0 căn giữa tọa độ thực tế NY/NJ bao trọn toàn bộ 452 trạm mà không thừa khoảng trắng.
    - Trả về tuple (pdk.Deck, plot_df đã gắn kích thước, màu sắc và tooltip).
    """
    center_lat = float(df["latitude"].mean()) if not df.empty else 40.7356
    center_lng = float(df["longitude"].mean()) if not df.empty else -74.0033

    symbol_layer, plot_df = create_station_symbol_layer(
        df, min_radius=min_radius, max_radius=max_radius
    )

    layers = []
    if show_heatmap:
        heatmap_layer = create_station_heatmap_layer(
            df,
            radius_pixels=heatmap_radius_pixels,
            opacity=heatmap_opacity,
            threshold=heatmap_threshold,
            intensity=heatmap_intensity,
            color_range=heatmap_color_range,
        )
        layers.append(heatmap_layer)
    layers.append(symbol_layer)

    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lng,
        zoom=11.0,
        pitch=0,
        bearing=0,
    )

    tooltip_cfg = tooltip if tooltip is not None else get_station_tooltip_config()
    selected_style = map_style if map_style is not None else pdk.map_styles.CARTO_LIGHT

    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style=selected_style,
        tooltip=tooltip_cfg,
    )

    return deck, plot_df


def show_station_symbol_map(
    df: pd.DataFrame,
    show_heatmap: bool = True,
    date_label: str | None = None,
    map_style: str | None = None,
    heatmap_radius_pixels: int = 45,
    heatmap_opacity: float = 0.50,
    heatmap_threshold: float = 0.05,
    heatmap_intensity: float = 1.2,
):
    """
    Hiển thị Point / Proportional Symbol Map & Heatmap cho các trạm xe đạp Citi Bike (Task 4-8).
    - Lớp nền bản đồ địa lý thực (CARTO Positron / Voyager) hiển thị đường phố, công viên, địa danh.
    - Lớp nền HeatmapLayer mật độ nhu cầu với dải màu vàng nhạt -> cam/đỏ nổi bật (Task 5 & Tối ưu).
    - Lớp trên ScatterplotLayer marker tại tọa độ hợp lệ, kích thước tỷ lệ với activity_count.
    - Thứ tự xếp lớp: Heatmap nằm dưới, Marker nằm trên.
    - Tooltip native PyDeck/Deck.gl an toàn, gọn gàng, 7 trường thông tin, pointer-events: none.
    - Legend giải thích kích thước, màu sắc và làm rõ Heatmap không phải tồn kho xe.
    - date_label: Nhãn thời gian hiển thị rõ phạm vi dữ liệu đang xem (Task 7).
    - Xử lý an toàn khi dữ liệu rỗng.
    """
    if df.empty or "latitude" not in df.columns or "longitude" not in df.columns:
        if date_label:
            st.warning(f"⚠️ Không có dữ liệu hoạt động trạm trong khoảng thời gian đã chọn: **{date_label}**.")
        else:
            st.warning("⚠️ Không có dữ liệu trạm để hiển thị trên bản đồ.")
        return

    # Lọc các trạm có tọa độ số thực hợp lệ
    valid_mask = (
        df["latitude"].notna()
        & df["longitude"].notna()
        & (df["latitude"] >= 40.0)
        & (df["latitude"] <= 41.5)
        & (df["longitude"] >= -74.5)
        & (df["longitude"] <= -73.0)
    )
    valid_df = df[valid_mask].copy()

    if valid_df.empty:
        if date_label:
            st.warning(f"⚠️ Không có trạm nào có tọa độ hợp lệ trong khoảng thời gian đã chọn: **{date_label}**.")
        else:
            st.warning("⚠️ Không có trạm nào có tọa độ hợp lệ để hiển thị.")
        return

    if date_label:
        st.caption(f"📅 **Khoảng thời gian đang hiển thị:** {date_label}")

    # Xây dựng PyDeck Deck đa lớp (Bản đồ địa lý thực, Heatmap dưới, Marker trên)
    deck, plot_df = build_station_map_deck(
        valid_df,
        show_heatmap=show_heatmap,
        map_style=map_style,
        heatmap_radius_pixels=heatmap_radius_pixels,
        heatmap_opacity=heatmap_opacity,
        heatmap_threshold=heatmap_threshold,
        heatmap_intensity=heatmap_intensity,
    )

    # Hiển thị bản đồ PyDeck
    try:
        st.pydeck_chart(deck, width="stretch")
    except TypeError:
        st.pydeck_chart(deck, use_container_width=True)

    # Hiển thị Legend (Chú giải kích thước và màu sắc)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            "🔴 **Rất cao (≥ 20,000)**<br>"
            "<small style='color: gray;'>Marker lớn nhất • Hub trung tâm</small>",
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            "🟠 **Cao (10,000 – 19,999)**<br>"
            "<small style='color: gray;'>Marker lớn • Tuyến đông</small>",
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            "🔵 **Trung bình (1,000 – 9,999)**<br>"
            "<small style='color: gray;'>Marker vừa • Khu dân cư</small>",
            unsafe_allow_html=True
        )
    with col4:
        st.markdown(
            "🟢 **Thấp (< 1,000)**<br>"
            "<small style='color: gray;'>Marker nhỏ • Bến phụ cận</small>",
            unsafe_allow_html=True
        )

    if show_heatmap:
        st.caption(
            "ℹ️ **Lớp nhiệt nền (Heatmap):** Thể hiện mật độ tập trung nhu cầu hoạt động (Activity Count) "
            "theo dải màu từ vàng nhạt đến cam/đỏ. Không phản ánh số lượng xe tồn kho hay thiếu xe tại trạm."
        )





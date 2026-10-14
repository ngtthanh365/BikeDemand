import sys
import re
from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DASHBOARD_DIR = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))


# ============================================================
# IMPORT DATABASE
# ============================================================

from database.postgres import (
    load_predictions,
    load_dashboard_trips,
    load_station_activity_data,
    normalize_date_range
)


from config import (
    MODEL_METRICS_FILE
)


# ============================================================
# PREDICTION DATA
# ============================================================

@st.cache_data
def load_prediction_data():

    # --------------------------------------------------------
    # Đọc prediction từ PostgreSQL
    # --------------------------------------------------------

    df = load_predictions(
        model_name="Random Forest",
        model_version="1.0"
    )

    if df.empty:
        return df


    # --------------------------------------------------------
    # Đổi tên cột PostgreSQL về cấu trúc Dashboard cũ
    # --------------------------------------------------------

    df = df.rename(
        columns={
            "target_time": "datetime",
            "actual_demand": "total_trips"
        }
    )


    # --------------------------------------------------------
    # Chuyển thời gian
    # --------------------------------------------------------

    df["datetime"] = pd.to_datetime(
        df["datetime"]
    )


    # --------------------------------------------------------
    # Tạo các cột thời gian
    # --------------------------------------------------------

    df["date"] = (
        df["datetime"]
        .dt.normalize()
    )

    df["hour"] = (
        df["datetime"]
        .dt.hour
    )

    df["day_of_week"] = (
        df["datetime"]
        .dt.dayofweek
    )

    df["month"] = (
        df["datetime"]
        .dt.month
    )


    # --------------------------------------------------------
    # Tính sai số dự đoán
    # --------------------------------------------------------

    df["error"] = (
        df["total_trips"]
        - df["predicted_demand"]
    )

    df["absolute_error"] = (
        df["error"]
        .abs()
    )


    # --------------------------------------------------------
    # Giữ cấu trúc giống Dashboard cũ
    # --------------------------------------------------------

    df = df[
        [
            "datetime",
            "date",
            "hour",
            "day_of_week",
            "month",
            "total_trips",
            "predicted_demand",
            "model_name",
            "error",
            "absolute_error"
        ]
    ]


    return df


# ============================================================
# FUTURE FORECAST DATA (PHASE 2)
# ============================================================

@st.cache_data(ttl=60)
def load_future_forecast_data():
    """
    Đọc dữ liệu Future Demand Forecast (168h) từ bảng predictions trong PostgreSQL.
    Lọc chính xác: model_name = 'Random Forest' và model_version = 'future-v1'.
    """

    df = load_predictions(
        model_name="Random Forest",
        model_version="future-v1"
    )

    if df.empty:
        return df

    df["target_time"] = pd.to_datetime(df["target_time"])
    df = df.sort_values("target_time").reset_index(drop=True)

    if "prediction_time" in df.columns:
        df["prediction_time"] = pd.to_datetime(df["prediction_time"])

    return df


# ============================================================
# MODEL METRICS
# ============================================================

@st.cache_data
def load_model_metrics():

    df = pd.read_csv(
        MODEL_METRICS_FILE
    )

    return df


# ============================================================
# RAW DATA FOR FILTER
# ============================================================

@st.cache_data
def load_raw_data():

    # --------------------------------------------------------
    # Đọc dữ liệu từ PostgreSQL
    # --------------------------------------------------------

    df = load_dashboard_trips()


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


# ============================================================
# STATION ACTIVITY & DISPLAY DATA (PHASE 3)
# ============================================================

def prepare_station_display_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Chuẩn bị và chuẩn hóa dữ liệu hiển thị cấp trạm (Task 3 — Phase 3).
    - Chuẩn hóa tên trạm (loại bỏ khoảng trắng thừa, fallback an toàn không bịa tên).
    - Bổ sung display_label kết hợp Station Name và Station ID để tra cứu phân biệt.
    - Đảm bảo tọa độ là số thực hợp lệ.
    - Đảm bảo tính duy nhất của Station ID.
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                "station_id",
                "station_name",
                "display_label",
                "latitude",
                "longitude",
                "start_count",
                "end_count",
                "activity_count"
            ]
        )

    out_df = df.copy()

    # 1. Đảm bảo kiểu dữ liệu station_id là string và chuẩn hóa
    out_df["station_id"] = out_df["station_id"].astype(str).str.strip()

    # Loại bỏ các ID rác nếu có
    invalid_id_mask = out_df["station_id"].isin(['"NaN"', "NaN", "nan", "None", "null", ""])
    out_df = out_df[~invalid_id_mask].copy()

    # Đảm bảo Station ID là duy nhất (loại bỏ trùng lặp nếu có)
    out_df = out_df.drop_duplicates(subset=["station_id"], keep="first")

    # 2. Chuẩn hóa tên trạm
    def _clean_name(row):
        val = row.get("station_name")
        if pd.isna(val) or val is None or str(val).strip() in ['"NaN"', "NaN", "nan", "None", "null", ""]:
            # Tên thiếu dữ liệu được ghi nhận minh bạch theo station_id, không tự đặt tên giả
            return f"Station {row['station_id']}"
        # Loại bỏ khoảng trắng thừa
        return re.sub(r"\s+", " ", str(val).strip())

    out_df["station_name"] = out_df.apply(_clean_name, axis=1)

    # 3. Tạo display_label kết hợp Tên trạm và Station ID (hỗ trợ phân biệt trạm trùng tên)
    out_df["display_label"] = out_df["station_name"] + " (" + out_df["station_id"] + ")"

    # 4. Xác thực và ép kiểu tọa độ là float hợp lệ
    out_df["latitude"] = pd.to_numeric(out_df["latitude"], errors="coerce")
    out_df["longitude"] = pd.to_numeric(out_df["longitude"], errors="coerce")

    # Loại bỏ các hàng có tọa độ NaN hoặc nằm ngoài phạm vi địa lý NY/NJ
    valid_coords = (
        out_df["latitude"].notna()
        & out_df["longitude"].notna()
        & (out_df["latitude"] >= 40.0)
        & (out_df["latitude"] <= 41.5)
        & (out_df["longitude"] >= -74.5)
        & (out_df["longitude"] <= -73.0)
    )
    out_df = out_df[valid_coords].copy()

    # 5. Đảm bảo các bộ đếm là integer không âm
    for col in ["start_count", "end_count", "activity_count"]:
        if col in out_df.columns:
            out_df[col] = pd.to_numeric(out_df[col], errors="coerce").fillna(0).astype(int)

    return out_df.reset_index(drop=True)


def get_station_by_id(df: pd.DataFrame, station_id: str) -> dict | None:
    """
    Tra cứu thông tin chi tiết của trạm theo Station ID.
    Trả về dict chứa thông tin trạm hoặc None nếu không tìm thấy.
    """
    if df.empty or not station_id:
        return None

    clean_id = str(station_id).strip()
    match = df[df["station_id"] == clean_id]

    if match.empty:
        return None

    return match.iloc[0].to_dict()


@st.cache_data(ttl=60)
def load_station_activity(start_date=None, end_date=None) -> pd.DataFrame:
    """
    Nạp và chuẩn hóa dữ liệu hoạt động cấp trạm từ PostgreSQL.
    Tái sử dụng hàm load_station_activity_data() từ database.postgres.
    Tự động hết hạn cache sau 60s để đồng bộ khi Phase 1 cập nhật dữ liệu.
    """
    raw_df = load_station_activity_data(
        start_date=start_date,
        end_date=end_date
    )
    return prepare_station_display_data(raw_df)


def format_date_range_label(start_date=None, end_date=None) -> str:
    """
    Tạo nhãn hiển thị khoảng thời gian thân thiện và rõ ràng cho giao diện và bản đồ:
    - Không lọc: 'Toàn bộ dữ liệu'
    - start > end: 'Khoảng thời gian không hợp lệ (Ngày bắt đầu > Ngày kết thúc)'
    - Khoảng hợp lệ: 'DD/MM/YYYY — DD/MM/YYYY' (hoặc kèm giờ nếu có)
    - Chỉ start_date: 'Từ DD/MM/YYYY'
    - Chỉ end_date: 'Đến DD/MM/YYYY'
    """
    if start_date is None and end_date is None:
        return "Toàn bộ dữ liệu"

    norm_start, norm_end, is_reversed = normalize_date_range(start_date, end_date)

    if is_reversed:
        return "Khoảng thời gian không hợp lệ (Ngày bắt đầu > Ngày kết thúc)"

    def _fmt(val_raw, is_end_val=False):
        if val_raw is None:
            return ""
        try:
            ts = pd.to_datetime(val_raw)
            if ts.hour == 0 and ts.minute == 0 and ts.second == 0 and (not is_end_val or ts.microsecond == 0):
                return ts.strftime("%d/%m/%Y")
            elif is_end_val and ts.hour == 23 and ts.minute == 59 and ts.second == 59:
                return ts.strftime("%d/%m/%Y")
            return ts.strftime("%d/%m/%Y %H:%M")
        except Exception:
            return str(val_raw)

    s_str = _fmt(norm_start, False) if norm_start else ""
    e_str = _fmt(norm_end, True) if norm_end else ""

    if s_str and e_str:
        return f"{s_str} — {e_str}"
    elif s_str:
        return f"Từ {s_str}"
    elif e_str:
        return f"Đến {e_str}"
    return "Toàn bộ dữ liệu"


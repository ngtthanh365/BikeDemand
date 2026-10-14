import os
from datetime import datetime, date

import pandas as pd
import psycopg2
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

# Đọc các biến cấu hình từ file .env
load_dotenv()


# ============================================================
# POSTGRESQL CONFIG
# ============================================================

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "citibike")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Tạo và trả về kết nối tới PostgreSQL.
    """

    connection = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )

    return connection


# ============================================================
# LOAD HOURLY DEMAND
# ============================================================

def load_hourly_demand():
    """
    Đọc dữ liệu hourly_demand từ PostgreSQL
    và trả về Pandas DataFrame.
    """

    query = """
        SELECT
            timestamp,
            date,
            hour,
            day_of_week,
            month,
            is_weekend,
            member_count,
            casual_count,
            electric_count,
            classic_count,
            demand
        FROM hourly_demand
        ORDER BY timestamp;
    """

    connection = get_connection()

    try:
        df = pd.read_sql_query(
            query,
            connection
        )
    finally:
        connection.close()

    return df

def save_predictions(
    df,
    model_name="Random Forest",
    model_version="1.0"
):
    """
    Lưu kết quả dự đoán vào bảng predictions.

    Chỉ xóa prediction của đúng model_name + model_version
    trước khi ghi lại, không ảnh hưởng model khác.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # ----------------------------------------------------
        # 1. Xóa dữ liệu cũ của đúng model/version này
        # ----------------------------------------------------

        delete_query = """
            DELETE FROM predictions
            WHERE model_name = %s
              AND model_version = %s;
        """

        cursor.execute(
            delete_query,
            (
                model_name,
                model_version
            )
        )

        deleted_rows = cursor.rowcount

        # ----------------------------------------------------
        # 2. Insert predictions mới
        # ----------------------------------------------------

        insert_query = """
            INSERT INTO predictions (
                prediction_time,
                target_time,
                predicted_demand,
                actual_demand,
                model_name,
                model_version
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            );
        """

        records = []

        for _, row in df.iterrows():
            # target_time: uu tien target_time neu co, fallback datetime
            target_time = row["target_time"] if "target_time" in row else row["datetime"]

            # prediction_time: uu tien prediction_time neu co, fallback datetime.now()
            if "prediction_time" in row and pd.notnull(row["prediction_time"]):
                pred_time = row["prediction_time"]
            else:
                pred_time = datetime.now()

            # actual_demand: xu ly an toan cho ca Phase 1 (int) va Future Forecast (None/NULL)
            actual_val = None
            if "actual_demand" in row and pd.notnull(row["actual_demand"]):
                actual_val = int(row["actual_demand"])
            elif "total_trips" in row and pd.notnull(row["total_trips"]):
                actual_val = int(row["total_trips"])

            records.append(
                (
                    pred_time,
                    target_time,
                    float(row["predicted_demand"]),
                    actual_val,
                    model_name,
                    model_version
                )
            )

        cursor.executemany(
            insert_query,
            records
        )

        inserted_rows = cursor.rowcount

        # ----------------------------------------------------
        # 3. Commit
        # ----------------------------------------------------

        connection.commit()

        print(
            f"Deleted old predictions: "
            f"{deleted_rows:,}"
        )

        print(
            f"Inserted predictions: "
            f"{inserted_rows:,}"
        )

    except Exception:
        # Nếu insert lỗi giữa chừng thì không lưu dữ liệu dở dang
        connection.rollback()
        raise

    finally:
        connection.close()


def save_future_predictions(
    df,
    model_name="Random Forest",
    model_version="future-v1"
):
    """
    Lưu kết quả dự báo tương lai (Future Forecast) vào bảng predictions.
    Đảm bảo actual_demand là NULL và model_version là future-v1.
    """
    return save_predictions(
        df=df,
        model_name=model_name,
        model_version=model_version
    )


def load_predictions(
    model_name="Random Forest",
    model_version="1.0"
):
    """
    Đọc prediction từ PostgreSQL.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        query = """
            SELECT
                prediction_time,
                target_time,
                predicted_demand,
                actual_demand,
                model_name,
                model_version
            FROM predictions
            WHERE model_name = %s
              AND model_version = %s
            ORDER BY target_time;
        """

        cursor.execute(
            query,
            (
                model_name,
                model_version
            )
        )

        rows = cursor.fetchall()

        columns = [
            description[0]
            for description in cursor.description
        ]

        df = pd.DataFrame(
            rows,
            columns=columns
        )

    finally:
        connection.close()

    return df

def load_dashboard_trips():
    """
    Đọc các cột cần thiết cho Dashboard
    từ bảng trips trong PostgreSQL.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        query = """
            SELECT
                started_at,
                ended_at,
                member_casual,
                rideable_type,
                start_station_id
            FROM trips
            ORDER BY started_at;
        """

        cursor.execute(query)

        rows = cursor.fetchall()

        columns = [
            description[0]
            for description in cursor.description
        ]

        df = pd.DataFrame(
            rows,
            columns=columns
        )

    finally:
        connection.close()

    return df


# ============================================================
# STATION ACTIVITY SUMMARY (PHASE 3)
# ============================================================

def normalize_date_range(start_date=None, end_date=None):
    """
    Chuẩn hóa và kiểm tra tính hợp lệ của khoảng thời gian (start_date, end_date):
    - Trả về tuple (norm_start, norm_end, is_reversed).
    - norm_start / norm_end: chuỗi datetime định dạng chuẩn (hoặc None nếu không lọc).
    - is_reversed: True nếu start_date > end_date (khoảng thời gian không hợp lệ).
    - Tự động mở rộng end_date đến cuối ngày (23:59:59.999999) nếu chỉ cung cấp ngày (date).
    """
    norm_start = None
    norm_end = None
    is_reversed = False

    if start_date is not None:
        if isinstance(start_date, str):
            s = start_date.strip()
            if len(s) == 10 and s.count("-") == 2:
                norm_start = f"{s} 00:00:00"
            elif s:
                norm_start = s
        elif isinstance(start_date, date) and not isinstance(start_date, datetime):
            norm_start = f"{start_date.strftime('%Y-%m-%d')} 00:00:00"
        elif isinstance(start_date, (datetime, pd.Timestamp)):
            norm_start = str(start_date)

    if end_date is not None:
        if isinstance(end_date, str):
            e = end_date.strip()
            if len(e) == 10 and e.count("-") == 2:
                norm_end = f"{e} 23:59:59.999999"
            elif e:
                norm_end = e
        elif isinstance(end_date, date) and not isinstance(end_date, datetime):
            norm_end = f"{end_date.strftime('%Y-%m-%d')} 23:59:59.999999"
        elif isinstance(end_date, (datetime, pd.Timestamp)):
            if end_date.hour == 0 and end_date.minute == 0 and end_date.second == 0 and getattr(end_date, "microsecond", 0) == 0:
                norm_end = f"{end_date.strftime('%Y-%m-%d')} 23:59:59.999999"
            else:
                norm_end = str(end_date)

    if norm_start is not None and norm_end is not None:
        try:
            ts_start = pd.to_datetime(norm_start)
            ts_end = pd.to_datetime(norm_end)
            if ts_start > ts_end:
                is_reversed = True
        except Exception:
            pass

    return norm_start, norm_end, is_reversed


def load_station_activity_data(start_date=None, end_date=None) -> pd.DataFrame:
    """
    Tổng hợp dữ liệu hoạt động cấp trạm trực tiếp từ PostgreSQL.
    Nhóm theo station_id, tính toán:
      - station_id: mã định danh trạm duy nhất
      - station_name: tên trạm (đã chuẩn hóa khoảng trắng thừa)
      - latitude: vĩ độ đại diện (trọng tâm tọa độ theo số lượt chuyến)
      - longitude: kinh độ đại diện (trọng tâm tọa độ theo số lượt chuyến)
      - start_count: số chuyến bắt đầu tại trạm
      - end_count: số chuyến kết thúc tại trạm
      - activity_count: tổng lượt hoạt động (start_count + end_count)
    
    Tự động loại bỏ dữ liệu rác ('NaN', NULL, rỗng, tọa độ không hợp lệ)
    mà không sửa đổi dữ liệu gốc trong bảng trips.

    Tham số:
      - start_date (optional): Timestamp hoặc str (YYYY-MM-DD [HH:MM:SS]) hoặc date
      - end_date (optional): Timestamp hoặc str (YYYY-MM-DD [HH:MM:SS]) hoặc date
    """
    norm_start, norm_end, is_reversed = normalize_date_range(start_date, end_date)

    if is_reversed:
        return pd.DataFrame(
            columns=[
                "station_id",
                "station_name",
                "latitude",
                "longitude",
                "start_count",
                "end_count",
                "activity_count",
            ]
        )

    connection = get_connection()

    try:
        cursor = connection.cursor()

        date_filter_start = ""
        date_filter_end = ""
        params = {}

        if norm_start is not None:
            date_filter_start += " AND started_at >= %(start_date)s"
            date_filter_end += " AND ended_at >= %(start_date)s"
            params["start_date"] = norm_start

        if norm_end is not None:
            date_filter_start += " AND started_at <= %(end_date)s"
            date_filter_end += " AND ended_at <= %(end_date)s"
            params["end_date"] = norm_end

        query = f"""
            WITH starts AS (
                SELECT 
                    start_station_id AS station_id,
                    MAX(REGEXP_REPLACE(TRIM(start_station_name), '\\s+', ' ', 'g')) AS station_name,
                    AVG(start_lat) AS lat,
                    AVG(start_lng) AS lng,
                    COUNT(*) AS start_count
                FROM trips
                WHERE start_station_id IS NOT NULL 
                  AND start_station_id != '"NaN"'
                  AND TRIM(start_station_id) != ''
                  AND start_lat != 'NaN'::double precision 
                  AND start_lat IS NOT NULL
                  AND start_lng != 'NaN'::double precision 
                  AND start_lng IS NOT NULL
                  {date_filter_start}
                GROUP BY start_station_id
            ),
            ends AS (
                SELECT 
                    end_station_id AS station_id,
                    MAX(REGEXP_REPLACE(TRIM(end_station_name), '\\s+', ' ', 'g')) AS station_name,
                    AVG(end_lat) AS lat,
                    AVG(end_lng) AS lng,
                    COUNT(*) AS end_count
                FROM trips
                WHERE end_station_id IS NOT NULL 
                  AND end_station_id != '"NaN"'
                  AND TRIM(end_station_id) != ''
                  AND end_lat != 'NaN'::double precision 
                  AND end_lat IS NOT NULL
                  AND end_lng != 'NaN'::double precision 
                  AND end_lng IS NOT NULL
                  {date_filter_end}
                GROUP BY end_station_id
            )
            SELECT 
                COALESCE(s.station_id, e.station_id) AS station_id,
                COALESCE(s.station_name, e.station_name) AS station_name,
                ROUND(
                    CASE 
                        WHEN s.lat IS NOT NULL AND e.lat IS NOT NULL 
                            THEN (s.lat * s.start_count + e.lat * e.end_count) / (s.start_count + e.end_count)
                        WHEN s.lat IS NOT NULL THEN s.lat
                        ELSE e.lat
                    END::numeric, 6
                )::double precision AS latitude,
                ROUND(
                    CASE 
                        WHEN s.lng IS NOT NULL AND e.lng IS NOT NULL 
                            THEN (s.lng * s.start_count + e.lng * e.end_count) / (s.start_count + e.end_count)
                        WHEN s.lng IS NOT NULL THEN s.lng
                        ELSE e.lng
                    END::numeric, 6
                )::double precision AS longitude,
                COALESCE(s.start_count, 0)::int AS start_count,
                COALESCE(e.end_count, 0)::int AS end_count,
                (COALESCE(s.start_count, 0) + COALESCE(e.end_count, 0))::int AS activity_count
            FROM starts s
            FULL OUTER JOIN ends e ON s.station_id = e.station_id
            ORDER BY activity_count DESC;
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [
            description[0]
            for description in cursor.description
        ]

        df = pd.DataFrame(
            rows,
            columns=columns
        )
    finally:
        connection.close()

    return df
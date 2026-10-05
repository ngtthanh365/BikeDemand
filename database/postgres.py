import os

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
                CURRENT_TIMESTAMP,
                %s,
                %s,
                %s,
                %s,
                %s
            );
        """

        records = []

        for _, row in df.iterrows():
            records.append(
                (
                    row["datetime"],
                    float(row["predicted_demand"]),
                    int(row["total_trips"]),
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
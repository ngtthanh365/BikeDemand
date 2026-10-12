"""
spark_streaming.py — Task 6: Cập nhật PostgreSQL.trips (Phase 1)

Đọc dữ liệu mới từ Kafka topic citibike-trips và ghi vào bảng trips.

Cơ chế idempotent:
  Trước khi ghi mỗi batch, truy vấn ride_id đã có trong trips trong
  cùng khoảng thời gian started_at của batch (date-range query).
  left_anti join → chỉ INSERT ride_id chưa tồn tại.
  → Không xóa / TRUNCATE dữ liệu cũ, không vi phạm PRIMARY KEY.

Checkpoint:
  /tmp/citibike-spark-postgres-checkpoint
  Giữ nguyên checkpoint để tiếp tục từ vị trí đã xử lý (sau H1 2026).
  Xóa checkpoint thủ công nếu muốn xử lý lại từ đầu.

Chế độ chạy:
  - Mặc định (availableNow=True): xử lý hết dữ liệu mới rồi tự kết
    thúc (phù hợp cho update pipeline tự động).
  - Flag --stream: streaming liên tục awaitTermination().
"""

import argparse

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    dayofweek,
    from_json,
    hour,
    max as spark_max,
    min as spark_min,
    month,
    to_date,
    to_timestamp,
    unix_timestamp,
)
from pyspark.sql.types import (
    DoubleType,
    StringType,
    StructField,
    StructType,
)

# ============================================================
# CẤU HÌNH
# ============================================================

KAFKA_BOOTSTRAP_SERVERS = "kafka:29092"
KAFKA_TOPIC = "citibike-trips"

POSTGRES_URL = "jdbc:postgresql://citibike-postgres:5432/citibike"
POSTGRES_TABLE = "trips"
POSTGRES_PROPERTIES = {
    "user": "postgres",
    "password": "postgres",
    "driver": "org.postgresql.Driver",
}

CHECKPOINT_LOCATION = "/tmp/citibike-spark-postgres-checkpoint"

# ============================================================
# SCHEMA — giữ nguyên từ v1.0 (13 trường)
# ============================================================

trip_schema = StructType([
    StructField("ride_id",            StringType(), True),
    StructField("rideable_type",      StringType(), True),
    StructField("started_at",         StringType(), True),
    StructField("ended_at",           StringType(), True),
    StructField("start_station_name", StringType(), True),
    StructField("start_station_id",   StringType(), True),
    StructField("end_station_name",   StringType(), True),
    StructField("end_station_id",     StringType(), True),
    StructField("start_lat",          DoubleType(), True),
    StructField("start_lng",          DoubleType(), True),
    StructField("end_lat",            DoubleType(), True),
    StructField("end_lng",            DoubleType(), True),
    StructField("member_casual",      StringType(), True),
])

# ============================================================
# FOREACHBATCH — GHI TRIPS (IDEMPOTENT)
# ============================================================

BATCHES_PROCESSED = 0
NEW_ROWS_WRITTEN = 0


def write_to_postgres(batch_df, batch_id):
    global BATCHES_PROCESSED, NEW_ROWS_WRITTEN

    """
    Ghi dữ liệu chuyến đi vào PostgreSQL.trips (idempotent).

    Thuật toán:
      1. Lọc ride_id hợp lệ, dropDuplicates trong batch.
      2. Lấy min/max started_at của batch (date-range).
      3. Truy vấn PostgreSQL: ride_id đã có trong khoảng thời gian đó.
      4. left_anti join → chỉ giữ ride_id chưa tồn tại.
      5. Append vào PostgreSQL.trips — không xóa dữ liệu cũ.
    """

    print("=" * 70)
    print(f"[PROCESS] TRIPS — BATCH {batch_id}")
    print("=" * 70)

    if batch_df.isEmpty():
        print("[PROCESS] Batch rong — khong co du lieu xu ly.")
        return

    spark = batch_df.sparkSession

    # ── 1. Chọn đúng 13 cột schema trips, lọc, dedup trong batch ──
    trips_df = batch_df.select(
        "ride_id",
        "rideable_type",
        "started_at",
        "ended_at",
        "start_station_name",
        "start_station_id",
        "end_station_name",
        "end_station_id",
        "start_lat",
        "start_lng",
        "end_lat",
        "end_lng",
        "member_casual",
    ).filter(
        col("ride_id").isNotNull()
        & col("started_at").isNotNull()
        & col("ended_at").isNotNull()
    ).dropDuplicates(["ride_id"])

    total_in_batch = trips_df.count()
    print(f"[PROCESS] Records hop le trong batch: {total_in_batch:,}")

    if total_in_batch == 0:
        print("[PROCESS] Khong co record hop le trong batch.")
        return

    # ── 2. Lấy date range của batch ─────────────────────────
    range_row = trips_df.agg(
        spark_min("started_at").alias("min_ts"),
        spark_max("started_at").alias("max_ts"),
    ).collect()[0]

    min_ts = range_row["min_ts"]
    max_ts = range_row["max_ts"]

    print(f"[PROCESS] Batch date range: {min_ts} → {max_ts}")

    # ── 3. Truy vấn ride_id đã có trong khoảng thời gian đó ─
    try:
        date_range_query = (
            f"(SELECT ride_id FROM trips "
            f"WHERE started_at >= '{min_ts}' "
            f"AND started_at <= '{max_ts}') AS existing_trips"
        )
        existing_df = spark.read.jdbc(
            url=POSTGRES_URL,
            table=date_range_query,
            properties=POSTGRES_PROPERTIES,
        )
        existing_count = existing_df.count()
        print(
            f"[PROCESS] ride_id da ton tai trong date range nay: "
            f"{existing_count:,}"
        )
    except Exception as exc:
        print(
            f"[PROCESS] Chua co du lieu trong date range "
            f"(co the la lan dau chay): {exc}"
        )
        existing_df = None
        existing_count = 0

    # ── 4. left_anti join → chỉ giữ ride_id mới ────────────
    if existing_df is not None and existing_count > 0:
        new_df = trips_df.join(
            existing_df,
            on="ride_id",
            how="left_anti",
        )
    else:
        new_df = trips_df

    new_count = new_df.count()
    skipped = total_in_batch - new_count

    print(f"[PROCESS] Records moi can ghi:       {new_count:,}")
    print(f"[PROCESS] Records da ton tai (skip): {skipped:,}")

    if new_count == 0:
        print(
            "[PROCESS] Tat ca ride_id da ton tai — "
            "khong ghi them. Du lieu H1 2026 nguyen ven."
        )
        return

    # ── 5. Append vào PostgreSQL.trips ──────────────────────
    new_df.write.jdbc(
        url=POSTGRES_URL,
        table=POSTGRES_TABLE,
        mode="append",
        properties=POSTGRES_PROPERTIES,
    )

    NEW_ROWS_WRITTEN += new_count
    BATCHES_PROCESSED += 1


    print(
        f"[DATABASE] Da ghi {new_count:,} records moi "
        f"vao PostgreSQL.trips"
    )
    print(
        f"[DATABASE] Du lieu cu (H1 2026) giu nguyen: "
        f"{existing_count:,} records skip, khong bi anh huong."
    )


# ============================================================
# PIPELINE TRANSFORM — GIỮ NGUYÊN LOGIC V1.0
# ============================================================

def build_stream(kafka_df):
    """
    Parse Kafka stream, chuẩn hóa thời gian.
    Logic giữ nguyên từ v1.0.
    """

    parsed_df = (
        kafka_df
        .selectExpr("CAST(value AS STRING) AS json_value")
        .select(
            from_json(col("json_value"), trip_schema).alias("trip")
        )
        .select("trip.*")
    )

    # Chuẩn hóa datetime — format giống v1.0
    datetime_df = (
        parsed_df
        .withColumn(
            "started_at",
            to_timestamp("started_at", "yyyy-MM-dd HH:mm:ss.SSS"),
        )
        .withColumn(
            "ended_at",
            to_timestamp("ended_at", "yyyy-MM-dd HH:mm:ss.SSS"),
        )
    )

    # Tạo các trường phái sinh (giữ nguyên v1.0, dùng trong logging)
    enriched_df = (
        datetime_df
        .withColumn(
            "ride_duration_minutes",
            (
                unix_timestamp("ended_at")
                - unix_timestamp("started_at")
            ) / 60.0,
        )
        .withColumn("date",        to_date("started_at"))
        .withColumn("hour",        hour("started_at"))
        .withColumn("day_of_week", dayofweek("started_at"))
        .withColumn("month",       month("started_at"))
    )

    return enriched_df


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description="Citi Bike Trips to PostgreSQL — Task 6"
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        default=False,
        help=(
            "Chay streaming lien tuc (awaitTermination). "
            "Mac dinh: availableNow=True — xu ly het roi tu ket thuc."
        ),
    )
    args, _ = parser.parse_known_args()

    # ── Khởi tạo Spark ──────────────────────────────────────
    spark = (
        SparkSession.builder
        .appName("CitibikeKafkaToPostgreSQL")
        .master("spark://spark-master:7077")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    mode_label = "STREAM" if args.stream else "AVAILABLE_NOW"

    print("=" * 70)
    print("[START] CITI BIKE — SPARK TRIPS TO POSTGRESQL (TASK 6)")
    print(f"[START] Mode: {mode_label}")
    print("[START] Kafka topic: citibike-trips")
    print("[START] Target table: PostgreSQL.trips")
    print("[START] Checkpoint: " + CHECKPOINT_LOCATION)
    print("=" * 70)

    # ── Đọc Kafka (resume từ checkpoint) ────────────────────
    print("[PROCESS] Ket noi Kafka bootstrap: kafka:29092")
    print("[PROCESS] startingOffsets=earliest (checkpoint se ghi de).")
    kafka_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", "earliest")
        .option("failOnDataLoss", "false")
        .load()
    )

    # ── Transform ────────────────────────────────────────────
    stream_df = build_stream(kafka_df)

    # ── Streaming writer ─────────────────────────────────────
    writer = (
        stream_df.writeStream
        .foreachBatch(write_to_postgres)
        .outputMode("append")
        .option("checkpointLocation", CHECKPOINT_LOCATION)
    )

    if args.stream:
        query = writer.start()
        print("[PROCESS] Streaming lien tuc — Ctrl+C de dung.")
        query.awaitTermination()
    else:
        query = writer.trigger(availableNow=True).start()
        print(
            "[PROCESS] availableNow=True — "
            "xu ly het du lieu hien co roi tu ket thuc."
        )
        query.awaitTermination()

        total_input_rows = 0
        if query.recentProgress:
            for p in query.recentProgress:
                if isinstance(p, dict):
                    total_input_rows += p.get("numInputRows", 0)
                elif hasattr(p, "numInputRows"):
                    total_input_rows += getattr(p, "numInputRows", 0)
                elif hasattr(p, "get"):
                    total_input_rows += p.get("numInputRows", 0)

        if total_input_rows == 0 or NEW_ROWS_WRITTEN == 0:
            print("[CHECK] No new data from Kafka topic (0 records processed).")
            print("[CHECK] Du lieu PostgreSQL.trips giu nguyen.")
        else:
            print(
                f"[DATABASE] Da ghi {NEW_ROWS_WRITTEN:,} records moi "
                f"vao PostgreSQL.trips."
            )


    print("=" * 70)
    print("[SUCCESS] Spark Trips Processing hoan thanh — Task 6.")
    print("=" * 70)

    spark.stop()


if __name__ == "__main__":
    main()

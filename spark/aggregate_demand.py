"""
aggregate_demand.py — Task 5: Spark Processing (Phase 1)

Đọc dữ liệu từ Kafka topic citibike-trips, tổng hợp nhu cầu theo giờ
và ghi kết quả vào PostgreSQL.hourly_demand.

Cơ chế idempotent:
  Trước khi ghi mỗi micro-batch, truy vấn danh sách timestamp đã có
  trong hourly_demand, loại bỏ các khung giờ đã tồn tại, chỉ INSERT
  các khung giờ mới → không gây duplicate key, không xóa dữ liệu cũ.

Chế độ chạy:
  - Mặc định (availableNow=True): xử lý hết dữ liệu mới rồi tự kết
    thúc (phù hợp cho update pipeline tự động).
  - Flag --stream: streaming liên tục awaitTermination().

Checkpoint:
  /tmp/citibike-spark-aggregate-postgres-checkpoint
  Checkpoint ghi nhớ vị trí đọc Kafka lần trước.
  Xóa checkpoint thủ công nếu muốn xử lý lại từ đầu.
"""

import argparse

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    count,
    dayofweek,
    from_json,
    hour,
    month,
    to_date,
    to_timestamp,
    when,
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
POSTGRES_TABLE = "hourly_demand"
POSTGRES_PROPERTIES = {
    "user": "postgres",
    "password": "postgres",
    "driver": "org.postgresql.Driver",
}

CHECKPOINT_LOCATION = (
    "/tmp/citibike-spark-aggregate-postgres-checkpoint"
)

# ============================================================
# SCHEMA — giữ nguyên từ v1.0
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
# FOREACHBATCH — GHI POSTGRESQL (IDEMPOTENT)
# ============================================================

BATCHES_PROCESSED = 0
NEW_ROWS_WRITTEN = 0


def write_to_postgres(batch_df, batch_id):
    global BATCHES_PROCESSED, NEW_ROWS_WRITTEN

    """
    Ghi kết quả aggregate vào PostgreSQL.hourly_demand (idempotent).

    Thuật toán:
      1. Tổng hợp demand theo (date, hour, ...) từ features trong batch.
      2. Tạo cột timestamp = ngày + giờ.
      3. Lấy danh sách timestamp đã có trong PostgreSQL.
      4. left_anti join → chỉ giữ timestamp chưa tồn tại.
      5. Append vào PostgreSQL (không xóa / không TRUNCATE dữ liệu cũ).
    """

    print("=" * 70)
    print(f"[PROCESS] HOURLY DEMAND — BATCH {batch_id}")
    print("=" * 70)

    if batch_df.isEmpty():
        print("[PROCESS] Batch rong — khong co du lieu xu ly.")
        return

    spark = batch_df.sparkSession

    # ── Bước 1: Aggregate từ batch (outputMode append) ───────
    # Trong chế độ append foreachBatch, batch_df đã là dữ liệu mới
    # chưa được commit. Cần gom nhóm thủ công để tổng hợp demand.
    demand_df = (
        batch_df
        .filter(
            col("started_at").isNotNull()
            & col("date").isNotNull()
            & col("hour").isNotNull()
            & col("ride_id").isNotNull()
        )
        .groupBy(
            "date",
            "hour",
            "day_of_week",
            "month",
            "is_weekend",
        )
        .agg(
            count("*").alias("demand"),
            count(
                when(col("member_casual") == "member", True)
            ).alias("member_count"),
            count(
                when(col("member_casual") == "casual", True)
            ).alias("casual_count"),
            count(
                when(col("rideable_type") == "electric_bike", True)
            ).alias("electric_count"),
            count(
                when(col("rideable_type") == "classic_bike", True)
            ).alias("classic_count"),
        )
        .dropDuplicates(["date", "hour"])
    )

    # ── Bước 2: Tạo cột timestamp (đầu giờ) ─────────────────
    demand_df = demand_df.withColumn(
        "timestamp",
        col("date").cast("timestamp")
        + (col("hour") * 3600).cast("interval second"),
    ).select(
        "timestamp",
        "date",
        "hour",
        "day_of_week",
        "month",
        "is_weekend",
        "member_count",
        "casual_count",
        "electric_count",
        "classic_count",
        "demand",
    )

    total_in_batch = demand_df.count()
    print(f"[PROCESS] Aggregate rows trong batch: {total_in_batch:,}")

    if total_in_batch == 0:
        print("[PROCESS] Khong co aggregate record.")
        return

    # ── Bước 3: Đọc timestamp đã có trong PostgreSQL ─────────
    try:
        existing_ts_df = spark.read.jdbc(
            url=POSTGRES_URL,
            table=(
                "(SELECT timestamp FROM hourly_demand) AS existing_ts"
            ),
            properties=POSTGRES_PROPERTIES,
        )
        existing_count = existing_ts_df.count()
        print(
            f"[PROCESS] Timestamp da co trong PostgreSQL: "
            f"{existing_count:,}"
        )
    except Exception as exc:
        print(
            f"[PROCESS] Chua co du lieu PostgreSQL "
            f"(co the la lan dau chay): {exc}"
        )
        existing_ts_df = None
        existing_count = 0

    # ── Bước 4: Lọc chỉ giữ timestamp chưa tồn tại ──────────
    if existing_ts_df is not None and existing_count > 0:
        new_df = demand_df.join(
            existing_ts_df,
            on="timestamp",
            how="left_anti",
        )
    else:
        new_df = demand_df

    new_count = new_df.count()
    skipped = total_in_batch - new_count

    print(f"[PROCESS] Rows moi can ghi:        {new_count:,}")
    print(f"[PROCESS] Rows da ton tai (skip):  {skipped:,}")

    if new_count == 0:
        print(
            "[PROCESS] Tat ca timestamp da ton tai — "
            "khong ghi them. Du lieu H1 2026 nguyen ven."
        )
        return

    # ── Bước 5: Append vào PostgreSQL ────────────────────────
    new_df.write.jdbc(
        url=POSTGRES_URL,
        table=POSTGRES_TABLE,
        mode="append",
        properties=POSTGRES_PROPERTIES,
    )

    NEW_ROWS_WRITTEN += new_count
    BATCHES_PROCESSED += 1


    print(
        f"[DATABASE] Da ghi {new_count:,} rows moi "
        f"vao PostgreSQL.hourly_demand"
    )
    print(
        f"[DATABASE] Du lieu cu (H1 2026) giu nguyen: "
        f"{existing_count:,} rows khong bi anh huong."
    )


# ============================================================
# PIPELINE TRANSFORM — GIỮ NGUYÊN LOGIC V1.0
# ============================================================

def build_features_stream(kafka_df):
    """
    Parse Kafka stream, chuẩn hóa thời gian, tạo trường phái sinh.
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
        .withColumn("date",        to_date("started_at"))
        .withColumn("hour",        hour("started_at"))
        .withColumn("day_of_week", dayofweek("started_at"))
        .withColumn("month",       month("started_at"))
    )

    # is_weekend: Spark dayofweek 1=Sun, 7=Sat (giống v1.0)
    features_df = datetime_df.withColumn(
        "is_weekend",
        col("day_of_week").isin([1, 7]),
    )

    return features_df


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description="Citi Bike Hourly Demand Aggregation — Task 5"
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
        .appName("CitibikeHourlyDemandToPostgreSQL")
        .master("spark://spark-master:7077")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    mode_label = "STREAM" if args.stream else "AVAILABLE_NOW"

    print("=" * 70)
    print("[START] CITI BIKE — SPARK PROCESSING (TASK 5 — PHASE 1)")
    print(f"[START] Mode: {mode_label}")
    print("[START] Kafka topic: citibike-trips")
    print("[START] Target table: PostgreSQL.hourly_demand")
    print("=" * 70)

    # ── Đọc Kafka ────────────────────────────────────────────
    print("[PROCESS] Ket noi Kafka bootstrap: kafka:29092")
    kafka_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", "earliest")
        .option("failOnDataLoss", "false")
        .load()
    )

    # ── Transform — logic v1.0 ───────────────────────────────
    features_df = build_features_stream(kafka_df)

    # ── Streaming writer ─────────────────────────────────────
    writer = (
        features_df.writeStream
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
            print("[CHECK] Du lieu PostgreSQL.hourly_demand giu nguyen.")
        else:
            print(
                f"[DATABASE] Da ghi {NEW_ROWS_WRITTEN:,} rows moi "
                f"vao PostgreSQL.hourly_demand."
            )


    print("=" * 70)
    print("[SUCCESS] Spark Processing hoan thanh — Task 5.")
    print("=" * 70)

    spark.stop()


if __name__ == "__main__":
    main()

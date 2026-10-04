from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    from_json,
    to_timestamp,
    to_date,
    hour,
    dayofweek,
    month,
    when,
    lit,
    count
)
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType
)

KAFKA_BOOTSTRAP_SERVERS = "kafka:29092"
KAFKA_TOPIC = "citibike-trips"

POSTGRES_URL = "jdbc:postgresql://citibike-postgres:5432/citibike"
POSTGRES_TABLE = "hourly_demand"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "postgres"
JDBC_DRIVER = "org.postgresql.Driver"

trip_schema = StructType([
    StructField("ride_id", StringType(), True),
    StructField("rideable_type", StringType(), True),
    StructField("started_at", StringType(), True),
    StructField("ended_at", StringType(), True),
    StructField("start_station_name", StringType(), True),
    StructField("start_station_id", StringType(), True),
    StructField("end_station_name", StringType(), True),
    StructField("end_station_id", StringType(), True),
    StructField("start_lat", DoubleType(), True),
    StructField("start_lng", DoubleType(), True),
    StructField("end_lat", DoubleType(), True),
    StructField("end_lng", DoubleType(), True),
    StructField("member_casual", StringType(), True)
])


def write_to_postgres(batch_df, batch_id):

    print("=" * 70)
    print(f"HOURLY DEMAND - BATCH {batch_id}")
    print("=" * 70)

    if batch_df.isEmpty():
        print("Batch rong - khong ghi PostgreSQL")
        return

    # Chọn đúng các trường cần lưu
    result_df = batch_df.select(
        "date",
        "hour",
        "day_of_week",
        "month",
        "is_weekend",
        "member_count",
        "casual_count",
        "electric_count",
        "classic_count",
        "demand"
    )

    result_df = result_df.dropDuplicates(
        ["date", "hour"]
    )

    record_count = result_df.count()

    print(f"So record aggregate trong batch: {record_count}")

    if record_count == 0:
        print("Khong co aggregate record")
        return

    # timestamp = thời điểm đầu giờ
    result_df = result_df.withColumn(
        "timestamp",
        col("date").cast("timestamp")
        + (col("hour") * 3600).cast("interval second")
    )

    result_df = result_df.select(
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
        "demand"
    )

    result_df.write \
        .format("jdbc") \
        .option("url", POSTGRES_URL) \
        .option("dbtable", POSTGRES_TABLE) \
        .option("user", POSTGRES_USER) \
        .option("password", POSTGRES_PASSWORD) \
        .option("driver", JDBC_DRIVER) \
        .mode("append") \
        .save()

    print(
        f"Da ghi {record_count} aggregate records "
        "vao PostgreSQL.hourly_demand"
    )


def main():

    spark = (
        SparkSession.builder
        .appName("CitibikeHourlyDemandToPostgreSQL")
        .master("spark://spark-master:7077")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    print("=" * 70)
    print("CITI BIKE - HOURLY DEMAND TO POSTGRESQL")
    print("=" * 70)

    # 1. Đọc Kafka
    kafka_df = (
        spark.readStream
        .format("kafka")
        .option(
            "kafka.bootstrap.servers",
            KAFKA_BOOTSTRAP_SERVERS
        )
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", "earliest")
        .option("failOnDataLoss", "false")
        .load()
    )

    # 2. Parse JSON
    parsed_df = (
        kafka_df
        .selectExpr(
            "CAST(value AS STRING) AS json_value"
        )
        .select(
            from_json(
                col("json_value"),
                trip_schema
            ).alias("trip")
        )
        .select("trip.*")
    )

    # 3. Chuẩn hóa datetime
    datetime_df = (
        parsed_df
        .withColumn(
            "started_at",
            to_timestamp(
                "started_at",
                "yyyy-MM-dd HH:mm:ss.SSS"
            )
        )
        .withColumn(
            "date",
            to_date("started_at")
        )
        .withColumn(
            "hour",
            hour("started_at")
        )
        .withColumn(
            "day_of_week",
            dayofweek("started_at")
        )
        .withColumn(
            "month",
            month("started_at")
        )
    )

    # 4. Tạo is_weekend
    features_df = datetime_df.withColumn(
        "is_weekend",
        col("day_of_week").isin([1, 7])
    )

    # 5. Aggregate theo ngày + giờ
    demand_df = (
        features_df
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
            "is_weekend"
        )
        .agg(
            count("*").alias("demand"),
            count(
                when(
                    col("member_casual") == "member",
                    True
                )
            ).alias("member_count"),
            count(
                when(
                    col("member_casual") == "casual",
                    True
                )
            ).alias("casual_count"),
            count(
                when(
                    col("rideable_type") == "electric_bike",
                    True
                )
            ).alias("electric_count"),
            count(
                when(
                    col("rideable_type") == "classic_bike",
                    True
                )
            ).alias("classic_count")
        )
    )

    # 6. Ghi PostgreSQL
    query = (
        demand_df.writeStream
        .foreachBatch(write_to_postgres)
        .outputMode("complete")
        .option(
            "checkpointLocation",
            "/tmp/citibike-spark-aggregate-postgres-checkpoint"
        )
        .start()
    )

    query.awaitTermination()


if __name__ == "__main__":
    main()

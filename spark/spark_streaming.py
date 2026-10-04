from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    from_json,
    to_timestamp,
    unix_timestamp,
    to_date,
    hour,
    dayofweek,
    month
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
POSTGRES_TABLE = "trips"
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
    print(f"POSTGRESQL - BATCH {batch_id}")
    print("=" * 70)

    if batch_df.isEmpty():
        print("Batch rong - khong ghi PostgreSQL")
        return

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
        "member_casual"
    )

    trips_df = trips_df.filter(
        col("ride_id").isNotNull()
    )

    trips_df = trips_df.dropDuplicates(["ride_id"])

    record_count = trips_df.count()

    print(f"So record hop le trong batch: {record_count}")

    if record_count == 0:
        print("Khong co record hop le")
        return

    trips_df.write \
        .format("jdbc") \
        .option("url", POSTGRES_URL) \
        .option("dbtable", POSTGRES_TABLE) \
        .option("user", POSTGRES_USER) \
        .option("password", POSTGRES_PASSWORD) \
        .option("driver", JDBC_DRIVER) \
        .mode("append") \
        .save()

    print(f"Da ghi {record_count} record vao PostgreSQL.trips")

def main():
    spark = (
        SparkSession.builder
        .appName("CitibikeKafkaToPostgreSQL")
        .master("spark://spark-master:7077")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    print("=" * 70)
    print("CITI BIKE - SPARK TO POSTGRESQL")
    print("=" * 70)

    kafka_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", "earliest")
        .option("failOnDataLoss", "false")
        .load()
    )

    parsed_df = (
        kafka_df
        .selectExpr("CAST(value AS STRING) AS json_value")
        .select(
            from_json(col("json_value"), trip_schema).alias("trip")
        )
        .select("trip.*")
    )

    datetime_df = (
        parsed_df
        .withColumn(
            "started_at",
            to_timestamp("started_at", "yyyy-MM-dd HH:mm:ss.SSS")
        )
        .withColumn(
            "ended_at",
            to_timestamp("ended_at", "yyyy-MM-dd HH:mm:ss.SSS")
        )
    )

    duration_df = (
        datetime_df
        .withColumn(
            "ride_duration_minutes",
            (
                unix_timestamp("ended_at")
                - unix_timestamp("started_at")
            ) / 60.0
        )
    )

    time_features_df = (
        duration_df
        .withColumn("date", to_date("started_at"))
        .withColumn("hour", hour("started_at"))
        .withColumn("day_of_week", dayofweek("started_at"))
        .withColumn("month", month("started_at"))
    )

    query = (
        time_features_df.writeStream
        .foreachBatch(write_to_postgres)
        .outputMode("append")
        .option(
            "checkpointLocation",
            "/tmp/citibike-spark-postgres-checkpoint"
        )
        .start()
    )

    query.awaitTermination()

if __name__ == "__main__":
    main()

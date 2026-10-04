from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    from_json,
    to_timestamp,
    unix_timestamp,
    sum as spark_sum
)
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType
)

KAFKA_BOOTSTRAP_SERVERS = "kafka:29092"
KAFKA_TOPIC = "citibike-trips"

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


spark = (
    SparkSession.builder
    .appName("CitibikeCheckAnomalies")
    .master("spark://spark-master:7077")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

kafka_df = (
    spark.read
    .format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
    .option("subscribe", KAFKA_TOPIC)
    .option("startingOffsets", "earliest")
    .option("endingOffsets", "latest")
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
        "started_at_ts",
        to_timestamp("started_at", "yyyy-MM-dd HH:mm:ss.SSS")
    )
    .withColumn(
        "ended_at_ts",
        to_timestamp("ended_at", "yyyy-MM-dd HH:mm:ss.SSS")
    )
)

check_df = (
    datetime_df
    .withColumn(
        "duration_seconds",
        unix_timestamp("ended_at_ts")
        - unix_timestamp("started_at_ts")
    )
)

print("=" * 70)
print("CITI BIKE - KIEM TRA DU LIEU BAT THUONG")
print("=" * 70)

total = check_df.count()

duration_invalid = check_df.filter(
    col("duration_seconds") <= 0
).count()

datetime_invalid = check_df.filter(
    col("started_at_ts").isNull() |
    col("ended_at_ts").isNull()
).count()

required_missing = check_df.filter(
    col("ride_id").isNull() |
    col("started_at").isNull() |
    col("ended_at").isNull() |
    col("start_station_id").isNull() |
    col("end_station_id").isNull()
).count()

print(f"Tong so ban ghi:              {total:,}")
print(f"Duration <= 0:                {duration_invalid:,}")
print(f"Datetime khong hop le:        {datetime_invalid:,}")
print(f"Thieu truong bat buoc:        {required_missing:,}")

print("=" * 70)

spark.stop()
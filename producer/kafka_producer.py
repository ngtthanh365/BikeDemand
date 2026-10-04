import json
import os
import sys

import pandas as pd
from kafka import KafkaProducer


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATASET_PATH = os.path.join(
    PROJECT_ROOT,
    "data",
    "processed",
    "citibike_2026_H1.csv",
)

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC = "citibike-trips"


def create_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        key_serializer=lambda key: key.encode("utf-8"),
        value_serializer=lambda value: json.dumps(
            value,
            ensure_ascii=False
        ).encode("utf-8"),
        acks="all",
        retries=3,
    )


def main():
    print("=" * 70)
    print("CITI BIKE KAFKA PRODUCER")
    print("=" * 70)

    if not os.path.exists(DATASET_PATH):
        print(f"Dataset not found: {DATASET_PATH}")
        sys.exit(1)

    print(f"Dataset: {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)

    print(f"Rows loaded: {len(df):,}")

    producer = create_producer()

    sent_count = 0
    error_count = 0

    print(f"Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"Topic: {KAFKA_TOPIC}")
    print("-" * 70)

    for _, row in df.iterrows():
        try:
            message = {
                "ride_id": row["ride_id"],
                "rideable_type": row["rideable_type"],
                "started_at": row["started_at"],
                "ended_at": row["ended_at"],
                "start_station_name": row["start_station_name"],
                "start_station_id": row["start_station_id"],
                "end_station_name": row["end_station_name"],
                "end_station_id": row["end_station_id"],
                "start_lat": row["start_lat"],
                "start_lng": row["start_lng"],
                "end_lat": row["end_lat"],
                "end_lng": row["end_lng"],
                "member_casual": row["member_casual"],
            }

            ride_id = str(row["ride_id"])

            producer.send(
                KAFKA_TOPIC,
                key=ride_id,
                value=message,
            )

            sent_count += 1

            if sent_count % 10_000 == 0:
                print(f"Sent: {sent_count:,}")

        except Exception as exc:
            error_count += 1
            print(f"Error at row {_}: {exc}")

    producer.flush()
    producer.close()

    print("-" * 70)
    print("PRODUCER COMPLETED")
    print(f"Messages sent:   {sent_count:,}")
    print(f"Errors:          {error_count:,}")
    print("=" * 70)


if __name__ == "__main__":
    main()
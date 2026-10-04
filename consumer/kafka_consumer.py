import json
import os
import sys
from datetime import datetime

from kafka import KafkaConsumer


KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC = "citibike-trips"
MAX_MESSAGES = 20


REQUIRED_FIELDS = [
    "ride_id",
    "rideable_type",
    "started_at",
    "ended_at",
    "start_station_id",
    "end_station_id",
    "start_lat",
    "start_lng",
    "end_lat",
    "end_lng",
    "member_casual",
]


def validate_message(data):
    """
    Validate một Kafka message sau khi deserialize JSON.
    Trả về:
        (True, "OK") nếu hợp lệ
        (False, "lý do lỗi") nếu không hợp lệ
    """

    if not isinstance(data, dict):
        return False, "Message không phải JSON object"

    # Kiểm tra các trường bắt buộc
    for field in REQUIRED_FIELDS:
        if field not in data:
            return False, f"Thiếu trường: {field}"

    # ride_id
    if not isinstance(data["ride_id"], str) or not data["ride_id"].strip():
        return False, "ride_id không hợp lệ"

    # started_at
    try:
        datetime.strptime(
            data["started_at"],
            "%Y-%m-%d %H:%M:%S.%f"
        )
    except (ValueError, TypeError):
        return False, "started_at không hợp lệ"

    # ended_at
    try:
        datetime.strptime(
            data["ended_at"],
            "%Y-%m-%d %H:%M:%S.%f"
        )
    except (ValueError, TypeError):
        return False, "ended_at không hợp lệ"

    # Kiểm tra kiểu dữ liệu số
    numeric_fields = [
        "start_lat",
        "start_lng",
        "end_lat",
        "end_lng",
    ]

    for field in numeric_fields:
        if not isinstance(data[field], (int, float)):
            return False, f"{field} không phải kiểu số"

    # Kiểm tra member_casual
    if data["member_casual"] not in ("member", "casual"):
        return False, "member_casual không hợp lệ"

    return True, "OK"


def create_consumer():
    return KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        group_id=None,
    )


def main():
    print("=" * 70)
    print("CITI BIKE KAFKA CONSUMER")
    print("=" * 70)
    print(f"Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"Topic: {KAFKA_TOPIC}")
    print("-" * 70)

    consumer = create_consumer()

    print("Consumer connected successfully.")
    print(f"Đang đọc tối đa {MAX_MESSAGES} message...")
    print("-" * 70)

    valid_count = 0
    invalid_count = 0
    processed_count = 0

    try:
        for message in consumer:
            processed_count += 1

            raw_value = message.value

            # --------------------------------------------------
            # 1. Deserialize JSON
            # --------------------------------------------------
            try:
                text_value = raw_value.decode("utf-8")
                data = json.loads(text_value)

            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                invalid_count += 1

                print(
                    f"[INVALID] "
                    f"partition={message.partition} "
                    f"offset={message.offset} "
                    f"Reason: JSON không hợp lệ - {exc}"
                )

            else:
                # --------------------------------------------------
                # 2. Validate schema + dữ liệu
                # --------------------------------------------------
                is_valid, reason = validate_message(data)

                if is_valid:
                    valid_count += 1

                    print(
                        f"[VALID] "
                        f"partition={message.partition} "
                        f"offset={message.offset} "
                        f"ride_id={data['ride_id']}"
                    )

                else:
                    invalid_count += 1

                    ride_id = data.get("ride_id", "UNKNOWN")

                    print(
                        f"[INVALID] "
                        f"partition={message.partition} "
                        f"offset={message.offset} "
                        f"ride_id={ride_id} "
                        f"Reason: {reason}"
                    )

            # --------------------------------------------------
            # 3. Dừng sau MAX_MESSAGES
            # --------------------------------------------------
            if processed_count >= MAX_MESSAGES:
                break

    except KeyboardInterrupt:
        print("\nConsumer stopped by user.")

    finally:
        consumer.close()

    print("-" * 70)
    print("CONSUMER COMPLETED")
    print(f"Valid messages:   {valid_count}")
    print(f"Invalid messages: {invalid_count}")
    print(f"Total processed:  {processed_count}")
    print("=" * 70)


if __name__ == "__main__":
    main()
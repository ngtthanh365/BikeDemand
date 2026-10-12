import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import pandas as pd
from kafka import KafkaProducer

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
DEFAULT_TOPIC = "citibike-trips"
STATE_FILE = PROJECT_ROOT / "data" / "processed" / ".kafka_producer_state.json"


def load_producer_state() -> Dict[str, Any]:
    """
    Đọc trạng thái các file/batch đã gửi vào Kafka để đảm bảo tính Idempotent.
    """
    if not STATE_FILE.exists():
        return {"sent_files": {}}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print(f"[CHECK] Lưu ý: Không thể đọc file trạng thái producer ({exc}). Khởi tạo mới.")
        return {"sent_files": {}}


def save_producer_state(state: Dict[str, Any]) -> None:
    """
    Lưu lại trạng thái sau khi gửi thành công.
    """
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as exc:
        print(f"[CHECK] Lưu ý: Không thể lưu file trạng thái producer ({exc}).")


def create_producer(
    bootstrap_servers: str = DEFAULT_BOOTSTRAP_SERVERS,
    retries: int = 3,
) -> KafkaProducer:
    """
    Khởi tạo KafkaProducer tương thích với cấu hình hệ thống.
    """
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        key_serializer=lambda key: str(key).encode("utf-8"),
        value_serializer=lambda val: json.dumps(val, ensure_ascii=False).encode("utf-8"),
        acks="all",
        retries=retries,
        batch_size=32 * 1024,
        linger_ms=10,
    )


def serialize_record(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Chuyển đổi một bản ghi Pandas sang định dạng JSON schema chuẩn của topic citibike-trips.
    Xử lý các giá trị NaN/NaT thành None (JSON null).
    """
    return {
        "ride_id": str(row["ride_id"]),
        "rideable_type": str(row["rideable_type"]) if pd.notna(row.get("rideable_type")) else None,
        "started_at": str(row["started_at"]) if pd.notna(row.get("started_at")) else None,
        "ended_at": str(row["ended_at"]) if pd.notna(row.get("ended_at")) else None,
        "start_station_name": str(row["start_station_name"]) if pd.notna(row.get("start_station_name")) else None,
        "start_station_id": str(row["start_station_id"]) if pd.notna(row.get("start_station_id")) else None,
        "end_station_name": str(row["end_station_name"]) if pd.notna(row.get("end_station_name")) else None,
        "end_station_id": str(row["end_station_id"]) if pd.notna(row.get("end_station_id")) else None,
        "start_lat": float(row["start_lat"]) if pd.notna(row.get("start_lat")) else None,
        "start_lng": float(row["start_lng"]) if pd.notna(row.get("start_lng")) else None,
        "end_lat": float(row["end_lat"]) if pd.notna(row.get("end_lat")) else None,
        "end_lng": float(row["end_lng"]) if pd.notna(row.get("end_lng")) else None,
        "member_casual": str(row["member_casual"]) if pd.notna(row.get("member_casual")) else None,
    }


def send_dataset_to_kafka(
    dataset: Union[Path, str, pd.DataFrame],
    bootstrap_servers: str = DEFAULT_BOOTSTRAP_SERVERS,
    topic: str = DEFAULT_TOPIC,
    batch_identifier: Optional[str] = None,
    check_db_duplicates: bool = True,
    force: bool = False,
) -> int:
    """
    Gửi dữ liệu đã validate vào Kafka topic citibike-trips.
    Đảm bảo Idempotency: Không gửi lại các bản ghi hoặc file đã xử lý.
    """
    print("=" * 70)
    print("[START] CITI BIKE KAFKA PRODUCER")
    print("=" * 70)
    print(f"[CHECK] Kafka Broker: {bootstrap_servers}")
    print(f"[CHECK] Kafka Topic:  {topic}")

    file_name = None
    if isinstance(dataset, (str, Path)):
        file_path = Path(dataset)
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset không tồn tại: {file_path}")
        file_name = file_path.name
        batch_id = batch_identifier or file_name
        print(f"[CHECK] Đọc dataset: {file_name}")
        df = pd.read_csv(file_path, low_memory=False)
    elif isinstance(dataset, pd.DataFrame):
        df = dataset
        batch_id = batch_identifier or f"dataframe_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    else:
        raise TypeError("Dataset phải là đường dẫn file hoặc DataFrame.")

    total_rows = len(df)
    print(f"[CHECK] Tổng số dòng cần nạp: {total_rows:,}")

    if total_rows == 0:
        print("[CHECK] Dataset rỗng. Kết thúc.")
        print("-" * 70)
        print("[SUMMARY] Messages sent: 0")
        print("=" * 70)
        return 0

    state = load_producer_state()
    sent_files = state.get("sent_files", {})

    # Kiểm tra Idempotency qua state file
    if not force and batch_id in sent_files:
        info = sent_files[batch_id]
        print(
            f"[CHECK] Batch/File '{batch_id}' đã được gửi thành công trước đó "
            f"vào {info.get('sent_at')} ({info.get('message_count', 0):,} msgs)."
        )
        print("[CHECK] Bỏ qua không gửi lại để tránh duplicate trong Kafka topic.")
        print("-" * 70)
        print("[SUMMARY] Messages sent: 0 (Already sent previously)")
        print("=" * 70)
        return 0

    # Kiểm tra Idempotency qua PostgreSQL trips (nếu bật)
    if check_db_duplicates:
        try:
            from database.postgres import get_connection

            conn = get_connection()
            try:
                with conn.cursor() as cursor:
                    # Kiểm tra xem các ride_id đã có trong trips chưa
                    sample_ids = list(df["ride_id"].dropna().astype(str).head(1000))
                    if sample_ids:
                        format_strings = ",".join(["%s"] * len(sample_ids))
                        cursor.execute(
                            f"SELECT COUNT(*) FROM trips WHERE ride_id IN ({format_strings});",
                            sample_ids,
                        )
                        existing_count = cursor.fetchone()[0]
                        if existing_count == len(sample_ids) and not force:
                            print(
                                f"[CHECK] Toàn bộ mẫu ride_id ({len(sample_ids)}) "
                                f"đã tồn tại trong PostgreSQL trips."
                            )
                            print("[CHECK] Dữ liệu này đã được nạp vào hệ thống. Bỏ qua gửi Kafka.")
                            print("-" * 70)
                            print("[SUMMARY] Messages sent: 0 (Already processed in DB)")
                            print("=" * 70)
                            return 0
            finally:
                conn.close()
        except Exception as exc:
            print(f"[CHECK] Bỏ qua kiểm tra DB do không kết nối được ({exc}).")

    # Bắt đầu gửi dữ liệu
    print("[PROCESS] Đang kết nối tới Kafka Broker...")
    producer = create_producer(bootstrap_servers=bootstrap_servers)

    print(f"[PROCESS] Bắt đầu gửi {total_rows:,} records vào topic '{topic}'...")
    records = df.to_dict(orient="records")
    sent_count = 0
    error_count = 0

    for i, row in enumerate(records):
        try:
            message = serialize_record(row)
            ride_id = message["ride_id"]

            producer.send(
                topic,
                key=ride_id,
                value=message,
            )
            sent_count += 1

            if sent_count % 25_000 == 0:
                print(f"[PROCESS] Đã gửi: {sent_count:,}/{total_rows:,} messages...")

        except Exception as exc:
            error_count += 1
            if error_count <= 5:
                print(f"[ERROR] Lỗi tại bản ghi {i}: {exc}")

    # Đảm bảo toàn bộ message được flush vào Kafka
    print("[PROCESS] Đang flush toàn bộ messages tới Kafka brokers...")
    producer.flush()
    producer.close()

    print(f"[SUCCESS] Đã gửi hoàn tất {sent_count:,} messages vào topic '{topic}'.")

    # Lưu lại trạng thái để không gửi lại
    sent_files[batch_id] = {
        "sent_at": datetime.now().isoformat(),
        "message_count": sent_count,
        "error_count": error_count,
        "min_started_at": str(df["started_at"].min()) if "started_at" in df else None,
        "max_started_at": str(df["started_at"].max()) if "started_at" in df else None,
    }
    state["sent_files"] = sent_files
    save_producer_state(state)

    print("-" * 70)
    print("[SUMMARY] KẾT QUẢ KAFKA PRODUCER:")
    print(f"  - Messages gửi thành công: {sent_count:,}")
    print(f"  - Lỗi:                     {error_count:,}")
    print(f"  - Batch ID:                {batch_id}")
    print("=" * 70)

    return sent_count


def main():
    parser = argparse.ArgumentParser(description="Citi Bike Dynamic Kafka Producer")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Đường dẫn tới file CSV cần gửi (ví dụ: data/processed/JC-202607-citibike-tripdata-clean.csv)",
    )
    parser.add_argument(
        "--bootstrap-servers",
        type=str,
        default=DEFAULT_BOOTSTRAP_SERVERS,
        help=f"Kafka bootstrap servers (mặc định: {DEFAULT_BOOTSTRAP_SERVERS})",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=DEFAULT_TOPIC,
        help=f"Kafka topic (mặc định: {DEFAULT_TOPIC})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bỏ qua kiểm tra Idempotency và cưỡng chế gửi lại.",
    )
    parser.add_argument(
        "--no-db-check",
        action="store_true",
        help="Bỏ qua kiểm tra tồn tại trong PostgreSQL.",
    )

    args = parser.parse_args()

    # Nếu không cung cấp file, tìm file sạch mới nhất trong data/processed/
    input_file = args.input
    if not input_file:
        processed_dir = PROJECT_ROOT / "data" / "processed"
        clean_files = sorted(processed_dir.glob("JC-*-citibike-tripdata-clean.csv"))
        state = load_producer_state()
        sent_files = state.get("sent_files", {})

        # Tìm file sạch chưa được gửi
        unsent_files = [f for f in clean_files if f.name not in sent_files]
        if unsent_files:
            input_file = str(unsent_files[0])
            print(f"[CHECK] Tự động chọn file sạch chưa gửi: {Path(input_file).name}")
        else:
            # Fallback về baseline v1.0 nếu có
            baseline_file = processed_dir / "citibike_2026_H1.csv"
            if baseline_file.exists():
                input_file = str(baseline_file)
                print(f"[CHECK] Không có file mới chưa gửi, sử dụng baseline: {baseline_file.name}")
            else:
                print("[ERROR] Không tìm thấy file dữ liệu nào để gửi.")
                sys.exit(1)

    send_dataset_to_kafka(
        dataset=Path(input_file),
        bootstrap_servers=args.bootstrap_servers,
        topic=args.topic,
        check_db_duplicates=not args.no_db_check,
        force=args.force,
    )


if __name__ == "__main__":
    main()
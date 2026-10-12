"""
update_data.py — Task 9: Logging và Error Handling (Phase 1)

Entry point duy nhất điều phối toàn bộ quy trình cập nhật dữ liệu tự động.
Chuẩn hóa 9 thẻ log bắt buộc:
  [START]    - Khởi động pipeline / cập nhật
  [CHECK]    - Kiểm tra nguồn S3, database, trạng thái trùng lặp, no new data
  [DOWNLOAD] - Quá trình tải và giải nén dữ liệu từ Citi Bike S3
  [VALIDATE] - Xác thực schema, làm sạch, loại bỏ lỗi tọa độ/thời gian
  [PROCESS]  - Gửi dữ liệu vào Kafka stream, chạy Spark jobs
  [DATABASE] - Ghi và cập nhật dữ liệu vào PostgreSQL
  [SUCCESS]  - Hoàn tất thành công từng bước và toàn bộ pipeline
  [ERROR]    - Ghi nhận và phân loại chính xác 9 nhóm lỗi hệ thống
  [SUMMARY]  - Báo cáo tổng kết số lượng bản ghi mới và thống kê DB

Xử lý và phân loại 9 loại ngoại lệ:
  1. Internet unavailable
  2. Source unavailable
  3. Download failed
  4. Invalid file
  5. Invalid schema
  6. Duplicate ride_id
  7. Kafka unavailable
  8. Spark processing error
  9. PostgreSQL unavailable
"""

import argparse
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import kafka.errors
import psycopg2
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import các module hiện có từ Task 1-8
from database.postgres import get_connection
from producer.kafka_producer import DEFAULT_TOPIC, send_dataset_to_kafka
from scripts.download_data import (
    DEFAULT_RAW_DIR,
    S3_BUCKET_URL,
    download_and_extract_month,
    find_new_months,
    get_local_months,
)
from scripts.validate_data import ValidationError, validate_file


def classify_error(exc: Exception, step: str = "") -> str:
    """
    Phân loại ngoại lệ thành 1 trong 9 nhóm lỗi chuẩn của Task 9.
    Trả về chuỗi tên loại lỗi chuẩn:
      1. Internet unavailable
      2. Source unavailable
      3. Download failed
      4. Invalid file
      5. Invalid schema
      6. Duplicate ride_id
      7. Kafka unavailable
      8. Spark processing error
      9. PostgreSQL unavailable
    Fallback: '<step> failed'
    """
    exc_type = type(exc).__name__
    exc_msg = str(exc)

    # 1. Internet unavailable
    if (
        isinstance(exc, (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout))
        or "Failed to establish a new connection" in exc_msg
        or "NameResolutionError" in exc_msg
        or "gaierror" in exc_msg
        or "Internet unavailable" in exc_msg
        or "Max retries exceeded" in exc_msg
        or "Network is unreachable" in exc_msg
    ):
        return "Internet unavailable"

    # 2. Source unavailable
    if (
        isinstance(exc, (requests.exceptions.HTTPError, requests.exceptions.Timeout, ET.ParseError))
        or "timed out" in exc_msg.lower()
        or "404" in exc_msg
        or "500" in exc_msg
        or "403" in exc_msg
        or "không có trên S3" in exc_msg
        or "Source unavailable" in exc_msg
    ):
        return "Source unavailable"

    # 3. Download failed
    if (
        "Tải file chưa hoàn tất" in exc_msg
        or "Download failed" in exc_msg
        or ("download" in exc_msg.lower() and isinstance(exc, (IOError, requests.RequestException)))
    ):
        return "Download failed"

    # 4. Invalid file
    if (
        isinstance(exc, (zipfile.BadZipFile, FileNotFoundError))
        or "BadZipFile" in exc_type
        or "File không tồn tại" in exc_msg
        or "EmptyDataError" in exc_type
        or "Invalid file" in exc_msg
    ):
        return "Invalid file"

    # 5. Invalid schema
    if (
        isinstance(exc, ValidationError)
        or "Schema không hợp lệ" in exc_msg
        or "Thiếu các cột bắt buộc" in exc_msg
        or "Invalid schema" in exc_msg
    ):
        return "Invalid schema"

    # 6. Duplicate ride_id
    if (
        "duplicate ride_id" in exc_msg.lower()
        or "trùng lặp ride_id" in exc_msg.lower()
        or "Duplicate ride_id" in exc_msg
        or ("trips_pkey" in exc_msg.lower() and "duplicate key" in exc_msg.lower())
        or ("unique constraint" in exc_msg.lower() and "ride_id" in exc_msg.lower())
    ):
        return "Duplicate ride_id"

    # 7. Kafka unavailable
    if (
        isinstance(exc, kafka.errors.KafkaError)
        or "NoBrokersAvailable" in exc_msg
        or "Kafka" in exc_type
        or "Kafka unavailable" in exc_msg
    ):
        return "Kafka unavailable"

    # 8. Spark processing error
    if (
        "Spark" in step
        or "Spark job" in exc_msg
        or (isinstance(exc, RuntimeError) and "Spark" in exc_msg)
        or "Spark processing error" in exc_msg
    ):
        return "Spark processing error"

    # 9. PostgreSQL unavailable
    if (
        isinstance(exc, psycopg2.OperationalError)
        or "could not connect to server" in exc_msg.lower()
        or "connection to server at" in exc_msg.lower()
        or "psycopg2" in exc_type
        or "PostgreSQL unavailable" in exc_msg
    ):
        return "PostgreSQL unavailable"

    # Fallback nếu không khớp chính xác 9 loại trên
    return f"{step} failed"


def get_db_snapshot() -> Dict[str, Any]:
    """Lấy snapshot số lượng bản ghi hiện tại trong PostgreSQL."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM trips;")
            trips_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*), COALESCE(SUM(demand), 0) FROM hourly_demand;")
            hd_row = cursor.fetchone()
            hourly_count = hd_row[0]
            total_demand = hd_row[1]

            return {
                "trips": trips_count,
                "hourly_demand": hourly_count,
                "total_demand": total_demand,
            }
    finally:
        conn.close()


def run_spark_job(script_name: str, step_name: str) -> None:
    """Thực thi Spark job qua docker exec trên citibike-spark-master."""
    spark_cmd = (
        f"docker exec citibike-spark-master "
        f"/opt/spark/bin/spark-submit "
        f"--master spark://spark-master:7077 "
        f"--conf spark.jars.ivy=/tmp/ivy-cache "
        f"--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.7,org.postgresql:postgresql:42.7.4 "
        f"/opt/spark-apps/{script_name}"
    )
    print(f"[PROCESS] Đang thực thi Spark job: {script_name}...")
    res = subprocess.run(
        spark_cmd,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print(res.stdout)
    if res.returncode != 0:
        err_msg = res.stderr.strip() if res.stderr else "Spark job trả về mã lỗi khác 0"
        raise RuntimeError(f"Spark processing error: {script_name} thất bại ({err_msg})")


def print_pipeline_summary(
    steps_status: Dict[str, str],
    baseline_db: Dict[str, Any],
    final_db: Dict[str, Any],
    elapsed_seconds: float,
    new_records_added: int,
) -> None:
    """In bảng tổng kết hoàn chỉnh của pipeline theo tag [SUMMARY]."""
    trips_delta = final_db["trips"] - baseline_db["trips"]
    hourly_delta = final_db["hourly_demand"] - baseline_db["hourly_demand"]
    demand_delta = final_db["total_demand"] - baseline_db["total_demand"]

    print("\n" + "=" * 75)
    print("CITI BIKE DATA PIPELINE — SUMMARY REPORT")
    print("=" * 75)
    print(f"{'Bước xử lý':<35} | {'Trạng thái':<20} | {'Ghi chú'}")
    print("-" * 75)
    for step, status in steps_status.items():
        print(f"{step:<35} | {status:<20} |")
    print("-" * 75)
    print("THỐNG KÊ CƠ SỞ DỮ LIỆU POSTGRESQL:")
    print(f"  - Trips tổng:            {final_db['trips']:,} (+{trips_delta:,})")
    print(f"  - Hourly Demand rows:    {final_db['hourly_demand']:,} (+{hourly_delta:,})")
    print(f"  - Tổng Demand tích lũy:  {final_db['total_demand']:,} (+{demand_delta:,})")
    print(f"  - Records mới nạp:       {new_records_added:,}")
    print(f"  - Tổng thời gian chạy:   {elapsed_seconds:.2f} giây")
    print("=" * 75)


def run_pipeline(
    specific_month: Optional[str] = None,
    limit: Optional[int] = 1,
    force: bool = False,
    debug: bool = False,
) -> int:
    """
    Điều phối toàn bộ quy trình cập nhật dữ liệu tự động.
    Chuẩn hóa theo 9 log tag và phân loại 9 nhóm lỗi.
    Trả về 0 nếu thành công, 1 nếu có lỗi.
    """
    start_time = time.time()
    steps_status: Dict[str, str] = {
        "1. Check source & Detect": "Chưa chạy",
        "2. Download raw data": "Chưa chạy",
        "3. Validate & Clean": "Chưa chạy",
        "4. Ingest to Kafka": "Chưa chạy",
        "5. Spark Aggregate Demand": "Chưa chạy",
        "6. Spark Trips Ingestion": "Chưa chạy",
    }

    print("=" * 75)
    print("[START] Automatic data update")
    print(f"Thời gian bắt đầu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)

    # Ghi nhận trạng thái DB ban đầu
    try:
        baseline_db = get_db_snapshot()
    except Exception as exc:
        err_cat = classify_error(exc, "PostgreSQL connection")
        print(f"[ERROR] {err_cat}: {exc}")
        if debug:
            import traceback
            traceback.print_exc()
        return 1

    print(f"[CHECK] Database hiện tại: {baseline_db['trips']:,} trips | {baseline_db['hourly_demand']:,} hourly rows")

    # ─────────────────────────────────────────────────────────────
    # BƯỚC 1: CHECK SOURCE & DETECT NEW DATA
    # ─────────────────────────────────────────────────────────────
    current_step = "Check source"
    print("\n[CHECK] Checking Citi Bike source")
    try:
        raw_dir = DEFAULT_RAW_DIR
        local_months = get_local_months(raw_dir=raw_dir)
        try:
            new_months_map = find_new_months(raw_dir=raw_dir, bucket_url=S3_BUCKET_URL)
        except Exception as net_exc:
            new_months_map = {}
            clean_m = specific_month.replace("-", "").strip() if specific_month else ""
            if not specific_month or clean_m not in local_months:
                raise net_exc
            print(f"[CHECK] Nguồn remote không phản hồi, tiếp tục kiểm tra từ local raw cho tháng {specific_month}.")

        target_months_to_process: Dict[str, str] = {}

        if specific_month:
            clean_m = specific_month.replace("-", "").strip()
            # Nếu chỉ định tháng cụ thể
            if clean_m in new_months_map:
                target_months_to_process[clean_m] = new_months_map[clean_m]
                print(f"[CHECK] New month detected: {clean_m[:4]}-{clean_m[4:]}")
            elif clean_m in local_months:
                # Tháng đã có tại local (kịch bản re-run)
                s3_key = f"JC-{clean_m}-citibike-tripdata.csv.zip"
                target_months_to_process[clean_m] = s3_key
                print(f"[CHECK] Tháng chỉ định {specific_month} đã tồn tại tại local raw. Sẽ kiểm tra quy trình re-run.")
            else:
                raise ValueError(f"Tháng {specific_month} không có trên S3 và cũng không có tại local.")
        else:
            # Tự động: Lấy các tháng mới nhất thực tế từ nguồn S3 thông qua find_new_months()
            if not new_months_map:
                print("[CHECK] No new data detected")
                steps_status["1. Check source & Detect"] = "SUCCESS (No new data)"
                for s in list(steps_status.keys())[1:]:
                    steps_status[s] = "SKIPPED (No new data)"
                print(f"\n[SUMMARY] New records: 0")
                print_pipeline_summary(steps_status, baseline_db, baseline_db, time.time() - start_time, 0)
                return 0

            # Giới hạn số tháng tải (mặc định limit=1 để xử lý từng tháng mới theo thứ tự)
            months_items = list(new_months_map.items())
            if limit and limit > 0:
                months_items = months_items[:limit]
            target_months_to_process = dict(months_items)

            for m in target_months_to_process:
                print(f"[CHECK] New month detected: {m[:4]}-{m[4:]}")

        steps_status["1. Check source & Detect"] = "SUCCESS"
    except Exception as exc:
        err_cat = classify_error(exc, current_step)
        print(f"[ERROR] {err_cat}: {exc}")
        if debug:
            import traceback
            traceback.print_exc()
        steps_status["1. Check source & Detect"] = f"FAILED ({err_cat})"
        print_pipeline_summary(steps_status, baseline_db, baseline_db, time.time() - start_time, 0)
        return 1

    # Duyệt qua từng tháng để thực thi các bước tiếp theo
    total_new_records = 0

    for month_id, s3_key in target_months_to_process.items():
        month_label = f"{month_id[:4]}-{month_id[4:]}"
        print(f"\n>>> XỬ LÝ CHU KỲ THÁNG {month_label} (Key: {s3_key}) <<<")

        # ─────────────────────────────────────────────────────────────
        # BƯỚC 2: DOWNLOAD RAW DATA
        # ─────────────────────────────────────────────────────────────
        current_step = "Download"
        print(f"\n[DOWNLOAD] Downloading {month_label}")
        try:
            raw_csv_path = download_and_extract_month(
                month_id=month_id,
                s3_key=s3_key,
                target_dir=raw_dir,
            )
            print(f"[SUCCESS] File thô đã sẵn sàng: {raw_csv_path.name}")
            steps_status["2. Download raw data"] = "SUCCESS"
        except Exception as exc:
            err_cat = classify_error(exc, current_step)
            print(f"[ERROR] {err_cat}: {exc}")
            if debug:
                import traceback
                traceback.print_exc()
            steps_status["2. Download raw data"] = f"FAILED ({err_cat})"
            print_pipeline_summary(steps_status, baseline_db, baseline_db, time.time() - start_time, 0)
            return 1

        # ─────────────────────────────────────────────────────────────
        # BƯỚC 3: VALIDATE & CLEAN
        # ─────────────────────────────────────────────────────────────
        current_step = "Validate"
        print(f"\n[VALIDATE] Validating dataset {raw_csv_path.name}...")
        clean_csv_path = PROJECT_ROOT / "data" / "processed" / f"JC-{month_id}-citibike-tripdata-clean.csv"
        try:
            df_clean, stats = validate_file(
                input_file=raw_csv_path,
                output_file=None,
                check_db_duplicates=True,
            )
            valid_rows = stats.get("valid_final_rows", len(df_clean))

            # Ghi nhận Duplicate ride_id nếu có
            dup_db_count = stats.get("db_duplicate_ride_id_dropped", 0)
            dup_file_count = stats.get("internal_duplicate_ride_id_dropped", 0)
            if dup_db_count > 0 or dup_file_count > 0:
                print(f"[CHECK] Duplicate ride_id: Đã phát hiện và deduplicate {dup_file_count:,} trùng nội bộ, {dup_db_count:,} trùng DB.")

            if valid_rows == 0:
                print(f"[VALIDATE] Dataset validation passed: 0 records new (all records already exist in DB).")
                steps_status["3. Validate & Clean"] = "SUCCESS (All exists in DB)"
                steps_status["4. Ingest to Kafka"] = "SKIPPED (Already in DB)"
                steps_status["5. Spark Aggregate Demand"] = "SKIPPED (Already in DB)"
                steps_status["6. Spark Trips Ingestion"] = "SKIPPED (Already in DB)"
                continue

            # Lưu file clean khi có dòng hợp lệ mới
            clean_csv_path.parent.mkdir(parents=True, exist_ok=True)
            df_to_save = df_clean.copy()
            df_to_save["started_at"] = df_to_save["started_at"].dt.strftime("%Y-%m-%d %H:%M:%S.%f").str[:-3]
            df_to_save["ended_at"] = df_to_save["ended_at"].dt.strftime("%Y-%m-%d %H:%M:%S.%f").str[:-3]
            df_to_save.to_csv(clean_csv_path, index=False)
            print(f"[SUCCESS] Đã lưu dữ liệu làm sạch vào: {clean_csv_path.name} ({len(df_to_save):,} dòng)")

            print("[VALIDATE] Dataset validation passed")
            steps_status["3. Validate & Clean"] = f"SUCCESS ({valid_rows:,} rows)"
        except Exception as exc:
            err_cat = classify_error(exc, current_step)
            print(f"[ERROR] {err_cat}: {exc}")
            if debug:
                import traceback
                traceback.print_exc()
            steps_status["3. Validate & Clean"] = f"FAILED ({err_cat})"
            print_pipeline_summary(steps_status, baseline_db, baseline_db, time.time() - start_time, 0)
            return 1

        # ─────────────────────────────────────────────────────────────
        # BƯỚC 4: INGEST TO KAFKA
        # ─────────────────────────────────────────────────────────────
        current_step = "Kafka Ingestion"
        print("\n[PROCESS] Sending records to Kafka")
        try:
            sent_count = send_dataset_to_kafka(
                dataset=clean_csv_path,
                check_db_duplicates=True,
                force=force,
            )
            print(f"[PROCESS] Đã gửi {sent_count:,} messages vào Kafka topic.")
            steps_status["4. Ingest to Kafka"] = f"SUCCESS ({sent_count:,} sent)"
        except Exception as exc:
            err_cat = classify_error(exc, current_step)
            print(f"[ERROR] {err_cat}: {exc}")
            if debug:
                import traceback
                traceback.print_exc()
            steps_status["4. Ingest to Kafka"] = f"FAILED ({err_cat})"
            print_pipeline_summary(steps_status, baseline_db, baseline_db, time.time() - start_time, 0)
            return 1

        # ─────────────────────────────────────────────────────────────
        # BƯỚC 5: SPARK AGGREGATE DEMAND & TRIPS INGESTION
        # ─────────────────────────────────────────────────────────────
        current_step = "Spark Processing"
        print(f"\n[PROCESS] Running Spark processing for {month_label}...")
        try:
            run_spark_job("aggregate_demand.py", "Spark Aggregate Demand")
            steps_status["5. Spark Aggregate Demand"] = "SUCCESS"

            run_spark_job("spark_streaming.py", "Spark Trips Ingestion")
            steps_status["6. Spark Trips Ingestion"] = "SUCCESS"

            print("[DATABASE] PostgreSQL updated")
        except Exception as exc:
            err_cat = classify_error(exc, current_step)
            print(f"[ERROR] {err_cat}: {exc}")
            if debug:
                import traceback
                traceback.print_exc()
            if "aggregate_demand" in str(exc):
                steps_status["5. Spark Aggregate Demand"] = f"FAILED ({err_cat})"
            else:
                steps_status["6. Spark Trips Ingestion"] = f"FAILED ({err_cat})"
            print_pipeline_summary(steps_status, baseline_db, baseline_db, time.time() - start_time, 0)
            return 1

        total_new_records += valid_rows

    # ─────────────────────────────────────────────────────────────
    # BƯỚC 6: SUMMARY REPORT & COMPLETION
    # ─────────────────────────────────────────────────────────────
    final_db = get_db_snapshot()
    elapsed = time.time() - start_time
    print("\n[SUCCESS] Automatic update completed")
    print(f"[SUMMARY] New records: {total_new_records}")
    print_pipeline_summary(steps_status, baseline_db, final_db, elapsed, total_new_records)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Citi Bike Automatic Update Pipeline (Task 9)")
    parser.add_argument(
        "--month",
        type=str,
        default=None,
        help="Chỉ định tháng cần cập nhật (ví dụ: YYYY-MM hoặc YYYYMM). Mặc định là tự động phát hiện tháng mới.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="Số lượng tháng tối đa xử lý trong một lần chạy (mặc định: 1).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bắt buộc gửi lại dữ liệu vào Kafka ngay cả khi đã gửi trước đó.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Hiển thị chi tiết traceback khi xảy ra lỗi để chẩn đoán sự cố.",
    )

    args = parser.parse_args()

    exit_code = run_pipeline(
        specific_month=args.month,
        limit=args.limit,
        force=args.force,
        debug=args.debug,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

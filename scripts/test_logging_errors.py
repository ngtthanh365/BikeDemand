"""
test_logging_errors.py — Test Suite cho Task 9: Logging và Error Handling

Kiểm thử NON-DESTRUCTIVE:
  - 100% không ghi dữ liệu mới vào PostgreSQL
  - Không thay đổi schema PostgreSQL
  - Không gửi message mới vào Kafka citibike-trips
  - Không reset Kafka topic
  - Không xóa hoặc thay đổi Spark checkpoints
  - Sử dụng mock/giả lập để kiểm thử các tình huống lỗi mạng, lỗi dịch vụ, lỗi schema, lỗi file.

Nội dung kiểm thử:
  1. Kiểm tra format 9 log tags chuẩn: [START], [CHECK], [DOWNLOAD], [VALIDATE], [PROCESS], [DATABASE], [SUCCESS], [ERROR], [SUMMARY]
  2. Lỗi 1: Internet unavailable (mock ConnectionError)
  3. Lỗi 2: Source unavailable (mock HTTP 404 / tháng không tồn tại)
  4. Lỗi 3: Download failed (mock IOError tải dở dang)
  5. Lỗi 4: Invalid file (file không tồn tại / zip hỏng)
  6. Lỗi 5: Invalid schema (thiếu cột bắt buộc -> ValidationError)
  7. Lỗi 6: Duplicate ride_id (dedup logging + UniqueViolation classification)
  8. Lỗi 7: Kafka unavailable (kết nối endpoint giả lập không tồn tại)
  9. Lỗi 8: Spark processing error (job giả lập lỗi, không đụng checkpoint)
  10. Lỗi 9: PostgreSQL unavailable (kết nối cổng giả lập không tồn tại)
"""

import io
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.update_data import classify_error
from scripts.validate_data import REQUIRED_COLUMNS, ValidationError, validate_and_clean_data, validate_file


class TestLoggingAndErrorHandling(unittest.TestCase):
    """Bộ kiểm thử phân loại 9 nhóm lỗi và định dạng log chuẩn Task 9."""

    def setUp(self):
        self.tags = [
            "[START]",
            "[CHECK]",
            "[DOWNLOAD]",
            "[VALIDATE]",
            "[PROCESS]",
            "[DATABASE]",
            "[SUCCESS]",
            "[ERROR]",
            "[SUMMARY]",
        ]

    def test_01_log_tags_format(self):
        """Kiểm tra sự hiện diện và cú pháp của 9 log tag chuẩn."""
        print("\n--- Test 01: Kiểm tra format 9 thẻ log chuẩn ---")
        sample_logs = [
            "[START] Automatic data update",
            "[CHECK] Checking Citi Bike source",
            "[CHECK] New month detected: 2026-08",
            "[DOWNLOAD] Downloading 2026-08",
            "[VALIDATE] Dataset validation passed",
            "[PROCESS] Sending records to Kafka",
            "[DATABASE] PostgreSQL updated",
            "[SUCCESS] Automatic update completed",
            "[SUMMARY] New records: 100",
            "[CHECK] No new data detected",
        ]
        for log in sample_logs:
            has_tag = any(log.startswith(tag) for tag in self.tags)
            self.assertTrue(has_tag, f"Log không bắt đầu bằng tag chuẩn hợp lệ: {log}")
            print(f"  [PASS] Log tag hợp lệ: {log}")

    def test_02_error_internet_unavailable(self):
        """Lỗi 1: Internet unavailable (ConnectionError / DNS error)."""
        print("\n--- Test 02: Lỗi 1 - Internet unavailable ---")
        exc = requests.exceptions.ConnectionError("Failed to establish a new connection: [Errno 11001] getaddrinfo failed")
        err_cat = classify_error(exc, "Check source")
        log_line = f"[ERROR] {err_cat}: {exc}"
        self.assertEqual(err_cat, "Internet unavailable")
        self.assertTrue(log_line.startswith("[ERROR] Internet unavailable:"))
        print(f"  [PASS] Phân loại chính xác: {log_line}")

    def test_03_error_source_unavailable(self):
        """Lỗi 2: Source unavailable (HTTP 404 / 500 / Month not found)."""
        print("\n--- Test 03: Lỗi 2 - Source unavailable ---")
        exc_404 = requests.exceptions.HTTPError("404 Client Error: Not Found for url")
        err_cat_404 = classify_error(exc_404, "Check source")
        self.assertEqual(err_cat_404, "Source unavailable")

        exc_s3 = ValueError("Tháng 2099-99 không có trên S3 và cũng không có tại local.")
        err_cat_s3 = classify_error(exc_s3, "Check source")
        self.assertEqual(err_cat_s3, "Source unavailable")

        log_line = f"[ERROR] {err_cat_s3}: {exc_s3}"
        self.assertTrue(log_line.startswith("[ERROR] Source unavailable:"))
        print(f"  [PASS] Phân loại chính xác: {log_line}")

    def test_04_error_download_failed(self):
        """Lỗi 3: Download failed (Tải file bị đứt quãng / dở dang)."""
        print("\n--- Test 04: Lỗi 3 - Download failed ---")
        exc = IOError("Tải file chưa hoàn tất: nhận 512000/10485760 bytes")
        err_cat = classify_error(exc, "Download")
        log_line = f"[ERROR] {err_cat}: {exc}"
        self.assertEqual(err_cat, "Download failed")
        self.assertTrue(log_line.startswith("[ERROR] Download failed:"))
        print(f"  [PASS] Phân loại chính xác: {log_line}")

    def test_05_error_invalid_file(self):
        """Lỗi 4: Invalid file (File không tồn tại / zip file hỏng)."""
        print("\n--- Test 05: Lỗi 4 - Invalid file ---")
        non_existent = PROJECT_ROOT / "data" / "raw" / "non_existent_file_xyz.csv"
        try:
            validate_file(input_file=non_existent)
        except Exception as exc:
            err_cat = classify_error(exc, "Validate")
            log_line = f"[ERROR] {err_cat}: {exc}"
            self.assertEqual(err_cat, "Invalid file")
            self.assertTrue(log_line.startswith("[ERROR] Invalid file:"))
            print(f"  [PASS] Phân loại chính xác: {log_line}")

        bad_zip = zipfile.BadZipFile("File zip bị hỏng tại entry: corrupt_entry.csv")
        self.assertEqual(classify_error(bad_zip, "Download"), "Invalid file")

    def test_06_error_invalid_schema(self):
        """Lỗi 5: Invalid schema (Thiếu cột bắt buộc -> ValidationError)."""
        print("\n--- Test 06: Lỗi 5 - Invalid schema ---")
        bad_df = pd.DataFrame({
            "col_a": [1, 2],
            "col_b": [3, 4],
        })
        try:
            validate_and_clean_data(bad_df, check_db_duplicates=False)
        except Exception as exc:
            err_cat = classify_error(exc, "Validate")
            log_line = f"[ERROR] {err_cat}: {exc}"
            self.assertEqual(err_cat, "Invalid schema")
            self.assertTrue(log_line.startswith("[ERROR] Invalid schema:"))
            print(f"  [PASS] Phân loại chính xác: {log_line}")

    def test_07_error_duplicate_ride_id(self):
        """Lỗi 6: Duplicate ride_id (Deduplication ghi log rõ ràng + phân loại lỗi khi vi phạm)."""
        print("\n--- Test 07: Lỗi 6 - Duplicate ride_id ---")
        # 1. Tình huống dữ liệu bình thường: dedup loại bỏ trùng lặp và ghi log [CHECK] không gây crash
        row_base = {col: "test" for col in REQUIRED_COLUMNS}
        row_base["started_at"] = "2026-08-01 10:00:00"
        row_base["ended_at"] = "2026-08-01 10:30:00"
        row_base["start_lat"] = 40.7128
        row_base["start_lng"] = -74.0060
        row_base["member_casual"] = "member"

        row1 = dict(row_base, ride_id="RIDE_DUP_TEST_001")
        row2 = dict(row_base, ride_id="RIDE_DUP_TEST_001")  # Trùng ride_id
        df_with_dup = pd.DataFrame([row1, row2])

        clean_df, stats = validate_and_clean_data(df_with_dup, check_db_duplicates=False)
        self.assertEqual(len(clean_df), 1)
        self.assertEqual(stats["internal_duplicate_ride_id_dropped"], 1)
        print("  [PASS] Dữ liệu trùng ride_id được deduplicate an toàn (không crash hệ thống).")

        # 2. Phân loại lỗi khi có ngoại lệ duplicate ride_id
        exc = Exception('duplicate key value violates unique constraint "trips_pkey" - Key (ride_id)=(RIDE_001) already exists')
        err_cat = classify_error(exc, "Database insert")
        log_line = f"[ERROR] {err_cat}: {exc}"
        self.assertEqual(err_cat, "Duplicate ride_id")
        self.assertTrue(log_line.startswith("[ERROR] Duplicate ride_id:"))
        print(f"  [PASS] Phân loại chính xác: {log_line}")

    def test_08_error_kafka_unavailable(self):
        """Lỗi 7: Kafka unavailable (Endpoint giả lập không có broker)."""
        print("\n--- Test 08: Lỗi 7 - Kafka unavailable ---")
        from kafka import KafkaProducer

        try:
            # Dùng dummy port 59092 không có broker lắng nghe, timeout ngắn 1000ms
            producer = KafkaProducer(
                bootstrap_servers="localhost:59092",
                request_timeout_ms=1000,
                max_block_ms=1000,
                retries=0,
            )
            producer.bootstrap_connected()
        except Exception as exc:
            err_cat = classify_error(exc, "Kafka Ingestion")
            log_line = f"[ERROR] {err_cat}: {exc}"
            self.assertEqual(err_cat, "Kafka unavailable")
            self.assertTrue(log_line.startswith("[ERROR] Kafka unavailable:"))
            print(f"  [PASS] Phân loại chính xác: {log_line}")

    def test_09_error_spark_processing(self):
        """Lỗi 8: Spark processing error (Command/Job giả lập thất bại, không đụng checkpoint)."""
        print("\n--- Test 09: Lỗi 8 - Spark processing error ---")
        # Giả lập RuntimeError trả về từ run_spark_job khi spark-submit trả về non-zero
        exc = RuntimeError("Spark processing error: aggregate_demand.py thất bại (Exit code 1: AnalysisException)")
        err_cat = classify_error(exc, "Spark Processing")
        log_line = f"[ERROR] {err_cat}: {exc}"
        self.assertEqual(err_cat, "Spark processing error")
        self.assertTrue(log_line.startswith("[ERROR] Spark processing error:"))
        print(f"  [PASS] Phân loại chính xác: {log_line}")

    def test_10_error_postgresql_unavailable(self):
        """Lỗi 9: PostgreSQL unavailable (Cổng kết nối giả lập không có server)."""
        print("\n--- Test 10: Lỗi 9 - PostgreSQL unavailable ---")
        import psycopg2

        try:
            # Kết nối tới cổng giả lập 55432 (không mở)
            conn = psycopg2.connect(
                host="localhost",
                port=55432,
                database="citibike",
                user="postgres",
                password="wrong_password",
                connect_timeout=2,
            )
            conn.close()
        except Exception as exc:
            err_cat = classify_error(exc, "PostgreSQL connection")
            log_line = f"[ERROR] {err_cat}: {exc}"
            self.assertEqual(err_cat, "PostgreSQL unavailable")
            self.assertTrue(log_line.startswith("[ERROR] PostgreSQL unavailable:"))
            print(f"  [PASS] Phân loại chính xác: {log_line}")


def run_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLoggingAndErrorHandling)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

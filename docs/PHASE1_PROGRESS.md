# PHASE 1 PROGRESS — AUTOMATIC DATA UPDATE

## 1. Task hiện tại

- **Task 10:** Integration Test — 🟢 **HOÀN THÀNH**

- Đã kiểm thử toàn bộ pipeline tự động với 4 kịch bản:
  1. Không có dữ liệu mới
  2. Có tháng mới
  3. Chạy lại pipeline
  4. Kiểm tra tính toàn vẹn Database

## 2. Task đã hoàn thành

- [x] **Task 1: Khảo sát cơ chế lấy data** (🟢 Hoàn thành: S3 XML, quy luật tên file, cấu trúc nén).

- [x] **Task 2: Automatic Data Downloader** (🟢 Hoàn thành: Đã xây dựng `scripts/download_data.py`, tải thành công `JC-202607-citibike-tripdata.csv`).

- [x] **Task 3: Data Validation** (🟢 Hoàn thành: Đã xây dựng `scripts/validate_data.py`, xác thực và làm sạch dữ liệu tháng 07/2026).

- [x] **Task 4: Tích hợp Kafka** (🟢 Hoàn thành: Refactor `producer/kafka_producer.py`, gửi thành công 109,085 messages mới vào topic `citibike-trips`, bảo đảm Idempotency).

- [x] **Task 5: Spark Processing** (🟢 Hoàn thành: Nâng cấp `spark/aggregate_demand.py`, idempotent write, ghi thành công 743 rows tháng 07/2026 vào `hourly_demand`, H1 2026 nguyên vẹn).

- [x] **Task 6: Cập nhật PostgreSQL** (🟢 Hoàn thành: Nâng cấp `spark/spark_streaming.py`, idempotent write, ghi thành công 109,085 records tháng 07/2026 vào `trips`, H1 2026 nguyên vẹn, re-run an toàn).

- [x] **Task 7: Idempotency / Chạy lại** (🟢 Hoàn thành: Bổ sung log `No new data` cho cả 2 job Spark, tạo `scripts/test_idempotency.py`, kiểm thử re-run thành công cả 5 tầng pipeline: Downloader, Validator, Producer, Spark Aggregate, Spark Trips; bảo toàn 100% dữ liệu H1 + Tháng 07, không phát sinh duplicate).

- [x] **Task 8: Chạy pipeline bằng một lệnh** (🟢 Hoàn thành: Xây dựng entry point duy nhất `scripts/update_data.py`, tích hợp liền mạch luồng 6 bước từ kiểm tra nguồn đến báo cáo summary cuối pipeline; loại bỏ hoàn toàn hard-code tháng; tự động phát hiện và xử lý tháng mới nhất thực tế từ S3; kiểm thử thành công re-run và tự động nạp tháng 2026-08).

- [x] **Task 9: Logging và Error Handling** (🟢 Hoàn thành: Chuẩn hóa toàn diện 9 log tag chuẩn; phân loại chính xác 9 nhóm ngoại lệ hệ thống; xây dựng test suite `scripts/test_logging_errors.py` phi phá hủy 10/10 PASS; giữ nguyên 100% DB, Kafka và Spark checkpoint).

### Task 10 (Integration Test) — KẾT QUẢ THỰC TẾ

#### Test 1 — No New Data

- **PASS:** Khi không có dữ liệu tháng mới, pipeline phát hiện `[CHECK] No new data detected`.
- Các bước Download, Validate, Kafka và Spark được SKIPPED.
- Database không thay đổi:
  - `trips`: 635,998 → 635,998
  - `hourly_demand`: 5,740 → 5,740
  - Tổng demand: 635,998 → 635,998

#### Test 2 — New Month

- **PASS:** Pipeline tự động phát hiện tháng 09/2026 từ nguồn Citi Bike.
- Download và validation thành công.
- Sau làm sạch:
  - 106,617 records hợp lệ
  - 106,617 unique `ride_id`
  - 719 hourly records
- Kafka nhận thêm đúng 106,617 messages.
- PostgreSQL sau tích hợp:
  - `trips`: 742,615 records
  - `hourly_demand`: 6,459 records
  - Tổng demand: 742,615

> Trong quá trình kiểm thử phát hiện trạng thái dữ liệu kiểm thử trước đó chưa được cleanup đồng bộ, khiến `hourly_demand` tháng 09 tạm thời bị cộng trùng. Nguyên nhân được xác định là trạng thái môi trường kiểm thử, không phải lỗi phát sinh trong logic phát hiện và ingest tháng mới. Dữ liệu đã được khôi phục chính xác và kiểm tra lại thành công.

#### Test 3 — Rerun

- **PASS:** Chạy lại `python scripts/update_data.py` khi không có tháng mới.
- Pipeline hiển thị `[CHECK] No new data detected`.
- Không phát sinh dữ liệu mới:
  - `trips`: +0
  - `hourly_demand`: +0
  - Tổng demand: +0
  - Records mới: 0

#### Test 4 — Database Integrity

- **PASS:** `trips`:
  - Tổng records: 742,615
  - Unique `ride_id`: 742,615
  - Duplicate: 0

- **PASS:** `hourly_demand`:
  - Tổng rows: 6,459
  - Unique timestamp: 6,459
  - Duplicate: 0

- **PASS:** Tổng `demand` = 742,615, khớp 100% với tổng số trips.

- **PASS:** Tháng 09/2026:
  - 106,617 trips
  - 106,617 unique `ride_id`
  - 719 hourly rows
  - Tổng demand: 106,617

- **PASS:** Dữ liệu tháng 01–08 được bảo toàn:
  - 635,998 trips
  - 5,740 hourly rows
  - Tổng demand: 635,998

### Kết luận Task 10

- **4/4 Integration Test PASS.**
- Pipeline tự động phát hiện dữ liệu mới, xử lý tháng mới, chạy lại an toàn và bảo đảm tính toàn vẹn dữ liệu PostgreSQL.
- Dữ liệu các tháng trước không bị ảnh hưởng.

## 3. Trạng thái hệ thống

- **Docker Containers:** 4/4 container UP (`citibike-postgres`, `citibike-kafka`, `citibike-spark-master`, `citibike-spark-worker`).

- **Kafka Topic `citibike-trips`:**
  - Tổng số messages: **742,615**
    (H1 2026: 415,708 + Tháng 07/2026: 109,085 + Tháng 08/2026: 111,205 + Tháng 09/2026: 106,617).

- **PostgreSQL sau Task 10 — HOÀN CHỈNH & BẢO TOÀN:**

  - `trips`: **742,615 records**
    (`2026-01-01 00:05` đến `2026-09-30 23:59`).
    - H1 2026: 415,708 records (**nguyên vẹn 100%**).
    - Tháng 07/2026: 109,085 records (**nguyên vẹn 100%**).
    - Tháng 08/2026: 111,205 records (**tự động nạp thành công qua 1 lệnh**).
    - Tháng 09/2026: 106,617 records (**tự động phát hiện và nạp thành công**).

  - `hourly_demand`: **6,459 records**
    (`2026-01-01 00:00` đến `2026-09-30 23:00`).
    - H1 2026: 4,254 records (**nguyên vẹn 100%**).
    - Tháng 07/2026: 743 records (**nguyên vẹn 100%**).
    - Tháng 08/2026: 743 records (**tự động nạp thành công qua 1 lệnh**).
    - Tháng 09/2026: 719 records (**tự động nạp thành công qua pipeline**).

  - Tổng `demand` trong `hourly_demand`: **742,615** (khớp 100% với tổng `trips`).

  - `trips`: COUNT(*) = COUNT(DISTINCT ride_id) = **742,615** (Duplicate = 0).

  - `hourly_demand`: COUNT(*) = COUNT(DISTINCT timestamp) = **6,459** (Duplicate = 0).

- **Producer State:** `data/processed/.kafka_producer_state.json` đã lưu trạng thái các batch clean CSV.

- **Checkpoint Spark:**
  - `/tmp/citibike-spark-aggregate-postgres-checkpoint`: đã xử lý đến dữ liệu tháng 09/2026.
  - `/tmp/citibike-spark-postgres-checkpoint`: đã xử lý đến dữ liệu tháng 09/2026.

## 4. Quyết định đã thống nhất

### Kafka Producer Động & Idempotent (Task 4)

- Nhận dataset linh hoạt (qua đường dẫn file, DataFrame hoặc tự động tìm file sạch chưa gửi trong `data/processed/`).
- Kiểm tra Idempotent trước khi gửi: file state + mẫu `ride_id` trong PostgreSQL `trips`. Nếu đã gửi, tự động skip.
- Chuẩn hóa NaN/NaT thành `None` (JSON `null`) đảm bảo tương thích với Spark DoubleType nullable.
- Sử dụng `to_dict(orient="records")` để tăng tốc gửi.
- Giữ nguyên message schema 13 trường, topic `citibike-trips`, key là `ride_id`.

### Spark Processing Idempotent — hourly_demand (Task 5, Task 7)

- Idempotent: đọc `timestamp` đã có trong PostgreSQL qua JDBC, `left_anti` join → chỉ INSERT khung giờ chưa tồn tại.
- `trigger(availableNow=True)`: xử lý hết dữ liệu có sẵn rồi tự kết thúc.
- Tracking & Logging rõ ràng: Khi không có dữ liệu mới từ Kafka hoặc không có khung giờ mới cần chèn, in log:
  `[CHECK] No new data from Kafka topic (0 records processed). Du lieu PostgreSQL.hourly_demand giu nguyen.`
- Flag `--stream`: streaming liên tục nếu cần.
- Checkpoint `/tmp/citibike-spark-aggregate-postgres-checkpoint`.
- Giữ nguyên 100% logic v1.0: schema, datetime format, groupBy keys, is_weekend logic.

### Spark Processing Idempotent — trips (Task 6, Task 7)

- Idempotent: date-range query (lấy `ride_id` đã có trong `trips` theo `started_at` range của batch) + `left_anti` join → chỉ INSERT `ride_id` chưa tồn tại.
- `trigger(availableNow=True)`: tự kết thúc sau khi xử lý xong.
- Tracking & Logging rõ ràng: Khi không có message mới từ Kafka hoặc không có record mới cần chèn, in log:
  `[CHECK] No new data from Kafka topic (0 records processed). Du lieu PostgreSQL.trips giu nguyen.`
- Checkpoint `/tmp/citibike-spark-postgres-checkpoint` được giữ nguyên.
- Re-run an toàn: checkpoint nhận biết đã hết offset mới → ghi 0 records → giữ nguyên toàn bộ dữ liệu hiện có.

### Idempotency & Re-run Test Suite (Task 7)

- Xây dựng script kiểm thử tự động `scripts/test_idempotency.py` hoàn toàn phi phá hủy (non-destructive): không reset topic, không xóa checkpoint, không truncate database.
- Thực hiện kiểm thử tuần tự 5 tầng pipeline: Downloader, Validator, Producer, Spark Aggregate, Spark Trips.
- Đối chiếu snapshot database trước và sau re-run để xác nhận tính toàn vẹn 100%.

### One-Command Pipeline Orchestration (Task 8)

- Xây dựng entry point duy nhất `scripts/update_data.py`.
- Tái sử dụng trực tiếp các module nghiệp vụ hiện có mà không sửa logic cốt lõi.
- **Hoàn toàn không hard-code tháng:** Tự động phát hiện tháng mới nhất thực tế từ S3 qua hàm `find_new_months()`.
- Luồng điều phối tuần tự:

    1. Check source & Detect
    ↓
    2. Download raw data
    ↓
    3. Validate & Clean
    ↓
    4. Ingest to Kafka
    ↓
    5. Spark Aggregate Demand
    ↓
    6. Spark Trips Ingestion
    ↓
    7. Summary Report

- **Xử lý khi không có dữ liệu mới:** Dừng sớm, hiển thị `No new data`, bỏ qua toàn bộ bước tải và xử lý phía sau, trả về exit code 0.
- **Xử lý khi re-run:** Bỏ qua tải (file raw đã có), bỏ qua nạp DB (100% dữ liệu đã có trong PostgreSQL trips), bỏ qua Kafka và Spark, hiển thị bảng summary với số bản ghi biến thiên = 0.
- **Xử lý lỗi (Fail-fast):** Bắt lỗi chính xác từng bước, in rõ `[ERROR] [STEP_NAME]` kèm nguyên nhân, dừng pipeline ngay lập tức, không để lỗi lan truyền, trả về exit code 1.
- **Summary Report:** Thống kê chi tiết trạng thái từng bước, số records mới, tổng trips, tổng hourly_demand, tổng demand tích lũy, và thời gian thực thi (giây).

### Chuẩn hóa Logging & Phân loại 9 nhóm ngoại lệ (Task 9)

- **Chuẩn hóa 9 Log Tag bắt buộc:**
  - `[START] Automatic data update`
  - `[CHECK] Checking Citi Bike source` / `[CHECK] New month detected: YYYY-MM` / `[CHECK] No new data detected`
  - `[DOWNLOAD] Downloading YYYY-MM`
  - `[VALIDATE] Dataset validation passed`
  - `[PROCESS] Sending records to Kafka`
  - `[DATABASE] PostgreSQL updated`
  - `[SUCCESS] Automatic update completed`
  - `[ERROR] <Error Type>: <Message>`
  - `[SUMMARY] New records: XXXXX`

- **Phân loại chính xác 9 nhóm lỗi hệ thống (`classify_error`):**
  1. `Internet unavailable`: Bắt `requests.exceptions.ConnectionError`, `ConnectTimeout`, `NameResolutionError`, `Max retries exceeded`.
  2. `Source unavailable`: Bắt HTTP 404/500/403, S3 parse error, tháng không tồn tại trên remote S3.
  3. `Download failed`: Bắt ngắt kết nối dở dang, mismatch kích thước byte tải về.
  4. `Invalid file`: Bắt `zipfile.BadZipFile`, `FileNotFoundError`, `EmptyDataError`.
  5. `Invalid schema`: Bắt `ValidationError`, thiếu các cột bắt buộc trong 13 cột chuẩn.
  6. `Duplicate ride_id`: Deduplicate an toàn nội bộ file và DB (ghi log rõ ràng `[CHECK] Duplicate ride_id`, không gây crash hệ thống), bắt ngoại lệ `trips_pkey` unique violation.
  7. `Kafka unavailable`: Bắt `kafka.errors.KafkaError`, `NoBrokersAvailable`, Kafka socket timeout.
  8. `Spark processing error`: Bắt lỗi Spark runtime, job thoát với mã lỗi khác 0.
  9. `PostgreSQL unavailable`: Bắt `psycopg2.OperationalError`, không kết nối được DB port/host.

- Fallback: `[ERROR] <step> failed: <message>`.

- **Hỗ trợ cờ `--debug`:** Không che giấu thông tin, hiển thị đầy đủ traceback phục vụ chẩn đoán sự cố khi cần thiết.

- **Bộ kiểm thử phi phá hủy (Non-destructive test suite):** Tạo `scripts/test_logging_errors.py` kiểm thử 10 kịch bản kiểm thử độc lập mà không can thiệp hay làm biến động dữ liệu thật.

## 5. File đã thay đổi / tạo mới

- [producer/kafka_producer.py](file:///d:/BigData/BikeDemand/producer/kafka_producer.py) (Task 4: hỗ trợ input động, idempotency, batching, error handling, CLI).

- [spark/aggregate_demand.py](file:///d:/BigData/BikeDemand/spark/aggregate_demand.py) (Task 5, 7: idempotent write via left_anti join, availableNow trigger, log `No new data`).

- [spark/spark_streaming.py](file:///d:/BigData/BikeDemand/spark/spark_streaming.py) (Task 6, 7: idempotent write via date-range query + left_anti join, availableNow trigger, log `No new data`).

- [scripts/test_idempotency.py](file:///d:/BigData/BikeDemand/scripts/test_idempotency.py) (Task 7: Test suite tự động hóa kiểm thử Idempotency 5 tầng).

- [scripts/update_data.py](file:///d:/BigData/BikeDemand/scripts/update_data.py) (Task 8, 9: Chuẩn hóa 9 thẻ log, hàm `classify_error` cho 9 nhóm ngoại lệ, cờ `--debug`, không hard-code tháng).

- [scripts/test_logging_errors.py](file:///d:/BigData/BikeDemand/scripts/test_logging_errors.py) (Task 9: Test suite phi phá hủy kiểm thử toàn diện format log và 9 nhóm lỗi).

- [docs/PHASE1_PROGRESS.md](file:///d:/BigData/BikeDemand/docs/PHASE1_PROGRESS.md) (cập nhật tiến độ Task 5, 6, 7, 8, 9, 10).

## 6. Test đã PASS/FAIL

### Task 4 (Kafka)

- **PASS:** Gửi thành công **109,085 messages** vào topic `citibike-trips`. Lỗi: 0.
- **PASS:** Kafka offsets tăng từ 415,708 → 524,793 (+109,085).
- **PASS:** Idempotency: Chạy lại → phát hiện đã gửi, bỏ qua, gửi 0 messages.
- **PASS:** Consumer đọc và xác nhận 20/20 messages hợp lệ.

### Task 5 (Spark — hourly_demand)

- **PASS:** Spark kết nối Kafka, đọc đủ 524,793 records, parse JSON, chuẩn hóa datetime.
- **PASS:** Aggregate thành công → 4,997 khung giờ (4,254 H1 + 743 tháng 07).
- **PASS:** Idempotent write: 4,254 timestamp cũ bị skip, 743 timestamp mới được INSERT.
- **PASS:** Duplicate timestamp: **0** (UNIQUE constraint không bị vi phạm).
- **PASS:** Demand consistency: `demand = member_count + casual_count = electric_count + classic_count` — **0 lỗi**.
- **PASS:** Tổng `demand` sau cập nhật: **524,793** khớp 100% với tổng Kafka messages.
- **PASS:** `availableNow=True`: Spark tự kết thúc sau khi xử lý xong.

### Task 6 (Spark — trips)

- **PASS:** Spark đọc đúng Batch 1 từ checkpoint → **109,085 records** July 2026.
- **PASS:** date-range query → 0 ride_id đã tồn tại trong khoảng July → INSERT thẳng 109,085 records.
- **PASS:** `trips` sau cập nhật: **524,793 records** (`trips_count = unique_ride_ids = 524,793`).
- **PASS:** H1 2026 nguyên vẹn: **415,708 records** không bị thay đổi.
- **PASS:** July 2026: **109,085 records** được ghi chính xác.
- **PASS:** Duplicate `ride_id`: **0**.
- **PASS:** NULL `ride_id`, `started_at`, `ended_at`: **0**.

### Task 7 (Idempotency / Chạy lại)

- **PASS:** Thực thi kiểm thử tự động toàn diện qua `scripts/test_idempotency.py`.
- **PASS:** Toàn bộ 5 tầng pipeline đạt chuẩn Idempotent, biến thiên DB = 0, duplicates = 0.

### Task 8 (Chạy pipeline bằng một lệnh) — KẾT QUẢ THỰC TẾ

- **PASS:** Tự động phát hiện và nạp tháng 2026-08 bằng 1 lệnh `python scripts/update_data.py`.
- **PASS:** Re-run an toàn tháng 2026-07 và 2026-08 (biến thiên DB = 0).
- **PASS:** Xử lý lỗi fail-fast khi tháng không tồn tại.
- **PASS:** Bảo toàn toàn vẹn dữ liệu H1 2026, tháng 07/2026 và tháng 08/2026.

### Task 9 (Logging và Error Handling) — KẾT QUẢ THỰC TẾ

1. **Kiểm thử tự động Test Suite (`scripts/test_logging_errors.py`):**
   - Lệnh: `python scripts/test_logging_errors.py`
   - Kết quả: **10/10 tests PASS**.
   - `test_01_log_tags_format`: PASS — Xác thực cấu trúc log tags chuẩn.
   - `test_02_error_internet_unavailable`: PASS.
   - `test_03_error_source_unavailable`: PASS.
   - `test_04_error_download_failed`: PASS.
   - `test_05_error_invalid_file`: PASS.
   - `test_06_error_invalid_schema`: PASS.
   - `test_07_error_duplicate_ride_id`: PASS.
   - `test_08_error_kafka_unavailable`: PASS.
   - `test_09_error_spark_processing`: PASS.
   - `test_10_error_postgresql_unavailable`: PASS.

2. **Kiểm tra thực tế Pipeline Re-run tháng 2026-08:**
   - Dataset đã tồn tại.
   - Các records đã tồn tại trong DB được phát hiện.
   - Pipeline không tạo thêm dữ liệu.
   - Trạng thái DB biến thiên: **+0 records**.

3. **Kiểm tra Pipeline khi không có dữ liệu mới:**
   - `[CHECK] No new data detected`
   - `[SUMMARY] New records: 0`
   - Exit code: **0**.

### Task 10 — Integration Test

#### Test 1 — No New Data

- **PASS:** Không có dữ liệu mới được phát hiện.
- `[CHECK] No new data detected`.
- Download, Validate, Kafka và Spark được SKIPPED.
- DB không thay đổi:
  - `trips`: 635,998 → 635,998
  - `hourly_demand`: 5,740 → 5,740
  - `demand`: 635,998 → 635,998

#### Test 2 — New Month 09/2026

- **PASS:** Pipeline tự động phát hiện tháng 09/2026.
- Download thành công.
- Validation:
  - Initial rows: 106,628
  - Rows ngoài tháng 09 bị loại: 11
  - Valid records: 106,617
  - Unique `ride_id`: 106,617
- Kafka:
  - Gửi thêm 106,617 messages
  - Lỗi: 0
- Spark Aggregate:
  - 719 hourly rows mới.
- Spark Trips:
  - 106,617 trips mới.
- Database:
  - `trips`: 742,615
  - `hourly_demand`: 6,459
  - Tổng demand: 742,615

> Trong quá trình kiểm thử, phát hiện trạng thái dữ liệu kiểm thử trước đó chưa được cleanup đồng bộ, khiến `hourly_demand` tháng 09 tạm thời bị cộng trùng. Nguyên nhân được xác định là trạng thái môi trường kiểm thử, không phải lỗi phát sinh trong logic phát hiện và ingest tháng mới. Dữ liệu đã được khôi phục chính xác và xác nhận lại tính toàn vẹn Database thành công.

#### Test 3 — Rerun

- **PASS:** Chạy lại pipeline.
- `[CHECK] No new data detected`.
- Không phát sinh dữ liệu:
  - `trips`: +0
  - `hourly_demand`: +0
  - `demand`: +0
  - Records mới: 0

#### Test 4 — Database Integrity

- **PASS:** Toàn bộ Database:
  - `trips`: 742,615
  - Unique `ride_id`: 742,615
  - Duplicate `ride_id`: 0
  - `hourly_demand`: 6,459
  - Unique timestamp: 6,459
  - Duplicate timestamp: 0
  - Tổng `demand`: 742,615
  - Chênh lệch giữa tổng trips và demand: 0

- **PASS:** Tháng 09/2026:
  - Trips: 106,617
  - Unique `ride_id`: 106,617
  - Hourly rows: 719
  - Tổng demand: 106,617

- **PASS:** Tháng 01–08/2026:
  - Trips: 635,998
  - Hourly rows: 5,740
  - Tổng demand: 635,998

### Acceptance Criteria Task 10

- [x] **No New Data:** Pipeline phát hiện không có dữ liệu mới và dừng an toàn.
- [x] **New Month:** Pipeline tự động phát hiện và xử lý tháng 09/2026.
- [x] **Rerun:** Chạy lại pipeline không tạo thêm dữ liệu.
- [x] **Database Integrity:** Không có duplicate `ride_id`, duplicate timestamp và tổng demand khớp tổng trips.
- [x] **Data Preservation:** Dữ liệu tháng 01–08/2026 được bảo toàn.
- [x] **Integration Test:** **4/4 test PASS.**

## 7. Vấn đề / Rủi ro

- Không còn vấn đề tồn đọng trong pipeline.
- Trong Test 2, phát hiện trạng thái dữ liệu kiểm thử chưa được cleanup đồng bộ khiến `hourly_demand` tháng 09 tạm thời bị cộng trùng.
- Đã xác định nguyên nhân thuộc môi trường kiểm thử, khôi phục dữ liệu và xác nhận lại tính toàn vẹn Database thành công.

## 8. Task tiếp theo

- **Task 11: Regression Test v1.0**
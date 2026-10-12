# TASK_PHASE1.md
# BIKEDEMAND v2.0 — PHASE 1: AUTOMATIC DATA UPDATE

> **Mục đích:** Tài liệu triển khai chính thức cho Phase 1 của BikeDemand v2.0.
>
> **Nguyên tắc:** Chỉ triển khai Automatic Data Update. Không triển khai Future Forecast 24 giờ và Station Map trong Phase 1.

---

# 1. THÔNG TIN TASK

| Thông tin | Nội dung |
|---|---|
| Project | BikeDemand |
| Phase | Phase 1 |
| Tên task | Automatic Data Update |
| Mục tiêu | Tự động phát hiện, tải và tích hợp dữ liệu Citi Bike mới |
| Trạng thái | ⬜ Chưa làm |
| Phiên bản mục tiêu | v2.0 |
| Hệ thống hiện tại | v1.0 đã hoàn thành |
| Dataset baseline | Citi Bike H1 2026 |
| Database | PostgreSQL |
| Message broker | Apache Kafka |
| Processing | Apache Spark |
| Dashboard | Streamlit |

---

# 2. BỐI CẢNH

BikeDemand v1.0 đã có pipeline:

```text
Citi Bike Dataset
       ↓
     Kafka
       ↓
     Spark
       ↓
  PostgreSQL
       ↓
 Analysis + ML
       ↓
   Dashboard
```

Dataset hiện tại là Citi Bike Trip Data H1 2026. Phase 1 mở rộng pipeline để có thể tiếp nhận dữ liệu tháng mới mà không phải sửa code thủ công cho từng tháng.

---

# 3. MỤC TIÊU PHASE 1

1. Tự động kiểm tra dữ liệu Citi Bike mới.
2. Tự động tải dữ liệu mới khi phát hiện tháng mới.
3. Không tải lại dữ liệu đã tồn tại.
4. Không tạo duplicate `ride_id`.
5. Tích hợp dữ liệu mới vào pipeline hiện tại.
6. Cập nhật PostgreSQL.
7. Cập nhật `hourly_demand`.
8. Giữ nguyên dữ liệu lịch sử.
9. Có log rõ ràng.
10. Có thể chạy lại an toàn.

---

# 4. PHẠM VI

## 4.1 IN-SCOPE

```text
Citi Bike System Data
        ↓
Phát hiện dữ liệu mới
        ↓
Download dữ liệu
        ↓
Validate dữ liệu
        ↓
Kafka Producer
        ↓
Kafka
        ↓
Spark
        ↓
PostgreSQL
        ↓
hourly_demand
```

Có thể bổ sung các thành phần nhỏ cần thiết để lưu trạng thái tháng đã tải, kiểm tra duplicate, retry download, logging và chạy pipeline bằng một lệnh.

## 4.2 OUT-OF-SCOPE

Không thực hiện trong Phase 1:

- Future Forecast 24 giờ.
- Recursive Forecasting.
- Retrain model.
- So sánh model mới.
- Thay đổi thuật toán Random Forest.
- Station Map.
- Heatmap.
- Thay đổi giao diện Dashboard lớn.
- Airflow.
- Kubernetes.
- Cloud deployment.
- Distributed scheduler phức tạp.
- Thay đổi kiến trúc Kafka → Spark → PostgreSQL nếu không bắt buộc.
- Rewrite toàn bộ pipeline v1.0.

> **Quan trọng:** Phase 1 chỉ cập nhật dữ liệu. Forecast tương lai thuộc Phase 2.

---

# 5. KIẾN TRÚC SAU PHASE 1

```text
        Citi Bike System Data
                 ↓
        Automatic Data Checker
                 ↓
          Download New Data
                 ↓
           Validate Data
                 ↓
          Kafka Producer
                 ↓
              Kafka
                 ↓
        Spark Processing
                 ↓
            PostgreSQL
          ↙           ↘
       trips       hourly_demand
```

Phase 2 sẽ sử dụng dữ liệu đã cập nhật:

```text
PostgreSQL
     ↓
Latest Actual Time
     ↓
Future Forecast 24h
```

---

# 6. NGUYÊN TẮC DỮ LIỆU

## 6.1 Không hard-code tháng mới

Không viết logic kiểu:

```python
download_july_2026()
download_august_2026()
```

Phải có logic tổng quát để phát hiện tháng mới.

Ví dụ:

```text
Đã có: 2026-01 ... 2026-06
Nguồn có thêm: 2026-07
→ Chỉ tải 2026-07
```

## 6.2 Không tải lại dữ liệu đã có

Nếu tháng đã được tải và xử lý thì lần chạy sau phải bỏ qua tháng đó.

## 6.3 Không duplicate `ride_id`

Phải kiểm soát:

```text
COUNT(*) = COUNT(DISTINCT ride_id)
```

đối với dữ liệu chuyến đi hợp lệ.

## 6.4 Không xóa dữ liệu lịch sử

Mục tiêu là:

```text
OLD DATA + NEW DATA
```

không phải xóa dữ liệu cũ rồi thay thế bằng dữ liệu mới.

---

# 7. TASK 1 — KHẢO SÁT CƠ CHẾ LẤY DATA

## Mục tiêu

Xác định cách truy cập Citi Bike System Data và cách phát hiện file/tháng mới.

## Kiểm tra

- URL/source hiện tại.
- Cấu trúc tên file.
- Quy luật tên file theo tháng.
- Format dữ liệu.
- Cách xác định tháng mới.
- Cách kiểm tra file đã tồn tại.

## Acceptance Criteria

- [ ] Xác định nguồn dữ liệu Citi Bike.
- [ ] Xác định quy luật file dữ liệu.
- [ ] Xác định được tháng chưa có.
- [ ] Không cần hard-code từng tháng.
- [ ] Có phương án download tự động.

## Điều kiện chuyển Task

Chỉ chuyển Task 2 khi cơ chế phát hiện dữ liệu mới đã rõ ràng.

---

# 8. TASK 2 — AUTOMATIC DATA DOWNLOADER

## Mục tiêu

Xây dựng module tải dữ liệu Citi Bike mới.

## Yêu cầu

Downloader phải:

- tải file mới;
- lưu đúng vị trí;
- không tải lại file đã có;
- xử lý lỗi download;
- có log;
- không làm thay đổi dataset cũ.

## Luồng

```text
Source
  ↓
Check available months
  ↓
Compare with local data
  ↓
New month?
  ├── No → Skip
  └── Yes → Download → Save
```

## Acceptance Criteria

- [ ] Download thành công dữ liệu mới.
- [ ] File được lưu đúng vị trí.
- [ ] File cũ không bị ghi đè tùy tiện.
- [ ] Chạy lại không download duplicate.
- [ ] Có log START / DOWNLOAD / SUCCESS / ERROR / SUMMARY.

---

# 9. TASK 3 — DATA VALIDATION

## Mục tiêu

Kiểm tra dữ liệu mới trước khi đưa vào pipeline.

## Schema tối thiểu

```text
ride_id
rideable_type
started_at
ended_at
start_station_name
start_station_id
end_station_name
end_station_id
start_lat
start_lng
end_lat
end_lng
member_casual
```

## Kiểm tra

- `ride_id`
- `started_at`
- `ended_at`
- duration
- station fields
- coordinates
- `member_casual`
- duplicate
- datetime parse

Không tự ý thay đổi quy tắc làm sạch v1.0.

## Acceptance Criteria

- [ ] Schema hợp lệ.
- [ ] Datetime hợp lệ.
- [ ] Duplicate được phát hiện.
- [ ] Dữ liệu lỗi được ghi log.
- [ ] Dữ liệu hợp lệ mới được đưa vào pipeline.

---

# 10. TASK 4 — TÍCH HỢP KAFKA

## Mục tiêu

Đưa dữ liệu mới vào Kafka Producer hiện tại.

```text
New CSV
   ↓
Producer
   ↓
Serialize
   ↓
Kafka
   ↓
citibike-trips
```

## Yêu cầu

- Tái sử dụng Producer hiện tại nếu có thể.
- Gửi dữ liệu mới.
- Log số record.
- Xử lý lỗi.
- Không gửi lại record đã xử lý nếu có cơ chế nhận diện duplicate.

## Acceptance Criteria

- [ ] Producer kết nối Kafka.
- [ ] Dữ liệu mới được gửi.
- [ ] Topic `citibike-trips` hoạt động.
- [ ] Có log số record.
- [ ] Không tạo duplicate không cần thiết.

---

# 11. TASK 5 — SPARK PROCESSING

## Mục tiêu

Đảm bảo Spark xử lý dữ liệu mới giống pipeline v1.0.

```text
Kafka
  ↓
Spark
  ↓
Parse
  ↓
Clean
  ↓
Transform
  ↓
Aggregate
  ↓
PostgreSQL
```

Giữ nguyên logic v1.0 nếu không có lỗi bắt buộc phải sửa, gồm các trường thời gian và hourly demand.

## Acceptance Criteria

- [ ] Spark đọc được dữ liệu mới.
- [ ] Spark xử lý thành công.
- [ ] Không làm hỏng dữ liệu cũ.
- [ ] `hourly_demand` được cập nhật.
- [ ] Tổng dữ liệu sau cập nhật hợp lý.

---

# 12. TASK 6 — CẬP NHẬT POSTGRESQL

## Mục tiêu

Đưa dữ liệu mới vào PostgreSQL mà không phá dữ liệu lịch sử.

## Bảng liên quan

```text
trips
hourly_demand
```

`predictions` không phải mục tiêu chính của Phase 1. Future Forecast thuộc Phase 2.

## Kiểm tra

```powershell
docker exec citibike-postgres psql -U postgres -d citibike -c "SELECT COUNT(*) FROM trips;"
```

```powershell
docker exec citibike-postgres psql -U postgres -d citibike -c "SELECT COUNT(*) FROM hourly_demand;"
```

## Acceptance Criteria

- [ ] Dữ liệu mới có trong `trips`.
- [ ] `hourly_demand` có dữ liệu mới.
- [ ] Không duplicate `ride_id`.
- [ ] Dữ liệu lịch sử vẫn tồn tại.
- [ ] PostgreSQL connection hoạt động.

---

# 13. TASK 7 — IDEMPOTENCY / CHẠY LẠI

## Mục tiêu

Pipeline chạy lại phải an toàn.

Ví dụ:

```text
Lần 1 → Load 2026-07
Lần 2 → 2026-07 đã tồn tại → Skip
```

Không được:

- nhân đôi toàn bộ dữ liệu;
- nhân đôi `ride_id`;
- làm sai `hourly_demand`;
- xóa dữ liệu cũ.

## Acceptance Criteria

- [ ] Chạy lần 1 thành công.
- [ ] Chạy lần 2 không tạo duplicate.
- [ ] Không có data mới thì số record ổn định.
- [ ] Log thể hiện `No new data` hoặc tương đương.

---

# 14. TASK 8 — CHẠY PIPELINE BẰNG MỘT LỆNH

## Mục tiêu

Có một entry point rõ ràng, ví dụ:

```powershell
python scripts/update_data.py
```

Tên file không bắt buộc; AI Agent phải kiểm tra cấu trúc project trước khi quyết định.

Mục tiêu flow:

```text
Check source
    ↓
Find new data
    ↓
Download
    ↓
Validate
    ↓
Run pipeline
    ↓
Update PostgreSQL
    ↓
Summary
```

## Acceptance Criteria

- [ ] Có một entry point rõ ràng.
- [ ] Không cần chạy nhiều script riêng lẻ cho một lần update.
- [ ] Có summary cuối pipeline.
- [ ] Lỗi được chỉ rõ bước xảy ra.

---

# 15. TASK 9 — LOGGING VÀ ERROR HANDLING

Logging tối thiểu:

```text
START
CHECK
DOWNLOAD
VALIDATE
PROCESS
DATABASE
SUCCESS
ERROR
SUMMARY
```

Ví dụ:

```text
[START] Automatic data update
[CHECK] Checking Citi Bike source
[CHECK] New month detected: 2026-07
[DOWNLOAD] Downloading 2026-07
[VALIDATE] Dataset validation passed
[PROCESS] Sending records to Kafka
[DATABASE] PostgreSQL updated
[SUCCESS] Automatic update completed
[SUMMARY] New records: XXXXX
```

Phải xử lý/log được:

```text
Internet unavailable
Source unavailable
Download failed
Invalid file
Invalid schema
Duplicate ride_id
Kafka unavailable
Spark processing error
PostgreSQL unavailable
```

---

# 16. TASK 10 — KIỂM THỬ TÍCH HỢP

## Test 1 — Không có dữ liệu mới

```powershell
python <update-script>
```

Kết quả mong đợi:

```text
No new data
```

Không duplicate và không xử lý lại không cần thiết.

## Test 2 — Có dữ liệu tháng mới

```text
Detect new month
↓
Download
↓
Validate
↓
Kafka
↓
Spark
↓
PostgreSQL
```

## Test 3 — Chạy lại

Chạy lại cùng command và xác nhận không duplicate.

## Test 4 — Kiểm tra database

```powershell
docker exec citibike-postgres psql -U postgres -d citibike -c "SELECT COUNT(*) FROM trips;"
```

```powershell
docker exec citibike-postgres psql -U postgres -d citibike -c "SELECT COUNT(*) FROM hourly_demand;"
```

Kiểm tra duplicate:

```sql
SELECT COUNT(*) AS total,
       COUNT(DISTINCT ride_id) AS unique_rides
FROM trips;
```

Phải thỏa:

```text
total = unique_rides
```

---

# 17. TASK 11 — REGRESSION TEST V1.0

Phase 1 không được làm hỏng v1.0.

Kiểm tra tối thiểu:

- [ ] Docker Compose vẫn chạy.
- [ ] PostgreSQL connection OK.
- [ ] `trips` vẫn truy cập được.
- [ ] `hourly_demand` vẫn truy cập được.
- [ ] Historical predictions không bị xóa.
- [ ] Dashboard vẫn mở được.
- [ ] Model v1.0 vẫn chạy được nếu chạy lại.
- [ ] Không thay đổi kết quả v1.0 ngoài phần dữ liệu mới.

---

# 18. TASK 12 — BÀN GIAO CHO PHASE 2

Phase 1 phải bàn giao:

```text
Latest actual time
Number of total trips
Number of hourly rows
New data range
Database status
Pipeline execution result
```

Đặc biệt Phase 2 phải lấy được actual mới nhất từ database.

## Quy tắc bắt buộc

Không hard-code:

```text
2026-06-30 23:00
```

Mốc này chỉ là ví dụ kiểm thử với dataset H1 hiện tại.

Nguyên tắc thực tế:

```text
Latest Actual
     ↓
+ 1 hour
     ↓
Future Forecast Start
```

---

# 19. QUY TẮC CHUNG

## 19.1 Không thay đổi kiến trúc tùy tiện

Không tự ý thay Kafka/Spark/PostgreSQL bằng công nghệ khác.

## 19.2 Không làm quá

Không tự ý thêm:

```text
Airflow
Kubernetes
Cloud Scheduler
AWS
GCP
Azure
```

Mục tiêu là hệ thống tự động cập nhật đủ dùng, dễ chạy, dễ kiểm thử và phù hợp đồ án.

## 19.3 Không sửa v1.0 nếu không cần

Ưu tiên reuse code hiện tại thay vì rewrite pipeline.

## 19.4 Không xóa dữ liệu tùy tiện

Không tự ý chạy:

```sql
DROP TABLE
TRUNCATE
DELETE
```

nếu chưa xác định rõ mục đích và ảnh hưởng.

## 19.5 Chỉ thêm thư viện khi thực sự cần

Trước khi thêm package:

1. Kiểm tra `requirements.txt`.
2. Kiểm tra thư viện hiện tại.
3. Chỉ thêm dependency khi thực sự cần.
4. Ghi nhận dependency mới.

---

# 20. QUY TẮC CODE

Python:

```text
snake_case
```

Class:

```text
PascalCase
```

Ví dụ:

```python
check_new_data()
download_dataset()
validate_dataset()
update_postgres()
```

---

# 21. QUY TRÌNH LÀM VIỆC VỚI AI AGENT

AI Agent chỉ được hỗ trợ triển khai, không tự ý mở rộng phạm vi.

## Trước khi giao Task

Cung cấp:

```text
TASK_PHASE1.md
docs/FINAL_SYSTEM_DESIGN.md
docs/FUTURE_FORECAST_HANDOVER.md
docs/TV2_HANDOVER.md
docs/ML_DATA_DICTIONARY.md
```

Prompt nguyên tắc:

```text
Bạn đang thực hiện TASK X của TASK_PHASE1.md.

Chỉ được làm trong phạm vi TASK X.
Không thực hiện Task tiếp theo.
Không triển khai Phase 2.
Không triển khai Station Map.
Không thay đổi kiến trúc nếu không bắt buộc.
Không sửa file ngoài phạm vi nếu không cần thiết.

Trước khi thay đổi code, hãy kiểm tra cấu trúc project hiện tại.

Sau khi hoàn thành, hãy liệt kê:
1. File đã thay đổi.
2. Thay đổi chính.
3. Lệnh kiểm thử.
4. Kết quả kiểm thử.
5. Các vấn đề còn lại.
```

---

# 22. SAU KHI AI AGENT HOÀN THÀNH TASK

Không chuyển Task ngay.

Phải thực hiện:

```text
1. git status
2. Kiểm tra file thay đổi
3. Đọc diff
4. Chạy chương trình
5. Chạy test/check
6. Đối chiếu Acceptance Criteria
7. Sửa lỗi nếu có
8. Kiểm tra regression
9. Commit Git
10. Đánh dấu Task hoàn thành
11. Chuyển Task tiếp theo
```

---

# 23. CHECKPOINT THEO TASK

| Task | Nội dung | Trạng thái | Ngày |
|---|---|---|---|
| 1 | Khảo sát cơ chế lấy data | ⬜ | |
| 2 | Automatic Data Downloader | ⬜ | |
| 3 | Data Validation | ⬜ | |
| 4 | Kafka Integration | ⬜ | |
| 5 | Spark Processing | ⬜ | |
| 6 | PostgreSQL Update | ⬜ | |
| 7 | Idempotency / Rerun | ⬜ | |
| 8 | One-command Pipeline | ⬜ | |
| 9 | Logging & Error Handling | ⬜ | |
| 10 | Integration Test | ⬜ | |
| 11 | Regression Test v1.0 | ⬜ | |
| 12 | Handoff to Phase 2 | ⬜ | |

Quy ước:

```text
⬜ Chưa làm
🟡 Đang làm
🟢 Hoàn thành
🔴 Có lỗi / cần xử lý
```

Không chuyển Task tiếp theo khi Task hiện tại chưa đạt Acceptance Criteria.

---

# 24. GIT WORKFLOW

Mỗi Task hoàn thành nên có commit riêng.

Trước khi commit:

```powershell
git status
git diff
```

Sau khi kiểm thử thành công:

```powershell
git add .
git commit -m "feat(phase1): ..."
```

Ví dụ:

```text
feat(phase1): add automatic data checker
feat(phase1): add automatic dataset downloader
feat(phase1): add data validation
feat(phase1): integrate new data with kafka pipeline
feat(phase1): update postgres incrementally
feat(phase1): add idempotent update flow
test(phase1): add automatic update integration checks
docs(phase1): add automatic update documentation
```

Không commit khi test chưa đạt.

---

# 25. ACCEPTANCE CRITERIA TỔNG THỂ PHASE 1

## Automatic Update

- [ ] Hệ thống có thể kiểm tra dữ liệu mới.
- [ ] Có thể tự động tải dữ liệu mới.
- [ ] Không cần hard-code từng tháng.
- [ ] Không tải lại dữ liệu đã có.

## Data Quality

- [ ] Schema hợp lệ.
- [ ] Datetime hợp lệ.
- [ ] Duplicate `ride_id` được kiểm soát.
- [ ] Không làm hỏng dữ liệu cũ.

## Pipeline

- [ ] Kafka nhận dữ liệu mới.
- [ ] Spark xử lý dữ liệu mới.
- [ ] PostgreSQL nhận dữ liệu mới.
- [ ] `hourly_demand` được cập nhật.

## Idempotency

- [ ] Chạy lần đầu thành công.
- [ ] Chạy lần hai không tạo duplicate.
- [ ] Không có data mới thì hệ thống báo rõ.

## Stability

- [ ] Docker vẫn hoạt động.
- [ ] PostgreSQL hoạt động.
- [ ] Kafka hoạt động.
- [ ] Spark hoạt động.
- [ ] Dashboard v1.0 vẫn hoạt động.

## Handoff

- [ ] Xác định được actual time mới nhất.
- [ ] Phase 2 có thể lấy latest actual.
- [ ] Không hard-code ngày `2026-06-30`.
- [ ] Có tài liệu hướng dẫn chạy Phase 1.

---

# 26. ĐIỀU KIỆN HOÀN THÀNH PHASE 1

Phase 1 chỉ được đánh dấu:

```text
🟢 PHASE 1 — COMPLETED
```

khi flow sau đã chạy thành công và được kiểm thử:

```text
New Data
   ↓
Automatic Detection
   ↓
Download
   ↓
Validation
   ↓
Kafka
   ↓
Spark
   ↓
PostgreSQL
   ↓
hourly_demand
   ↓
Latest Actual Time
```

Sau đó mới chuyển sang:

```text
PHASE 2 — FUTURE FORECAST 24 HOURS
```

---

# 27. KẾT QUẢ BÀN GIAO

Phase 1 cần bàn giao:

```text
1. Automatic update module
2. Data validation module/check
3. Pipeline execution command
4. Updated PostgreSQL data
5. Logs / test results
6. Documentation
7. Git commit
```

Thông tin quan trọng nhất cho Phase 2:

```text
Latest actual timestamp
Latest available data range
Updated hourly demand
Database status
```

---

# 28. NGUYÊN TẮC CUỐI CÙNG

> **Không làm nhiều hơn đặc tả.**

Nếu AI Agent đề xuất:

```text
Forecast
Map
Heatmap
Model retraining
Airflow
Kubernetes
Cloud
```

thì **không thực hiện trong Phase 1**.

Phase 1 chỉ có một nhiệm vụ:

> **Làm cho BikeDemand có khả năng tự động lấy dữ liệu Citi Bike mới và đưa dữ liệu đó an toàn vào pipeline hiện tại.**

Sau khi Phase 1 được kiểm thử và xác nhận hoàn thành, mới bắt đầu Phase 2.

# TASK NV1 — DATA ENGINEERING & SYSTEM INFRASTRUCTURE

> **Dự án:** BikeDemand — Phân tích và dự báo nhu cầu sử dụng xe đạp Citi Bike  
> **Học phần:** Tích hợp và phân tích dữ liệu lớn  
> **Vai trò:** Thành viên 1 — Data Engineering / System Integration  
> **Phụ trách:** [Tên thành viên]  
> **Ngày bắt đầu:** [DD/MM/YYYY]  
> **Trạng thái:** 🔵 Chưa bắt đầu

---

# 0. THÔNG TIN TỔNG QUAN

## 0.1. Vai trò của NV1

NV1 phụ trách phần **Data Engineering và hạ tầng xử lý dữ liệu** của hệ thống.

Nhiệm vụ chính:

- Quản lý dataset Citi Bike chính thức.
- Xây dựng và duy trì pipeline dữ liệu.
- Xây dựng Kafka Producer / Consumer.
- Đưa dữ liệu vào Kafka.
- Xử lý dữ liệu bằng Apache Spark.
- Làm sạch và biến đổi dữ liệu.
- Lưu dữ liệu vào PostgreSQL.
- Chuẩn bị dữ liệu đầu vào cho NV2 thực hiện phân tích và Machine Learning.
- Tích hợp các thành phần Kafka → Spark → PostgreSQL.
- Kiểm tra tính đúng đắn và ổn định của pipeline.

NV1 **không phụ trách chính**:

- Phân tích thống kê chuyên sâu.
- Xây dựng mô hình Machine Learning.
- Đánh giá mô hình dự báo.
- Xây dựng Dashboard phân tích cuối cùng.

Các phần trên thuộc nhiệm vụ chính của NV2, nhưng NV1 phải cung cấp dữ liệu đầu vào cần thiết.

---

# 1. ĐỊNH DANH VÀ MỤC TIÊU

## 1.1. Tên Task

**[NV1] Data Engineering & Big Data Pipeline**

---

## 1.2. Mục tiêu

Xây dựng hoàn chỉnh pipeline dữ liệu lớn cho dự án BikeDemand:

```text
Citi Bike CSV
     ↓
Data Preparation
     ↓
Kafka Producer
     ↓
Kafka Topic
     ↓
Spark Processing
     ↓
Data Cleaning / Transformation
     ↓
PostgreSQL
     ↓
Dữ liệu đầu vào cho Analysis + ML
```

Sau khi hoàn thành NV1, hệ thống phải có khả năng:

1. Đọc dataset Citi Bike chính thức.
2. Đưa dữ liệu vào Kafka.
3. Kafka tiếp nhận và phân phối dữ liệu.
4. Spark đọc dữ liệu từ Kafka.
5. Spark xử lý dữ liệu.
6. Dữ liệu sau xử lý được lưu vào PostgreSQL.
7. NV2 có thể sử dụng dữ liệu PostgreSQL để phân tích và xây dựng mô hình.

---

## 1.3. Bối cảnh

Đây là phần Data Engineering của toàn bộ hệ thống.

Hệ thống được chia thành hai hướng chính:

### NV1

```text
DATA ENGINEERING
CSV
 ↓
Kafka
 ↓
Spark
 ↓
PostgreSQL
```

### NV2

```text
DATA ANALYSIS + MACHINE LEARNING
PostgreSQL
 ↓
Phân tích
 ↓
Feature Engineering
 ↓
ML
 ↓
Prediction
 ↓
Dashboard
```

Hai phần kết hợp thành:

```text
Citi Bike Dataset
        ↓
      Kafka
        ↓
      Spark
        ↓
   PostgreSQL
        ↓
 ┌──────┴────────┐
 ↓               ↓
Analysis         ML
 ↓               ↓
 └──────┬────────┘
        ↓
    Dashboard
```

---

# 2. DATASET CHÍNH THỨC

## 2.1. Dataset sử dụng

Dataset chính thức của dự án:

```text
Citi Bike Trip Data — 6 tháng đầu năm 2026
```

Khoảng thời gian:

```text
2026-01-01 → 2026-06-30
```

Dataset chính thức sau khi làm sạch:

```text
data/processed/citibike_2026_H1.csv
```

---

## 2.2. Dataset nguồn

6 file CSV:

```text
data/raw/trips/
├── JC-202601-citibike-tripdata.csv
├── JC-202602-citibike-tripdata.csv
├── JC-202603-citibike-tripdata.csv
├── JC-202604-citibike-tripdata.csv
├── JC-202605-citibike-tripdata.csv
└── JC-202606-citibike-tripdata.csv
```

Không sử dụng dataset tháng 12/2025 trong pipeline chính thức.

---

## 2.3. Dataset sau khi chuẩn hóa

Dataset chính thức:

```text
data/processed/citibike_2026_H1.csv
```

Số lượng bản ghi:

```text
415,708 trips
```

Số lượng cột:

```text
13 cột dữ liệu gốc
```

Các cột:

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

---

## 2.4. Kiểm tra dataset

Dataset chính thức đã được kiểm tra:

- Không còn `ride_id` trùng.
- `started_at` hợp lệ.
- `ended_at` hợp lệ.
- Dữ liệu nằm trong khoảng 6 tháng đầu năm 2026.
- Có một số giá trị thiếu ở thông tin trạm đích và tọa độ đích.
- Không tự ý loại bỏ các bản ghi thiếu nếu chưa có yêu cầu xử lý cụ thể.

Thông tin kiểm tra chi tiết nằm trong:

```text
scripts/inspect_dataset.py
scripts/inspect_official_dataset.py
scripts/create_official_dataset.py
```

---

# 3. YÊU CẦU KỸ THUẬT & PHẠM VI

# TASK 1 — QUẢN LÝ DATASET 🟢 Hoàn thành

## Mục tiêu

Đảm bảo dataset chính thức được xác định rõ ràng và có thể tái tạo.

## In-Scope

- Kiểm tra dataset nguồn.
- Kiểm tra số lượng bản ghi.
- Kiểm tra schema.
- Kiểm tra kiểu dữ liệu.
- Kiểm tra missing values.
- Kiểm tra duplicate `ride_id`.
- Kiểm tra datetime.
- Tạo dataset chính thức.
- Lưu dataset vào `data/processed/`.

## Out-of-Scope

- Không thêm dataset khác.
- Không tự ý thay đổi phạm vi 6 tháng.
- Không xây dựng ML.
- Không thực hiện phân tích chuyên sâu.

## File liên quan

```text
data/raw/trips/
data/processed/
scripts/inspect_dataset.py
scripts/create_official_dataset.py
scripts/inspect_official_dataset.py
```

## Acceptance Criteria

- [ ] Có đủ 6 file CSV tháng 01 → tháng 06/2026.
- [ ] Có dataset chính thức `citibike_2026_H1.csv`.
- [ ] Dataset có 415,708 bản ghi.
- [ ] Không còn duplicate `ride_id`.
- [ ] `started_at` nằm trong khoảng 2026-01-01 → 2026-06-30.
- [ ] Không có datetime không hợp lệ.

## Điều kiện chuyển Task

Chỉ chuyển sang Task 2 khi toàn bộ Acceptance Criteria đạt.

---

# TASK 2 — DOCKER INFRASTRUCTURE 🟢 Hoàn thành

## Mục tiêu

Xây dựng môi trường chạy thống nhất bằng Docker Compose.

## Thành phần

```text
PostgreSQL
Kafka
Spark Master
Spark Worker
```

## Docker Compose

File:

```text
docker-compose.yml
```

## Các container

```text
citibike-postgres
citibike-kafka
citibike-spark-master
citibike-spark-worker
```

## Công nghệ

- Docker
- Docker Compose
- PostgreSQL 16
- Apache Kafka 3.9.0
- Apache Spark 3.5.7

## Kiểm tra

Chạy:

```powershell
docker compose config
```

Sau đó:

```powershell
docker compose up -d
```

Kiểm tra:

```powershell
docker compose ps
```

## Acceptance Criteria

- [ ] Docker Compose không báo lỗi.
- [ ] PostgreSQL ở trạng thái `Up`.
- [ ] Kafka ở trạng thái `Up`.
- [ ] Spark Master ở trạng thái `Up`.
- [ ] Spark Worker ở trạng thái `Up`.
- [ ] Spark Worker đăng ký thành công với Spark Master.

Kiểm tra log:

```powershell
docker logs citibike-spark-worker --tail 30
```

Phải có thông báo tương tự:

```text
Successfully registered with master
```

## Điều kiện chuyển Task

Chỉ chuyển sang Task 3 khi toàn bộ service hoạt động ổn định.

---

# TASK 3 — POSTGRESQL DATABASE 🟢 DONE về phần infrastructure/schema

## Mục tiêu

Xây dựng database làm nơi lưu trữ dữ liệu sau khi Spark xử lý.

## Database

```text
Database: citibike
User: postgres
Port: 5432
```

## Schema dự kiến

### Bảng trips

Lưu dữ liệu chuyến đi sau xử lý.

Các nhóm dữ liệu:

```text
ride information
station information
time information
member information
location information
```

### Bảng hourly_demand

Lưu dữ liệu nhu cầu theo giờ.

Dùng cho:

- Phân tích.
- Feature Engineering.
- Machine Learning.
- Dashboard.

### Bảng predictions

Lưu kết quả dự báo của mô hình ML.

---

## File

```text
postgres/init/01_schema.sql
```

## Kiểm tra

```powershell
docker exec -it citibike-postgres psql -U postgres -d citibike
```

Sau đó:

```sql
\dt
```

Phải có:

```text
hourly_demand
predictions
trips
```

## Acceptance Criteria

- [ ] Database `citibike` hoạt động.
- [ ] Bảng `trips` tồn tại.
- [ ] Bảng `hourly_demand` tồn tại.
- [ ] Bảng `predictions` tồn tại.
- [ ] Schema không bị lỗi.
- [ ] Có thể kết nối PostgreSQL từ application/Python.

## Điều kiện chuyển Task

Database phải kết nối thành công trước khi triển khai pipeline Kafka → Spark.

---

# TASK 4 — KAFKA 🟢 DONE

## Mục tiêu

Thiết lập Kafka làm hệ thống truyền dữ liệu trung gian.

## Kafka Broker

```text
localhost:9092
```

Trong Docker network:

```text
kafka:9092
```

---

## Topic chính

```text
citibike-trips
```

Cấu hình:

```text
Partitions: 3
Replication Factor: 1
```

---

## Kiểm tra Topic

Liệt kê:

```powershell
docker exec citibike-kafka `
/opt/kafka/bin/kafka-topics.sh `
--bootstrap-server localhost:9092 `
--list
```

Kiểm tra:

```powershell
docker exec citibike-kafka `
/opt/kafka/bin/kafka-topics.sh `
--bootstrap-server localhost:9092 `
--describe `
--topic citibike-trips
```

## Acceptance Criteria

- [ ] Kafka hoạt động.
- [ ] Topic `citibike-trips` tồn tại.
- [ ] Topic có 3 partitions.
- [ ] Producer có thể gửi message.
- [ ] Consumer có thể nhận message.

## Điều kiện chuyển Task

Kafka phải gửi và nhận được dữ liệu thành công.

---

# TASK 5 — KAFKA PRODUCER 🟢 DONE

## Mục tiêu

Xây dựng Producer đọc dữ liệu Citi Bike và gửi dữ liệu vào Kafka.

## Input

```text
data/processed/citibike_2026_H1.csv
```

## Output

```text
Kafka topic:
citibike-trips
```

## Luồng

```text
CSV
 ↓
Python Producer
 ↓
Serialize record
 ↓
Kafka
 ↓
citibike-trips
```

## Dữ liệu message

Mỗi message đại diện cho một chuyến đi.

Ví dụ cấu trúc logic:

```json
{
  "ride_id": "...",
  "rideable_type": "...",
  "started_at": "...",
  "ended_at": "...",
  "start_station_name": "...",
  "start_station_id": "...",
  "end_station_name": "...",
  "end_station_id": "...",
  "start_lat": 0,
  "start_lng": 0,
  "end_lat": 0,
  "end_lng": 0,
  "member_casual": "..."
}
```

## Yêu cầu

- Đọc dataset theo từng record/chunk.
- Không cần nạp toàn bộ dataset vào RAM nếu không cần thiết.
- Gửi message vào Kafka.
- Có log số lượng record đã gửi.
- Có xử lý lỗi cơ bản.
- Có thể cấu hình tốc độ gửi nếu cần.

## Acceptance Criteria

- [ ] Producer kết nối Kafka thành công.
- [ ] Producer gửi được message.
- [ ] Consumer nhận được message.
- [ ] Message có cấu trúc hợp lệ.
- [ ] Có log số lượng record gửi.
- [ ] Không làm thay đổi dataset gốc.

---

# TASK 6 — KAFKA CONSUMER

## Mục tiêu

Kiểm tra dữ liệu từ Kafka trước khi đưa vào Spark.

## Luồng

```text
Kafka
 ↓
Consumer
 ↓
Deserialize
 ↓
Validate
```

## Kiểm tra

Consumer phải kiểm tra:

- Có message hay không.
- JSON/schema có hợp lệ hay không.
- `ride_id` có tồn tại hay không.
- `started_at` có hợp lệ hay không.
- Các trường dữ liệu chính có đúng kiểu hay không.

## Acceptance Criteria

- [ ] Consumer kết nối thành công.
- [ ] Consumer đọc được message.
- [ ] Có thể kiểm tra một số record.
- [ ] Không crash khi gặp dữ liệu lỗi.
- [ ] Có log dữ liệu nhận được.

---

# TASK 7 — SPARK PROCESSING

## Mục tiêu

Sử dụng Apache Spark để xử lý dữ liệu từ Kafka.

## Luồng

```text
Kafka
 ↓
Spark Structured Streaming
 ↓
Parse dữ liệu
 ↓
Transform
 ↓
Clean
 ↓
Aggregate
 ↓
PostgreSQL
```

## Spark

Version:

```text
Apache Spark 3.5.7
```

## Các bước xử lý

### Bước 1 — Đọc Kafka

Spark đọc:

```text
citibike-trips
```

### Bước 2 — Parse message

Chuyển JSON message thành schema Spark.

### Bước 3 — Chuẩn hóa datetime

Xử lý:

```text
started_at
ended_at
```

### Bước 4 — Tính duration

Tạo:

```text
ride_duration_minutes
```

### Bước 5 — Tạo các trường thời gian

Có thể tạo:

```text
date
hour
day_of_week
month
```

### Bước 6 — Xử lý dữ liệu bất thường

Kiểm tra:

```text
duration <= 0
missing required fields
invalid datetime
```

Không tự ý loại bỏ dữ liệu nếu chưa có quy tắc rõ ràng.

### Bước 7 — Aggregate

Tạo dữ liệu nhu cầu theo giờ:

```text
date
hour
trip_count
```

---

# TASK 8 — GHI DỮ LIỆU VÀO POSTGRESQL

## Mục tiêu

Đưa dữ liệu sau Spark vào PostgreSQL.

## Luồng

```text
Spark
 ↓
Processed trips
 ↓
PostgreSQL.trips
```

Và:

```text
Spark
 ↓
Hourly aggregation
 ↓
PostgreSQL.hourly_demand
```

## Yêu cầu

- Ghi dữ liệu đúng schema.
- Không tạo duplicate không kiểm soát.
- Có thể kiểm tra số lượng record.
- Có log quá trình ghi.
- Có khả năng chạy lại pipeline có kiểm soát.

## Acceptance Criteria

- [ ] PostgreSQL nhận dữ liệu.
- [ ] Bảng `trips` có dữ liệu.
- [ ] Bảng `hourly_demand` có dữ liệu.
- [ ] Dữ liệu có thể truy vấn bằng SQL.
- [ ] Số lượng dữ liệu hợp lý.
- [ ] Không xảy ra duplicate ngoài quy tắc đã thống nhất.

---

# TASK 9 — DATA QUALITY CHECK

## Mục tiêu

Kiểm tra dữ liệu sau pipeline có còn đảm bảo chất lượng hay không.

## Kiểm tra

### Trips

```sql
SELECT COUNT(*) FROM trips;
```

### Duplicate

```sql
SELECT ride_id, COUNT(*)
FROM trips
GROUP BY ride_id
HAVING COUNT(*) > 1;
```

### Null

Kiểm tra các trường bắt buộc.

### Hourly demand

Kiểm tra:

```text
date
hour
trip_count
```

## Acceptance Criteria

- [ ] Không có duplicate `ride_id` ngoài dự kiến.
- [ ] Không có datetime không hợp lệ.
- [ ] `trip_count >= 0`.
- [ ] Dữ liệu theo giờ có đầy đủ trường.
- [ ] Có thể truy vấn dữ liệu bằng SQL.

---

# TASK 10 — BÀN GIAO DỮ LIỆU CHO NV2

## Mục tiêu

Cung cấp dữ liệu sạch và ổn định cho phần Analysis + ML.

## Dataset bàn giao

### trips

Dùng cho:

- Phân tích chuyến đi.
- Phân tích member/casual.
- Phân tích station.
- Feature Engineering.

### hourly_demand

Dùng cho:

- Phân tích nhu cầu.
- Time Series.
- Machine Learning.
- Dự báo.

---

## Thông tin bàn giao

NV1 phải cung cấp cho NV2:

```text
Database connection information
Table structure
Column descriptions
Data types
Data cleaning rules
Data quality results
Sample SQL queries
```

Tài liệu bàn giao dự kiến:

```text
docs/DATA_DICTIONARY.md
docs/PIPELINE.md
```

---

# 4. CÔNG NGHỆ SỬ DỤNG

## Ngôn ngữ

```text
Python 3.11
SQL
```

## Big Data

```text
Apache Kafka 3.9.0
Apache Spark 3.5.7
```

## Database

```text
PostgreSQL 16
```

## Container

```text
Docker
Docker Compose
```

## Python libraries dự kiến

```text
pandas
kafka-python hoặc confluent-kafka
pyspark
psycopg2-binary
```

Chỉ bổ sung thư viện mới khi thực sự cần thiết.

---

# 5. QUY CHUẨN VÀ RÀNG BUỘC

## 5.1. Quy tắc chung

- Không sửa dataset gốc.
- Không xóa dữ liệu tùy tiện.
- Không thay đổi schema đã thống nhất nếu chưa kiểm tra ảnh hưởng.
- Không tự ý thay đổi kiến trúc hệ thống.
- Không triển khai ML trong phần NV1.
- Không xây dựng Dashboard trong phần NV1.

---

## 5.2. Quy tắc dữ liệu

Dataset gốc:

```text
data/raw/
```

Không được chỉnh sửa trực tiếp.

Dataset đã xử lý:

```text
data/processed/
```

---

## 5.3. Quy tắc code

Python:

```text
snake_case
```

Ví dụ:

```python
create_producer()
process_trip()
save_to_postgres()
```

Class:

```text
PascalCase
```

Ví dụ:

```python
KafkaProducer
SparkProcessor
```

---

## 5.4. Logging

Các module chính phải có log tối thiểu:

```text
START
CONNECT
PROCESS
SUCCESS
ERROR
SUMMARY
```

Ví dụ:

```text
Producer started
Connected to Kafka
Sent 10000 records
Producer completed
```

---

## 5.5. Xử lý lỗi

Các thành phần chính phải có xử lý lỗi:

```text
Kafka unavailable
PostgreSQL unavailable
Invalid message
Invalid data
Spark processing error
```

Không được để lỗi không được ghi nhận.

---

# 6. TÀI NGUYÊN VÀ FILE LIÊN QUAN

## Dataset

```text
data/raw/trips/
data/processed/citibike_2026_H1.csv
```

## Docker

```text
docker-compose.yml
```

## PostgreSQL

```text
postgres/init/01_schema.sql
```

## Dataset scripts

```text
scripts/inspect_dataset.py
scripts/create_official_dataset.py
scripts/inspect_official_dataset.py
```

## Tài liệu hệ thống

```text
docs/FINAL_SYSTEM_DESIGN.md
docs/TASK_ASSIGNMENT.md
docs/TASK_NV1.md
```

---

# 7. ACCEPTANCE CRITERIA TỔNG THỂ

NV1 được xem là hoàn thành khi toàn bộ các điều kiện sau đạt:

## Dataset

- [ ] Dataset chính thức 6 tháng đầu năm 2026 tồn tại.
- [ ] Có 415,708 bản ghi.
- [ ] Không duplicate `ride_id`.
- [ ] Không có datetime không hợp lệ.

## Docker

- [ ] PostgreSQL hoạt động.
- [ ] Kafka hoạt động.
- [ ] Spark Master hoạt động.
- [ ] Spark Worker hoạt động.
- [ ] Spark Worker đăng ký với Master thành công.

## Kafka

- [ ] Topic `citibike-trips` tồn tại.
- [ ] Có 3 partitions.
- [ ] Producer gửi dữ liệu thành công.
- [ ] Consumer nhận dữ liệu thành công.

## Spark

- [ ] Spark đọc được Kafka.
- [ ] Spark parse được dữ liệu.
- [ ] Spark xử lý được dữ liệu.
- [ ] Spark tạo được dữ liệu hourly demand.

## PostgreSQL

- [ ] Bảng `trips` tồn tại.
- [ ] Bảng `hourly_demand` tồn tại.
- [ ] Bảng `predictions` tồn tại.
- [ ] `trips` nhận được dữ liệu.
- [ ] `hourly_demand` nhận được dữ liệu.

## Integration

Pipeline chạy được:

```text
CSV
 ↓
Kafka Producer
 ↓
Kafka
 ↓
Spark
 ↓
PostgreSQL
```

## Bàn giao

- [ ] Có Data Dictionary.
- [ ] Có Pipeline documentation.
- [ ] Có hướng dẫn chạy hệ thống.
- [ ] NV2 có thể truy cập và sử dụng dữ liệu.

---

# 8. CHECKPOINT THEO TỪNG TASK

| Task | Nội dung | Trạng thái | Ngày hoàn thành |
|---|---|---|---|
| 1 | Dataset | ⬜ | |
| 2 | Docker Infrastructure | ⬜ | |
| 3 | PostgreSQL | ⬜ | |
| 4 | Kafka | ⬜ | |
| 5 | Kafka Producer | ⬜ | |
| 6 | Kafka Consumer | ⬜ | |
| 7 | Spark Processing | ⬜ | |
| 8 | PostgreSQL Loading | ⬜ | |
| 9 | Data Quality | ⬜ | |
| 10 | Bàn giao NV2 | ⬜ | |

Quy tắc:

```text
⬜ Chưa làm
🟡 Đang làm
🟢 Hoàn thành
🔴 Có lỗi / cần xử lý
```

Không chuyển sang Task tiếp theo khi Task hiện tại chưa đạt Acceptance Criteria.

---

# 9. QUY TRÌNH LÀM VIỆC VỚI AI AGENT

AI Agent chỉ được sử dụng để hỗ trợ triển khai, không tự ý thay đổi kiến trúc.

## Trước khi giao Task

Cung cấp:

```text
TASK_NV1.md
FINAL_SYSTEM_DESIGN.md
TASK_ASSIGNMENT.md
```

Sau đó chỉ rõ:

```text
Bạn đang thực hiện TASK X.
Chỉ được làm trong phạm vi TASK X.
Không thực hiện TASK tiếp theo.
Không thay đổi kiến trúc hệ thống.
Không sửa các file ngoài phạm vi nếu không cần thiết.
```

---

## Sau khi AI Agent hoàn thành

Không chuyển Task ngay.

Phải thực hiện:

```text
1. Kiểm tra file thay đổi
2. Chạy hệ thống
3. Chạy test/check
4. Đối chiếu Acceptance Criteria
5. Sửa lỗi nếu có
6. Commit Git
7. Đánh dấu Task hoàn thành
8. Chuyển Task tiếp theo
```

---

# 10. QUY TRÌNH GIT

Mỗi Task hoàn thành nên có một commit riêng.

Ví dụ:

```bash
git status
git add .
git commit -m "feat(nv1): setup kafka infrastructure"
```

Các commit dự kiến:

```text
feat(nv1): finalize dataset
feat(nv1): setup docker infrastructure
feat(nv1): setup postgresql schema
feat(nv1): setup kafka topic
feat(nv1): implement kafka producer
feat(nv1): implement kafka consumer
feat(nv1): implement spark processing
feat(nv1): load processed data to postgresql
feat(nv1): add data quality checks
docs(nv1): add pipeline documentation
```

---

# 11. ĐIỀU KIỆN HOÀN THÀNH NV1

NV1 chỉ được đánh dấu:

```text
🟢 COMPLETED
```

khi pipeline chính chạy thành công:

```text
Citi Bike CSV
      ↓
Kafka Producer
      ↓
citibike-trips
      ↓
Spark
      ↓
Data Processing
      ↓
PostgreSQL
      ↓
hourly_demand
      ↓
NV2
```

Và:

- [ ] Dataset chính xác.
- [ ] Pipeline hoạt động.
- [ ] Kafka hoạt động.
- [ ] Spark hoạt động.
- [ ] PostgreSQL hoạt động.
- [ ] Dữ liệu được lưu thành công.
- [ ] Data quality đạt yêu cầu.
- [ ] Tài liệu đầy đủ.
- [ ] Git repository được cập nhật.
- [ ] NV2 có thể sử dụng dữ liệu.

---

# 12. TRẠNG THÁI CUỐI

```text
NV1 STATUS: ⬜ NOT STARTED
```

Ngày hoàn thành:

```text
[DD/MM/YYYY]
```

Commit cuối:

```text
[COMMIT HASH]
```

Ghi chú:

```text
[Notes]
```
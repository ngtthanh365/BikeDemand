# DATA PIPELINE

## 1. Tổng quan

Pipeline xử lý dữ liệu Citi Bike:

CSV Dataset
→ Kafka Producer
→ Kafka Topic `citibike-trips`
→ Apache Spark
→ PostgreSQL
→ Machine Learning / Analytics

---

## 2. Kafka

Kafka nhận dữ liệu chuyến đi từ Dataset và truyền dữ liệu qua topic:

`citibike-trips`

Kafka bootstrap server trong Docker:

`kafka:29092`

Dữ liệu được truyền dưới dạng JSON.

---

## 3. Spark

Spark đọc dữ liệu từ Kafka bằng Structured Streaming.

Các bước xử lý chính:

1. Đọc message từ Kafka.
2. Parse JSON theo schema chuyến đi.
3. Chuẩn hóa `started_at` và `ended_at`.
4. Tạo các trường thời gian:
   - `date`
   - `hour`
   - `day_of_week`
   - `month`
5. Phân loại cuối tuần bằng `is_weekend`.
6. Tổng hợp nhu cầu theo ngày và giờ.
7. Tính:
   - `demand`
   - `member_count`
   - `casual_count`
   - `electric_count`
   - `classic_count`
8. Ghi kết quả vào PostgreSQL.

---

## 4. PostgreSQL

PostgreSQL database:

`citibike`

Container:

`citibike-postgres`

Các bảng chính:

- `trips`
- `hourly_demand`
- `predictions`

---

## 5. Dữ liệu đầu ra

### `trips`

Lưu dữ liệu chuyến đi đã được xử lý.

Hiện tại:

`415708 records`

### `hourly_demand`

Lưu dữ liệu nhu cầu theo giờ.

Hiện tại:

`4254 records`

Tổng `demand`:

`415708`

Điều này khớp với tổng số bản ghi trong `trips`.

---

## 6. Kiểm tra tính đúng đắn

Các kiểm tra đã thực hiện:

- Không có duplicate `ride_id`.
- Không có dữ liệu thời gian không hợp lệ.
- Không có duplicate timestamp trong `hourly_demand`.
- `demand` khớp với tổng `member_count` và `casual_count`.
- `demand` khớp với tổng `electric_count` và `classic_count`.


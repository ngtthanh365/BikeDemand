# DATA DICTIONARY

## 1. PostgreSQL Database

- Database: `citibike`
- PostgreSQL container: `citibike-postgres`

---

## 2. Bảng `trips`

Bảng lưu dữ liệu chuyến đi Citi Bike sau khi được Spark xử lý và ghi vào PostgreSQL.

| Cột | Kiểu dữ liệu | Ý nghĩa |
|---|---|---|
| `ride_id` | varchar(100) | Mã chuyến đi |
| `rideable_type` | varchar(30) | Loại xe |
| `started_at` | timestamp | Thời điểm bắt đầu chuyến |
| `ended_at` | timestamp | Thời điểm kết thúc chuyến |
| `start_station_name` | varchar(255) | Tên trạm bắt đầu |
| `start_station_id` | varchar(50) | Mã trạm bắt đầu |
| `end_station_name` | varchar(255) | Tên trạm kết thúc |
| `end_station_id` | varchar(50) | Mã trạm kết thúc |
| `start_lat` | double precision | Vĩ độ trạm bắt đầu |
| `start_lng` | double precision | Kinh độ trạm bắt đầu |
| `end_lat` | double precision | Vĩ độ trạm kết thúc |
| `end_lng` | double precision | Kinh độ trạm kết thúc |
| `member_casual` | varchar(20) | Loại khách hàng: member/casual |

Primary Key: `ride_id`

---

## 3. Bảng `hourly_demand`

Bảng lưu dữ liệu nhu cầu sử dụng xe theo từng giờ.

| Cột | Kiểu dữ liệu | Ý nghĩa |
|---|---|---|
| `id` | bigint | Khóa chính |
| `timestamp` | timestamp | Thời điểm đầu giờ |
| `date` | date | Ngày |
| `hour` | integer | Giờ trong ngày, 0–23 |
| `day_of_week` | integer | Thứ trong tuần |
| `month` | integer | Tháng |
| `is_weekend` | boolean | Có phải cuối tuần hay không |
| `member_count` | integer | Số chuyến của member |
| `casual_count` | integer | Số chuyến của casual |
| `electric_count` | integer | Số chuyến bằng electric bike |
| `classic_count` | integer | Số chuyến bằng classic bike |
| `demand` | integer | Tổng số chuyến trong giờ |

Primary Key: `id`

Unique: `timestamp`

---

## 4. Bảng `predictions`

Bảng dành cho dữ liệu dự đoán nhu cầu.

Schema và dữ liệu dự đoán được sử dụng bởi các thành phần Machine Learning ở bước tiếp theo của hệ thống.

---

## 5. Dữ liệu hiện tại

Tại thời điểm bàn giao:

- `trips`: 415708 records
- `hourly_demand`: 4254 records
- Khoảng thời gian dữ liệu: 2026-01-01 đến 2026-06-30
- Số ngày: 180
- Số giờ khác nhau: 24

Các kiểm tra dữ liệu đã thực hiện:

- Không có `ride_id` trùng.
- Không có `ride_id` rỗng/null.
- Không có thời gian bắt đầu/kết thúc null.
- Không có chuyến có `ended_at < started_at`.
- Không có timestamp `hourly_demand` trùng.
- `demand = member_count + casual_count`.
- `demand = electric_count + classic_count`.


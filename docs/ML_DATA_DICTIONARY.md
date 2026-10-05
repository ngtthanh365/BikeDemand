# ML DATA DICTIONARY

## 1. PostgreSQL Database

Database:

``` text
citibike
```

PostgreSQL container:

``` text
citibike-postgres
```

TV2 sử dụng ba bảng:

``` text
trips
hourly_demand
predictions
```

------------------------------------------------------------------------

## 2. Bảng `trips`

Nguồn:

``` text
Kafka → Spark → PostgreSQL
```

Bảng chứa dữ liệu chuyến đi Citi Bike.

  Cột                    Kiểu dữ liệu       Ý nghĩa
  ---------------------- ------------------ -----------------------
  `ride_id`              varchar(100)       Mã chuyến đi
  `rideable_type`        varchar(30)        Loại xe
  `started_at`           timestamp          Thời gian bắt đầu
  `ended_at`             timestamp          Thời gian kết thúc
  `start_station_name`   varchar(255)       Tên trạm bắt đầu
  `start_station_id`     varchar(50)        Mã trạm bắt đầu
  `end_station_name`     varchar(255)       Tên trạm kết thúc
  `end_station_id`       varchar(50)        Mã trạm kết thúc
  `start_lat`            double precision   Vĩ độ trạm bắt đầu
  `start_lng`            double precision   Kinh độ trạm bắt đầu
  `end_lat`              double precision   Vĩ độ trạm kết thúc
  `end_lng`              double precision   Kinh độ trạm kết thúc
  `member_casual`        varchar(20)        member/casual

Primary Key:

``` text
ride_id
```

Dữ liệu hiện tại:

``` text
415,708 records
```

Dashboard sử dụng bảng này cho:

``` text
Date filter
User filter
Bike filter
Total Trips
Avg Trips / Day
Peak Hour
Member vs Casual
Bike Type
Top Stations
Hourly/Daily Actual Demand
```

------------------------------------------------------------------------

## 3. Bảng `hourly_demand`

Nguồn:

``` text
Spark Aggregation → PostgreSQL
```

  Cột                Kiểu dữ liệu   Ý nghĩa
  ------------------ -------------- --------------------------
  `id`               bigint         Khóa chính
  `timestamp`        timestamp      Thời điểm đầu giờ
  `date`             date           Ngày
  `hour`             integer        Giờ 0--23
  `day_of_week`      integer        Thứ trong tuần
  `month`            integer        Tháng
  `is_weekend`       boolean        Cuối tuần
  `member_count`     integer        Số chuyến member
  `casual_count`     integer        Số chuyến casual
  `electric_count`   integer        Số chuyến electric bike
  `classic_count`    integer        Số chuyến classic bike
  `demand`           integer        Tổng số chuyến trong giờ

Primary Key:

``` text
id
```

Unique:

``` text
timestamp
```

Dữ liệu:

``` text
4,254 records
2026-01-01 00:00
→
2026-06-30 23:00
```

Kiểm tra:

``` text
SUM(demand)         = 415,708
SUM(member_count)   = 322,484
SUM(casual_count)   = 93,224
SUM(electric_count) = 267,614
SUM(classic_count)  = 148,094
```

TV2 dùng bảng này làm nguồn Feature Engineering.

------------------------------------------------------------------------

## 4. Full Hourly Timeline

`hourly_demand` chỉ chứa các giờ có trip.

H1 2026:

``` text
181 × 24 = 4,344 giờ
```

PostgreSQL:

``` text
4,254 giờ có demand
```

Missing zero-demand hours:

``` text
90
```

Feature Engineering tạo full timeline và fill:

``` text
total_trips = 0
```

cho 90 giờ này.

------------------------------------------------------------------------

## 5. ML Dataset

Output:

``` text
analysis/outputs/ml/citibike_ml_dataset.csv
```

Các cột chính:

  Cột             Ý nghĩa
  --------------- --------------------------------
  `datetime`      Thời điểm dự đoán
  `hour`          Giờ trong ngày
  `day_of_week`   Thứ, Monday=0
  `month`         Tháng
  `total_trips`   Target demand
  `lag_1`         Demand 1 giờ trước
  `lag_24`        Demand 24 giờ trước
  `lag_168`       Demand 168 giờ trước
  `rolling_24h`   Rolling mean 24h từ quá khứ
  `rolling_7d`    Rolling mean 7 ngày từ quá khứ

Final rows:

``` text
4,176
```

Range:

``` text
2026-01-08 00:00
→
2026-06-30 23:00
```

------------------------------------------------------------------------

## 6. Bảng `predictions`

  Cột                  Kiểu dữ liệu        Ý nghĩa
  -------------------- ------------------- ------------------------
  `id`                 bigint              Khóa chính
  `prediction_time`    timestamp           Thời điểm model chạy
  `target_time`        timestamp           Thời điểm được dự đoán
  `predicted_demand`   double precision    Demand dự đoán
  `actual_demand`      integer, nullable   Demand thực tế
  `model_name`         varchar(100)        Tên model
  `model_version`      varchar(50)         Phiên bản model

Historical prediction hiện tại:

``` text
model_name    = Random Forest
model_version = 1.0
COUNT         = 4,176
```

Range:

``` text
2026-01-08 00:00
→
2026-06-30 23:00
```

Mapping từ ML output:

``` text
datetime          → target_time
predicted_demand  → predicted_demand
total_trips       → actual_demand
CURRENT_TIMESTAMP → prediction_time
```

------------------------------------------------------------------------

## 7. Ý nghĩa `actual_demand`

Historical prediction:

``` text
actual_demand != NULL
```

vì actual đã tồn tại.

Future Forecast sau này:

``` text
actual_demand = NULL
```

vì thời điểm tương lai chưa có demand thực tế.

Schema hiện tại có thể tái sử dụng cho Future Forecast.

------------------------------------------------------------------------

## 8. Model Version

Historical:

``` text
model_name    = Random Forest
model_version = 1.0
```

Khuyến nghị Future Forecast:

``` text
model_name    = Random Forest
model_version = future-v1
```

Không dùng cùng version để tránh script historical xóa nhầm future rows.

------------------------------------------------------------------------

## 9. Dashboard Data Source

``` text
PostgreSQL.trips
→ Dashboard Actual / Filter / KPI
```

``` text
PostgreSQL.predictions
→ Historical Prediction
```

``` text
dashboard_model_metrics.csv
→ Model Comparison / Test MAE
```

Các CSV hourly/daily/member/bike/station cũ không còn là nguồn chính của
Dashboard.

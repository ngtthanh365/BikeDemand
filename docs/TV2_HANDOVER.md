# TV2 HANDOVER

## 1. Phạm vi bàn giao

TV2 phụ trách:

-   Data Analysis.
-   Feature Engineering.
-   Machine Learning.
-   Prediction.
-   Dashboard.
-   Tích hợp phần TV2 với PostgreSQL do TV1 xây dựng.

Trạng thái hiện tại:

  Thành phần                        Trạng thái
  --------------------------------- ------------
  Feature Engineering               Hoàn thành
  Train / Validation / Test split   Hoàn thành
  Feature Leakage Check             Hoàn thành
  Linear Regression                 Hoàn thành
  Random Forest                     Hoàn thành
  Gradient Boosting                 Hoàn thành
  Model Comparison                  Hoàn thành
  Historical Prediction             Hoàn thành
  Prediction → PostgreSQL           Hoàn thành
  PostgreSQL → Dashboard            Hoàn thành
  Dashboard Filter / KPI            Hoàn thành
  Future Forecast                   Chưa làm

------------------------------------------------------------------------

## 2. Luồng hệ thống sau tích hợp

``` text
CSV H1 2026
    ↓
Kafka
    ↓
Spark
    ↓
PostgreSQL
    ├── trips
    ├── hourly_demand
    └── predictions
          ↑
          │
hourly_demand
    ↓
Feature Engineering
    ↓
Machine Learning
    ↓
Random Forest
    ↓
predictions
    ↓
Dashboard
```

TV2 không thay đổi pipeline Kafka/Spark của TV1.

------------------------------------------------------------------------

## 3. Dữ liệu đầu vào

Dataset chính:

``` text
data/processed/citibike_2026_H1.csv
```

Phạm vi:

``` text
2026-01-01 → 2026-06-30
```

Tổng:

``` text
415,708 trips
```

Sau tích hợp, Feature Engineering không còn lấy nguồn chính từ CSV mà
đọc:

``` text
PostgreSQL.hourly_demand
```

Dashboard đọc:

``` text
PostgreSQL.trips
PostgreSQL.predictions
```

------------------------------------------------------------------------

## 4. Feature Engineering

File:

``` text
analysis/feature_engineering/01_create_ml_dataset.py
```

Features:

``` text
hour
day_of_week
month
lag_1
lag_24
lag_168
rolling_24h
rolling_7d
```

Target:

``` text
total_trips
```

PostgreSQL có:

``` text
4,254 hourly_demand records
```

H1 2026 có:

``` text
181 × 24 = 4,344 giờ
```

Feature Engineering tạo full timeline 4,344 giờ và điền `demand = 0` cho
các giờ không có trip.

Do sử dụng `lag_168`, sau warm-up còn:

``` text
4,176 ML rows
```

Khoảng thời gian:

``` text
2026-01-08 00:00
→
2026-06-30 23:00
```

------------------------------------------------------------------------

## 5. Data Split

Chia theo thời gian, không shuffle.

``` text
Train
3,456 rows
2026-01-08 → 2026-05-31

Validation
360 rows
2026-06-01 → 2026-06-15

Test
360 rows
2026-06-16 → 2026-06-30
```

Đã xác nhận:

``` text
Train end < Validation start
Validation end < Test start
```

------------------------------------------------------------------------

## 6. Feature Leakage Check

File:

``` text
analysis/ml/00_check_feature_leakage.py
```

Kết quả:

``` text
RESULT: PASS
No feature leakage detected.
```

Đã kiểm tra:

``` text
lag_1
lag_24
lag_168
rolling_24h
rolling_7d
```

------------------------------------------------------------------------

## 7. Machine Learning

### Linear Regression

``` text
Validation MAE = 28.5756
Test MAE       = 28.2812
Test R²        = 0.8530
```

### Random Forest

``` text
Validation MAE = 22.1037
Test MAE       = 24.8594
Test R²        = 0.8789
```

Random Forest là model chính.

Parameters:

``` python
RandomForestRegressor(
    n_estimators=200,
    max_depth=15,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)
```

### Gradient Boosting

``` text
Validation MAE = 40.0635
Test MAE       = 32.2233
Test R²        = 0.8270
```

------------------------------------------------------------------------

## 8. Prediction

Historical prediction hiện tại:

``` text
2026-01-08 → 2026-06-30
```

Số prediction:

``` text
4,176
```

File lưu PostgreSQL:

``` text
analysis/ml/07_save_predictions_to_postgres.py
```

Model:

``` text
model_name    = Random Forest
model_version = 1.0
```

Script chỉ xóa prediction của đúng `model_name + model_version` trước
khi insert lại.

Đã kiểm tra chạy lại:

``` text
Deleted old predictions = 4,176
Inserted predictions    = 4,176
Final predictions       = 4,176
```

Không bị duplicate.

------------------------------------------------------------------------

## 9. Dashboard

Dashboard hiện lấy dữ liệu chính từ PostgreSQL.

``` text
trips
  ↓
load_raw_data()
  ↓
KPI / Filter / Hourly / Daily /
Member / Bike / Station
```

``` text
predictions
  ↓
load_prediction_data()
  ↓
Actual vs Predicted
```

Model metrics vẫn lấy từ:

``` text
analysis/outputs/ml/dashboard_model_metrics.csv
```

KPI đã kiểm tra:

``` text
Total Trips       = 415,708
Avg Trips / Day   = 2,297
Peak Hour          = 17:00
Peak Hour Trips    = 41,689
Test MAE           = 24.86
```

Filter đã kiểm tra:

``` text
Member   = 322,484
Casual   = 93,224
Electric = 267,614
Classic  = 148,094
```

------------------------------------------------------------------------

## 10. Prediction Filter

Model hiện tại dự đoán tổng demand, không dự đoán riêng
Member/Casual/Electric/Classic.

Vì vậy:

``` text
User = All + Bike = All
→ Actual + Prediction

User = Member/Casual
→ Actual only

Bike = Electric/Classic
→ Actual only
```

Date Range vẫn cho phép hiển thị prediction.

------------------------------------------------------------------------

## 11. File TV2 / Integration chính

``` text
analysis/feature_engineering/01_create_ml_dataset.py
analysis/ml/07_save_predictions_to_postgres.py

database/__init__.py
database/postgres.py

dashboard/app.py
dashboard/config.py
dashboard/services/data_loader.py

requirements.txt
```

Output ML:

``` text
analysis/outputs/ml/dashboard_prediction_full.csv
analysis/outputs/ml/random_forest_metrics.csv
analysis/outputs/ml/random_forest_predictions.csv
```

------------------------------------------------------------------------

## 12. Dependency mới

``` text
psycopg2-binary
python-dotenv
```

`.env` không được commit.

Máy TV2 hiện dùng:

``` text
Windows PostgreSQL: localhost:5432
Citi Bike Docker PostgreSQL: localhost:5433
```

Spark trong Docker vẫn dùng:

``` text
citibike-postgres:5432
```

------------------------------------------------------------------------

## 13. Lưu ý bàn giao

Không chạy lại Producer/Spark nếu không cần.

Không chạy:

``` text
docker compose down -v
```

nếu muốn giữ PostgreSQL volume.

Không hard-code host port PostgreSQL vào code dùng chung.

Phần integration hiện tại đã hoàn thành.

Phần tiếp theo:

``` text
Future Forecast
```

Chi tiết nằm trong:

``` text
docs/FUTURE_FORECAST_HANDOVER.md
```

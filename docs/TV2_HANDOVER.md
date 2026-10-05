# TV2 HANDOVER

## 1. Phạm vi bàn giao

TV2 phụ trách:

- Data Analysis.
- Feature Engineering.
- Machine Learning.
- Prediction.
- Dashboard.
- Tích hợp phần TV2 với PostgreSQL do TV1 xây dựng.

Trạng thái hiện tại:

| Thành phần | Trạng thái |
|---|---|
| Feature Engineering | Hoàn thành |
| Train / Validation / Test Split | Hoàn thành |
| Feature Leakage Check | Hoàn thành |
| Linear Regression | Hoàn thành |
| Random Forest | Hoàn thành |
| Gradient Boosting | Hoàn thành |
| Model Comparison | Hoàn thành |
| Historical Prediction | Hoàn thành |
| Prediction → PostgreSQL | Hoàn thành |
| PostgreSQL → Dashboard | Hoàn thành |
| Dashboard Filter / KPI | Hoàn thành |
| Future Forecast | Chưa làm |

---

## 2. Luồng hệ thống sau tích hợp

```text
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

Sau khi tích hợp:

- `trips` được Dashboard sử dụng cho dữ liệu thực tế, KPI và Filter.
- `hourly_demand` được TV2 sử dụng cho Feature Engineering và Machine Learning.
- `predictions` lưu kết quả dự đoán của Random Forest.
- Dashboard đọc dữ liệu chính từ PostgreSQL.

---

# 3. Dữ liệu đầu vào

Dataset chính:

```text
data/processed/citibike_2026_H1.csv
```

Phạm vi:

```text
2026-01-01
→
2026-06-30
```

Tổng:

```text
415,708 trips
```

Sau tích hợp, Feature Engineering không còn lấy nguồn dữ liệu chính trực tiếp từ CSV mà đọc:

```text
PostgreSQL.hourly_demand
```

Dashboard đọc:

```text
PostgreSQL.trips
PostgreSQL.predictions
```

---

# 4. PostgreSQL được TV2 sử dụng

Database:

```text
citibike
```

Các bảng chính:

```text
trips
hourly_demand
predictions
```

## 4.1. `trips`

Dữ liệu hiện tại:

```text
415,708 records
```

Thống kê:

```text
Member   = 322,484
Casual   = 93,224

Electric = 267,614
Classic  = 148,094
```

Dashboard sử dụng bảng này để tính:

```text
Total Trips
Avg Trips / Day
Peak Hour
Peak Hour Trips
Demand by Hour
Demand by Day
Member vs Casual
Bike Type
Top Stations
```

và các Filter:

```text
Date Range
User Type
Bike Type
```

---

## 4.2. `hourly_demand`

Dữ liệu:

```text
4,254 records
```

Khoảng thời gian:

```text
2026-01-01 00:00
→
2026-06-30 23:00
```

Đã kiểm tra:

```text
SUM(demand)         = 415,708
SUM(member_count)   = 322,484
SUM(casual_count)   = 93,224
SUM(electric_count) = 267,614
SUM(classic_count)  = 148,094
```

TV2 sử dụng bảng này làm nguồn cho Feature Engineering.

---

## 4.3. `predictions`

Bảng chứa kết quả prediction của Machine Learning.

Schema chính:

```text
id
prediction_time
target_time
predicted_demand
actual_demand
model_name
model_version
```

Historical prediction hiện tại:

```text
model_name    = Random Forest
model_version = 1.0
```

Số lượng:

```text
4,176 predictions
```

Khoảng thời gian:

```text
2026-01-08 00:00
→
2026-06-30 23:00
```

---

# 5. Database Python Layer

TV2 bổ sung:

```text
database/
├── __init__.py
└── postgres.py
```

`database/__init__.py` có thể để trống.

`database/postgres.py` hiện cung cấp:

```text
get_connection()
load_hourly_demand()
save_predictions()
load_predictions()
load_dashboard_trips()
```

Mục đích của layer này là tách phần kết nối PostgreSQL khỏi:

```text
Feature Engineering
Machine Learning
Dashboard
```

để các phần trên không cần tự viết lại code kết nối database.

---

# 6. Feature Engineering

File:

```text
analysis/feature_engineering/01_create_ml_dataset.py
```

Luồng hiện tại:

```text
PostgreSQL.hourly_demand
        ↓
Create Full Hourly Timeline
        ↓
Fill Missing Demand = 0
        ↓
Feature Engineering
        ↓
ML Dataset
```

Features:

```text
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

```text
total_trips
```

---

## 6.1. Full Hourly Timeline

PostgreSQL có:

```text
4,254 hourly_demand records
```

H1 2026 có:

```text
181 ngày × 24 giờ
=
4,344 giờ
```

Do đó có:

```text
4,344 - 4,254
=
90 giờ
```

không có chuyến đi.

Feature Engineering tạo lại full timeline:

```text
4,344 hourly rows
```

và điền:

```text
total_trips = 0
```

cho các giờ không có trip.

---

## 6.2. Warm-up

Feature lớn nhất:

```text
lag_168
```

cần 168 giờ lịch sử.

Do đó:

```text
4,344
-
168
=
4,176 ML rows
```

ML Dataset cuối:

```text
4,176 rows
```

Khoảng thời gian:

```text
2026-01-08 00:00
→
2026-06-30 23:00
```

Output:

```text
analysis/outputs/ml/citibike_ml_dataset.csv
```

---

## 6.3. Day of Week

`day_of_week` trong ML được tính lại bằng Pandas để giữ convention:

```text
Monday    = 0
Tuesday   = 1
Wednesday = 2
Thursday  = 3
Friday    = 4
Saturday  = 5
Sunday    = 6
```

Không sử dụng trực tiếp convention `dayofweek` của Spark cho feature ML.

---

# 7. Train / Validation / Test Split

Dữ liệu được chia theo thời gian.

Không shuffle.

## Train

```text
3,456 rows

2026-01-08 00:00
→
2026-05-31 23:00
```

## Validation

```text
360 rows

2026-06-01 00:00
→
2026-06-15 23:00
```

## Test

```text
360 rows

2026-06-16 00:00
→
2026-06-30 23:00
```

Đã xác nhận:

```text
Train end < Validation start

Validation end < Test start
```

---

# 8. Feature Leakage Check

File:

```text
analysis/ml/00_check_feature_leakage.py
```

Kết quả:

```text
RESULT: PASS

No feature leakage detected.
```

Đã kiểm tra:

```text
lag_1
lag_24
lag_168
rolling_24h
rolling_7d
```

Rolling Features sử dụng dữ liệu quá khứ thông qua:

```text
shift(1)
```

để tránh sử dụng demand của chính thời điểm đang cần dự đoán.

---

# 9. Machine Learning

Ba model đã được huấn luyện và đánh giá.

---

## 9.1. Linear Regression

Validation:

```text
MAE  = 28.5756
RMSE = 39.5162
R²   = 0.8724
```

Test:

```text
MAE  = 28.2812
RMSE = 39.8107
R²   = 0.8530
```

---

## 9.2. Random Forest

Random Forest là model chính hiện tại.

Validation:

```text
MAE  = 22.1037
RMSE = 32.1959
R²   = 0.9153
```

Test:

```text
MAE  = 24.8594
RMSE = 36.1243
R²   = 0.8789
```

Parameters:

```python
RandomForestRegressor(
    n_estimators=200,
    max_depth=15,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)
```

---

## 9.3. Gradient Boosting

Validation:

```text
MAE  = 40.0635
RMSE = 50.7503
R²   = 0.7895
```

Test:

```text
MAE  = 32.2233
RMSE = 43.1804
R²   = 0.8270
```

---

## 9.4. Model được chọn

Model tốt nhất:

```text
Random Forest
```

Kết quả Test:

```text
MAE = 24.8594
R²  = 0.8789
```

---

# 10. Historical Prediction

Prediction hiện tại là:

```text
Historical / Offline Prediction
```

Khoảng thời gian:

```text
2026-01-08
→
2026-06-30
```

Số lượng:

```text
4,176 predictions
```

Actual Demand của khoảng thời gian này đã tồn tại.

Do đó có thể so sánh:

```text
Actual
vs
Predicted
```

Prediction hiện tại **chưa phải Future Forecast**.

---

# 11. Lưu Prediction vào PostgreSQL

File:

```text
analysis/ml/07_save_predictions_to_postgres.py
```

Nguồn:

```text
analysis/outputs/ml/dashboard_prediction_full.csv
```

Mapping:

```text
datetime
→ target_time

predicted_demand
→ predicted_demand

total_trips
→ actual_demand

Random Forest
→ model_name

1.0
→ model_version
```

---

## 11.1. Chống Duplicate

Trước khi insert, script xóa prediction cũ của đúng:

```text
model_name
+
model_version
```

Sau đó insert prediction mới.

Đã kiểm tra chạy lại:

```text
Deleted old predictions = 4,176

Inserted predictions = 4,176
```

Sau khi chạy lại:

```text
COUNT(*) = 4,176
```

Không bị duplicate.

---

# 12. Dashboard

Các file chính:

```text
dashboard/
├── app.py
├── config.py
├── components/
│   ├── charts.py
│   └── kpi.py
└── services/
    └── data_loader.py
```

---

## 12.1. Dashboard Data Flow

Actual Data:

```text
PostgreSQL.trips
        ↓
load_raw_data()
        ↓
Filter
        ↓
KPI
        ↓
Charts
```

Prediction:

```text
PostgreSQL.predictions
        ↓
load_prediction_data()
        ↓
Actual vs Predicted
```

Model Metrics:

```text
dashboard_model_metrics.csv
        ↓
load_model_metrics()
        ↓
Test MAE
Model Comparison
```

---

## 12.2. CSV cũ

Dashboard không còn cần load trực tiếp:

```text
dashboard_hourly_demand.csv
dashboard_daily_demand.csv
member type CSV
bike type CSV
top station CSV
```

Các CSV ML Output vẫn được giữ như artifact của quá trình Machine Learning.

---

# 13. Dashboard KPI

Kết quả toàn H1 2026:

```text
Total Trips
415,708

Avg Trips / Day
2,297

Peak Hour
17:00

Peak Hour Trips
41,689

Test MAE
24.86
```

---

## 13.1. Avg Trips / Day

H1 2026:

```text
181 calendar days
```

Có một ngày không có trip.

Average được tính:

```text
415,708 / 181
≈
2,297
```

Không sử dụng 180 active days để tính KPI này.

---

## 13.2. Peak Hour

Peak Hour:

```text
17:00
```

Tổng trips của giờ 17 trên toàn H1:

```text
41,689
```

Giá trị cũ:

```text
4,868
```

chỉ thuộc Test Period 15 ngày, không phải toàn H1.

---

# 14. Dashboard Filter

Các Filter:

```text
Date Range
User Type
Bike Type
```

Đã kiểm tra:

```text
User = Member
Total Trips = 322,484
```

```text
User = Casual
Total Trips = 93,224
```

```text
Bike = Electric
Total Trips = 267,614
```

```text
Bike = Classic
Total Trips = 148,094
```

Tất cả đã PASS.

---

# 15. Prediction khi sử dụng Filter

Random Forest hiện tại dự đoán:

```text
TOTAL HOURLY DEMAND
```

Model không dự đoán riêng:

```text
Member Demand
Casual Demand
Electric Demand
Classic Demand
```

Do đó Dashboard sử dụng quy tắc:

| User Filter | Bike Filter | Prediction |
|---|---|---|
| All | All | Hiển thị |
| Member | All | Ẩn |
| Casual | All | Ẩn |
| All | Electric | Ẩn |
| All | Classic | Ẩn |
| Member/Casual | Electric/Classic | Ẩn |

Date Range không làm ẩn Prediction.

Mục đích là tránh trường hợp so sánh sai:

```text
Actual Member Demand
vs
Predicted Total Demand
```

---

# 16. File TV2 / Integration chính

Các file code chính:

```text
analysis/feature_engineering/01_create_ml_dataset.py

analysis/ml/07_save_predictions_to_postgres.py

database/__init__.py
database/postgres.py

dashboard/app.py
dashboard/config.py
dashboard/services/data_loader.py

requirements.txt
```

ML Output được sinh lại:

```text
analysis/outputs/ml/dashboard_prediction_full.csv

analysis/outputs/ml/random_forest_metrics.csv

analysis/outputs/ml/random_forest_predictions.csv
```

---

# 17. Dependency mới

TV2 bổ sung:

```text
psycopg2-binary
python-dotenv
```

Các package này đã được thêm vào:

```text
requirements.txt
```

---

# 18. Cấu hình PostgreSQL

Máy TV2 hiện có PostgreSQL Windows sử dụng:

```text
localhost:5432
```

Do đó PostgreSQL Docker của Citi Bike được map:

```text
localhost:5433
→
container:5432
```

`.env` trên máy TV2:

```env
POSTGRES_DB=citibike
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_PORT=5433

KAFKA_PORT=9092

SPARK_MASTER_PORT=7077
SPARK_UI_PORT=8080
```

`.env` đã được Git ignore.

Không hard-code:

```text
5433
```

vào code dùng chung.

TV1 có thể sử dụng:

```text
5432
```

hoặc port phù hợp với máy TV1.

Spark bên trong Docker vẫn kết nối:

```text
citibike-postgres:5432
```

Host Port không ảnh hưởng kết nối nội bộ Docker.

---

# 19. TV1 cần biết gì sau khi pull code TV2

Sau khi pull phiên bản tích hợp của TV2, TV1 **không cần chạy lại toàn bộ Kafka → Spark pipeline** nếu PostgreSQL hiện tại đã có dữ liệu đúng.

---

## 19.1. Cài Dependency

Sau khi pull:

```powershell
pip install -r requirements.txt
```

Dependency TV2 bổ sung:

```text
psycopg2-binary
python-dotenv
```

---

## 19.2. Kiểm tra `.env`

`.env` không được commit lên Git.

TV1 cần tự cấu hình `.env` theo môi trường máy đang chạy.

Ví dụ nếu Docker PostgreSQL sử dụng port mặc định:

```env
POSTGRES_DB=citibike
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_PORT=5432
```

Nếu `5432` đã bị chương trình PostgreSQL khác sử dụng thì có thể map Docker sang port khác, ví dụ:

```env
POSTGRES_PORT=5433
```

Không hard-code port này vào Python.

---

## 19.3. Kiểm tra PostgreSQL Connection

Chạy:

```powershell
python -c "from database.postgres import get_connection; conn=get_connection(); print('POSTGRES CONNECTION OK'); conn.close()"
```

Kết quả mong đợi:

```text
POSTGRES CONNECTION OK
```

Nếu lỗi ở bước này thì kiểm tra:

```text
Docker PostgreSQL
.env
POSTGRES_PORT
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
```

trước khi chạy Feature Engineering hoặc Dashboard.

---

## 19.4. Kiểm tra `hourly_demand`

Chạy:

```powershell
python -c "from database.postgres import load_hourly_demand; df=load_hourly_demand(); print('Rows:', len(df)); print('Total demand:', df['demand'].sum())"
```

Kết quả mong đợi:

```text
Rows: 4254

Total demand: 415708
```

Nếu hai giá trị này đúng thì luồng:

```text
TV1 PostgreSQL
→
TV2 Feature Engineering
```

đang hoạt động đúng.

---

## 19.5. Kiểm tra dữ liệu Dashboard

Chạy:

```powershell
python -c "from database.postgres import load_dashboard_trips; df=load_dashboard_trips(); print('Rows:', len(df)); print(df.head())"
```

Kết quả mong đợi:

```text
Rows: 415708
```

Các cột cần có:

```text
started_at
ended_at
member_casual
rideable_type
start_station_id
```

---

## 19.6. Kiểm tra Prediction

PostgreSQL hiện tại cần có:

```text
Random Forest

model_version = 1.0

4,176 historical predictions
```

Nếu cần tạo lại Prediction từ ML Output:

```powershell
python analysis/ml/07_save_predictions_to_postgres.py
```

Kết quả mong đợi:

```text
Inserted predictions: 4176
```

Nếu đã tồn tại prediction cũ:

```text
Deleted old predictions: 4176

Inserted predictions: 4176
```

Đây là hành vi bình thường.

Script chỉ xóa prediction của đúng:

```text
model_name
+
model_version
```

nên chạy lại không làm nhân đôi Historical Prediction.

---

## 19.7. Chạy Dashboard

Chạy:

```powershell
streamlit run dashboard/app.py
```

Kết quả toàn H1 cần khớp:

```text
Total Trips       = 415,708

Avg Trips / Day   = 2,297

Peak Hour          = 17:00

Peak Hour Trips    = 41,689

Test MAE           = 24.86
```

---

## 19.8. Kiểm tra Filter

### Member

```text
User Type = Member

Total Trips = 322,484
```

### Casual

```text
User Type = Casual

Total Trips = 93,224
```

### Electric

```text
Bike Type = Electric

Total Trips = 267,614
```

### Classic

```text
Bike Type = Classic

Total Trips = 148,094
```

Khi sử dụng User Type hoặc Bike Type Filter:

```text
Prediction phải được ẩn.
```

Dashboard sẽ thông báo Prediction hiện chỉ áp dụng cho tổng nhu cầu.

---

## 19.9. TV1 không cần chạy lại

Nếu PostgreSQL đã có:

```text
trips = 415,708

hourly_demand = 4,254
```

thì không cần chạy lại:

```text
Kafka Producer

Spark Streaming

Spark Aggregation
```

chỉ để kiểm tra phần TV2.

---

## 19.10. Không xóa PostgreSQL Volume

Không chạy:

```powershell
docker compose down -v
```

nếu muốn giữ database hiện tại.

`-v` có thể xóa PostgreSQL Volume.

Nếu chỉ cần dừng container, sử dụng:

```powershell
docker compose stop
```

hoặc lệnh phù hợp với tình trạng hệ thống hiện tại.

---

# 20. Trạng thái Integration hiện tại

```text
Giai đoạn 1
TV1 Kafka / Spark / PostgreSQL
DONE

Giai đoạn 2
PostgreSQL → TV2
DONE

Giai đoạn 3
Feature Engineering
DONE

Giai đoạn 4
Machine Learning
DONE

Giai đoạn 5
ML → PostgreSQL Predictions
DONE

Giai đoạn 6
PostgreSQL → Dashboard
DONE

Giai đoạn 7
Dashboard Filter / KPI
DONE

Giai đoạn 8
Historical Prediction
DONE

Giai đoạn 9
Future Forecast
NOT IMPLEMENTED
```

---

# 21. Phần chưa làm

Phần chính tiếp theo:

```text
Future Forecast
```

Prediction hiện tại chỉ là:

```text
Historical / Offline Prediction
```

Không được gọi Historical Prediction hiện tại là Future Forecast.

Chi tiết kế hoạch Future Forecast nằm trong:

```text
docs/FUTURE_FORECAST_HANDOVER.md
```

---

# 22. Lưu ý khi tiếp tục phát triển

Không chạy lại Producer nếu không cần thiết.

Không chạy Spark Streaming/Aggregation lại chỉ để làm ML hoặc Dashboard.

Không chạy:

```text
docker compose down -v
```

nếu cần giữ PostgreSQL.

Không commit:

```text
.env
```

Không hard-code:

```text
PostgreSQL Port
Password
Host configuration
```

Không thay Historical Prediction bằng Future Forecast.

Future Forecast nên được phát triển thành chức năng riêng.

---

# 23. Các tài liệu bàn giao TV2

TV2 bàn giao ba tài liệu:

```text
docs/
├── TV2_HANDOVER.md
├── ML_DATA_DICTIONARY.md
└── FUTURE_FORECAST_HANDOVER.md
```

### `TV2_HANDOVER.md`

Mô tả:

```text
Feature Engineering
Machine Learning
PostgreSQL Integration
Dashboard Integration
Testing
Cách TV1 kiểm tra sau khi pull
```

### `ML_DATA_DICTIONARY.md`

Mô tả:

```text
trips
hourly_demand
ML Dataset
predictions
Historical Prediction
Future Prediction Data Convention
```

### `FUTURE_FORECAST_HANDOVER.md`

Mô tả:

```text
Trạng thái trước Future Forecast
Recursive Forecasting
PostgreSQL Future Prediction
Dashboard Future Forecast
Các bước triển khai tiếp theo
```

---

# 24. Checkpoint bàn giao

Tại thời điểm bàn giao:

```text
Dataset
415,708 trips
```

```text
PostgreSQL.trips
415,708 records
```

```text
PostgreSQL.hourly_demand
4,254 records
```

```text
ML Dataset
4,176 records
```

```text
PostgreSQL.predictions
4,176 historical predictions
```

Random Forest:

```text
Test MAE = 24.8594

Test R² = 0.8789
```

Dashboard:

```text
Total Trips       = 415,708
Avg Trips / Day   = 2,297
Peak Hour          = 17:00
Peak Hour Trips    = 41,689
Test MAE           = 24.86
```

---

# 25. Kết luận bàn giao

Phần tích hợp:

```text
TV1 Data Engineering
        +
TV2 Data Analysis / ML / Dashboard
```

đã hoàn thành.

Luồng hệ thống hiện tại:

```text
Citi Bike Dataset
        ↓
      Kafka
        ↓
      Spark
        ↓
   PostgreSQL
        ↓
Feature Engineering
        ↓
 Machine Learning
        ↓
Random Forest Prediction
        ↓
   PostgreSQL
        ↓
    Dashboard
```

Checkpoint hiện tại có thể được sử dụng làm phiên bản ổn định trước khi phát triển:

```text
Future Forecast
```

Giai đoạn tiếp theo nên bắt đầu từ:

```text
FUTURE_FORECAST_HANDOVER.md
```

và không cần xây dựng lại pipeline Kafka/Spark/PostgreSQL hiện tại nếu dữ liệu vẫn còn đầy đủ và các kiểm tra Integration ở trên đều PASS.
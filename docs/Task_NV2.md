# TASK — THÀNH VIÊN 2

## Data Analysis + Machine Learning

**Dự án:** Citi Bike Demand Analysis & Prediction
**Vai trò:** Thành viên 2 — Data Analysis + Machine Learning
**Dataset:** `data/processed/citibike_2026_H1.csv`
**Thời gian dữ liệu:** 01/01/2026 → 30/06/2026
**Tổng số chuyến:** 415,708

---

# 1. Mục tiêu

Xây dựng toàn bộ phần **phân tích nhu cầu sử dụng xe đạp và mô hình dự báo nhu cầu**, đồng thời chuẩn bị dữ liệu phục vụ Dashboard.

Phần công việc của NV2 gồm:

* Tìm hiểu và kiểm tra dataset chính thức.
* Phân tích nhu cầu theo thời gian.
* Phân tích Member/Casual.
* Phân tích station.
* Xây dựng feature cho Machine Learning.
* Xây dựng và đánh giá các mô hình dự báo.
* Sinh kết quả dự báo.
* Chuẩn bị dữ liệu cho Dashboard.
* Xây dựng Dashboard.
* Phối hợp tích hợp Dashboard với hệ thống của NV1.

---

# 2. Tiến độ tổng quan

| STT | Nhiệm vụ                              |    Trạng thái    |
| --: | ------------------------------------- | :--------------: |
|   1 | Làm quen dataset chính thức           |   ✅ Hoàn thành   |
|   2 | Phân tích nhu cầu theo thời gian      |   ✅ Hoàn thành   |
|   3 | Phân tích theo giờ/ngày/tháng         |   ✅ Hoàn thành   |
|   4 | Phân tích Member/Casual               |   ✅ Hoàn thành   |
|   5 | Phân tích Station                     |   ✅ Hoàn thành   |
|   6 | Feature Engineering                   |   ✅ Hoàn thành   |
|   7 | Xây dựng mô hình dự báo               |   ✅ Hoàn thành   |
|   8 | Đánh giá mô hình                      |   ✅ Hoàn thành   |
|   9 | Sinh bảng kết quả dự báo              |   ✅ Hoàn thành   |
|  10 | Chuẩn bị dữ liệu cho Dashboard        |   ✅ Hoàn thành   |
|  11 | Xây dựng Dashboard                    | ⏳ Đang thực hiện |
|  12 | Tích hợp Dashboard với hệ thống chung |  ⏳ Chờ tích hợp  |
|  13 | Kiểm thử và hoàn thiện                | ⏳ Chưa thực hiện |
|  14 | Hỗ trợ báo cáo và Demo                | ⏳ Chưa thực hiện |

> **Tiến độ nhiệm vụ Data Analysis + Machine Learning: 10/10 nhiệm vụ cốt lõi đã hoàn thành.**

---

# 3. Dataset chính thức

Dataset được tạo từ 6 file dữ liệu Citi Bike:

```text
JC-202601-citibike-tripdata.csv
JC-202602-citibike-tripdata.csv
JC-202603-citibike-tripdata.csv
JC-202604-citibike-tripdata.csv
JC-202605-citibike-tripdata.csv
JC-202606-citibike-tripdata.csv
```

Dataset chính thức:

```text
data/processed/citibike_2026_H1.csv
```

## Thông tin dataset

```text
Số dòng: 415,708
Thời gian: 2026-01-01 → 2026-06-30
Số cột: 13
Duplicate ride_id: 0
Invalid started_at: 0
Invalid ended_at: 0
```

## Các cột

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

# 4. Data Understanding

## Script

```text
scripts/inspect_official_dataset.py
```

## Nội dung đã thực hiện

* Kiểm tra số lượng bản ghi.
* Kiểm tra số lượng cột.
* Kiểm tra kiểu dữ liệu.
* Kiểm tra khoảng thời gian.
* Kiểm tra duplicate `ride_id`.
* Kiểm tra missing values.
* Kiểm tra dữ liệu thời gian không hợp lệ.
* Phân tích loại xe.
* Phân tích Member/Casual.
* Phân tích thời lượng chuyến đi.
* Phân tích theo tháng, ngày, giờ và station.

## Một số kết quả

### Member/Casual

```text
Member: 322,484 — 77.57%
Casual: 93,224 — 22.43%
```

### Bike type

```text
Electric bike: 267,614 — 64.38%
Classic bike: 148,094 — 35.62%
```

---

# 5. Exploratory Data Analysis

## Thư mục

```text
analysis/eda/
├── 01_data_overview.py
├── 02_time_analysis.py
├── 03_user_analysis.py
├── 04_bike_analysis.py
└── 05_station_analysis.py
```

## 5.1. Phân tích nhu cầu theo thời gian

Đã phân tích:

* Tổng số chuyến theo tháng.
* Tổng số chuyến theo ngày.
* Tổng số chuyến theo giờ.
* Ngày trong tuần.

### Theo tháng

| Tháng    |   Trips |
| -------- | ------: |
| January  |  40,037 |
| February |  25,808 |
| March    |  62,362 |
| April    |  82,272 |
| May      |  95,341 |
| June     | 109,888 |

### Theo giờ

Giờ có nhu cầu cao nhất:

```text
17:00
41,689 trips
```

### Theo ngày trong tuần

Ngày có nhiều chuyến nhất:

```text
Friday — 66,587 trips
```

Ngày có ít chuyến nhất:

```text
Sunday — 47,942 trips
```

---

# 6. Member/Casual Analysis

Đã phân tích nhu cầu của:

* Member.
* Casual.

Phân tích theo:

* Giờ.
* Ngày trong tuần.

### Kết quả chính

Member:

```text
77.57%
```

Casual:

```text
22.43%
```

Cả Member và Casual đều có nhu cầu cao nhất vào khoảng:

```text
17:00
```

---

# 7. Bike Analysis

Đã phân tích:

* Electric bike.
* Classic bike.
* Nhu cầu theo giờ.
* Nhu cầu theo ngày trong tuần.

### Kết quả

```text
Electric bike: 64.38%
Classic bike: 35.62%
```

---

# 8. Station Analysis

Đã phân tích:

* Top station theo lượt bắt đầu.
* Top station theo lượt kết thúc.
* So sánh hoạt động start/end.
* Tổng hoạt động station.

## Output

```text
analysis/outputs/tables/
├── station_top_10_start.csv
├── station_top_10_end.csv
└── station_start_end_comparison.csv
```

## Figures

```text
analysis/outputs/figures/
├── station_top_10_activity.png
├── station_top_10_start.png
└── station_top_10_end.png
```

Station có hoạt động cao nhất:

```text
JC115 – Grove St PATH
```

---

# 9. Feature Engineering

## Thư mục

```text
analysis/feature_engineering/
├── 01_create_ml_dataset.py
└── 02_split_ml_dataset.py
```

## Target

```text
total_trips
```

## Features

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

## Ý nghĩa

| Feature       | Ý nghĩa                         |
| ------------- | ------------------------------- |
| `hour`        | Giờ trong ngày                  |
| `day_of_week` | Ngày trong tuần                 |
| `month`       | Tháng                           |
| `lag_1`       | Nhu cầu giờ trước               |
| `lag_24`      | Nhu cầu cùng giờ ngày trước     |
| `lag_168`     | Nhu cầu cùng giờ tuần trước     |
| `rolling_24h` | Trung bình nhu cầu 24 giờ trước |
| `rolling_7d`  | Trung bình nhu cầu 7 ngày trước |

Rolling features được tính dựa trên dữ liệu quá khứ để tránh sử dụng target của thời điểm cần dự báo.

---

# 10. ML Dataset

Output:

```text
analysis/outputs/ml/citibike_ml_dataset.csv
```

Kết quả:

```text
Rows: 4,176
Missing values: 0
```

Khoảng thời gian:

```text
2026-01-08 00:00
→
2026-06-30 23:00
```

168 giờ đầu được loại bỏ do chưa đủ dữ liệu lịch sử cho các feature lag/rolling.

---

# 11. Train / Validation / Test

Sử dụng chronological split thay vì random split.

```text
Train:
2026-01-08 → 2026-05-31
3,456 rows

Validation:
2026-06-01 → 2026-06-15
360 rows

Test:
2026-06-16 → 2026-06-30
360 rows
```

## Output

```text
analysis/outputs/ml/
├── train.csv
├── validation.csv
└── test.csv
```

---

# 12. Leakage Check

Script:

```text
analysis/ml/00_check_feature_leakage.py
```

Kết quả:

```text
Lag features correct: True
Rolling features correct: True
Time order correct: True

RESULT: PASS
No feature leakage detected.
```

Feature leakage không được phát hiện.

---

# 13. Machine Learning Models

Đã xây dựng 3 mô hình:

```text
analysis/ml/
├── 01_linear_regression.py
├── 02_random_forest.py
└── 03_gradient_boosting.py
```

## 13.1. Linear Regression

Test:

```text
MAE  = 28.2812
RMSE = 39.8107
R²   = 0.8530
```

## 13.2. Random Forest

Test:

```text
MAE  = 24.8594
RMSE = 36.1243
R²   = 0.8789
```

## 13.3. Gradient Boosting

Test:

```text
MAE  = 32.2233
RMSE = 43.1804
R²   = 0.8270
```

---

# 14. So sánh mô hình

Script:

```text
analysis/ml/04_model_comparison.py
```

Output:

```text
analysis/outputs/ml/model_comparison.csv
```

## Kết quả tập Test

| Model             |         MAE |        RMSE |         R² |
| ----------------- | ----------: | ----------: | ---------: |
| Linear Regression |     28.2812 |     39.8107 |     0.8530 |
| Random Forest     | **24.8594** | **36.1243** | **0.8789** |
| Gradient Boosting |     32.2233 |     43.1804 |     0.8270 |

Trong ba mô hình và cấu hình đã thử nghiệm, **Random Forest được sử dụng làm mô hình chính cho bước dự báo tiếp theo**.

---

# 15. Prediction

Script:

```text
analysis/ml/05_prediction_analysis.py
```

Output:

```text
analysis/outputs/ml/random_forest_predictions.csv
```

Các thông tin được lưu:

```text
datetime
date
hour
day_of_week
month
total_trips
predicted_demand
model_name
error
absolute_error
```

## Kết quả

```text
MAE: 24.8594
RMSE: 36.1243
Mean Error: -1.2563
Maximum Absolute Error: 149.9178
```

Tập dự báo gồm:

```text
360 hourly prediction points
```

cho giai đoạn:

```text
2026-06-16 → 2026-06-30
```

---

# 16. Prediction Error Analysis

Đã phân tích sai số:

* Theo giờ.
* Theo ngày trong tuần.
* Sai số trung bình.
* Sai số tuyệt đối.
* Maximum absolute error.

## Output

```text
analysis/outputs/ml/
├── random_forest_error_summary.csv
├── random_forest_error_by_hour.csv
└── random_forest_error_by_day.csv
```

## Figures

```text
analysis/outputs/figures/
├── random_forest_actual_vs_predicted.png
├── random_forest_scatter.png
└── random_forest_error.png
```

Một kết quả đáng chú ý:

```text
17:00
MAE ≈ 62.83
```

Đây cũng là giờ có nhu cầu cao nhất trong EDA.

---

# 17. Chuẩn bị dữ liệu cho Dashboard

Script:

```text
analysis/ml/06_prepare_dashboard_data.py
```

## Output

```text
analysis/outputs/ml/
├── dashboard_prediction.csv
├── dashboard_hourly_demand.csv
├── dashboard_daily_demand.csv
└── dashboard_model_metrics.csv
```

## Mục đích

### `dashboard_prediction.csv`

Dùng cho:

```text
Actual vs Predicted Demand
```

### `dashboard_hourly_demand.csv`

Dùng cho:

```text
Nhu cầu theo giờ
```

### `dashboard_daily_demand.csv`

Dùng cho:

```text
Nhu cầu theo ngày
```

### `dashboard_model_metrics.csv`

Dùng cho:

```text
MAE
RMSE
R²
```

---

# 18. Dashboard

## Trạng thái

⏳ Đang thực hiện.

Dashboard dự kiến gồm:

```text
┌─────────────────────────────────────────────────────┐
│              CITIBIKE DEMAND DASHBOARD              │
├─────────────────────────────────────────────────────┤
│ Total Trips │ Avg Trips/Day │ Peak Hour │ Model MAE│
├─────────────────────────────────────────────────────┤
│       Actual vs Predicted Demand over Time          │
├──────────────────────────┬──────────────────────────┤
│ Nhu cầu theo giờ         │ Nhu cầu theo ngày       │
├──────────────────────────┴──────────────────────────┤
│ Member vs Casual                                    │
├──────────────────────────┬──────────────────────────┤
│ Electric / Classic       │ Top Stations            │
└──────────────────────────┴──────────────────────────┘
```

## KPI dự kiến

* Total Trips.
* Average Trips/Day.
* Peak Hour.
* Model MAE.

## Biểu đồ

* Actual vs Predicted Demand.
* Demand theo giờ.
* Demand theo ngày.
* Member vs Casual.
* Electric vs Classic.
* Top Stations.
* Model Metrics.

---

# 19. Tích hợp với TV1

Dashboard được phát triển theo hai giai đoạn.

## Giai đoạn hiện tại

Dashboard có thể sử dụng dữ liệu đã chuẩn bị:

```text
CSV
 ↓
Dashboard
```

Mục đích:

* Hoàn thiện giao diện.
* Kiểm tra biểu đồ.
* Kiểm tra KPI.
* Kiểm tra dữ liệu dự báo.

## Giai đoạn tích hợp

Sau khi TV1 hoàn thiện Data Engineering:

```text
CSV
 ↓
Kafka
 ↓
Spark
 ↓
PostgreSQL
 ↓
Dashboard
```

Hoặc thông qua API:

```text
PostgreSQL
 ↓
Backend/API
 ↓
Dashboard
```

Dashboard cần được thiết kế để có thể thay đổi nguồn dữ liệu mà không phải viết lại toàn bộ giao diện.

---

# 20. Phối hợp với TV1

NV2 cần thống nhất với NV1 về:

* Database PostgreSQL.
* Tên bảng.
* Tên cột.
* Kiểu dữ liệu.
* Cách truy vấn dữ liệu.
* Cách lấy dữ liệu dự báo.
* Cách Dashboard kết nối với PostgreSQL/API.

Không tự ý thay đổi schema hoặc kiến trúc chung.

---

# 21. Cấu trúc thư mục hiện tại

```text
analysis/
├── eda/
│   ├── 01_data_overview.py
│   ├── 02_time_analysis.py
│   ├── 03_user_analysis.py
│   ├── 04_bike_analysis.py
│   └── 05_station_analysis.py
│
├── feature_engineering/
│   ├── 01_create_ml_dataset.py
│   └── 02_split_ml_dataset.py
│
├── ml/
│   ├── 00_check_feature_leakage.py
│   ├── 01_linear_regression.py
│   ├── 02_random_forest.py
│   ├── 03_gradient_boosting.py
│   ├── 04_model_comparison.py
│   ├── 05_prediction_analysis.py
│   └── 06_prepare_dashboard_data.py
│
└── outputs/
    ├── figures/
    ├── tables/
    └── ml/
```

---

# 22. Việc cần làm tiếp theo

## Ưu tiên 1 — Dashboard

* [ ] Chốt framework Dashboard.
* [ ] Tạo cấu trúc Dashboard.
* [ ] Đọc dữ liệu từ các file Dashboard.
* [ ] Tạo KPI.
* [ ] Tạo biểu đồ nhu cầu theo giờ.
* [ ] Tạo biểu đồ nhu cầu theo ngày.
* [ ] Tạo Actual vs Predicted.
* [ ] Tạo Member/Casual.
* [ ] Tạo Electric/Classic.
* [ ] Tạo Top Stations.
* [ ] Hiển thị Model Metrics.
* [ ] Thêm bộ lọc nếu cần.

## Ưu tiên 2 — Tích hợp với TV1

* [ ] Thống nhất PostgreSQL schema.
* [ ] Kiểm tra dữ liệu TV1 đưa vào PostgreSQL.
* [ ] Xác định bảng Dashboard sử dụng.
* [ ] Thay nguồn CSV bằng PostgreSQL/API.
* [ ] Kiểm tra dữ liệu end-to-end.

## Ưu tiên 3 — Hoàn thiện

* [ ] Kiểm thử Dashboard.
* [ ] Kiểm tra số liệu Dashboard với EDA.
* [ ] Kiểm tra prediction với model output.
* [ ] Chuẩn bị hình ảnh cho báo cáo.
* [ ] Viết phần Data Analysis.
* [ ] Viết phần Machine Learning.
* [ ] Viết phần Dashboard.
* [ ] Chuẩn bị Demo.

---

# 23. Nguyên tắc làm việc

1. Dataset chính thức không được tự ý thay đổi.
2. Không chỉnh sửa thủ công dữ liệu raw.
3. Dataset processed phải có khả năng tái tạo từ raw.
4. Không tự ý thay đổi Kafka topic.
5. Không tự ý thay đổi PostgreSQL schema.
6. Không thay đổi kiến trúc chung nếu chưa thống nhất với nhóm.
7. Feature Engineering phải tránh data leakage.
8. Train/Validation/Test phải giữ đúng thứ tự thời gian.
9. Dashboard hiện tại có thể phát triển độc lập bằng CSV.
10. Khi TV1 hoàn thành pipeline, Dashboard phải có khả năng tích hợp vào hệ thống chung.
11. Không cần tạo thêm ML model nếu chưa có yêu cầu mới.
12. Random Forest hiện là model chính dựa trên kết quả của ba mô hình đã thử nghiệm.

---

# 24. Trạng thái hiện tại

```text
DATA UNDERSTANDING       ✅
EDA                      ✅
TIME ANALYSIS            ✅
USER ANALYSIS            ✅
STATION ANALYSIS         ✅
FEATURE ENGINEERING      ✅
DATA SPLIT               ✅
LEAKAGE CHECK            ✅
LINEAR REGRESSION        ✅
RANDOM FOREST            ✅
GRADIENT BOOSTING        ✅
MODEL COMPARISON         ✅
MODEL EVALUATION         ✅
PREDICTION               ✅
DASHBOARD DATA           ✅

DASHBOARD UI             ⏳
TV1 INTEGRATION          ⏳
FINAL TESTING            ⏳
REPORT                   ⏳
DEMO                     ⏳
```

## Kết luận tiến độ

**Phần Data Analysis + Machine Learning cốt lõi của Thành viên 2 đã hoàn thành 10/10 nhiệm vụ.**

Công việc hiện tại chuyển sang:

```text
Dashboard
    ↓
Tích hợp với TV1
    ↓
Kiểm thử hệ thống
    ↓
Báo cáo + Demo
```

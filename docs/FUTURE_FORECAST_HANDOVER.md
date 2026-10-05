# FUTURE FORECAST HANDOVER

## 1. Mục tiêu

Đây là phần tiếp theo sau khi hoàn thành integration TV1 + TV2.

Trạng thái:

``` text
Historical Prediction = DONE
Future Forecast        = NOT IMPLEMENTED
```

Không sửa lại historical prediction nếu không cần thiết.

------------------------------------------------------------------------

## 2. Prediction hiện tại là gì?

Hiện tại Random Forest dự đoán trong khoảng:

``` text
2026-01-08
→
2026-06-30
```

Actual demand của các thời điểm này đã tồn tại.

Vì vậy có thể đánh giá:

``` text
MAE
RMSE
R²
Actual vs Predicted
```

Đây là:

``` text
Historical / Offline Prediction
```

Không phải Future Forecast.

------------------------------------------------------------------------

## 3. Future Forecast cần làm gì?

Mục tiêu đầu tiên:

``` text
Forecast 24 giờ tiếp theo
```

Sau khi ổn định mới mở rộng:

``` text
Forecast 7 ngày tiếp theo
```

Với dataset hiện tại, thời điểm actual cuối là:

``` text
2026-06-30 23:00
```

Future Forecast đầu tiên bắt đầu:

``` text
2026-07-01 00:00
```

------------------------------------------------------------------------

## 4. Vấn đề chính

Random Forest hiện dùng:

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

Để forecast:

``` text
2026-07-01 00:00
```

có thể lấy lag từ historical data.

Nhưng để forecast:

``` text
2026-07-01 01:00
```

`lag_1` cần demand của:

``` text
2026-07-01 00:00
```

Đây là future value, không có actual.

Do đó không được sử dụng future actual data.

------------------------------------------------------------------------

## 5. Hướng đề xuất

Sử dụng:

``` text
Recursive Forecasting
```

Luồng:

``` text
Historical demand
      ↓
Tạo features cho t+1
      ↓
Predict t+1
      ↓
Thêm predicted t+1 vào demand history
      ↓
Tạo features cho t+2
      ↓
Predict t+2
      ↓
...
```

Ví dụ:

``` text
Last actual:
2026-06-30 23:00

Predict:
2026-07-01 00:00
      ↓
Dùng prediction 00:00 để tạo lag/rolling
      ↓
Predict:
2026-07-01 01:00
```

------------------------------------------------------------------------

## 6. Không sửa historical pipeline

Giữ nguyên:

``` text
analysis/ml/01_linear_regression.py
analysis/ml/02_random_forest.py
analysis/ml/03_gradient_boosting.py
analysis/ml/04_model_comparison.py
analysis/ml/05_prediction_analysis.py
analysis/ml/06_prepare_dashboard_data.py
analysis/ml/07_save_predictions_to_postgres.py
```

Tạo script mới:

``` text
analysis/ml/08_future_forecast.py
```

Mục đích là Future Forecast độc lập với evaluation hiện tại.

------------------------------------------------------------------------

## 7. Output đề xuất

Có thể tạo:

``` text
analysis/outputs/ml/future_forecast.csv
```

Schema tối thiểu:

``` text
target_time
predicted_demand
model_name
model_version
```

Ví dụ:

``` text
2026-07-01 00:00 | 85.4 | Random Forest | future-v1
2026-07-01 01:00 | 72.1 | Random Forest | future-v1
...
```

------------------------------------------------------------------------

## 8. PostgreSQL

Có thể tiếp tục dùng bảng:

``` text
predictions
```

Future row:

``` text
prediction_time   = CURRENT_TIMESTAMP
target_time       = future timestamp
predicted_demand  = forecast result
actual_demand     = NULL
model_name        = Random Forest
model_version     = future-v1
```

Historical hiện tại:

``` text
Random Forest / 1.0
```

Future:

``` text
Random Forest / future-v1
```

Không dùng `1.0` cho Future Forecast.

------------------------------------------------------------------------

## 9. Lưu ý khi save prediction

Hàm save historical hiện xóa dữ liệu theo:

``` text
model_name + model_version
```

Do đó Future Forecast phải dùng version riêng.

Ví dụ:

``` text
Historical:
Random Forest + 1.0

Future:
Random Forest + future-v1
```

Như vậy hai loại prediction không xóa lẫn nhau.

------------------------------------------------------------------------

## 10. Dashboard

Sau khi Future Forecast chạy ổn định, thêm section mới:

``` text
🔮 Future Demand Forecast
```

Không thay thế biểu đồ:

``` text
Actual vs Predicted
```

hiện tại.

Dashboard nên phân biệt:

``` text
Actual Demand
Historical Prediction
Future Forecast
```

Có thể thêm:

``` text
Forecast Horizon
- Next 24 Hours
- Next 7 Days
```

Nhưng triển khai 24h trước.

------------------------------------------------------------------------

## 11. Quy trình triển khai

### Phase 1 --- Chuẩn bị

``` text
1. Chốt integration hiện tại.
2. Commit/push phiên bản hiện tại.
3. Không sửa Kafka/Spark/PostgreSQL pipeline của TV1.
```

### Phase 2 --- Forecast 24h

``` text
4. Tạo 08_future_forecast.py.
5. Load historical hourly demand.
6. Tạo recursive feature generation.
7. Forecast 24 bước.
8. Kiểm tra không sử dụng future actual.
9. Xuất future_forecast.csv.
```

### Phase 3 --- PostgreSQL

``` text
10. Save forecast vào predictions.
11. actual_demand = NULL.
12. model_version = future-v1.
13. Kiểm tra historical prediction vẫn còn nguyên.
```

### Phase 4 --- Dashboard

``` text
14. Tạo loader future prediction.
15. Thêm Future Demand Forecast section.
16. Hiển thị 24h forecast.
17. Kiểm thử.
```

### Phase 5 --- Mở rộng

``` text
18. Sau khi 24h ổn định, thử 7 ngày.
19. Đánh giá độ ổn định của recursive forecast.
```

------------------------------------------------------------------------

## 12. Checkpoint trước khi bắt đầu

Phải đảm bảo:

``` text
trips          = 415,708
hourly_demand  = 4,254
predictions    = 4,176 historical rows

Random Forest Test MAE = 24.8594
Random Forest Test R²  = 0.8789
```

Dashboard:

``` text
Total Trips       = 415,708
Avg Trips / Day   = 2,297
Peak Hour          = 17:00
Peak Hour Trips    = 41,689
Test MAE           = 24.86
```

Filter:

``` text
Member   = 322,484
Casual   = 93,224
Electric = 267,614
Classic  = 148,094
```

------------------------------------------------------------------------

## 13. Không làm các việc sau khi bắt đầu Future Forecast

Không chạy lại Producer nếu không cần.

Không chạy lại Spark append chỉ để làm Forecast.

Không chạy:

``` text
docker compose down -v
```

Không hard-code PostgreSQL host port.

Không commit `.env`.

Không sửa historical prediction thành Future Forecast.

------------------------------------------------------------------------

## 14. Điểm bắt đầu lần sau

Bắt đầu từ:

``` text
analysis/ml/08_future_forecast.py
```

Mục tiêu đầu tiên:

``` text
Forecast chính xác 24 timestamps:
2026-07-01 00:00
→
2026-07-01 23:00
```

Sau khi 24h forecast chạy đúng mới tích hợp PostgreSQL và Dashboard.

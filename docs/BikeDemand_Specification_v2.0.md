# ĐẶC TẢ NÂNG CẤP HỆ THỐNG BIKEDEMAND

## Phiên bản 2.0

### 1. Mục tiêu

Nâng cấp BikeDemand từ hệ thống phân tích và đánh giá dự báo trên dữ
liệu lịch sử thành hệ thống có khả năng: 1. Tự động lấy dữ liệu Citi
Bike mới và cập nhật pipeline. 2. Dự báo nhu cầu 24 giờ tiếp theo. 3.
Hiển thị tên/vị trí trạm và bản đồ nhu cầu hoạt động.

Nguyên tắc: đơn giản, ổn định, dễ kiểm thử, không làm quá phạm vi bài
tập.

### 2. Phạm vi bắt buộc

  Mã    Chức năng                                             Mức độ
  ----- ----------------------------------------------------- ----------
  U01   Tự động kiểm tra và tải dữ liệu Citi Bike mới         Bắt buộc
  U02   Cập nhật dữ liệu vào pipeline hiện tại                Bắt buộc
  U03   Tự động chạy các bước xử lý cần thiết                 Bắt buộc
  F01   Forecast 24 giờ tiếp theo                             Bắt buộc
  F02   Lưu Future Forecast tách khỏi Historical Prediction   Bắt buộc
  F03   Hiển thị Future Forecast trên Dashboard               Bắt buộc
  M01   Hiển thị tên trạm và tọa độ                           Bắt buộc
  M02   Proportional Symbol/Point Map                         Bắt buộc
  M03   Heatmap mờ                                            Bắt buộc

### 3. Ngoài phạm vi

Không làm trong v2.0: - Forecast 7 ngày. - Forecast riêng Member/Casual
hoặc Electric/Classic. - Dự đoán tồn kho xe, thiếu xe hoặc hết chỗ. -
Airflow, Kubernetes, cloud deployment. - Thay thế Kafka/Spark/PostgreSQL
hiện tại. - Xây dựng lại toàn bộ ML pipeline. - Thay đổi Historical
Prediction nếu không cần thiết.

### 4. Kiến trúc mục tiêu

``` text
Citi Bike System Data
        ↓
Automatic Data Updater
        ↓
Kafka → Spark → PostgreSQL
        ↓
 ┌──────┴──────────┐
 ↓                 ↓
Analysis/FE     Future Forecast
 └──────┬──────────┘
        ↓
   PostgreSQL
        ↓
    Dashboard
```

### 5. Nâng cấp U -- Automatic Data Update

Chọn phương án hệ thống **tự lấy dữ liệu từ Citi Bike System Data**,
thay vì yêu cầu người dùng tải CSV thủ công.

Luồng:

``` text
Kiểm tra nguồn
   ↓
Có file tháng mới?
   ↓ Có
Download CSV
   ↓
Kiểm tra/chống duplicate
   ↓
Kafka → Spark → PostgreSQL
   ↓
Feature Engineering → Forecast
   ↓
Dashboard
```
Bổ sung:

Citi Bike System Data
        ↓
Phát hiện dữ liệu mới
        ↓
Download + chống duplicate
        ↓
Kafka → Spark → PostgreSQL
        ↓
Xác định actual cuối cùng
        ↓
Future Forecast 24h
        ↓
Dashboard

Yêu cầu: - Không tải lại file tháng đã có. - Không insert trùng
`ride_id`. - Có thể chạy updater nhiều lần mà dữ liệu không tăng sai. -
Không yêu cầu real-time; chỉ cần kiểm tra định kỳ đơn giản.

### 6. Nâng cấp F -- Future Forecast 24h

Historical Prediction hiện tại giữ nguyên. Future Forecast là chức năng
mới.

Nguyên tắc xác định thời gian forecast: Hệ thống phải tự động xác định thời điểm actual mới nhất trong PostgreSQL. Forecast luôn bắt đầu từ 1 giờ sau actual cuối cùng và kéo dài đúng 24 giờ.

Ví dụ kiểm thử ban đầu: Với dataset hiện tại, actual cuối là 2026-06-30 23:00, do đó forecast đầu tiên là 2026-07-01 00:00 đến 2026-07-01 23:00.

Khi Phase 1 cập nhật dữ liệu mới, mốc forecast phải tự động thay đổi theo dữ liệu mới, không được hard-code ngày 2026-06-30.
Phương pháp: **Recursive Forecasting với Random Forest**.

Features giữ nguyên:

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

Luồng:

``` text
Historical demand
      ↓
Tạo feature t+1
      ↓
Predict t+1
      ↓
Đưa prediction t+1 vào history tạm
      ↓
Tạo feature t+2
      ↓
Predict t+2
      ↓
...
      ↓
Predict t+24
```

Không được dùng `actual_demand` của tương lai.

Tạo:

``` text
analysis/ml/08_future_forecast.py
analysis/outputs/ml/future_forecast.csv
```

Schema:

``` text
target_time
predicted_demand
model_name
model_version
```

Future Forecast lưu vào bảng `predictions`:

``` text
prediction_time = thời điểm chạy
target_time = thời điểm tương lai
predicted_demand = forecast
actual_demand = NULL
model_name = Random Forest
model_version = future-v1
```

Historical:

``` text
Random Forest / 1.0
```

Future:

``` text
Random Forest / future-v1
```

Hai loại prediction không được xóa lẫn nhau.

### 7. Dashboard Future Forecast

Giữ biểu đồ:

``` text
Actual vs Predicted
```

và thêm:

``` text
🔮 Future Demand Forecast
```

Dashboard phải phân biệt:

``` text
Actual Demand
Historical Prediction
Future Forecast
```

Chỉ hiển thị 24 giờ trước mắt.

### 8. Nâng cấp M -- Station Map

Dataset có:

``` text
start_station_name
start_station_id
end_station_name
end_station_id
start_lat
start_lng
end_lat
end_lng
```

Dashboard phải ưu tiên hiển thị tên trạm thay vì chỉ ID.

#### 8.1. Composite / Hybrid Map

Gồm:

``` text
Point / Proportional Symbol Map
+
Heatmap mờ
```

Mỗi trạm có:

``` text
Station Name
Station ID
Latitude
Longitude
Activity Count
```

Activity Count:

``` text
Số lượt bắt đầu
+
Số lượt kết thúc
```

Hoạt động càng nhiều → marker càng lớn; màu có thể biểu diễn mức độ hoạt
động.

Heatmap chỉ biểu diễn **mật độ hoạt động**, không kết luận trực tiếp về
thiếu xe/hết xe vì hệ thống chưa có dữ liệu tồn kho theo thời gian.

Tooltip tối thiểu:

``` text
Tên trạm
Tổng hoạt động
```

Có thể bổ sung Start/End Count nếu triển khai thuận lợi.

### 9. Cấu trúc Dashboard mục tiêu

``` text
Filters
KPI tổng quan
Demand Analysis
Historical Prediction
Future Demand Forecast – Next 24 Hours
User & Bike Analysis
Station Analysis
Station Composite Map
Model Information
```

### 10. Thứ tự triển khai

**Phase 0 -- Checkpoint** - Commit phiên bản 1.0. - Đảm bảo hệ thống
hiện tại chạy. - Không phá pipeline.

**Phase 1 -- Future Forecast** - Tạo `08_future_forecast.py`. - Forecast
24 bước. - Kiểm tra không dùng future actual. - Xuất CSV.

**Phase 2 -- PostgreSQL** - Lưu Future Forecast. -
`actual_demand = NULL`. - `model_version = future-v1`. - Kiểm tra
Historical Prediction vẫn còn.

**Phase 3 -- Dashboard Forecast** - Loader. - Section Future Demand
Forecast. - Hiển thị 24 giờ. - Kiểm thử.

**Phase 4 -- Station Map** - Lấy tên + tọa độ. - Tính Activity Count. -
Point/Proportional Symbol Map. - Heatmap. - Tooltip. - Kiểm thử.

**Phase 5 -- Automatic Update** - Tạo updater. - Phát hiện file mới. -
Download. - Chống duplicate. - Chạy pipeline. - Feature Engineering. -
Forecast. - Dashboard đọc dữ liệu mới. - Kiểm thử toàn flow.

### 11. Regression Check

Phải giữ được checkpoint v1.0:

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
Peak Hour         = 17:00
Peak Hour Trips   = 41,689
Test MAE          = 24.86
```

### 12. Kiểm thử bắt buộc

**Automatic Update** - Phát hiện dữ liệu mới. - Không tải lại file cũ. -
Không duplicate `ride_id`. - PostgreSQL cập nhật. - Forecast cập nhật.

**Future Forecast** - Đúng 24 dòng. - Bắt đầu = actual cuối + 1 giờ. -
Kết thúc = actual cuối + 24 giờ. - Không có future `actual_demand`. -
Không dùng future actual.

**Prediction** - Historical `Random Forest / 1.0` vẫn tồn tại. - Future
`Random Forest / future-v1`. - Không duplicate.

**Map** - Đúng tọa độ. - Đúng tên trạm. - Activity Count hợp lý. -
Marker thay đổi theo hoạt động. - Heatmap hiển thị. - Tooltip hoạt động.

**Dashboard** - Mở bình thường. - Filter/KPI cũ không sai. - Historical
Prediction vẫn có. - Future Forecast hiển thị. - Station Map hiển thị.

### 13. Tiêu chí hoàn thành v2.0

-   [ ] Automatic Data Update hoạt động.
-   [ ] Không duplicate dữ liệu.
-   [ ] Future Forecast 24h hoạt động.
-   [ ] Forecast không dùng future actual.
-   [ ] Future Forecast lưu PostgreSQL.
-   [ ] Historical Prediction không bị mất.
-   [ ] Dashboard hiển thị Future Forecast.
-   [ ] Station name + location hiển thị.
-   [ ] Composite Station Map hoạt động.
-   [ ] Heatmap hoạt động.
-   [ ] Dashboard v1.0 vẫn hoạt động.

### 14. Nguyên tắc chống làm quá

Mọi thay đổi phải trả lời: \> Thay đổi này có trực tiếp phục vụ
Automatic Data Update, Future Forecast 24 Hours hoặc Station Map
Visualization không?

Nếu không, không đưa vào v2.0.

Ưu tiên:

``` text
Đơn giản
↓
Ổn định
↓
Dễ kiểm thử
↓
Đúng mục tiêu đề tài
```

### 15. Mở rộng sau v2.0

Chỉ xem xét sau khi v2.0 ổn định: - Forecast 7 ngày. - Đánh giá Future
Forecast khi actual xuất hiện. - Scheduling nâng cao. - Phân tích
station nâng cao. - Phân tích thiếu xe/hết chỗ khi có dữ liệu phù hợp.

### 16. Kết luận

Phạm vi chính thức của BikeDemand v2.0:

``` text
Automatic Data Update
        +
24h Future Forecast
        +
Station Composite Map
```

Nền tảng Kafka → Spark → PostgreSQL → Dashboard của v1.0 được giữ lại;
chỉ bổ sung các thành phần cần thiết cho ba mục tiêu trên.

# FINAL SYSTEM DESIGN
# Citi Bike Demand Analysis & Prediction

## 1. Thông tin đề tài

Tên đề tài:
Phân tích và dự báo nhu cầu sử dụng xe đạp Citi Bike bằng hệ thống Big Data

Dataset:
Citi Bike Trip Data

Phạm vi:
6 tháng đầu năm 2026

Thời gian:
01/01/2026 - 30/06/2026

Tổng số chuyến:
415,708 trips

Dataset chính thức:
data/processed/citibike_2026_H1.csv


## 2. Mục tiêu

Xây dựng hệ thống xử lý dữ liệu lớn có khả năng:

1. Thu thập dữ liệu Citi Bike.
2. Đưa dữ liệu vào hệ thống streaming bằng Apache Kafka.
3. Xử lý và biến đổi dữ liệu bằng Apache Spark.
4. Lưu trữ dữ liệu phân tích trong PostgreSQL.
5. Phân tích nhu cầu sử dụng xe đạp theo thời gian.
6. Xây dựng mô hình Machine Learning dự báo nhu cầu.
7. Trực quan hóa kết quả bằng Dashboard.


## 3. Phạm vi dữ liệu

Sử dụng 6 file:

JC-202601-citibike-tripdata.csv
JC-202602-citibike-tripdata.csv
JC-202603-citibike-tripdata.csv
JC-202604-citibike-tripdata.csv
JC-202605-citibike-tripdata.csv
JC-202606-citibike-tripdata.csv

Dataset được hợp nhất thành:

citibike_2026_H1.csv


## 4. Kiến trúc hệ thống

Citi Bike CSV
      |
      v
Kafka Producer
      |
      v
Apache Kafka
      |
      | citibike-trips
      v
Kafka Consumer / Spark Streaming
      |
      v
Apache Spark
      |
      +------------------+
      |                  |
      v                  v
PostgreSQL          ML Pipeline
      |                  |
      +--------+---------+
               |
               v
          Dashboard


## 5. Công nghệ

### Data Collection
- Python
- Pandas

### Streaming
- Apache Kafka 3.9

### Big Data Processing
- Apache Spark 3.5.7
- PySpark

### Database
- PostgreSQL 16

### Machine Learning
- Python
- PySpark ML hoặc Scikit-learn

### Containerization
- Docker
- Docker Compose

### Visualization
- Dashboard framework sẽ được lựa chọn
  trong giai đoạn triển khai.

### Orchestration
- Apache Airflow
- Chỉ triển khai sau khi pipeline chính hoạt động ổn định.


## 6. Docker Services

postgres
    Port: 5432

kafka
    Port: 9092

spark-master
    Port: 7077
    UI: 8080

spark-worker
    Kết nối spark-master:7077


## 7. Kafka

Topic chính:

citibike-trips

Partitions:
3

Replication factor:
1

Luồng:

Producer
    ↓
citibike-trips
    ↓
Consumer / Spark


## 8. PostgreSQL Schema

### trips

Lưu dữ liệu chuyến đi đã xử lý.

Các trường chính:

- ride_id
- rideable_type
- started_at
- ended_at
- start_station_name
- start_station_id
- end_station_name
- end_station_id
- start_lat
- start_lng
- end_lat
- end_lng
- member_casual
- ride_duration_minutes
- start_hour
- day_of_week
- month


### hourly_demand

Lưu dữ liệu nhu cầu theo giờ.

Các trường:

- date
- hour
- day_of_week
- total_trips
- member_trips
- casual_trips


### predictions

Lưu kết quả dự báo.

Các trường:

- prediction_date
- prediction_hour
- predicted_demand
- actual_demand
- model_name


## 9. Các bước xử lý dữ liệu

Raw CSV
    ↓
Schema validation
    ↓
Datetime conversion
    ↓
Filter thời gian
    ↓
Remove duplicate ride_id
    ↓
Missing value handling
    ↓
Outlier validation
    ↓
Feature engineering
    ↓
Spark processing
    ↓
Aggregation
    ↓
PostgreSQL


## 10. Phân tích

Các chỉ số chính:

- Số chuyến theo ngày
- Số chuyến theo giờ
- Số chuyến theo tháng
- Số chuyến theo thứ trong tuần
- Member vs Casual
- Electric bike vs Classic bike
- Top start stations
- Top end stations
- Thời lượng chuyến đi
- Xu hướng nhu cầu


## 11. Machine Learning

Mục tiêu:

Dự báo số chuyến xe dự kiến theo thời gian.

Input features dự kiến:

- hour
- day_of_week
- month
- previous_demand
- rolling_average
- member_demand
- casual_demand

Target:

total_trips


Các mô hình có thể thử:

- Linear Regression
- Random Forest
- Gradient Boosting

Mô hình cuối cùng được lựa chọn dựa trên kết quả đánh giá.


## 12. Dashboard

Dashboard dự kiến hiển thị:

- Tổng số trips
- Trips theo ngày
- Trips theo giờ
- Trips theo tháng
- Member/Casual
- Bike type
- Top stations
- Actual vs Predicted Demand
- Peak hours


## 13. Airflow

Airflow không nằm trong MVP ban đầu.

Sau khi pipeline chính hoạt động:

Kafka
  ↓
Spark
  ↓
PostgreSQL
  ↓
ML
  ↓
Dashboard

mới xem xét dùng Airflow để:

- Scheduling
- Dependency management
- Monitoring
- Retry


## 14. Giai đoạn triển khai

### Phase 1
Đặc tả đề tài

### Phase 2
Thiết kế hệ thống

Đã hoàn thành:

- Dataset
- Data schema
- Pipeline
- Kafka
- PostgreSQL
- Spark
- Docker Compose
- Technology stack

### Phase 3
Phân công thành viên

TV1:
Data Engineering

TV2:
Data Analysis + Machine Learning

### Phase 4
Triển khai

TV1:
- Kafka Producer
- Kafka Consumer
- Spark
- PostgreSQL pipeline

TV2:
- Data Analysis
- Feature Engineering
- Machine Learning
- Evaluation

### Phase 5
Tích hợp

Kafka
→ Spark
→ PostgreSQL
→ ML
→ Dashboard

### Phase 6
Kiểm thử và hoàn thiện

- Pipeline testing
- Data validation
- Model evaluation
- Dashboard testing
- Report
- Demo


## 15. Nguyên tắc thực hiện

1. Không thay đổi dataset chính thức nếu không thống nhất.
2. Không tự ý đổi Kafka topic.
3. Không tự ý đổi PostgreSQL schema.
4. Mọi thay đổi kiến trúc phải được thống nhất trong nhóm.
5. Raw data không được chỉnh sửa trực tiếp.
6. Dataset processed phải có thể tái tạo từ raw data.
7. ML chỉ triển khai sau khi pipeline dữ liệu ổn định.
8. Airflow triển khai sau cùng.
# PHÂN CÔNG NHIỆM VỤ DỰ ÁN

## 1. Thông tin chung

**Tên đề tài:** Phân tích và dự báo nhu cầu sử dụng xe đạp Citi Bike bằng hệ thống Big Data

**Dataset:** Citi Bike 2026 H1

**Thời gian dữ liệu:** 01/01/2026 – 30/06/2026

**Số bản ghi chính thức:** 415.708 lượt thuê xe

**Số thành viên:** 2

---

# 2. Phân công nhiệm vụ

## TV1 — Nhóm trưởng / Data Engineering

### Mục tiêu
Xây dựng hạ tầng và pipeline xử lý dữ liệu của hệ thống, đảm bảo dữ liệu được thu thập, truyền tải, xử lý và lưu trữ ổn định.

### Nhiệm vụ chính

1. **Quản lý dự án**
   - Quản lý Git repository.
   - Quản lý cấu trúc thư mục và tài liệu dự án.
   - Theo dõi tiến độ và phối hợp công việc giữa các thành viên.
   - Quản lý quá trình tích hợp hệ thống.

2. **Kafka**
   - Thiết lập Kafka bằng Docker.
   - Quản lý Kafka Topic.
   - Xây dựng Producer đưa dữ liệu vào Kafka.
   - Xây dựng Consumer đọc dữ liệu từ Kafka.
   - Kiểm tra và xử lý luồng dữ liệu.

3. **Data Pipeline**
   - Xây dựng pipeline:
     
     Dataset → Kafka → Spark → PostgreSQL
     
   - Thực hiện các bước xử lý và kiểm tra dữ liệu cần thiết trong pipeline.
   - Đảm bảo dữ liệu truyền qua các thành phần của hệ thống chính xác.

4. **Apache Spark**
   - Thiết lập Spark Master và Worker.
   - Tích hợp Spark với Kafka.
   - Xử lý dữ liệu bằng Spark.
   - Chuẩn bị dữ liệu đầu ra cho PostgreSQL và các bước phân tích.

5. **PostgreSQL**
   - Thiết kế và quản lý database.
   - Xây dựng schema và các bảng dữ liệu.
   - Lưu trữ dữ liệu sau xử lý.
   - Kiểm tra tính toàn vẹn dữ liệu.

6. **Tích hợp hệ thống**
   - Phối hợp với TV2 để kết nối pipeline dữ liệu với mô hình phân tích và dự báo.
   - Hỗ trợ chuẩn bị dữ liệu đầu vào cho Dashboard.

### Sản phẩm bàn giao

- Docker Compose
- Kafka Producer
- Kafka Consumer
- Kafka Topics
- Spark Pipeline
- PostgreSQL Schema
- Dữ liệu sau xử lý
- Các script kiểm tra pipeline
- Tài liệu kiến trúc và Data Engineering


---

# 3. TV2 — Data Analysis / Machine Learning

### Mục tiêu
Phân tích dữ liệu Citi Bike và xây dựng mô hình dự báo nhu cầu sử dụng xe đạp.

### Nhiệm vụ chính

1. **Tìm hiểu và phân tích dữ liệu**
   - Tìm hiểu cấu trúc dataset chính thức.
   - Phân tích số lượng chuyến đi.
   - Phân tích nhu cầu theo tháng, ngày và giờ.
   - Phân tích theo ngày trong tuần.
   - Phân tích theo loại người dùng Member/Casual.
   - Phân tích theo trạm xe.

2. **Exploratory Data Analysis**
   - Xác định các xu hướng chính của nhu cầu sử dụng xe.
   - Phân tích các thời điểm có nhu cầu cao/thấp.
   - Trực quan hóa các kết quả phân tích.

3. **Feature Engineering**
   - Xây dựng các đặc trưng phục vụ dự báo.
   - Xử lý thời gian và các đặc trưng liên quan.
   - Chuẩn bị dữ liệu train/test.

4. **Machine Learning**
   - Lựa chọn mô hình dự báo phù hợp.
   - Huấn luyện mô hình.
   - Thực hiện dự báo nhu cầu.
   - Đánh giá kết quả mô hình bằng các chỉ số phù hợp.

5. **Prediction**
   - Sinh kết quả dự báo.
   - Chuẩn bị dữ liệu dự báo để lưu vào PostgreSQL.
   - Phối hợp với TV1 trong quá trình tích hợp.

6. **Dashboard / Visualization**
   - Chuẩn bị các dữ liệu và biểu đồ phục vụ Dashboard.
   - Trực quan hóa nhu cầu thực tế và kết quả dự báo.

### Sản phẩm bàn giao

- Script/Notebook phân tích dữ liệu
- Các kết quả EDA
- Bộ đặc trưng Machine Learning
- Mô hình dự báo
- Kết quả đánh giá mô hình
- Dữ liệu dự báo
- Biểu đồ và dữ liệu phục vụ Dashboard
- Tài liệu Data Analysis và Machine Learning


---

# 4. Phối hợp giữa hai thành viên

Hai thành viên làm việc song song trong phạm vi nhiệm vụ của mình.

## TV1 phụ trách

```text
Dataset
   ↓
Kafka Producer
   ↓
Kafka Topic
   ↓
Kafka Consumer
   ↓
Spark
   ↓
PostgreSQL

## TV2 phụ trách

Official Dataset / Processed Data
          ↓
         EDA
          ↓
Feature Engineering
          ↓
    Machine Learning
          ↓
      Prediction
          ↓
     Visualization

Giai đoạn tích hợp

Hai nhánh được kết nối thành:

                    Kafka
                      ↓
                    Spark
                 ↙       ↘
        PostgreSQL        ML
             ↓             ↓
             └──────┬──────┘
                    ↓
                Dashboard
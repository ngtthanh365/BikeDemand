# RUN GUIDE

## 1. Kiểm tra Docker

Kiểm tra các container:

    docker ps

Các thành phần cần hoạt động:

- Kafka
- Spark Master
- Spark Worker
- PostgreSQL

## 2. Kiểm tra PostgreSQL

Kiểm tra PostgreSQL:

    docker exec citibike-postgres pg_isready -U postgres

Kết quả mong đợi:

    accepting connections

Kiểm tra các bảng:

    docker exec citibike-postgres psql -U postgres -d citibike -c "\dt"

Các bảng chính:

- trips
- hourly_demand
- predictions

## 3. Kiểm tra dữ liệu

Kiểm tra số lượng dữ liệu trong trips:

    docker exec citibike-postgres psql -U postgres -d citibike -c "SELECT COUNT(*) AS trips_count FROM trips;"

Kiểm tra số lượng dữ liệu trong hourly_demand:

    docker exec citibike-postgres psql -U postgres -d citibike -c "SELECT COUNT(*) AS hourly_demand_count FROM hourly_demand;"

Trạng thái dữ liệu hiện tại:

- trips: 415708 records
- hourly_demand: 4254 records
- Khoảng thời gian: 2026-01-01 đến 2026-06-30

## 4. Kiểm tra Kafka

Kiểm tra các Kafka topic:

    docker exec citibike-kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:29092 --list

Topic chính:

    citibike-trips

Kiểm tra offset:

    docker exec citibike-kafka /opt/kafka/bin/kafka-get-offsets.sh --bootstrap-server kafka:29092 --topic citibike-trips

## 5. Kiểm tra Spark

Các Spark application nằm trong container tại:

    /opt/spark-apps/

Các file chính:

- spark_streaming.py
- aggregate_demand.py
- check_anomalies.py

Kiểm tra:

    docker exec citibike-spark-master bash -c "find /opt/spark-apps -maxdepth 1 -type f -printf '%f\n'"

## 6. Chạy Spark Aggregation

Chạy ứng dụng aggregate dữ liệu:

    docker exec citibike-spark-master /opt/spark/bin/spark-submit `
      --master spark://spark-master:7077 `
      --conf spark.jars.ivy=/tmp/ivy-cache `
      --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.7,org.postgresql:postgresql:42.7.4 `
      /opt/spark-apps/aggregate_demand.py

Ứng dụng thực hiện:

1. Đọc dữ liệu từ Kafka topic citibike-trips.
2. Parse dữ liệu JSON.
3. Chuẩn hóa thời gian.
4. Tạo các trường thời gian.
5. Aggregate nhu cầu theo ngày và giờ.
6. Tính member_count và casual_count.
7. Tính electric_count và classic_count.
8. Ghi kết quả vào PostgreSQL.hourly_demand.

## 7. Kiểm tra kết quả

Kiểm tra số lượng bản ghi:

    docker exec citibike-postgres psql -U postgres -d citibike -c "SELECT COUNT(*) AS trips_count FROM trips; SELECT COUNT(*) AS hourly_demand_count FROM hourly_demand;"

Kiểm tra dữ liệu hourly_demand:

    docker exec citibike-postgres psql -U postgres -d citibike -c "SELECT * FROM hourly_demand ORDER BY timestamp LIMIT 10;"

Kiểm tra tổng dữ liệu:

    docker exec citibike-postgres psql -U postgres -d citibike -c "SELECT SUM(demand) AS total_demand, SUM(member_count) AS total_member, SUM(casual_count) AS total_casual, SUM(electric_count) AS total_electric, SUM(classic_count) AS total_classic FROM hourly_demand;"

Kết quả hiện tại:

    total_demand  = 415708
    total_member  = 322484
    total_casual  = 93224
    total_electric = 267614
    total_classic = 148094

## 8. Kiểm tra tính toàn vẹn dữ liệu

Kiểm tra dữ liệu thiếu:

    docker exec citibike-postgres psql -U postgres -d citibike -c "SELECT COUNT(*) AS invalid_rows FROM hourly_demand WHERE timestamp IS NULL OR date IS NULL OR hour IS NULL OR demand IS NULL;"

Kiểm tra giờ:

    docker exec citibike-postgres psql -U postgres -d citibike -c "SELECT MIN(hour) AS min_hour, MAX(hour) AS max_hour, COUNT(DISTINCT hour) AS distinct_hours FROM hourly_demand;"

Kết quả mong đợi:

    min_hour = 0
    max_hour = 23
    distinct_hours = 24

Kiểm tra duplicate timestamp:

    docker exec citibike-postgres psql -U postgres -d citibike -c "SELECT timestamp, COUNT(*) FROM hourly_demand GROUP BY timestamp HAVING COUNT(*) > 1;"

Kết quả mong đợi:

    (0 rows)

Kiểm tra tính đúng của demand:

    docker exec citibike-postgres psql -U postgres -d citibike -c "SELECT COUNT(*) AS invalid_rows FROM hourly_demand WHERE demand <> member_count + casual_count OR demand <> electric_count + classic_count;"

Kết quả mong đợi:

    invalid_rows = 0

## 9. Thông tin bàn giao

PostgreSQL:

    Host trong Docker network: citibike-postgres
    Port: 5432
    Database: citibike
    User: postgres

Bảng trips:

    415708 records

Bảng hourly_demand:

    4254 records

Bảng predictions:

    Dành cho kết quả dự đoán của bước Machine Learning.

NV2 sử dụng chủ yếu bảng hourly_demand cho các bước phân tích và xây dựng mô hình dự đoán.

Bảng trips được giữ lại để phục vụ truy vấn dữ liệu chi tiết và kiểm tra nguồn dữ liệu.

## 10. Luồng dữ liệu

    Citi Bike Dataset
            |
            v
    Kafka Producer
            |
            v
    Kafka Topic: citibike-trips
            |
            v
    Apache Spark
            |
            +----> trips
            |
            +----> hourly_demand
            |
            v
    PostgreSQL
            |
            v
    NV2 - Machine Learning / Analytics

## 11. Lưu ý

Không xóa hoặc thay đổi dữ liệu PostgreSQL nếu chưa thống nhất với các thành viên khác.

NV2 sử dụng chủ yếu hourly_demand.

trips được giữ lại để truy vấn dữ liệu chi tiết và kiểm tra nguồn dữ liệu.

predictions dành cho kết quả dự đoán.

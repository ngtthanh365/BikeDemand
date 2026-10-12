# TASK_PHASE2.md
# BIKEDEMAND v2.0 — PHASE 2: FUTURE DEMAND FORECAST

> **Mục đích:** Tài liệu triển khai chính thức cho Phase 2 của BikeDemand v2.0.
>
> **Phạm vi:** Xây dựng Future Demand Forecast dựa trên dữ liệu actual mới nhất trong PostgreSQL, sử dụng Random Forest + Recursive Forecasting, lưu riêng với Historical Prediction và hiển thị trên Dashboard.
>
> **Quyết định triển khai:** Làm luôn **7 ngày tiếp theo (168 giờ)** trong Phase 2, không chia thành 24h rồi mới nâng cấp.
>
> **Nguyên tắc:** Làm gọn, ổn định, dễ kiểm thử; không mở rộng kiến trúc; không sửa Phase 1 nếu không bắt buộc; không Scheduler/Airflow/Kubernetes/Cloud; không Station Map trong Phase 2.

---

# 1. THÔNG TIN TASK

| Thông tin | Nội dung |
|---|---|
| Project | BikeDemand |
| Phase | Phase 2 |
| Tên task | Future Demand Forecast |
| Mục tiêu | Dự báo nhu cầu 7 ngày tiếp theo |
| Trạng thái | ⬜ Chưa làm |
| Phiên bản mục tiêu | v2.0 |
| Database | PostgreSQL |
| Model | Random Forest |
| Phương pháp | Recursive Forecasting |
| Forecast horizon | 168 giờ |
| Dashboard | Streamlit |

---

# 2. BỐI CẢNH SAU PHASE 1

Phase 1 đã hoàn thành:

```text
Citi Bike
    ↓
Detect new month
    ↓
Download
    ↓
Validate
    ↓
Kafka
    ↓
Spark
    ↓
PostgreSQL
    ↓
Dashboard
```

Trạng thái bàn giao hiện tại:

```text
trips          = 742,615
hourly_demand  = 6,459
predictions    = 4,176 historical predictions
actual range   = 2026-01-01 → 2026-09-30
```

Historical Prediction:

```text
Random Forest / 1.0
```

Future Forecast:

```text
NOT IMPLEMENTED
```

Phase 2 bắt đầu từ đúng trạng thái trên.

---

# 3. MỤC TIÊU PHASE 2

## 3.1 In-scope

1. Lấy `latest actual timestamp` động từ PostgreSQL.
2. Forecast bắt đầu từ 1 giờ sau actual cuối.
3. Forecast **168 giờ liên tục = 7 ngày**.
4. Tái sử dụng Random Forest hiện tại.
5. Sử dụng Recursive Forecasting.
6. Không sử dụng `actual_demand` của tương lai.
7. Lưu Future Forecast tách biệt với Historical Prediction.
8. Hiển thị Future Forecast trên Dashboard.
9. Giữ nguyên Historical Prediction v1.0.
10. Có test đầy đủ cho 168 timestamps, leakage, duplicate và rerun.

## 3.2 Out-of-scope

- Scheduler tự động theo giờ.
- Airflow/Kubernetes/Cloud.
- Deep Learning/LSTM/Transformer.
- Model mới chỉ để forecast 7 ngày.
- Forecast riêng Member/Casual hoặc Electric/Classic.
- Station Map/Heatmap.
- Inventory prediction.
- Dự đoán thiếu xe/hết xe.
- Rewrite Kafka/Spark/PostgreSQL.
- Rewrite toàn bộ ML pipeline.
- Thay đổi Historical Prediction nếu không bắt buộc.

---

# 4. QUYẾT ĐỊNH FORECAST 7 NGÀY

Tài liệu cũ đề xuất 24h trước rồi mới mở rộng 7 ngày. Phase 2 này **thống nhất làm luôn 7 ngày**.

Lý do:

- 24h và 7 ngày dùng cùng cơ chế Recursive Forecasting.
- 24 bước và 168 bước không cần hai model khác nhau.
- Tránh phải sửa lại output/database/dashboard lần thứ hai.
- Phù hợp mục tiêu “làm một lần cho hoàn chỉnh”.

Điểm cần chấp nhận:

> Recursive Forecasting 168 bước có sai số tích lũy lớn hơn 24 bước. Vì vậy Phase 2 ưu tiên đúng quy trình, không leakage, ổn định và dễ kiểm thử; không cam kết độ chính xác 7 ngày cao chỉ bằng cách đổi kiến trúc.

---

# 5. LUỒNG PHASE 2

```text
PostgreSQL
    ↓
Read hourly_demand
    ↓
Find latest actual timestamp
    ↓
Latest actual + 1 hour
    ↓
Create features t+1
    ↓
Random Forest
    ↓
Predict t+1
    ↓
Append prediction vào temporary history
    ↓
Create features t+2
    ↓
Predict t+2
    ↓
...
    ↓
Predict t+168
    ↓
Validate
    ↓
CSV
    ↓
PostgreSQL
    ↓
Dashboard
```

---

# 6. NGUYÊN TẮC THỜI GIAN

Không hard-code ngày/tháng.

Phải lấy:

```sql
SELECT MAX(timestamp) FROM hourly_demand;
```

Sau đó:

```text
forecast_start = latest_actual + 1 hour
forecast_end   = latest_actual + 168 hours
```

Ví dụ nếu actual cuối là:

```text
2026-09-30 23:00
```

forecast phải là:

```text
2026-10-01 00:00
→
2026-10-07 23:00
```

Nếu Phase 1 cập nhật thêm dữ liệu, forecast phải tự chuyển theo actual mới nhất.

---

# 7. TASK 0 — CHECKPOINT TRƯỚC KHI CODE

## Mục tiêu

Bảo vệ trạng thái Phase 1 trước mọi thay đổi.

AI Agent phải kiểm tra:

```text
git status
git diff
project structure
Docker
PostgreSQL
historical predictions
ML scripts
Dashboard
```

Xác nhận:

```text
trips = 742,615
hourly_demand = 6,459
predictions = 4,176
```

### Acceptance Criteria

- [ ] Docker hoạt động.
- [ ] PostgreSQL truy cập được.
- [ ] Historical Prediction tồn tại.
- [ ] `git status` được kiểm tra.
- [ ] Không có thay đổi ngoài ý muốn.

> Nếu checkpoint không đạt: **STOP**, không làm Task 1.

---

# 8. TASK 1 — KHẢO SÁT ML PIPELINE HIỆN TẠI

## Mục tiêu

Không viết lại ML pipeline khi chưa hiểu code.

Đọc tối thiểu:

```text
analysis/ml/01_linear_regression.py
analysis/ml/02_random_forest.py
analysis/ml/03_gradient_boosting.py
analysis/ml/04_model_comparison.py
analysis/ml/05_prediction_analysis.py
analysis/ml/06_prepare_dashboard_data.py
analysis/ml/07_save_predictions_to_postgres.py
```

Nếu path thực tế khác, phải kiểm tra project structure trước.

Xác định:

- Feature engineering.
- Cách load dataset.
- Cách train/load Random Forest.
- `hour`, `day_of_week`, `month`.
- `lag_1`, `lag_24`, `lag_168`.
- `rolling_24h`, `rolling_7d`.
- Schema `predictions`.
- Cách lưu Historical Prediction.

### Quy tắc

**Task 1 chỉ khảo sát. Không sửa các file ML hiện tại.**

### Acceptance Criteria

- [ ] Hiểu model hiện tại.
- [ ] Hiểu feature engineering.
- [ ] Hiểu schema prediction.
- [ ] Có phương án tái sử dụng.

---

# 9. TASK 2 — FUTURE FORECAST ENGINE

## Mục tiêu

Tạo module độc lập:

```text
analysis/ml/08_future_forecast.py
```

Output:

```text
analysis/outputs/ml/future_forecast.csv
```

Phương pháp:

```text
Random Forest
+
Recursive Forecasting
```

Luồng:

```text
Historical demand
      ↓
Features t+1
      ↓
Predict t+1
      ↓
Temporary history += prediction t+1
      ↓
Features t+2
      ↓
Predict t+2
      ↓
...
      ↓
Predict t+168
```

## Cấm

Không được dùng future `actual_demand` để tạo:

```text
lag_1
lag_24
lag_168
rolling_24h
rolling_7d
```

Các giá trị cần thiết ở tương lai phải đến từ:

```text
historical actual
+
previous predictions
```

### Acceptance Criteria

- [ ] Đúng 168 timestamps.
- [ ] Mỗi timestamp cách nhau 1 giờ.
- [ ] Start = latest actual + 1h.
- [ ] End = latest actual + 168h.
- [ ] Không future actual leakage.
- [ ] Không duplicate timestamp.
- [ ] Không hard-code ngày/tháng.
- [ ] Script chạy độc lập thành công.

---

# 10. TASK 3 — VALIDATE FUTURE FORECAST

Kiểm tra trước khi lưu DB:

### Số dòng

```text
168 rows
```

### Timestamp

```text
COUNT = 168
COUNT DISTINCT = 168
```

### Khoảng thời gian

```text
first = latest_actual + 1 hour
last  = latest_actual + 168 hours
```

### Giá trị

- Không NULL.
- Không NaN.
- Không infinite.
- Demand không âm nếu logic hiện tại yêu cầu.

Không tự ý thêm clipping hoặc quy tắc mới nếu chưa kiểm tra code hiện tại; nếu cần phải báo cáo.

### Acceptance Criteria

- [ ] 168/168 hợp lệ.
- [ ] Không duplicate.
- [ ] Không NULL/NaN/Inf.
- [ ] Không leakage.
- [ ] Time range chính xác.

---

# 11. TASK 4 — LƯU FUTURE FORECAST VÀO POSTGRESQL

Dùng bảng hiện tại:

```text
predictions
```

Future row:

```text
prediction_time = thời điểm chạy
target_time = timestamp tương lai
predicted_demand = forecast
actual_demand = NULL
model_name = Random Forest
model_version = future-v1
```

Historical:

```text
Random Forest / 1.0
```

Future:

```text
Random Forest / future-v1
```

## Quy tắc

Không dùng `model_version = 1.0` cho Future.

Không DELETE toàn bộ `predictions`.

Không thay thế Historical Prediction.

Khi rerun cùng horizon, Future `future-v1` phải được refresh an toàn mà không làm mất Historical `1.0`. Agent phải đọc logic save hiện tại trước khi quyết định cơ chế refresh.

### Acceptance Criteria

- [ ] Future Forecast có trong PostgreSQL.
- [ ] `actual_demand IS NULL`.
- [ ] `model_version = future-v1`.
- [ ] Historical 1.0 còn nguyên.
- [ ] Future không duplicate `target_time`.
- [ ] Rerun an toàn.

---

# 12. TASK 5 — DASHBOARD FUTURE FORECAST

Thêm một section riêng:

```text
🔮 Future Demand Forecast
```

Dashboard phải phân biệt:

```text
Actual Demand
Historical Prediction
Future Forecast
```

Hiển thị:

- 7 ngày forecast.
- target time.
- predicted demand.
- model/version nếu phù hợp.
- forecast start/end.

Có thể dùng line chart.

Không được:

- Xóa `Actual vs Predicted`.
- Xóa Historical Prediction.
- Phá KPI/filter hiện tại.
- Thiết kế lại toàn bộ Dashboard.
- Thêm Station Map.

### Acceptance Criteria

- [ ] Dashboard mở bình thường.
- [ ] Hiển thị đủ 168 điểm.
- [ ] Historical Prediction vẫn có.
- [ ] Actual Demand vẫn có.
- [ ] Filter/KPI cũ không bị phá.
- [ ] Không hiển thị future actual như dữ liệu đã biết.

---

# 13. TASK 6 — LUỒNG CẬP NHẬT FUTURE FORECAST

Hiện tại hệ thống **không dùng Scheduler** và Phase 2 không thêm Scheduler.

Luồng sử dụng:

```text
python scripts/update_data.py
        ↓
PostgreSQL actual mới
        ↓
python analysis/ml/08_future_forecast.py
        ↓
Refresh Future Forecast 7 ngày
```

Mục tiêu là mỗi lần actual data được cập nhật, khi chạy forecast lại thì forecast tự lấy actual cuối mới nhất.

## Cấm

Không tự biến `update_data.py` thành:

- Scheduler.
- Background service.
- Airflow DAG.
- Cron service.

Nếu Agent cho rằng cần tích hợp trực tiếp forecast vào `update_data.py`, phải **STOP và báo cáo trước**, không tự sửa.

---

# 14. TASK 7 — INTEGRATION TEST

## Test 1 — Forecast hiện tại

Với actual cuối hiện tại:

```text
2026-09-30 23:00
```

Expected:

```text
2026-10-01 00:00
→
2026-10-07 23:00
Rows = 168
```

## Test 2 — Không leakage

Xác nhận mỗi bước chỉ dùng:

```text
actual history
+
previous predictions
```

## Test 3 — Rerun

Chạy forecast lại.

Expected:

```text
Future-v1 không duplicate
Historical 1.0 không đổi
```

## Test 4 — Database integrity

Kiểm tra:

```text
trips
hourly_demand
historical predictions
future predictions
```

## Test 5 — Dashboard

HTTP status:

```text
200
```

và Future Forecast đủ 168 điểm.

---

# 15. TASK 8 — REGRESSION TEST

Phase 2 không được làm hỏng Phase 1/v1.0.

Kiểm tra:

```text
trips
hourly_demand
Kafka
Spark
Historical Prediction
Dashboard
```

Đặc biệt:

```text
Historical Random Forest / 1.0
```

phải còn nguyên.

---

# 16. TASK 9 — DOCUMENTATION / HANDOVER

Sau khi hoàn thành, cập nhật tài liệu phù hợp:

```text
docs/PHASE1_PROGRESS.md
docs/FUTURE_FORECAST_HANDOVER.md
```

Chỉ cập nhật phần trạng thái thực tế; không sửa các tài liệu NV1 cũ chỉ để “đồng bộ”.

Phải ghi:

- latest actual timestamp;
- forecast start/end;
- horizon = 168h;
- model = Random Forest;
- version = future-v1;
- output file;
- PostgreSQL status;
- test results;
- limitations.

---

# 17. QUY TẮC PHẠM VI — BẮT BUỘC

Nếu phát hiện vấn đề ngoài Phase 2:

```text
→ ghi nhận
→ báo cáo
→ KHÔNG tự sửa
```

Các nội dung không tự mở rộng:

```text
Station Map
Heatmap
Kafka architecture
Spark architecture
Scheduler
Cloud
Model mới
Deep Learning
UI redesign
```

Ưu tiên:

```text
Tái sử dụng
    ↓
Bổ sung module mới
    ↓
Sửa tối thiểu
    ↓
Không rewrite
```

---

# 18. BẢO VỆ PHASE 1

Ưu tiên giữ nguyên:

```text
scripts/update_data.py
producer/
spark/
Kafka
Spark checkpoints
PostgreSQL schema
Historical Prediction
```

Không sửa Phase 1 nếu không trực tiếp cần cho Future Forecast.

---

# 19. CẤM DESTRUCTIVE COMMAND

AI Agent **KHÔNG ĐƯỢC tự ý chạy**:

```text
docker compose down -v
docker system prune
DROP TABLE
TRUNCATE
DELETE FROM predictions
DELETE FROM trips
DELETE FROM hourly_demand
```

Nếu cần thao tác dữ liệu thật:

> **STOP và hỏi người dùng trước.**

Không tự ý cleanup bằng SQL.

---

# 20. DEPENDENCY

Trước `pip install` / `npm install`:

1. Kiểm tra dependency hiện tại.
2. Xác định có thực sự cần không.
3. Báo cáo lý do.
4. Chỉ cài khi cần.

Không thêm dependency lớn để giải quyết vấn đề có thể xử lý bằng code hiện tại.

---

# 21. GIT / CHECKPOINT

Trước Phase 2:

```text
git status
git diff
```

Phải có checkpoint Phase 1 ổn định.

Sau mỗi Task lớn:

```text
git status
git diff
test
```

Không commit:

```text
.env
credentials
secrets
database dumps
```

---

# 22. QUY TRÌNH LÀM VIỆC VỚI AI AGENT

Trước mỗi Task:

```text
1. Đọc TASK_PHASE2.md.
2. Đọc file liên quan.
3. Xác định phạm vi.
4. Kiểm tra code hiện tại.
5. Nêu kế hoạch ngắn.
6. Chỉ sau đó mới sửa code.
```

Không được tự động chạy chuỗi:

```text
Task 2 → Task 3 → Task 4 → Dashboard
```

Mỗi Task phải được kiểm tra trước khi chuyển Task tiếp theo.

---

# 23. BẮT BUỘC BÁO CÁO SAU MỖI TASK

Agent phải báo cáo:

```text
## Task X — Completed

### 1. Files changed
- ...

### 2. Changes
- ...

### 3. Commands/tests
- ...

### 4. Results
- PASS/FAIL

### 5. Acceptance Criteria
- [x] ...
- [ ] ...

### 6. Remaining issues
- ...

### 7. Out-of-scope findings
- ...
```

Nếu có FAIL:

> Không được đánh dấu Task hoàn thành.

---

# 24. QUY TẮC STOP VÀ HỎI NGƯỜI DÙNG

Agent phải STOP nếu:

1. Schema PostgreSQL khác dự kiến.
2. Random Forest hiện tại không thể tái sử dụng.
3. Cần sửa Historical Prediction.
4. Cần sửa Kafka/Spark pipeline.
5. Cần xóa/sửa dữ liệu thật.
6. Cần thay đổi database schema.
7. Cần thêm dependency lớn.
8. Cần thay đổi kiến trúc.
9. Cần Scheduler/Airflow.
10. Acceptance Criteria không thể đạt bằng thiết kế hiện tại.

Không tự suy đoán để tiếp tục.

---

# 25. ACCEPTANCE CRITERIA TOÀN PHASE 2

Chỉ đánh dấu:

```text
🟢 PHASE 2 — COMPLETED
```

khi tất cả đạt:

- [ ] Latest actual lấy động từ PostgreSQL.
- [ ] Forecast start = latest actual + 1 hour.
- [ ] Đúng 168 timestamps.
- [ ] Đúng 7 ngày.
- [ ] Không duplicate `target_time`.
- [ ] Không future actual leakage.
- [ ] Recursive Forecasting hoạt động.
- [ ] Random Forest được tái sử dụng.
- [ ] Future `model_version = future-v1`.
- [ ] Future `actual_demand = NULL`.
- [ ] Historical `Random Forest / 1.0` vẫn tồn tại.
- [ ] Future Forecast lưu PostgreSQL.
- [ ] Future Forecast xuất CSV.
- [ ] Dashboard hiển thị 7 ngày.
- [ ] Historical Prediction vẫn hoạt động.
- [ ] Phase 1 pipeline không bị phá.
- [ ] Rerun an toàn.
- [ ] Integration Test PASS.
- [ ] Regression Test PASS.
- [ ] Không có thay đổi ngoài phạm vi chưa được phê duyệt.

---

# 26. PHẠM VI SAU PHASE 2

Không đưa vào Phase 2:

```text
Station Map
Heatmap
Forecast Member/Casual
Forecast Electric/Classic
Inventory prediction
Airflow
Kubernetes
Cloud
Deep Learning
```

---

# 27. LUỒNG HOÀN CHỈNH SAU PHASE 2

```text
Citi Bike
    ↓
python scripts/update_data.py
    ↓
Detect new data
    ↓
Download
    ↓
Validate
    ↓
Kafka
    ↓
Spark
    ↓
PostgreSQL
    ↓
Latest Actual
    ↓
python analysis/ml/08_future_forecast.py
    ↓
Recursive Random Forest
    ↓
168 future hours
    ↓
Validate
    ↓
PostgreSQL predictions
    ↓
Dashboard
```

Không Scheduler.

Không real-time requirement.

Không thay đổi Kafka → Spark → PostgreSQL.

---

# 28. KẾT QUẢ BÀN GIAO PHASE 2

```text
1. 08_future_forecast.py
2. future_forecast.csv
3. Future Forecast trong PostgreSQL
4. Dashboard Future Forecast
5. Test results
6. Regression results
7. Documentation
8. Git checkpoint/commit
```

Thông tin bàn giao:

```text
Latest Actual
Forecast Start
Forecast End
Forecast Rows = 168
Model = Random Forest
Model Version = future-v1
Historical Prediction = preserved
```

---

# 29. NGUYÊN TẮC CUỐI CÙNG

> **Phase 2 chỉ làm Future Demand Forecast 7 ngày.**

> **Không vì thấy cơ hội cải tiến mà tự mở rộng sang chức năng khác.**

> **Không sửa cái đang chạy tốt nếu không bắt buộc.**

> **Không dùng future actual để tạo future prediction.**

> **Không destructive operation nếu chưa được người dùng cho phép.**

> **Không tự chuyển sang kiến trúc phức tạp hơn.**

Ưu tiên:

```text
Đúng phạm vi
    ↓
Đúng dữ liệu
    ↓
Không leakage
    ↓
Ổn định
    ↓
Dễ kiểm thử
    ↓
Dễ bàn giao
```

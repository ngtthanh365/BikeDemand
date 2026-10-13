# FUTURE FORECAST HANDOVER — BIKEDEMAND v2.0

## 1. Trạng thái Hoàn thành Nghiệm thu (Handover Status)

Giai đoạn Phase 2 — Future Demand Forecast (7 ngày / 168 giờ) đã hoàn thành toàn diện và nghiệm thu đạt 100% PASS:

```text
Historical Prediction (Phase 1) = DONE (Random Forest / 1.0 — 4,176 rows)
Future Demand Forecast (Phase 2) = DONE (Random Forest / future-v1 — 168 rows)
Integration & Regression Tests  = DONE (100% PASS)
Dashboard Streamlit (Port 8501) = DONE (HTTP 200 OK — Section 5 Live)
```

---

## 2. Thông số Kỹ thuật Bàn giao Bắt buộc

| Thông số bàn giao | Giá trị thực tế đã nghiệm thu |
|---|---|
| **Mốc thời gian thực tế mới nhất (`latest_actual`)** | `2026-09-30 23:00:00` (Xác định động từ PostgreSQL `hourly_demand`) |
| **Mốc thời gian bắt đầu dự báo (`forecast_start`)** | `2026-10-01 00:00:00` (`latest_actual + 1 hour`) |
| **Mốc thời gian kết thúc dự báo (`forecast_end`)** | `2026-10-07 23:00:00` (`latest_actual + 168 hours`) |
| **Chu kỳ dự báo (`forecast_horizon`)** | **168 giờ liên tục (7 ngày)**, strictly 1 giờ giữa các mốc liên tiếp |
| **Thuật toán & Mô hình (`model_name`)** | **Random Forest Regressor** (`n_estimators=200`, `max_depth=15`, `random_state=42`) |
| **Phiên bản mô hình (`model_version`)** | **`future-v1`** |
| **Nhãn thực tế tương lai (`actual_demand`)** | **`NULL`** (168/168 dòng đều là NULL, tuyệt đối không leakage) |
| **File kết quả xuất ra (`output_file`)** | [analysis/outputs/ml/future_forecast.csv](file:///d:/BigData/BikeDemand/analysis/outputs/ml/future_forecast.csv) (19,105 bytes, 168 rows) |
| **Trạng thái bảng `predictions` PostgreSQL** | **4,344 dòng tổng cộng**:<br>• `Random Forest / 1.0`: 4,176 dòng (H1 2026, 0 NULL actual)<br>• `Random Forest / future-v1`: 168 dòng (100% NULL actual) |
| **Kết quả kiểm thử tự động** | • `tests/test_future_forecast_integration.py`: **6/6 PASS**<br>• `tests/test_validate_data.py`: **8/8 PASS** |
| **Giao diện Dashboard Streamlit** | [http://localhost:8501](http://localhost:8501) • **HTTP 200 OK** • Section **🔮 Future Demand Forecast** |

---

## 3. Kiến trúc Luồng Dự báo Tương lai (Future Forecast Pipeline Architecture)

```text
Citi Bike S3 (Dữ liệu mới)
        │
        ▼
python scripts/update_data.py (Tải, validate, Kafka, Spark aggregate)
        │
        ▼
PostgreSQL: Bảng hourly_demand cập nhật MAX(timestamp) mới
        │
        ▼
python analysis/ml/08_future_forecast.py
        │
        ├─► [1/5] Lấy động latest_actual = MAX(timestamp) từ DB
        ├─► [2/5] Huấn luyện Random Forest in-memory trên 6,384 mẫu hợp lệ
        ├─► [3/5] Trích xuất 168 giờ lịch sử trực tiếp làm buffer ban đầu
        ├─► [4/5] Chạy Recursive Forecasting 168 bước (No Future Leakage)
        ├─► [5/5] Xuất file analysis/outputs/ml/future_forecast.csv
        └─► [6/6] Ghi đè an toàn vào bảng predictions (future-v1, actual=NULL)
        │
        ▼
Streamlit Dashboard (http://localhost:8501)
        └─► load_future_forecast_data() tự động nạp 168 điểm dự báo
```

---

## 4. Hướng dẫn Vận hành Thủ công (Runbook)

Hệ thống tuân thủ nguyên tắc **Không Scheduler / Không Daemon / Không Cron ngầm**, vận hành hoàn toàn theo mô hình **On-Demand**:

### Bước 1: Cập nhật dữ liệu thực tế mới
```powershell
python scripts/update_data.py
```
- Tự động phát hiện dữ liệu tháng mới trên Citi Bike S3, tải về, làm sạch và nạp vào PostgreSQL.
- Nếu chưa có tháng mới, script báo `[CHECK] No new data detected` và thoát an toàn với mã `0`.

### Bước 2: Tạo và làm mới dự báo 7 ngày tiếp theo
```powershell
python analysis/ml/08_future_forecast.py
```
- Tự động lấy `latest_actual` mới nhất từ PostgreSQL, huấn luyện Random Forest in-memory và tạo đúng 168 giờ dự báo tiếp theo.
- Tự động lưu vào CSV và cập nhật bảng `predictions` với phiên bản `future-v1`.

### Bước 3: Kiểm tra kết quả trong Database và Dashboard
- **Kiểm tra cơ sở dữ liệu:**
  ```powershell
  python -c "from database.postgres import get_connection; conn=get_connection(); cur=conn.cursor(); cur.execute('SELECT model_name, model_version, COUNT(*), MIN(target_time), MAX(target_time) FROM predictions GROUP BY model_name, model_version ORDER BY model_name, model_version;'); print(cur.fetchall()); conn.close()"
  ```
  *Kỳ vọng:* `1.0` có đúng 4,176 dòng; `future-v1` có đúng 168 dòng.
- **Mở Dashboard Streamlit:**
  ```powershell
  streamlit run dashboard/app.py
  ```
  Truy cập tại `http://localhost:8501`. Section **🔮 Future Demand Forecast** hiển thị 5 thẻ KPI, biểu đồ Plotly 168 giờ và bảng dữ liệu chi tiết.

---

## 5. Cẩm nang Xử lý Sự cố Cơ bản (Troubleshooting Guide)

| Tình huống sự cố | Nguyên nhân | Hướng dẫn xử lý |
|---|---|---|
| **Lỗi kết nối PostgreSQL** (`psycopg2.OperationalError`) | Container PostgreSQL đang dừng | Chạy `docker compose up -d postgres` và kiểm tra lại cổng 5432. |
| **Bảng `hourly_demand` rỗng** | Chưa có dữ liệu tổng hợp giờ trong DB | Chạy `python scripts/update_data.py` để nạp dữ liệu chuyến đi và kích hoạt Spark aggregation. |
| **Thông báo `No new data detected`** | Chưa có tháng mới trên S3 | Bình thường. Để cập nhật forecast trên dữ liệu hiện có, chạy trực tiếp `python analysis/ml/08_future_forecast.py`. |
| **Dashboard hiển thị dự báo cũ** | Cache Streamlit đang giữ bản ghi cũ | Bấm phím `R` trên Dashboard hoặc chọn `Clear cache` $\rightarrow$ `Rerun` (cache tự động refresh sau 60 giây). |
| **Cổng 8501 bị chiếm dụng** | Tiến trình Streamlit khác đang chạy | Truy cập trực tiếp `http://localhost:8501` hoặc đóng tiến trình cũ trước khi chạy lại. |

---

## 6. Các Giới hạn Kỹ thuật (Known Limitations)

1. **Huấn luyện In-Memory:** Mô hình Random Forest được fit trực tiếp trong RAM mỗi khi chạy dự báo (khoảng 10-15s) để học từ dữ liệu mới nhất mà không ghi đè lên file trọng số Phase 1.
2. **Độ dài lịch sử tối thiểu:** Cần tối thiểu 168 giờ lịch sử liên tục trước mốc dự báo để đủ buffer tính toán `lag_168` và `rolling_7d`.
3. **Phụ thuộc PostgreSQL:** Yêu cầu container PostgreSQL đang chạy và có sẵn bảng `hourly_demand`.
4. **Không tự động kích hoạt:** Hệ thống không tự động lên lịch chạy ngầm; người vận hành cần chủ động kích hoạt lệnh khi có nhu cầu làm mới dự báo.

---

## 7. Danh mục File Bàn giao

1. **Engine dự báo:** [analysis/ml/08_future_forecast.py](file:///d:/BigData/BikeDemand/analysis/ml/08_future_forecast.py)
2. **Script nạp DB phụ trợ:** [analysis/ml/09_save_future_forecast_to_postgres.py](file:///d:/BigData/BikeDemand/analysis/ml/09_save_future_forecast_to_postgres.py)
3. **File CSV kết quả:** [analysis/outputs/ml/future_forecast.csv](file:///d:/BigData/BikeDemand/analysis/outputs/ml/future_forecast.csv)
4. **Bộ test tích hợp:** [tests/test_future_forecast_integration.py](file:///d:/BigData/BikeDemand/tests/test_future_forecast_integration.py)
5. **Dashboard giao diện:** [dashboard/app.py](file:///d:/BigData/BikeDemand/dashboard/app.py) & [dashboard/components/charts.py](file:///d:/BigData/BikeDemand/dashboard/components/charts.py)
6. **Data service:** [dashboard/services/data_loader.py](file:///d:/BigData/BikeDemand/dashboard/services/data_loader.py) & [database/postgres.py](file:///d:/BigData/BikeDemand/database/postgres.py)
7. **Tài liệu theo dõi tiến độ:** [docs/PHASE2_PROGRESS.md](file:///d:/BigData/BikeDemand/docs/PHASE2_PROGRESS.md)
8. **Tài liệu bàn giao:** [docs/FUTURE_FORECAST_HANDOVER.md](file:///d:/BigData/BikeDemand/docs/FUTURE_FORECAST_HANDOVER.md)

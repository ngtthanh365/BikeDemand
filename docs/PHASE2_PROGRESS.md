# PHASE 2 PROGRESS — FUTURE DEMAND FORECAST

## 1. Trạng thái tổng thể

| Thông tin | Chi tiết |
|---|---|
| Project | BikeDemand v2.0 |
| Phase | Phase 2 — Future Demand Forecast (7 ngày / 168 giờ) |
| Task hiện tại | **Task 0: Checkpoint & Baseline** — 🟡 **Đang xác nhận Git Checkpoint** |
| Task tiếp theo | Task 1: Khảo sát ML Pipeline hiện tại (Chờ reviewer phê duyệt) |
| Ngày thực hiện | 2026-10-12 |

---

## 2. Tiến độ các Task

- [x] **Task 0: Checkpoint & Baseline** (🟡 Đã kiểm tra xong hệ thống & Git; đang chờ reviewer chốt phương án tạo Git Checkpoint an toàn).
- [ ] **Task 1: Khảo sát ML Pipeline hiện tại** (⬜ Chưa thực hiện).
- [ ] **Task 2: Future Forecast Engine (168h)** (⬜ Chưa thực hiện).
- [ ] **Task 3: Validate Future Forecast** (⬜ Chưa thực hiện).
- [ ] **Task 4: Lưu Future Forecast vào PostgreSQL (`future-v1`)** (⬜ Chưa thực hiện).
- [ ] **Task 5: Dashboard Future Forecast (168h visual)** (⬜ Chưa thực hiện).
- [ ] **Task 6: Luồng cập nhật Future Forecast** (⬜ Chưa thực hiện).
- [ ] **Task 7: Integration Test** (⬜ Chưa thực hiện).
- [ ] **Task 8: Regression Test Phase 1** (⬜ Chưa thực hiện).
- [ ] **Task 9: Documentation & Handover** (⬜ Chưa thực hiện).

---

## 3. Chi tiết kết quả Task 0 — Checkpoint & Baseline

### 3.1. Git Status & Repository State
- **Branch:** `main` (đồng bộ với `origin/main` ở commit `3dd3cef`).
- **Recent commit:** `3dd3cef update` (ngày 05/10/2026 bởi Hoang <hoang20052810@gmail.com>).
- **Git Stash tồn tại:** `stash@{0}: On main: backup FINAL_SYSTEM_DESIGN before member2 integration`.

### 3.2. Phân loại chi tiết các thay đổi trong Working Tree

#### Nhóm 1: Modified Source Code (Mã nguồn đã sửa trong Phase 1)
| File | Loại thay đổi | Mục đích trong Phase 1 |
|---|---|---|
| `producer/kafka_producer.py` | +257 / -56 dòng | Idempotency state (`.kafka_producer_state.json`), phát hiện tháng mới, log chuẩn `[KAFKA]` |
| `spark/aggregate_demand.py` | +300 / -172 dòng | Idempotent write vào `hourly_demand`, phát hiện không có data mới, log chuẩn `[SPARK_AGG]` |
| `spark/spark_streaming.py` | +286 / -82 dòng | Idempotent write vào `trips`, log chuẩn `[SPARK_STREAM]`, resume checkpoint an toàn |

#### Nhóm 2: Modified ML Output Artifacts (Kết quả ML chạy lại sau khi cập nhật dữ liệu)
| File | Nội dung |
|---|---|
| `analysis/outputs/figures/random_forest_error.png` | Biểu đồ sai số mô hình Random Forest |
| `analysis/outputs/ml/dashboard_daily_demand.csv` | Tổng hợp nhu cầu theo ngày xuất cho Dashboard |
| `analysis/outputs/ml/dashboard_hourly_demand.csv` | Tổng hợp nhu cầu theo giờ xuất cho Dashboard |
| `analysis/outputs/ml/dashboard_model_metrics.csv` | Metrics MAE, RMSE, R2 của các mô hình |
| `analysis/outputs/ml/dashboard_prediction.csv` | Dữ liệu dự đoán phục vụ hiển thị Dashboard |
| `analysis/outputs/ml/dashboard_prediction_full.csv` | Toàn bộ tập dữ liệu dự đoán lịch sử |
| `analysis/outputs/ml/model_comparison.csv` | So sánh hiệu năng Linear Regression, RF, GBDT |
| `analysis/outputs/ml/random_forest_error_by_day.csv` | Phân tích sai số RF theo ngày trong tuần |
| `analysis/outputs/ml/random_forest_error_by_hour.csv` | Phân tích sai số RF theo khung giờ |
| `analysis/outputs/ml/random_forest_error_summary.csv` | Thống kê tổng hợp sai số RF |
| `analysis/outputs/ml/random_forest_metrics.csv` | Metrics chi tiết mô hình Random Forest |
| `analysis/outputs/ml/random_forest_predictions.csv` | Tập kết quả dự đoán của Random Forest |

#### Nhóm 3: Untracked Scripts Phase 1 (Mã nguồn mới tạo trong Phase 1)
| File | Vai trò |
|---|---|
| `scripts/update_data.py` | Entry point 1 lệnh chạy toàn bộ pipeline tự động cập nhật dữ liệu tháng mới |
| `scripts/download_data.py` | Tải dữ liệu tự động từ AWS S3 Citi Bike bucket |
| `scripts/validate_data.py` | Xác thực, làm sạch dữ liệu và kiểm tra cấu trúc file tải về |
| `scripts/test_idempotency.py` | Test suite kiểm thử tính bất biến (Idempotency) 5 tầng pipeline |
| `scripts/test_logging_errors.py` | Test suite kiểm thử chuẩn hóa 9 tag logging và bắt ngoại lệ |

#### Nhóm 4: Untracked Tests
| File | Vai trò |
|---|---|
| `tests/test_validate_data.py` | Unit test cho module validate dữ liệu |

#### Nhóm 5: Untracked Documents (Tài liệu đặc tả & theo dõi)
| File | Vai trò |
|---|---|
| `docs/TASK_PHASE1.md` | Đặc tả yêu cầu và kế hoạch 10 task của Phase 1 |
| `docs/PHASE1_PROGRESS.md` | Nhật ký tiến độ chi tiết quá trình hoàn thành Phase 1 |
| `docs/PHASE1_PROGRESS_FINAL.md` | Báo cáo nghiệm thu hoàn tất Phase 1 |
| `docs/BikeDemand_Specification_v2.0.md` | Tài liệu đặc tả kỹ thuật hệ thống BikeDemand v2.0 |
| `docs/TASK_PHASE2.md` | Nhiệm vụ chính thức triển khai Phase 2: Future Demand Forecast |
| `docs/PHASE2_PROGRESS.md` | Nhật ký tiến độ triển khai Phase 2 |

### 3.3. Đánh giá trạng thái lưu trữ trong Git & Cảnh báo rủi ro
- **Tình trạng hiện tại:** Commit gần nhất trên Git là `3dd3cef` (từ ngày 05/10/2026), tức là **toàn bộ mã nguồn cốt lõi, script mới, test suite và tài liệu của Phase 1 CHƯA ĐƯỢC COMMIT VÀO GIT**.
- **Cảnh báo rủi ro nghiêm trọng:**
  > [!CAUTION]
  > Nếu người dùng hoặc agent vô tình thực hiện các lệnh như `git reset --hard`, `git checkout -- .`, `git clean -fd`, hoặc `git pull` gây conflict thì **toàn bộ thành quả Phase 1 đang ở Working Tree sẽ bị mất vĩnh viễn hoặc bị ghi đè**.
  > Do đó, việc tạo Checkpoint Git lưu giữ trạng thái Phase 1 trước khi bắt tay vào code Phase 2 là **bắt buộc và tối quan trọng**.

---

### 3.4. Đề xuất phương án tạo Checkpoint trước Phase 2

AI Agent đề xuất 3 phương án bảo vệ trạng thái an toàn:

#### Phương án 1 (Khuyến nghị cao nhất — Tách branch an toàn kép):
- **Ý tưởng:** Tạo một branch riêng lưu lại toàn bộ Phase 1, sau đó mở branch mới cho Phase 2.
- **Các bước thực hiện:**
  ```bash
  # 1. Tạo branch checkpoint Phase 1 từ trạng thái hiện tại
  git checkout -b phase1-baseline-checkpoint

  # 2. Stage mã nguồn, test, script, tài liệu và output Phase 1
  git add producer/ spark/ scripts/ tests/ docs/ analysis/outputs/

  # 3. Commit checkpoint
  git commit -m "feat(phase1): checkpoint complete Phase 1 pipeline, tests and documentation"

  # 4. Tạo branch làm việc riêng cho Phase 2
  git checkout -b phase2-future-forecast
  ```
- **Ưu điểm:**
  - Giữ an toàn 100% Phase 1 trên branch `phase1-baseline-checkpoint`.
  - Mọi thay đổi của Phase 2 diễn ra trên branch `phase2-future-forecast`, branch `main` không bị xáo trộn.
  - Có thể so sánh `git diff` giữa Phase 2 và Phase 1 bất kỳ lúc nào.

#### Phương án 2 (Commit checkpoint trực tiếp trên branch `main`):
- **Ý tưởng:** Commit toàn bộ Phase 1 vào branch `main` hiện tại trước khi bắt đầu Phase 2.
- **Các bước thực hiện:**
  ```bash
  git add producer/ spark/ scripts/ tests/ docs/ analysis/outputs/
  git commit -m "feat(phase1): complete Phase 1 automatic data pipeline checkpoint"
  ```
- **Ưu điểm:** Đơn giản, giữ một nhánh làm việc duy nhất.
- **Nhược điểm:** Thay đổi trực tiếp lịch sử commit trên `main`.

#### Phương án 3 (Backup vật lý ra thư mục dự phòng độc lập):
- **Ý tưởng:** Sao chép các thư mục quan trọng sang một thư mục backup nằm ngoài git repository (ví dụ `d:\BigData\BikeDemand_phase1_backup_20261012`) trước khi thực hiện thao tác Git.
- **Ưu điểm:** Zero-risk, độc lập hoàn toàn với Git.

---

### 3.5. PostgreSQL Baseline
Kết quả truy vấn trực tiếp từ cơ sở dữ liệu `citibike`:
- **Bảng `trips`:** `742,615` records (`2026-01-01 00:05:49` → `2026-09-30 23:55:36`).
- **Bảng `hourly_demand`:** `6,459` rows (`2026-01-01 00:00:00` → `2026-09-30 23:00:00`), tổng demand: `742,615` (Khớp 100% với `trips`).
- **Bảng `predictions` (Historical):** `4,176` rows (`Random Forest / 1.0`, target: `2026-01-08 00:00:00` → `2026-06-30 23:00:00`).
- **Bảng `predictions` (Future):** `0` rows (Chưa triển khai, đúng yêu cầu).

### 3.6. Docker & Infrastructure
- 4/4 containers UP: `citibike-postgres`, `citibike-kafka`, `citibike-spark-master`, `citibike-spark-worker`.
- Kafka topic `citibike-trips`: 3 partitions, tổng offset `849,232`.
- Spark checkpoints: 2 checkpoint directories trong `/tmp/` của Spark Master còn nguyên vẹn.
- Dashboard: Streamlit `1.65.0` phản hồi HTTP `200` OK.

---

## 4. Các mục chưa xác nhận (Chờ Reviewer phê duyệt)

- [ ] **Lựa chọn phương án Checkpoint:** Reviewer chọn Phương án 1 (Branch riêng), Phương án 2 (Commit trên main), hay Phương án 3 (Backup ngoài).
- [ ] **Phạm vi commit artifacts:** Xác nhận có commit các file CSV/PNG trong `analysis/outputs/` hay chỉ commit source code (`producer/`, `spark/`, `scripts/`, `tests/`, `docs/`).
- [ ] **Phê duyệt hoàn tất Task 0:** Sau khi chốt phương án checkpoint, chính thức đóng Task 0 và chuyển sang Task 1 (Khảo sát ML Pipeline).

> **Lưu ý:** Agent tuân thủ nghiêm ngặt quy tắc an toàn: Không tự ý commit, reset hay thay đổi repository khi chưa có chỉ thị từ reviewer.

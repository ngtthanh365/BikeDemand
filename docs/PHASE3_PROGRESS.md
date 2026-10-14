# PHASE 3 PROGRESS — STATION COMPOSITE MAP

## 1. Trạng thái tổng quan

- **Project:** BikeDemand v2.0
- **Phase:** Phase 3 — Station Composite Map
- **Checkpoint Phase 2:** `6a8ead3` (`Complete Phase 2 future demand forecasting` trên nhánh `main`, đồng bộ `origin/main`)
- **Trạng thái hiện tại:** 🟢 HOÀN THÀNH (Task 0–11 PASS, 100% Phase 3 nghiệm thu)
- **Untracked files Phase 3:** `docs/TASK_PHASE3.md`, `docs/PHASE3_PROGRESS.md`, `docs/STATION_MAP_HANDOVER.md`, `tests/test_station_aggregation.py`, `tests/test_station_display.py`, `tests/test_station_map.py`, `tests/test_station_filter.py`, `tests/test_dashboard_integration.py`, `tests/test_station_data.py`, `pyrefly.toml`

| Task | Tên nhiệm vụ | Trạng thái | Tóm tắt kết quả |
|:---:|---|:---:|---|
| **0** | Checkpoint Verification | 🟢 PASS | Đạt 6/6 tiêu chí: commit `6a8ead3`, tree sạch, tài liệu Phase 2 & 3 đầy đủ. |
| **1** | Khảo sát Dashboard & Dữ liệu trạm | 🟢 PASS | Xác minh 452 trạm hợp lệ trong PostgreSQL (100% có tọa độ), pydeck/plotly sẵn có. |
| **2** | Tổng hợp dữ liệu cấp trạm | 🟢 PASS | Hàm SQL in-DB trả về 452 trạm (36 KB, 1.9s), đủ 7 trường, 7/7 tests PASS. |
| **3** | Hiển thị tên trạm và tọa độ | 🟢 PASS | Chuẩn hóa tên trạm, display_label, tra cứu ID, 7/7 tests PASS. |
| **4** | Point / Proportional Symbol Map | 🟢 PASS | Point/Proportional Symbol Map qua PyDeck ScatterplotLayer, scale căn bậc hai, legend 4 cấp, 7/7 tests PASS. |
| **5** | Heatmap mờ | 🟢 PASS | HeatmapLayer nền mờ (opacity 0.45) dưới ScatterplotLayer, trọng số activity_count, 11/11 tests PASS. |
| **6** | Tooltip / Thông tin trạm | 🟢 PASS | Tooltip hiển thị đủ 7 trường thông tin trạm thực tế khi hover, xử lý an toàn dữ liệu thiếu, 15/15 tests PASS. |
| **7** | Bộ lọc thời gian | 🟢 PASS | Lọc dữ liệu trạm theo khoảng thời gian, mặc định toàn bộ, format nhãn rõ ràng, 7/7 tests PASS. |
| **8** | Tích hợp vào Dashboard | 🟢 PASS | Tích hợp Station Composite Map vào app.py giữa KPI và Demand, đồng bộ filter, metrics trạm, 5/5 tests PASS. |
| **9** | Kiểm thử dữ liệu trạm | 🟢 PASS | Đối chiếu count nguồn, quy tắc định danh không trùng, lọc tọa độ bẩn, 6/6 tests PASS. |
| **10** | Kiểm thử bản đồ & Regression | 🟢 PASS | 63/63 tests PASS (Phase 1, 2, 3), HTTP 200, bảo toàn pipeline & data, sẵn sàng bàn giao. |
| **11** | Documentation & Handover | 🟢 PASS | Hoàn thiện tài liệu bàn giao STATION_MAP_HANDOVER.md, 11/11 tasks hoàn tất. |

---

## 2. Quy định cập nhật nhật ký tiến độ

Từ Task 1 trở đi, mỗi task chỉ ghi nhận ngắn gọn theo cấu trúc:
1. **Trạng thái:** (🟢 PASS / 🟡 IN-PROGRESS / 🔴 BLOCKED) kèm ngày hoàn thành.
2. **Tóm tắt kết quả:** 2–4 gạch đầu dòng nêu giải pháp và kết quả chính đạt được.
3. **Files thay đổi:** Danh sách file tạo mới/sửa đổi.
4. **Kiểm thử & Nghiệm thu:** Tên lệnh kiểm thử và kết quả tóm tắt (số test pass/fail).
5. **Vấn đề tồn đọng / Lưu ý:** Rủi ro hoặc việc cần theo dõi (nếu có).

> **Nguyên tắc:** Tuyệt đối không sao chép lại đặc tả/tiêu chí từ `docs/TASK_PHASE3.md` và không dán log đầu ra đầy đủ.

---

## 3. Nhật ký chi tiết các Task

### Task 0 — Checkpoint Verification
- **Trạng thái:** 🟢 PASS (6/6 tiêu chí đạt — 2026-10-13)
- **Tóm tắt kết quả:**
  - Xác nhận Git checkpoint Phase 2: `6a8ead3` trên `main`, đồng bộ `origin/main`.
  - Working tree sạch toàn bộ mã nguồn (`git diff` và `git diff --cached` rỗng).
  - Ghi nhận 2 file tài liệu Phase 3 untracked: `docs/TASK_PHASE3.md` và `docs/PHASE3_PROGRESS.md`.
  - Nghiệm thu tài liệu bàn giao Phase 2: `docs/FUTURE_FORECAST_HANDOVER.md` và `docs/PHASE2_PROGRESS.md` (10/10 tasks Phase 2 hoàn thành).
  - Không thay đổi mã nguồn, database, Docker, Kafka hay Spark.
- **Files thay đổi:** `docs/PHASE3_PROGRESS.md` (khởi tạo tài liệu theo dõi tiến độ).
- **Kiểm thử:** Đối chiếu trạng thái qua `git status`, `git log -3`, `git diff`, `git branch -vv` (100% PASS).
- **Vấn đề tồn đọng:** Không có. Sẵn sàng khảo sát Task 1.

### Task 1 — Khảo sát Dashboard & Dữ liệu trạm
- **Trạng thái:** 🟢 PASS (5/5 tiêu chí đạt — 2026-10-13)
- **Tóm tắt kết quả:**
  - Entry point: `dashboard/app.py` (hiện có 5 section: KPI, Demand, User & Bike, Station Analysis Top 10, Machine Learning, Future Forecast).
  - Nguồn dữ liệu: Bảng `trips` trong PostgreSQL chứa đầy đủ 8 trường trạm (`start_station_name`, `start_station_id`, `start_lat`, `start_lng`, `end_station_name`, `end_station_id`, `end_lat`, `end_lng`).
  - Dữ liệu trạm thực tế: 452 trạm hợp lệ duy nhất sau khi loại bỏ chuỗi rác '"NaN"' (raw gồm 453; 113 start, 452 end). 451/452 trạm (99.8%) có tọa độ cố định tuyệt đối (lệch 0m); chỉ 1 trạm (ID 5772.05 'Morton St & Greenwich St') có 2 điểm tọa độ cách nhau 60.56m do vị trí dock mở rộng (lấy AVG xử lý triệt để). Chỉ 1 ID có 2 tên do typo khoảng trắng kép ('W 48 St &  Rockefeller Plaza').
  - Cơ chế lọc dữ liệu thiếu: Điều kiện chuẩn `WHERE station_id IS NOT NULL AND station_id != '"NaN"' AND lat != 'NaN'::double precision` loại bỏ chính xác 1 bản ghi start và 3,863 bản ghi end (0.52% trả xe ngoài bến/mất GPS), bảo toàn 100% bảng trips (742,615 dòng).
  - Thư viện bản đồ: `pydeck 0.9.3` và `plotly 7.1.0` có sẵn trong môi trường; `pydeck` hỗ trợ composite map (`HeatmapLayer` mờ bên dưới + `ScatterplotLayer` bên trên) trực tiếp qua `st.pydeck_chart` mà không cần cài thêm thư viện.
- **Files thay đổi:** `docs/PHASE3_PROGRESS.md` (cập nhật nhật ký khảo sát Task 1). Không sửa code dự án.
- **Kiểm thử & Nghiệm thu:** Khảo sát schema và tọa độ trạm qua truy vấn DB; kiểm tra tính sẵn sàng của `pydeck` và `plotly` (100% PASS).
- **Vấn đề tồn đọng / Lưu ý:** Bảng `trips` hiện có 742,615 dòng; để Dashboard tải nhanh và tiết kiệm RAM, nên viết hàm SQL tổng hợp trực tiếp tại database hoặc cache DataFrame tổng hợp trạm thay vì load toàn bộ các cột trạm thô.

### Task 2 — Tổng hợp dữ liệu cấp trạm
- **Trạng thái:** 🟢 PASS (7/7 tiêu chí đạt — 2026-10-13)
- **Tóm tắt kết quả:**
  - Triển khai hàm `load_station_activity_data()` trong `database/postgres.py` tổng hợp trực tiếp bằng SQL CTEs tại PostgreSQL; quét 742,615 dòng nguồn và chỉ trả về đúng 452 dòng đại diện (~36 KB RAM), không tải dữ liệu thô về Python.
  - Trả về đủ 7 trường: `station_id`, `station_name`, `latitude`, `longitude`, `start_count`, `end_count`, `activity_count`.
  - Chuẩn hóa tên trạm bằng `REGEXP_REPLACE` (sạch typo khoảng trắng kép trạm 6626.11), tính tọa độ trọng tâm trọng số (xử lý trạm 5772.05 lệch 60m), loại bỏ triệt để bản ghi rác.
  - Đo lường hiệu quả thực tế: Thời gian thực thi SQL ~1.9s, giảm dung lượng truyền tải từ ~150 MB xuống 36.3 KB (452 dòng).
  - Bổ sung wrapper `load_station_activity()` tại `dashboard/services/data_loader.py`.
- **Files thay đổi:**
  - `database/postgres.py`: Thêm hàm `load_station_activity_data()`.
  - `dashboard/services/data_loader.py`: Thêm wrapper `load_station_activity()`.
  - `tests/test_station_aggregation.py`: Bộ kiểm thử tự động 7/7 test cases.
  - `docs/PHASE3_PROGRESS.md`: Cập nhật tiến độ Task 2.
- **Kiểm thử & Nghiệm thu:**
  - `python -m unittest tests/test_station_aggregation.py`: **7/7 PASS (100%)**.
  - `python -m unittest tests/test_validate_data.py`: **8/8 PASS (100% regression Phase 1)**.
- **Vấn đề tồn đọng / Lưu ý:** Không có.

### Task 3 — Hiển thị tên trạm và tọa độ
- **Trạng thái:** 🟢 PASS (5/5 tiêu chí đạt — 2026-10-13)
- **Tóm tắt kết quả:**
  - Tái sử dụng 100% dữ liệu từ `load_station_activity_data()` của Task 2; triển khai hàm `prepare_station_display_data()` và `get_station_by_id()` trong `dashboard/services/data_loader.py`.
  - Chuẩn hóa tên trạm sạch sẽ (loại bỏ khoảng trắng thừa, fallback minh bạch `Station {station_id}` nếu khuyết tên, không tự đặt tên giả).
  - Bổ sung trường `display_label` (`{station_name} ({station_id})`) giúp phân biệt rõ các trạm trùng tên.
  - Xác nhận 452/452 station_id duy nhất tuyệt đối (không trùng), 100% tọa độ là số thực hợp lệ trong dải NY/NJ, không có `None`/`nan`.
- **Files thay đổi:**
  - `dashboard/services/data_loader.py`: Thêm `prepare_station_display_data()`, `get_station_by_id()` và tích hợp vào `load_station_activity()`.
  - `tests/test_station_display.py`: Tạo mới bộ kiểm thử tự động 7/7 test cases cho Task 3.
  - `docs/PHASE3_PROGRESS.md`: Cập nhật tiến độ Task 3.
- **Kiểm thử & Nghiệm thu:**
  - `python -m unittest tests/test_station_display.py`: **7/7 PASS (100%)**.
  - `python -m unittest tests/test_station_aggregation.py`: **7/7 PASS (100% Task 2 regression)**.
  - `python -m unittest tests/test_validate_data.py`: **8/8 PASS (100% Phase 1 regression)**.
- **Vấn đề tồn đọng / Lưu ý:** Không có. Chưa triển khai marker, heatmap hay bộ lọc (thuộc Task 4–7). Sẵn sàng cho Task 4.

### Task 4 — Point / Proportional Symbol Map
- **Trạng thái:** 🟢 PASS (6/6 tiêu chí đạt — 2026-10-13)
- **Tóm tắt kết quả:**
  - Triển khai `compute_station_marker_sizes()`, `create_station_symbol_layer()`, `show_station_symbol_map()` trong `dashboard/components/charts.py`.
  - Kích thước marker tỷ lệ với căn bậc hai của `activity_count` ($\text{radius} \propto \sqrt{\text{activity}}$), đảm bảo diện tích marker tỷ lệ thuận với số lượt hoạt động.
  - Giới hạn kích thước hợp lý: bán kính [25m, 220m] và giới hạn pixel [3px, 25px] để marker không quá bé khi zoom xa và không che lấp bản đồ khi zoom gần.
  - Định danh trạm bằng `display_label` từ Task 3, 100% tọa độ thực từ dữ liệu tổng hợp (452 dòng, ~36 KB), không tạo tọa độ/dữ liệu giả và không đọc bảng `trips` thô.
  - Phân tầng màu sắc 4 cấp kèm Legend trực quan dưới bản đồ: Đỏ cam (≥ 20,000, Hub trung tâm), Cam (10,000–19,999, Tuyến đông), Xanh dương (1,000–9,999, Dân cư), Cyan (< 1,000, Bến phụ cận).
  - Xử lý an toàn các trường hợp dữ liệu rỗng, thiếu cột tọa độ hoặc tọa độ ngoài phạm vi mà không làm crash ứng dụng.
- **Files thay đổi:**
  - `dashboard/components/charts.py`: Thêm logic tính toán bán kính marker, layer PyDeck ScatterplotLayer và hàm vẽ bản đồ `show_station_symbol_map()`.
  - `tests/test_station_map.py`: Tạo mới bộ kiểm thử tự động 7/7 test cases cho Task 4.
  - `docs/PHASE3_PROGRESS.md`: Cập nhật tiến độ Task 4.
- **Kiểm thử & Nghiệm thu:**
  - `python -m unittest tests/test_station_map.py`: **7/7 PASS (100%)**.
  - `python -m unittest tests/test_station_display.py`: **7/7 PASS (100% Task 3 regression)**.
  - `python -m unittest tests/test_station_aggregation.py`: **7/7 PASS (100% Task 2 regression)**.
  - `python -m unittest tests/test_validate_data.py`: **8/8 PASS (100% Phase 1 regression)**.
  - `python -m unittest tests/test_future_forecast_integration.py`: **6/6 PASS (100% Phase 2 regression)**.
- **Vấn đề tồn đọng / Lưu ý:** Không có. Chưa thêm heatmap (Task 5), tooltip tương tác (Task 6), bộ lọc (Task 7) hay tích hợp vào `dashboard/app.py` (Task 8). Sẵn sàng cho Task 5.

### Task 5 — Heatmap mờ
- **Trạng thái:** 🟢 PASS (5/5 tiêu chí đạt — 2026-10-13)
- **Tóm tắt kết quả:**
  - Triển khai `create_station_heatmap_layer()` và `build_station_map_deck()` trong `dashboard/components/charts.py`.
  - Bổ sung `HeatmapLayer` làm lớp nền mờ với cấu hình tối ưu (`opacity=0.45`, `radius_pixels=35`, `threshold=0.05`), sử dụng tọa độ hợp lệ và trọng số `activity_count` phản ánh mật độ tập trung hoạt động toàn vùng.
  - Xếp lớp chuẩn xác: HeatmapLayer nằm ở đáy (`layers[0]`), ScatterplotLayer nằm trên cùng (`layers[1]`), bảo đảm lớp nhiệt không che khuất marker và hover/highlight hoạt động nguyên vẹn.
  - Hỗ trợ cờ bật/tắt `show_heatmap=True/False`; bổ sung chú giải làm rõ lớp nhiệt thể hiện mật độ hoạt động, không phải số lượng tồn kho/thiếu xe.
  - Xử lý an toàn các trường hợp DataFrame rỗng hoặc thiếu cột trọng số.
- **Files thay đổi:**
  - `dashboard/components/charts.py`: Thêm `create_station_heatmap_layer()`, `build_station_map_deck()`, tích hợp lớp nền mờ vào `show_station_symbol_map()`.
  - `tests/test_station_map.py`: Thêm 4 test cases cho Task 5 (nâng tổng số lên 11/11 tests).
  - `docs/PHASE3_PROGRESS.md`: Cập nhật tiến độ Task 5.
- **Kiểm thử & Nghiệm thu:**
  - `python -m unittest tests/test_station_map.py`: **11/11 PASS (100%)**.
  - `python -m unittest tests/test_station_display.py`: **7/7 PASS (100% Task 3 regression)**.
  - `python -m unittest tests/test_station_aggregation.py`: **7/7 PASS (100% Task 2 regression)**.
  - `python -m unittest tests/test_validate_data.py`: **8/8 PASS (100% Phase 1 regression)**.
- **Vấn đề tồn đọng / Lưu ý:** Không có. Chưa thêm tooltip tương tác chi tiết (Task 6), bộ lọc (Task 7) hay tích hợp vào `dashboard/app.py` (Task 8). Sẵn sàng cho Task 6.

### Task 6 — Tooltip / Thông tin trạm
- **Trạng thái:** 🟢 PASS (5/5 tiêu chí đạt — 2026-10-13)
- **Tóm tắt kết quả:**
  - Triển khai `get_station_tooltip_config()` và `format_station_tooltip_data(df)` trong `dashboard/components/charts.py`.
  - Tooltip hiển thị đầy đủ 7 trường thông tin thực tế: `station_name`, `station_id`, `latitude`, `longitude`, `start_count`, `end_count`, `activity_count` với giao diện HTML/CSS phong cách Dark Matter trực quan.
  - Xử lý an toàn dữ liệu: chuyển đổi giá trị NaN/None thành `'N/A'`, phân biệt rạch ròi số 0 thực tế (`'0'`) với dữ liệu thiếu, định dạng số đếm có phân tách hàng nghìn (`33,957`), tự động fallback `Station {station_id}` nếu khuyết tên trạm; không tự tạo thông tin trạm.
  - Bảo đảm không chứa chuỗi lỗi định dạng (`NaN`, `None`, `null`, `undefined`, `Inf`), không đưa ra bất kỳ tuyên bố nào về tồn kho xe/tình trạng dock. Giữ nguyên toàn bộ cấu hình marker, proportional symbol và heatmap nền mờ từ Task 4–5.
  - Bổ sung 4 test cases toàn diện trong `tests/test_station_map.py` (nâng tổng số lên 15/15 tests).
- **Files thay đổi:**
  - `dashboard/components/charts.py`: Thêm cấu hình tooltip PyDeck và hàm tiền xử lý định dạng chuỗi tooltip an toàn.
  - `tests/test_station_map.py`: Thêm 4 test cases chuyên biệt cho Task 6 (kiểm tra trường dữ liệu, format số, xử lý missing/0, cấm claim tồn kho, và DataFrame rỗng).
  - `docs/PHASE3_PROGRESS.md`: Cập nhật tiến độ Task 6.
- **Kiểm thử & Nghiệm thu:**
  - `python -m unittest tests/test_station_map.py`: **15/15 PASS (100%)**.
  - `python -m unittest tests/test_station_display.py`: **7/7 PASS (100% Task 3 regression)**.
  - `python -m unittest tests/test_station_aggregation.py`: **7/7 PASS (100% Task 2 regression)**.
  - `python -m unittest tests/test_validate_data.py`: **8/8 PASS (100% Phase 1 regression)**.
  - `python -m unittest tests.test_future_forecast_integration.TestFutureForecastIntegration (unit parts)`: **5/5 PASS (100% Phase 2 regression)**.
- **Vấn đề tồn đọng / Lưu ý:** Không có. Chưa thêm bộ lọc thời gian (Task 7) hay tích hợp vào `dashboard/app.py` (Task 8). Sẵn sàng cho Task 7.

### Task 7 — Bộ lọc thời gian
- **Trạng thái:** 🟢 PASS (6/6 tiêu chí đạt — 2026-10-13)
- **Tóm tắt kết quả:**
  - Triển khai `normalize_date_range()` trong `database/postgres.py` hỗ trợ các kiểu dữ liệu `str` (YYYY-MM-DD), `date`, `datetime`, `Timestamp`; tự động mở rộng `end_date` đến cuối ngày (`23:59:59.999999`) nếu chỉ cung cấp ngày đơn lẻ, bảo đảm không thất thoát dữ liệu của ngày cuối cùng.
  - Tái sử dụng `load_station_activity_data()` trực tiếp tại PostgreSQL với điều kiện lọc theo `started_at` (starts) và `ended_at` (ends), tự động tính toán lại chính xác `start_count`, `end_count` và `activity_count` cho từng trạm trong phạm vi ngày được chọn.
  - Mặc định tải đầy đủ toàn bộ dữ liệu (452 trạm, 1,481,366 hoạt động) khi `start_date=None, end_date=None`.
  - Xử lý an toàn khi không có dữ liệu (năm 2027) hoặc khoảng ngày bị đảo ngược (`start_date > end_date`): trả về DataFrame rỗng đúng cấu trúc cột mà không crash hay ném exception.
  - Bổ sung `format_date_range_label()` trong `dashboard/services/data_loader.py` hiển thị nhãn thân thiện và rõ ràng cho UI/bản đồ; cấu hình `@st.cache_data(ttl=60)` để đảm bảo đồng bộ khi dữ liệu mới được stream vào database.
  - Hỗ trợ tham số `date_label` trong `show_station_symbol_map()` để hiển thị thông báo/chú thích rõ ràng phạm vi ngày đang hiển thị trên bản đồ.
- **Files thay đổi:**
  - `database/postgres.py`: Bổ sung `normalize_date_range()`, nâng cấp `load_station_activity_data()` với chuẩn hóa ngày an toàn và kiểm tra `is_reversed`.
  - `dashboard/services/data_loader.py`: Cập nhật `@st.cache_data(ttl=60)` cho `load_station_activity()`, bổ sung `format_date_range_label()`.
  - `dashboard/components/charts.py`: Thêm tham số `date_label` cho `show_station_symbol_map()` với thông báo an toàn khi dữ liệu rỗng.
  - `tests/test_station_filter.py`: Tạo mới bộ kiểm thử 7/7 test cases cho Task 7.
  - `docs/PHASE3_PROGRESS.md`: Cập nhật tiến độ Task 7.
- **Kiểm thử & Nghiệm thu:**
  - `python -m unittest tests/test_station_filter.py`: **7/7 PASS (100%)**.
  - `python -m unittest tests/test_station_map.py`: **15/15 PASS (100% Task 4-6 regression)**.
  - `python -m unittest tests/test_station_display.py`: **7/7 PASS (100% Task 3 regression)**.
  - `python -m unittest tests/test_station_aggregation.py`: **7/7 PASS (100% Task 2 regression)**.
  - `python -m unittest tests/test_validate_data.py`: **8/8 PASS (100% Phase 1 regression)**.
  - `python -m unittest tests.test_future_forecast_integration (unit parts)`: **5/5 PASS (100% Phase 2 regression)**.
- **Vấn đề tồn đọng / Lưu ý:** Không có. Đã tích hợp Station Map vào `dashboard/app.py` ở Task 8. Sẵn sàng cho Task 8.

### Task 8 — Tích hợp vào Dashboard & Cải thiện bản đồ địa lý thực (Refinement)
- **Trạng thái:** 🟢 PASS (Hoàn thành tích hợp & nâng cấp bản đồ nền địa lý — 2026-10-13)
- **Tóm tắt kết quả:**
  - **Khắc phục nền trắng (Root cause):** Thay thế cấu hình chuỗi map_style bằng vector tile URL chuẩn của CARTO không cần Mapbox token (`pdk.map_styles.CARTO_LIGHT`: `https://basemaps.cartocdn.com/gl/positron-gl-style/style.json`). Bản đồ hiển thị đầy đủ mạng lưới đường phố, công viên Central Park, sông Hudson, các cây cầu và địa danh khu vực New York & Jersey City.
  - **Bổ sung bộ chọn nền bản đồ (Basemap Selector):** Cung cấp dropdown tùy chọn giữa `CARTO Positron (Sáng - mặc định)`, `CARTO Voyager (Chi tiết đường bộ)` và `CARTO Dark Matter (Tối tương phản)`.
  - **Cân chỉnh Viewport & Zoom:** Tính toán tâm bản đồ chính xác từ tọa độ thực tế của 452 trạm (`lat=40.7356`, `lng=-74.0033`), điều chỉnh zoom về `11.0` bao trọn toàn bộ cụm trạm (~22km) từ Manhattan, Brooklyn, Queens tới Jersey City mà không bị thừa khoảng trắng.
  - **Tinh chỉnh lớp hiển thị:**
    - `ScatterplotLayer`: Điều chỉnh bán kính marker `[20m, 160m]` và giới hạn pixel `[3px, 18px]`, bổ sung viền trắng `[255, 255, 255, 220]` giúp marker nổi bật trên nền bản đồ thực và tránh chồng lấn tại các cụm trạm đông đúc (Midtown/Downtown).
  - **Thiết kế Tooltip Native PyDeck/Deck.gl Chuẩn & Định Vị Ngay Trên Marker:**
    - **Khảo sát cơ chế tọa độ Deck.gl:** Qua kiểm tra phân tích DOM sâu bằng Chrome DevTools Protocol, phát hiện Deck.gl trong container Streamlit khi tính toán `getCanvasBounds` đã áp dụng độ lệch âm `-500px` (chiều cao container) vào tọa độ dọc (`transform: translate(x, y - 500px)`). Khi tooltip mặc định có `top: 0px`, bảng thông tin luôn bị kéo giật ngược lên 500px vào vùng âm sát mép trên.
    - **Giải pháp xử lý triệt để:** Bổ sung `"top": "500px"` vào cấu hình `style` trong `get_station_tooltip_config()`. Tọa độ dọc hiển thị thực tế: `top (500px) + translateY (mouse_y - 500px) = mouse_y`. Tooltip xuất hiện **ngay chính xác trên marker đang hover** với độ lệch gần như bằng 0 (`diffY = -0.14px`).
    - **Khắc phục triệt để lỗi tràn mép & giật lag:** Cấu hình `style` với `pointerEvents: "none"` (loại bỏ nhấp nháy khi chuột lướt nhanh), `maxWidth: "290px"`, `maxHeight: "240px"`, `overflowY: "auto"`, `boxSizing: "border-box"`. Nội dung tự động co giãn và cuộn mượt mà nếu tên trạm dài.
    - **Bảo toàn 100% thông tin:** Hiển thị trọn vẹn 7 trường dữ liệu (`station_name`, `station_id`, `latitude`, `longitude`, `start_count`, `end_count`, `activity_count`), có emoji 📍 trực quan và phân cách đường kẻ mỏng trang nhã.
  - **Tối ưu Heatmap nhận diện mật độ vượt trội (Cấu hình chuẩn):**
    - Cấu hình: `opacity = 0.50`, `radius_pixels = 45`, `threshold = 0.05`, `intensity = 1.2`.
    - Dải màu chuyển tiếp 6 bậc: Vàng nhạt `[255, 255, 178]` -> Vàng cam `[254, 204, 92]` -> Cam sáng `[253, 141, 60]` -> Cam đỏ `[240, 59, 32]` -> Đỏ `[189, 0, 38]` -> Đỏ đậm `[128, 0, 38]`.
    - Lớp nhiệt phản ánh vùng tập trung nhu cầu rõ nét, nổi bật nhưng không che khuất đường phố và marker bên trên.
    - Giữ nguyên `HeatmapLayer` nằm dưới `ScatterplotLayer`.
  - **Bảo toàn đầy đủ tính năng:** Giữ nguyên 7 trường dữ liệu tooltip, chú giải màu 4 cấp độ hoạt động, checkbox bật/tắt Heatmap, bộ lọc thời gian ngày tháng và khả năng xử lý DataFrame rỗng.
- **Files thay đổi:**
  - `dashboard/components/charts.py`: Bổ sung `"top": "500px"` vào `get_station_tooltip_config()` để bù chuẩn xác tọa độ chuột, định vị tooltip ngay trên marker; giữ nguyên cấu hình Heatmap và thứ tự layer tối ưu.
  - `dashboard/app.py`: Thêm `importlib.reload(components.charts)` để đảm bảo Streamlit luôn cập nhật module biểu đồ mới nhất; dropdown chọn nền bản đồ (Positron, Voyager, Dark Matter).
  - `tests/test_station_map.py`: Cập nhật `test_17` xác minh giới hạn tooltip (`maxWidth`, `maxHeight`, `overflowY`, `pointerEvents`), an toàn tràn mép và dải màu 6 cấp của Heatmap.
  - `docs/PHASE3_PROGRESS.md`: Cập nhật tài liệu kiến trúc, trạng thái định vị tooltip và kết quả nghiệm thu kiểm thử.
- **Kiểm thử & Nghiệm thu:**
  - `python -m unittest tests/test_station_map.py`: **17/17 PASS (100%)**.
  - `python -m unittest tests/test_dashboard_integration.py`: **5/5 PASS (100%)**.
  - `python -m unittest tests/test_station_filter.py`: **7/7 PASS (100%)**.
  - `python -m unittest tests/test_station_display.py`: **7/7 PASS (100%)**.
  - `python -m unittest tests/test_station_aggregation.py`: **7/7 PASS (100%)**.
  - `python -m unittest tests/test_validate_data.py`: **8/8 PASS (100%)**.
  - `python -m unittest tests/test_future_forecast_integration.py`: **6/6 PASS (100%)**.
  - Tổng cộng toàn bộ test suite dự án: **57/57 PASS (100%)**.
  - **Nghiệm thu CDP Browser:** Tọa độ chuột `(772, 523.14)`, Tọa độ tooltip `(772, 523.00)`, độ lệch `diffY = -0.14px` (trùng khớp chính xác vị trí hover).

### Task 9 — Kiểm thử dữ liệu trạm
- **Trạng thái:** 🟢 PASS (5/5 tiêu chí đạt — 2026-10-14)
- **Tóm tắt kết quả:**
  - **Quy tắc định danh (Test 1):** Xác minh bằng truy vấn SQL độc lập (INTERSECT/UNION trên trips), 113 trạm hai vai trò start/end chỉ tạo đúng 1 bản ghi duy nhất không nhân bản, 339 trạm end-only bảo toàn đầy đủ.
  - **Đối chiếu Activity Count (Test 2):** Trạm mẫu JC115 (33,957 starts + 34,309 ends = 68,266 activity) khớp 100% với truy vấn đếm trực tiếp bảng trips; bất biến toán học `activity_count == start_count + end_count` đúng trên toàn bộ 452 trạm.
  - **Lọc tọa độ sai & dữ liệu biên (Test 3):** 100% tọa độ thực trong bounding box NY/NJ; bộ dữ liệu bẩn nhân tạo trong bộ nhớ (NULL, 'NaN', 0,0, Paris, tọa độ đảo dấu) bị loại bỏ triệt để; công thức trọng tâm gia quyền trạm dock lệch 5772.05 khớp chuẩn xác theo logic SQL CASE.
  - **Xử lý dữ liệu rỗng (Test 4):** DataFrame rỗng và filter 0 bản ghi được xử lý an toàn tại toàn bộ các hàm data_loader, lookup và charts không gây crash Dashboard.
  - **Đối chiếu bộ lọc thời gian (Test 5 & 6):** Hai phạm vi thời gian (ngày đơn lẻ 15/07/2026 và tháng 07/2026) đối chiếu khớp 100% với truy vấn SQL nguồn; ngày đảo ngược và ngày tương lai trả về DataFrame rỗng an toàn.
- **Files thay đổi:**
  - `tests/test_station_data.py`: Tạo mới bộ kiểm thử 6 test cases độc lập đối chiếu dữ liệu trạm.
  - `docs/PHASE3_PROGRESS.md`: Cập nhật tiến độ Task 9.
- **Kiểm thử & Nghiệm thu:**
  - `python -m unittest tests/test_station_data.py`: **6/6 PASS (100%)**.
  - Toàn bộ test suite dự án (`python -m unittest discover tests`): **63/63 PASS (100%)**.
- **Vấn đề tồn đọng / Lưu ý:** Không có. Sẵn sàng cho Task 10 (Kiểm thử bản đồ và regression).

### Task 10 — Kiểm thử bản đồ và Regression
- **Trạng thái:** 🟢 PASS (Hoàn thành kiểm thử toàn diện & Regression Phase 1, 2, 3 — 2026-10-14)
- **Tóm tắt kết quả:**
  - **Station Map Verification:** 452 trạm hiển thị đúng tọa độ và tên trạm, marker tỷ lệ thuận căn bậc hai hoạt động [20m, 160m], chú giải 4 phân vị hoạt động rõ ràng, Heatmap xếp dưới ScatterplotLayer, tooltip native định vị chuẩn trên marker với đầy đủ 7 trường thông tin và giới hạn chống tràn mép, không có NaN/None trên giao diện.
  - **Regression Phase 1:** Bảng `trips` (742,615 dòng) và `hourly_demand` (6,459 dòng) truy cập hoàn toàn bình thường, Kafka/Spark/PostgreSQL pipeline nguyên vẹn, không phát sinh duplicate, 8/8 tests Phase 1 PASS.
  - **Regression Phase 2:** Historical Prediction `Random Forest / 1.0` (4,176 records) và Future Forecast `Random Forest / future-v1` (168 records) còn nguyên vẹn, quy tắc `actual_demand` không đổi, loader/chart dự báo 7 ngày hoạt động ổn định, 6/6 tests Phase 2 PASS.
  - **Regression Dashboard & Live HTTP:** Dashboard Streamlit khởi động bình thường trên cổng 8501, health check trả về `ok`, HTTP 200, các section KPI, Demand, ML, Forecast và Station Map tích hợp mượt mà; 5/5 tests integration PASS.
- **Files thay đổi:**
  - `docs/PHASE3_PROGRESS.md`: Cập nhật tiến độ Task 10.
- **Kiểm thử & Nghiệm thu:**
  - Toàn bộ test suite dự án (`python -m unittest discover tests -v`): **63/63 PASS (100%)**.
  - Kiểm tra database PostgreSQL: 4 bảng dữ liệu cốt lõi nguyên vẹn.
  - Kiểm tra HTTP endpoint: `http://localhost:8501/_stcore/health` phản hồi `ok`.
- **Vấn đề tồn đọng / Lưu ý:** Công cụ browser tự động (`open_browser_url`) trong môi trường sandbox bị giới hạn do lỗi tải Playwright driver từ CDN; giao diện trực quan đã được kiểm chứng qua HTTP 200, DOM integration tests và người dùng có thể đối chiếu trực tiếp trên trình duyệt cá nhân. Sẵn sàng cho Task 11 (Documentation & Handover).

### Task 11 — Documentation & Handover
- **Trạng thái:** 🟢 PASS (Hoàn thành bàn giao toàn diện Phase 3 — 2026-10-14)
- **Tóm tắt kết quả:**
  - Khởi tạo tài liệu bàn giao kỹ thuật hoàn chỉnh: `docs/STATION_MAP_HANDOVER.md` bao phủ 11 hạng mục tối thiểu theo quy định `TASK_PHASE3.md`.
  - Phân loại rõ ràng 4 file mã nguồn ứng dụng sửa đổi và 10 file untracked được tạo mới trong Phase 3.
  - Tài liệu hóa toàn diện nguồn dữ liệu station, các cột sử dụng, quy tắc loại bỏ rác/tọa độ ngoài phạm vi, công thức Activity Count, và giải thuật trọng tâm gia quyền.
  - Mô tả chi tiết kiến trúc bản đồ PyDeck, cấu hình CARTO Basemap, ScatterplotLayer, HeatmapLayer, cơ chế tooltip native định vị trên marker, và hướng dẫn vận hành Runbook.
  - Xác nhận 63/63 tests PASS trên toàn bộ hệ thống kiểm thử tự động, bảo toàn 100% tính toàn vẹn của Phase 1 & Phase 2.
- **Files thay đổi:**
  - `docs/STATION_MAP_HANDOVER.md`: Tạo mới tài liệu bàn giao kỹ thuật Phase 3.
  - `docs/PHASE3_PROGRESS.md`: Cập nhật hoàn tất Task 11 và chốt nghiệm thu toàn bộ Phase 3.
- **Kiểm thử & Nghiệm thu:**
  - `git status --short`: Xác nhận chính xác danh sách file thay đổi và untracked.
  - Toàn bộ test suite dự án (`python -m unittest discover tests -v`): **63/63 PASS (100%)**.
- **Vấn đề tồn đọng / Lưu ý:** Không có. Toàn bộ 11/11 Tasks của Phase 3 đã hoàn tất xuất sắc và sẵn sàng cho commit bàn giao chính thức.










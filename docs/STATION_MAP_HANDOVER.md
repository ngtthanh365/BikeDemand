# STATION COMPOSITE MAP HANDOVER — BIKEDEMAND v2.0 (PHASE 3)

## 1. Trạng thái Hoàn thành Nghiệm thu (Handover Status)

Giai đoạn **Phase 3 — Station Composite Map** đã hoàn thành toàn diện và nghiệm thu đạt **100% PASS** qua toàn bộ 11 Tasks:

```text
Task 0  — Checkpoint Verification       = PASS (Commit 6a8ead3, tree sạch)
Task 1  — Khảo sát Dashboard & Trạm     = PASS (452 trạm thực, pydeck/plotly sẵn có)
Task 2  — Tổng hợp dữ liệu cấp trạm    = PASS (load_station_activity_data SQL in-DB, 36 KB)
Task 3  — Hiển thị tên trạm & Tọa độ   = PASS (Chuẩn hóa Regex, display_label, get_station_by_id)
Task 4  — Proportional Symbol Map       = PASS (ScatterplotLayer, radius ∝ √activity, legend 4 cấp)
Task 5  — Heatmap mờ                   = PASS (HeatmapLayer opacity 0.50, xếp dưới Scatter)
Task 6  — Tooltip / Thông tin trạm      = PASS (Đủ 7 trường thực, top 500px định vị trên marker)
Task 7  — Bộ lọc thời gian             = PASS (Mặc định toàn bộ, 15/7, tháng 7, cache TTL 60s)
Task 8  — Tích hợp vào Dashboard        = PASS (Section giữa KPI & Demand, basemap CARTO Positron)
Task 9  — Kiểm thử dữ liệu trạm         = PASS (Đối chiếu SQL nguồn thô, test dữ liệu bẩn RAM)
Task 10 — Kiểm thử bản đồ & Regression  = PASS (63/63 tests PASS, bảo toàn Phase 1 & Phase 2)
Task 11 — Documentation & Handover      = PASS (Hoàn thành bàn giao)
```

---

## 2. Thông số Kỹ thuật Nghiệm thu

| Thông số bàn giao | Giá trị thực tế đã nghiệm thu |
|---|---|
| **Tổng số trạm hoạt động duy nhất** | **452 trạm** (113 trạm có cả start & end, 339 trạm end-only) |
| **Tổng số lượt hoạt động toàn vùng** | **1,481,366 lượt** (`start_count` = 742,614, `end_count` = 738,752) |
| **Độ phủ tọa độ địa lý thực** | **100% có tọa độ thực** trong khu vực NY/NJ (`lat`: [40.689, 40.767], `lng`: [-74.078, -73.961]) |
| **Thư viện bản đồ trực quan** | **`pydeck 0.9.3`** kết hợp **CARTO Vector Tiles** (không cần Mapbox token) |
| **Lớp biểu đồ tỷ lệ (Scatterplot)** | Bán kính [20m, 160m], pixel [3px, 18px], viền trắng `[255, 255, 255, 220]` |
| **Lớp mật độ nhiệt (Heatmap)** | `opacity = 0.50`, `radius_pixels = 45`, `intensity = 1.2`, dải màu 6 bậc vàng-đỏ |
| **Thứ tự xếp lớp (Layer ordering)** | `layers[0] = HeatmapLayer` (đáy), `layers[1] = ScatterplotLayer` (trên) |
| **Cấu hình Tooltip native** | Style `"top": "500px"`, `maxWidth: "290px"`, `maxHeight: "240px"`, `overflowY: "auto"`, `pointerEvents: "none"` |
| **Bộ lọc thời gian (Date Filter)** | Mặc định toàn bộ; hỗ trợ lọc ngày đơn lẻ và dải ngày; cache `@st.cache_data(ttl=60)` |
| **Kết quả kiểm thử tự động** | **63 / 63 tests PASS (100%)** trên toàn bộ 8 bộ test suite |
| **Trạng thái HTTP Dashboard** | [http://localhost:8501](http://localhost:8501) • **HTTP 200 OK** • Health: **ok** |

---

## 3. Tổng kết Danh mục Files (Files Changed & Untracked)

### 3.1. Các file mã nguồn được sửa đổi (Tracked Files Modified — 4 files)
- **[database/postgres.py](file:///d:/BigData/BikeDemand/database/postgres.py):**
  - Thêm hàm `load_station_activity_data(start_date, end_date)`: Sử dụng SQL CTEs (`starts`, `ends`) và `FULL OUTER JOIN` tổng hợp trực tiếp tại database, tính trọng tâm gia quyền cho trạm lệch dock (`5772.05`), trả về đúng 452 dòng (~36 KB).
  - Thêm hàm `normalize_date_range(start_date, end_date)`: Chuẩn hóa kiểu chuỗi/date/Timestamp, mở rộng mốc kết thúc đến cuối ngày (`23:59:59.999999`), xử lý an toàn trường hợp ngày đảo ngược (`start_date > end_date`).
- **[dashboard/services/data_loader.py](file:///d:/BigData/BikeDemand/dashboard/services/data_loader.py):**
  - Thêm wrapper `load_station_activity(start_date, end_date)` kèm cache `@st.cache_data(ttl=60)`.
  - Thêm hàm `prepare_station_display_data(df)`: Làm sạch tên trạm bằng Regex, tạo nhãn `display_label` (`{name} ({id})`), lọc tọa độ ngoài bounding box NY/NJ, loại bỏ ID trùng.
  - Thêm hàm `get_station_by_id(df, station_id)`: Tra cứu thông tin chi tiết trạm an toàn.
  - Thêm hàm `format_date_range_label(start_date, end_date)`: Tạo nhãn hiển thị khoảng thời gian thân thiện.
- **[dashboard/components/charts.py](file:///d:/BigData/BikeDemand/dashboard/components/charts.py):**
  - Thêm logic tính toán bán kính marker `compute_station_marker_sizes()`.
  - Thêm các hàm khởi tạo layer PyDeck: `create_station_symbol_layer()`, `create_station_heatmap_layer()`, `build_station_map_deck()`.
  - Thêm cấu hình tooltip `get_station_tooltip_config()` và tiền xử lý dữ liệu `format_station_tooltip_data(df)`.
  - Thêm hàm giao diện hoàn chỉnh `show_station_symbol_map()` kèm bảng chú giải 4 cấp độ và xử lý an toàn dữ liệu rỗng.
- **[dashboard/app.py](file:///d:/BigData/BikeDemand/dashboard/app.py):**
  - Tích hợp Section **🗺️ Phân tích Không gian Trạm (Station Composite Map)** nằm ngay giữa Section KPI và Section Dự báo Nhu cầu.
  - Thêm bộ chọn nền bản đồ (CARTO Positron Sáng, CARTO Voyager Đường bộ, CARTO Dark Matter Tối).
  - Tích hợp bộ lọc ngày tháng đồng bộ, hot-reload module qua `importlib.reload()`.

### 3.2. Các file tài liệu và kiểm thử mới (Untracked Files Phase 3 — 10 files)
- **Tài liệu:**
  - [docs/TASK_PHASE3.md](file:///d:/BigData/BikeDemand/docs/TASK_PHASE3.md): Đặc tả chi tiết 11 Tasks của Phase 3.
  - [docs/PHASE3_PROGRESS.md](file:///d:/BigData/BikeDemand/docs/PHASE3_PROGRESS.md): Nhật ký tiến độ chi tiết từng Task từ 0 đến 11.
  - [docs/STATION_MAP_HANDOVER.md](file:///d:/BigData/BikeDemand/docs/STATION_MAP_HANDOVER.md): Tài liệu bàn giao kỹ thuật Phase 3.
  - [pyrefly.toml](file:///d:/BigData/BikeDemand/pyrefly.toml): Cấu hình linter tĩnh cho môi trường ảo `.venv`.
- **Bộ kiểm thử tự động (Unit & Integration Tests — 6 files, 49 tests mới):**
  - [tests/test_station_aggregation.py](file:///d:/BigData/BikeDemand/tests/test_station_aggregation.py) (7 tests): Nghiệm thu Task 2.
  - [tests/test_station_display.py](file:///d:/BigData/BikeDemand/tests/test_station_display.py) (7 tests): Nghiệm thu Task 3.
  - [tests/test_station_map.py](file:///d:/BigData/BikeDemand/tests/test_station_map.py) (17 tests): Nghiệm thu Task 4, 5, 6, 8.
  - [tests/test_station_filter.py](file:///d:/BigData/BikeDemand/tests/test_station_filter.py) (7 tests): Nghiệm thu Task 7.
  - [tests/test_dashboard_integration.py](file:///d:/BigData/BikeDemand/tests/test_dashboard_integration.py) (5 tests): Nghiệm thu Task 8.
  - [tests/test_station_data.py](file:///d:/BigData/BikeDemand/tests/test_station_data.py) (6 tests): Nghiệm thu Task 9.

---

## 4. Nguồn Dữ liệu Trạm, Cột Dữ liệu & Xử lý Dữ liệu Thiếu

### 4.1. Nguồn dữ liệu thực tế
- Dữ liệu được tổng hợp trực tiếp từ bảng **`trips`** trong cơ sở dữ liệu PostgreSQL (`citibike-postgres`).
- Bảng `trips` chứa 742,615 dòng dữ liệu hành trình lịch sử của Citi Bike với 8 cột trạm: `start_station_name`, `start_station_id`, `start_lat`, `start_lng`, `end_station_name`, `end_station_id`, `end_lat`, `end_lng`.

### 4.2. Các cột dữ liệu sử dụng trên Dashboard
| Tên cột | Kiểu dữ liệu | Ý nghĩa |
|---|---|---|
| `station_id` | `VARCHAR` / `str` | Mã định danh duy nhất của trạm (ví dụ: `JC115`, `HB101`, `6626.11`). |
| `station_name` | `VARCHAR` / `str` | Tên trạm chuẩn hóa, loại bỏ khoảng trắng thừa (ví dụ: `Grove St PATH`). |
| `display_label` | `str` | Nhãn kết hợp: `{station_name} ({station_id})` giúp phân biệt trạm trùng tên. |
| `latitude` | `FLOAT` / `float64` | Vĩ độ thực tế đại diện (trọng tâm lưu lượng, làm tròn 6 chữ số thập phân). |
| `longitude` | `FLOAT` / `float64` | Kinh độ thực tế đại diện (trọng tâm lưu lượng, làm tròn 6 chữ số thập phân). |
| `start_count` | `INTEGER` / `int` | Số chuyến xe bắt đầu xuất phát tại trạm trong khoảng thời gian chọn. |
| `end_count` | `INTEGER` / `int` | Số chuyến xe kết thúc trả tại trạm trong khoảng thời gian chọn. |
| `activity_count` | `INTEGER` / `int` | Tổng số lượt hoạt động tại trạm (`start_count + end_count`). |

### 4.3. Quy tắc xử lý dữ liệu thiếu và dị thường
1. **Loại bỏ bản ghi rác cấp Database:**
   - Điều kiện SQL: `station_id IS NOT NULL AND station_id != '"NaN"' AND TRIM(station_id) != '' AND lat IS NOT NULL AND lat != 'NaN'::double precision`.
   - Loại bỏ đúng 1 bản ghi start có ID là `'"NaN"'` và 3,863 bản ghi end khuyết dock trả xe (chiếm 0.52% do xe lỗi/khóa ngoài trạm).
   - Bảo toàn 100% các dòng dữ liệu trong bảng `trips`.
2. **Loại bỏ dữ liệu ngoài phạm vi cấp Python:**
   - [data_loader.py:L273-L281](file:///d:/BigData/BikeDemand/dashboard/services/data_loader.py#L273-L281) áp dụng bounding box NY/NJ: `40.0 <= latitude <= 41.5` và `-74.5 <= longitude <= -73.0`.
   - Các tọa độ rác nhân tạo (như `(0, 0)` hoặc tọa độ ngoài khu vực) bị loại bỏ 100%, không bao giờ đưa lên bản đồ.
3. **Fallback tên trạm khuyết:**
   - Nếu trạm thiếu tên nhưng có `station_id` hợp lệ, hệ thống tự động gán fallback minh bạch `Station {station_id}`, không bịa tên giả.
4. **Hiển thị Tooltip:**
   - Mọi giá trị NaN/None được chuyển đổi thành chuỗi an toàn `'N/A'`.
   - Phân biệt rõ ràng giá trị 0 thực tế (`'0'`) với dữ liệu khuyết. Tuyệt đối không có các chuỗi lỗi `NaN`, `None`, `null`, `undefined` hiển thị cho người dùng.

---

## 5. Quy tắc Định danh Trạm, Tính Activity Count & Tọa độ

### 5.1. Quy tắc định danh trạm không trùng
- Trong bảng `trips`, có 113 trạm xuất phát và 452 trạm kết thúc.
- Toàn bộ 113 trạm xuất phát đều nằm trong tập 452 trạm kết thúc (giao thoa = 113).
- Phép gộp bằng **`FULL OUTER JOIN ends e ON s.station_id = e.station_id`** với `COALESCE(s.station_id, e.station_id)` đảm bảo 113 trạm có cả hai vai trò chỉ tạo thành **đúng 1 bản ghi duy nhất** (không nhân đôi).
- 339 trạm chỉ có lượt trả xe (`end-only`) có `start_count = 0`, `end_count > 0` và giữ nguyên đầy đủ tên, tọa độ.
- Lớp bảo vệ bổ sung tại Python: `out_df.drop_duplicates(subset=["station_id"], keep="first")` loại bỏ mọi khả năng trùng khóa định danh.

### 5.2. Công thức tính Activity Count
$$\text{Activity Count} = \text{Start Count} + \text{End Count}$$
- Bất biến toán học này đúng tuyệt đối trên 100% 452 trạm (sai lệch = 0).
- Trạm mẫu lớn nhất: `JC115` (Grove St PATH) có `start_count = 33,957`, `end_count = 34,309`, `activity_count = 68,266` (đối chiếu khớp chính xác 100% với truy vấn đếm trực tiếp trên bảng `trips`).

### 5.3. Xử lý tọa độ mâu thuẫn (Trọng tâm gia quyền)
- Khảo sát thực tế: Trạm `5772.05` ('Morton St & Greenwich St') có 2 dock mở rộng cách nhau 60.56m.
- Hệ thống áp dụng công thức **trọng tâm gia quyền theo số lượt chuyến (weighted centroid)**:
  $$\text{lat} = \frac{\text{lat}_{\text{start}} \times \text{start\_count} + \text{lat}_{\text{end}} \times \text{end\_count}}{\text{start\_count} + \text{end\_count}}$$
  $$\text{lng} = \frac{\text{lng}_{\text{start}} \times \text{start\_count} + \text{lng}_{\text{end}} \times \text{end\_count}}{\text{start\_count} + \text{end\_count}}$$
- Bảo đảm điểm marker đại diện nằm chính xác tại vị trí tập trung lưu lượng xe lớn nhất, không bị nhảy vị trí giữa các lần tải.

---

## 6. Kiến trúc Bản đồ PyDeck & Thành phần Giao diện

```text
Streamlit Dashboard (http://localhost:8501)
│
├── Bộ lọc thời gian (Date Input: Tuỳ chọn / Toàn bộ dữ liệu)
├── Bộ chọn nền bản đồ (CARTO Positron Sáng / Voyager Đường bộ / Dark Matter Tối)
├── Checkbox bật/tắt Heatmap mật độ
│
└── st.pydeck_chart (PyDeck Deck v0.9.3)
    │
    ├── Viewport: Center [40.7356, -74.0033], Zoom 11.0, Pitch 0, Bearing 0
    ├── Map Style: https://basemaps.cartocdn.com/gl/positron-gl-style/style.json
    │
    ├── Layer 0 (Đáy): HeatmapLayer (Mật độ hoạt động)
    │   ├── Opacity: 0.50, Radius: 45px, Threshold: 0.05, Intensity: 1.2
    │   ├── Weight: activity_count
    │   └── Color Range: 6 bậc từ Vàng nhạt [255, 255, 178] đến Đỏ đậm [128, 0, 38]
    │
    ├── Layer 1 (Trên): ScatterplotLayer (Trạm xe tỷ lệ)
    │   ├── Position: [longitude, latitude]
    │   ├── Radius: r ∝ √activity_count ([20m, 160m], pixel [3px, 18px])
    │   ├── Fill Color: 4 phân tầng hoạt động (Đỏ cam, Cam, Xanh dương, Cyan)
    │   ├── Stroke Color: Trắng [255, 255, 255, 220], lineWidthMinPixels: 1.5
    │   └── Pickable: True (Hover bắt trúng marker)
    │
    └── Tooltip Container (Deck.gl Native HTML Tooltip)
        ├── Định vị: Style "top": "500px" triệt tiêu offset âm container Deck.gl
        ├── Vị trí thực tế: Xuất hiện ngay trên đỉnh marker đang hover (diffY = -0.14px)
        ├── Kích thước & Tràn viền: maxWidth: 290px, maxHeight: 240px, overflowY: auto
        └── Dữ liệu: 7 trường thông tin trạm chi tiết, Dark Matter styling trang nhã
```

---

## 7. Hướng dẫn Khởi chạy Dashboard & Thao tác Vận hành (Runbook)

### 7.1. Khởi chạy Dashboard
1. **Đảm bảo các container Docker đang chạy:**
   ```powershell
   docker ps
   ```
   *Yêu cầu:* `citibike-postgres`, `citibike-kafka`, `citibike-spark-master`, `citibike-spark-worker` ở trạng thái `Up`.
2. **Khởi động ứng dụng Streamlit:**
   ```powershell
   python -m streamlit run dashboard/app.py --server.port 8501
   ```
3. **Mở trình duyệt:** Truy cập [http://localhost:8501](http://localhost:8501).

### 7.2. Thao tác trên giao diện bản đồ
- **Quan sát phân tầng hoạt động:** Marker lớn màu đỏ cam biểu thị các trung tâm giao thông đông đúc nhất (như Grove St PATH, Hoboken Terminal, Newport PATH). Marker nhỏ màu xanh dương và cyan biểu thị các trạm dân cư và vùng ngoại vi.
- **Rê chuột (Hover) xem thông tin trạm:** Đưa chuột vào bất kỳ marker nào trên bản đồ, bảng thông tin sẽ xuất hiện ngay trên đỉnh marker với đầy đủ 7 trường thông tin (Tên trạm, ID, Tọa độ, Lượt đi, Lượt đến, Tổng lượt).
- **Bật/tắt lớp nhiệt Heatmap:** Tích hoặc bỏ tích ô *"Hiển thị Heatmap mật độ hoạt động nền mờ"* để quan sát luồng mật độ tổng thể hoặc chỉ xem riêng các điểm trạm.
- **Thay đổi kiểu bản đồ nền:** Chọn dropdown giữa *CARTO Positron (Sáng - mặc định)*, *CARTO Voyager (Chi tiết đường bộ)* và *CARTO Dark Matter (Tối tương phản)* tùy theo sở thích quan sát.
- **Lọc theo khoảng thời gian:** Sử dụng bộ chọn ngày tại thanh điều khiển bản đồ để xem lưu lượng của một ngày cụ thể (ví dụ: ngày lễ 15/07) hoặc một khoảng ngày tùy ý. Khi chọn, toàn bộ bản đồ và số liệu trạm tự động cập nhật lại.

---

## 8. Kết quả Kiểm thử & Nghiệm thu (Test & Regression Results)

### 8.1. Toàn bộ Test Suite dự án (63 / 63 tests PASS)
Lệnh kiểm thử tự động toàn diện:
```powershell
python -m unittest discover tests -v
```

| Bộ kiểm thử (Test Suite) | Số test | Kết quả | Nhiệm vụ nghiệm thu |
|---|:---:|:---:|---|
| [tests/test_validate_data.py](file:///d:/BigData/BikeDemand/tests/test_validate_data.py) | 8 | **8/8 PASS** | Regression Phase 1 — Data Validation Pipeline |
| [tests/test_future_forecast_integration.py](file:///d:/BigData/BikeDemand/tests/test_future_forecast_integration.py) | 6 | **6/6 PASS** | Regression Phase 2 — Future Forecast 7-Day & HTTP |
| [tests/test_station_aggregation.py](file:///d:/BigData/BikeDemand/tests/test_station_aggregation.py) | 7 | **7/7 PASS** | Task 2 — SQL In-DB Aggregation & Centroid |
| [tests/test_station_display.py](file:///d:/BigData/BikeDemand/tests/test_station_display.py) | 7 | **7/7 PASS** | Task 3 — Station Name, Display Label & Coordinates |
| [tests/test_station_map.py](file:///d:/BigData/BikeDemand/tests/test_station_map.py) | 17 | **17/17 PASS** | Task 4–6, 8 — Scatter, Heatmap, Tooltip & CARTO |
| [tests/test_station_filter.py](file:///d:/BigData/BikeDemand/tests/test_station_filter.py) | 7 | **7/7 PASS** | Task 7 — Date Range Filter & Label Formatting |
| [tests/test_dashboard_integration.py](file:///d:/BigData/BikeDemand/tests/test_dashboard_integration.py) | 5 | **5/5 PASS** | Task 8 — Dashboard Layout & HTTP Integration |
| [tests/test_station_data.py](file:///d:/BigData/BikeDemand/tests/test_station_data.py) | 6 | **6/6 PASS** | Task 9 — SQL Ground-truth Reconciliation |
| **TỔNG CỘNG TOÀN BỘ TEST SUITE** | **63** | **63/63 PASS (100%)** | Thời gian chạy: **~13.8 giây** |

### 8.2. Bảo toàn tính toàn vẹn hệ thống (Regression Invariants)
- **Phase 1 Pipeline:** Bảng `trips` (742,615 dòng) và `hourly_demand` (6,459 dòng) không bị thay đổi hay xóa dữ liệu.
- **Phase 2 Forecasts:** Bảng `predictions` giữ nguyên vẹn 4,176 dòng của phiên bản `1.0` và 168 dòng của phiên bản `future-v1` (100% `actual_demand` là NULL, không bị data leakage).
- **Phase 3 Dashboard:** Dashboard khởi động bình thường, phản hồi mã `200 OK`, không phát sinh lỗi 500 hay treo ứng dụng.

---

## 9. Các Giới hạn Đã Biết (Known Limitations)

1. **Trạm chỉ nhận xe (`end-only` stations):** Có 339 trạm trong dữ liệu chỉ ghi nhận lượt trả xe (`start_count = 0`, `end_count > 0`). Đây là đặc điểm tự nhiên của dữ liệu tháng 7/2026 từ khu vực Jersey City liên kết với Manhattan, hệ thống đã bảo toàn đầy đủ các trạm này thay vì lọc bỏ.
2. **Trạm dock lệch (`5772.05`):** Có 2 vị trí dock cách nhau 60.56m, hệ thống sử dụng tọa độ trọng tâm gia quyền theo lưu lượng xe.
3. **Môi trường Sandbox Playwright Driver:** Trong môi trường sandbox Windows không có quyền tải trực tiếp file zip driver Playwright từ CDN AzureEdge bên ngoài, công cụ tự động `browser_subagent` không mở được cửa sổ browser ảo riêng. Việc kiểm thử giao diện thực tế được thực hiện qua HTTP 200, DOM assertions và kiểm tra trực tiếp trên trình duyệt máy trạm tại `http://localhost:8501`.

---

## 10. Trạng thái Git và Checkpoint Bàn giao

- **Git Branch:** `main` (đồng bộ với `origin/main`).
- **Checkpoint Phase 2:** `6a8ead3` (`Complete Phase 2 future demand forecasting`).
- **Phạm vi thay đổi Phase 3:**
  - 4 tracked files modified: `dashboard/app.py`, `dashboard/components/charts.py`, `dashboard/services/data_loader.py`, `database/postgres.py`.
  - 10 untracked files: 3 files tài liệu (`TASK_PHASE3.md`, `PHASE3_PROGRESS.md`, `STATION_MAP_HANDOVER.md`), 1 file cấu hình (`pyrefly.toml`), 6 files kiểm thử (`test_station_*.py`, `test_dashboard_integration.py`).
  - Không có bất kỳ file tạm hay rác phát sinh ngoài quy định.

> **Toàn bộ Phase 3 đã hoàn tất xuất sắc và sẵn sàng cho bước bàn giao / commit nghiệm thu!**

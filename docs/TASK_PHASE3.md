# TASK_PHASE3.md

# BIKEDEMAND v2.0 --- PHASE 3: STATION COMPOSITE MAP

> **Mục đích:** Tài liệu triển khai chính thức cho Phase 3 của
> BikeDemand v2.0.
>
> **Phạm vi:** Bổ sung Station Composite Map vào Dashboard hiện tại, thể
> hiện tên/vị trí trạm và mức độ hoạt động; kết hợp Point/Proportional
> Symbol Map với Heatmap mờ.
>
> **Nguyên tắc:** Khảo sát trước, sửa tối thiểu, triển khai từng Task,
> kiểm thử trước khi chuyển bước. Phase 3 không phải giai đoạn redesign
> toàn bộ Dashboard.

------------------------------------------------------------------------

# 1. THÔNG TIN TASK

  Thông tin            Nội dung
  -------------------- --------------------------------------------
  Project              BikeDemand
  Phase                Phase 3
  Tên task             Station Composite Map
  Mục tiêu             Hiển thị bản đồ hoạt động các trạm xe đạp
  Phiên bản mục tiêu   v2.0
  Database             PostgreSQL
  Dashboard            Streamlit
  Thành phần bản đồ    Point/Proportional Symbol Map + Heatmap mờ
  Trạng thái           ⬜ Chưa làm

Quy ước: ⬜ Chưa làm · 🟡 Đang làm · 🟢 Hoàn thành · 🔴 Có lỗi/cần xử
lý.

------------------------------------------------------------------------

# 2. BỐI CẢNH VÀ BASELINE

Phase 1 đã triển khai Automatic Data Update; Phase 2 đã triển khai
Future Demand Forecast theo trạng thái thực tế của repo. Agent phải xác
minh baseline hiện tại trước khi sửa code.

Baseline tham khảo từ tài liệu bàn giao Phase 2:

``` text
trips          = 742,615
hourly_demand  = 6,459
historical predictions = 4,176 rows
actual range   = 2026-01-01 → 2026-09-30
historical model = Random Forest / 1.0
future model     = Random Forest / future-v1
```

Đây là số liệu checkpoint tham khảo, không phải số liệu luôn đúng sau
khi Phase 1 cập nhật dữ liệu mới.

Đặc tả v2.0 nêu các trường station:

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

**Không được giả định các trường này chắc chắn đang có trong PostgreSQL
hiện tại.** Phải khảo sát schema, source code và dữ liệu thực tế trước
khi quyết định cách triển khai.

------------------------------------------------------------------------

# 3. MỤC TIÊU PHASE 3

1.  Hiển thị tên trạm và tọa độ.
2.  Tính Activity Count từ số chuyến bắt đầu và số chuyến kết thúc tại
    trạm.
3.  Hiển thị trạm bằng Point/Proportional Symbol Map.
4.  Kích thước marker phản ánh Activity Count.
5.  Thêm Heatmap mờ để thể hiện mật độ hoạt động.
6.  Có tooltip/thông tin trạm khi tương tác với marker.
7.  Mặc định xem toàn bộ dữ liệu; hỗ trợ lọc tháng/khoảng thời gian nếu
    dữ liệu và cấu trúc hiện tại cho phép.
8.  Giữ nguyên các section Dashboard đang hoạt động.
9.  Có test dữ liệu trạm, bản đồ và regression.
10. Có tài liệu bàn giao.

------------------------------------------------------------------------

# 4. PHẠM VI

## 4.1 In-scope

-   Khảo sát dữ liệu station, schema PostgreSQL, Dashboard và
    dependency.
-   Tái sử dụng loader, component và thư viện hiện có nếu phù hợp.
-   Tổng hợp dữ liệu cấp trạm.
-   Hiển thị Point/Proportional Symbol Map và Heatmap.
-   Tooltip/thông tin trạm.
-   Bộ lọc thời gian nếu tích hợp được gọn và chính xác.
-   Kiểm thử, regression, tài liệu bàn giao.
-   Chỉnh bố cục cục bộ để bản đồ đủ không gian.

## 4.2 Out-of-scope

Không thực hiện trong Phase 3:

-   Redesign toàn bộ Dashboard.
-   Viết lại toàn bộ `dashboard/app.py` hoặc data loader nếu không bắt
    buộc.
-   Thay đổi Automatic Data Update của Phase 1.
-   Thay đổi logic Future Forecast hoặc Historical Prediction.
-   Thay thế Kafka/Spark/PostgreSQL.
-   Thay đổi schema hoặc xóa/sửa dữ liệu thật khi chưa được chấp thuận.
-   Thêm dependency lớn khi chưa báo cáo và được chấp thuận.
-   Dự báo tồn kho xe, thiếu xe hoặc hết chỗ.
-   Airflow/Kubernetes/Cloud/Scheduler.
-   Thay đổi model ML.
-   Tạo dữ liệu station giả.
-   Nâng cấp giao diện tổng thể --- phần này sẽ làm ở giai đoạn sau.

------------------------------------------------------------------------

# 5. ĐỊNH HƯỚNG THIẾT KẾ ĐÃ CHỐT

``` text
Phong cách: Geospatial Intelligence Dashboard
Bố cục: KPI phía trên, bản đồ lớn ở trung tâm, biểu đồ phía dưới
Tông màu: xanh đen + cyan + điểm nhấn cam/đỏ
Phạm vi mặc định: toàn bộ dữ liệu, có filter tháng/khoảng thời gian
```

Trong Phase 3 chỉ áp dụng định hướng này ở mức cần thiết cho Station
Map. Không cần chốt chi tiết font, spacing, từng pixel hoặc redesign các
phần khác.

-   Bản đồ là điểm nhấn chính.
-   Màu và kích thước marker phải có ý nghĩa dữ liệu.
-   Heatmap phải đủ mờ để không che marker.
-   Tooltip và legend dễ đọc.
-   Giữ các phần phân tích/dự báo hiện có.

------------------------------------------------------------------------

# 6. ĐỊNH NGHĨA ACTIVITY COUNT

``` text
Activity Count = Start Count + End Count
```

-   `Start Count`: số chuyến bắt đầu tại trạm.
-   `End Count`: số chuyến kết thúc tại trạm.
-   Một chuyến bắt đầu và kết thúc tại cùng trạm đóng góp một lượt Start
    và một lượt End theo định nghĩa này.

Ưu tiên dùng station ID làm định danh khi hợp lệ; tên trạm là nhãn hiển
thị. Không để cùng một trạm tạo thành hai marker chỉ vì nó xuất hiện
trong cả dữ liệu start và end.

Tọa độ phải lấy từ dữ liệu thực tế, kiểm tra NULL/NaN/Inf và phạm vi hợp
lệ. Không tự bịa tọa độ. Nếu một ID có tên/tọa độ mâu thuẫn đáng kể, ghi
nhận và báo cáo trước khi chọn quy tắc xử lý.

**Giới hạn diễn giải:** Activity Count và Heatmap chỉ phản ánh hoạt động
được ghi nhận từ chuyến đi. Không được kết luận số xe còn tại trạm, trạm
hết xe hoặc thiếu chỗ vì hệ thống không có dữ liệu tồn kho theo thời
gian.

------------------------------------------------------------------------

# 7. LUỒNG DỮ LIỆU MỤC TIÊU

``` text
Nguồn chuyến đi hiện có
        ↓
Khảo sát schema thực tế
        ↓
Lấy station start/end
        ↓
Chuẩn hóa định danh và tọa độ
        ↓
Tổng hợp Start Count / End Count
        ↓
Tính Activity Count
        ↓
Validate dữ liệu tổng hợp
        ↓
Point/Proportional Symbol Map + Heatmap mờ
        ↓
Streamlit Dashboard
```

Đây là luồng logic mục tiêu. Agent không bắt buộc phải tạo file/module
mới nếu có thể tái sử dụng code hiện tại một cách rõ ràng.

------------------------------------------------------------------------

# 8. TASK 0 --- CHECKPOINT TRƯỚC KHI CODE

## Kiểm tra

``` text
git status
git diff
project structure
Docker containers
PostgreSQL connection
trips / hourly_demand / predictions
Dashboard
Automatic Data Update
Future Forecast
```

Ghi nhận thay đổi Git có sẵn, file chưa commit, số liệu baseline thực
tế, trạng thái Docker/PostgreSQL và Dashboard.

## Quy tắc

-   Không reset/checkout đè thay đổi chưa commit.
-   Không apply/drop stash.
-   Không xóa hoặc ghi đè dữ liệu.
-   Nếu baseline không ổn định, báo cáo và dừng.

## Acceptance Criteria

-   [ ] Git status/diff đã được kiểm tra.
-   [ ] Các thay đổi có sẵn được ghi nhận.
-   [ ] Docker/PostgreSQL được kiểm tra.
-   [ ] Dashboard được kiểm tra.
-   [ ] Phase 1/2 được xác nhận hoặc ghi rõ vấn đề.
-   [ ] Task 0 không sửa code.

------------------------------------------------------------------------

# 9. TASK 1 --- KHẢO SÁT DASHBOARD VÀ DỮ LIỆU TRẠM

## Khảo sát tối thiểu

-   Entry point Streamlit và các section hiện có.
-   Data loader và cách kết nối PostgreSQL.
-   Bảng/cột thực tế có station name, station ID, start/end coordinates.
-   Tỷ lệ dữ liệu thiếu và tọa độ không hợp lệ.
-   Dependency bản đồ hiện có trong file dependency.
-   Cơ chế cache và làm mới dữ liệu.
-   Cách truyền dữ liệu từ loader đến component/chart.

## Báo cáo đầu ra

``` text
1. Dashboard entry point:
2. Data loader liên quan:
3. Nguồn dữ liệu station:
4. Các cột station thực tế:
5. Dữ liệu thiếu/không hợp lệ:
6. Thư viện bản đồ/dependency hiện có:
7. Phương án ít thay đổi nhất:
8. Rủi ro hoặc thiếu dữ liệu:
```

## Acceptance Criteria

-   [ ] Nguồn dữ liệu station được xác minh.
-   [ ] Schema và chất lượng dữ liệu được khảo sát.
-   [ ] Dashboard/dependency được khảo sát.
-   [ ] Có phương án dựa trên code thực tế.
-   [ ] Task 1 chỉ khảo sát, chưa sửa code.

> **STOP:** Nếu không có tọa độ đủ dùng hoặc không thể định danh trạm
> nhất quán, báo cáo và chờ người dùng. Không tạo dữ liệu giả, không tự
> đổi schema.

------------------------------------------------------------------------

# 10. TASK 2 --- XÂY DỰNG DỮ LIỆU TỔNG HỢP CẤP TRẠM

## Các trường đầu ra mục tiêu

Tên trường có thể theo quy ước hiện tại, nhưng dữ liệu phải biểu diễn
được:

``` text
station_id
station_name
latitude
longitude
start_count
end_count
activity_count
```

## Quy tắc xử lý

1.  Tạo danh sách trạm từ cả vai trò start và end.
2.  Chuẩn hóa định danh để một trạm chỉ có một bản ghi tổng hợp.
3.  Đếm Start Count và End Count riêng.
4.  Tính Activity Count bằng tổng hai count.
5.  Không đưa bản ghi tọa độ không hợp lệ lên bản đồ; báo cáo số lượng
    bị loại.
6.  Không xóa chuyến đi nguồn chỉ vì thiếu thông tin trạm.
7.  Không thay đổi schema hoặc dữ liệu nguồn nếu chưa được phê duyệt.
8.  Nếu dữ liệu ID/tên/tọa độ mâu thuẫn đáng kể, báo cáo trước khi áp
    dụng quy tắc có thể ảnh hưởng kết quả.

## Acceptance Criteria

-   [ ] Không có trạm trùng do gộp start/end sai.
-   [ ] Count không âm.
-   [ ] Activity Count = Start Count + End Count.
-   [ ] Tọa độ đầu ra hợp lệ.
-   [ ] Bản ghi bị loại được đếm/báo cáo.
-   [ ] Dữ liệu nguồn không bị xóa/sửa.
-   [ ] Kết quả được đối chiếu với dữ liệu chuyến đi.

------------------------------------------------------------------------

# 11. TASK 3 --- HIỂN THỊ TÊN TRẠM VÀ TỌA ĐỘ

Mỗi trạm phải có thể tra cứu:

``` text
Station Name
Station ID
Latitude
Longitude
Activity Count
```

Tên trạm là nhãn hiển thị chính khi có dữ liệu hợp lệ; Station ID hỗ trợ
phân biệt các trạm trùng tên.

## Acceptance Criteria

-   [ ] Tên trạm hiển thị đúng.
-   [ ] Station ID tra cứu được.
-   [ ] Tọa độ lấy từ dữ liệu thật.
-   [ ] Không hiển thị `None`, `nan` hoặc lỗi tương tự.
-   [ ] Tên thiếu dữ liệu được xử lý rõ ràng, không tự đặt tên giả.

------------------------------------------------------------------------

# 12. TASK 4 --- POINT / PROPORTIONAL SYMBOL MAP

## Yêu cầu

-   Mỗi trạm hợp lệ được thể hiện bằng marker tại tọa độ của trạm.
-   Kích thước marker phản ánh `activity_count`.
-   Marker lớn hơn phải tương ứng với hoạt động cao hơn.
-   Scale kích thước phải dễ đọc, tránh marker lớn che bản đồ.
-   Nếu dùng màu biểu diễn hoạt động, phải có legend.
-   Các trạm gần nhau vẫn cần có cách tương tác/tra cứu phù hợp.
-   Không tạo marker cho tọa độ giả hoặc không hợp lệ.

Agent phải khảo sát thư viện hiện tại. Không tự cài thư viện mới trước
khi kiểm tra dependency; nếu cần dependency mới, báo cáo lý do và chờ
chấp thuận.

## Acceptance Criteria

-   [ ] Marker đúng vị trí.
-   [ ] Kích thước marker phản ánh Activity Count.
-   [ ] Marker dễ quan sát.
-   [ ] Legend/ý nghĩa màu sắc rõ ràng.
-   [ ] Tương tác marker hoạt động nếu thư viện hỗ trợ.
-   [ ] Dữ liệu rỗng không làm Dashboard crash.

------------------------------------------------------------------------

# 13. TASK 5 --- HEATMAP MỜ

## Yêu cầu

-   Heatmap là lớp nền dưới marker nếu thư viện hỗ trợ.
-   Độ đậm vừa phải, không che tên/điểm trạm.
-   Có thể bật/tắt lớp nếu tích hợp thuận tiện.
-   Heatmap dùng tọa độ và hoạt động hợp lệ.
-   Không diễn giải Heatmap thành số xe tồn kho hoặc thiếu xe.
-   Nếu thư viện hiện tại không hỗ trợ lớp kết hợp, báo cáo trước khi
    đổi kiến trúc hoặc thêm dependency lớn.

## Acceptance Criteria

-   [ ] Heatmap hiển thị khi có dữ liệu.
-   [ ] Heatmap không che marker.
-   [ ] Có thể nhận biết vùng hoạt động tương đối.
-   [ ] Phân biệt được Heatmap và marker.
-   [ ] Không kết luận về tồn kho xe.

------------------------------------------------------------------------

# 14. TASK 6 --- TOOLTIP / THÔNG TIN TRẠM

Thông tin tối thiểu:

``` text
Station Name
Activity Count
```

Nếu triển khai thuận lợi, bổ sung:

``` text
Station ID
Latitude / Longitude
Start Count
End Count
```

Tooltip phải có nhãn rõ ràng. Giá trị thiếu phải phân biệt với số 0 thực
tế.

## Acceptance Criteria

-   [ ] Tooltip hoặc tương tác chọn trạm hoạt động.
-   [ ] Có tên trạm và Activity Count.
-   [ ] Trường bổ sung đúng nếu được triển khai.
-   [ ] Không có `NaN`, `None`, `Inf` hoặc lỗi định dạng.
-   [ ] Không tuyên bố trạm còn/hết xe.

------------------------------------------------------------------------

# 15. TASK 7 --- BỘ LỌC THỜI GIAN

Mặc định:

``` text
All available data
```

Có thể chọn tháng/khoảng thời gian nếu timestamp trong dữ liệu hỗ trợ
lọc chính xác.

## Quy tắc

-   Start Count, End Count và Activity Count phải tính lại theo phạm vi
    được chọn.
-   Marker, Heatmap và bảng phải dùng cùng một phạm vi thời gian.
-   Hiển thị rõ khoảng thời gian đang xem.
-   Nếu không có dữ liệu, hiển thị thông báo phù hợp.
-   Kiểm tra cache để tránh giữ dữ liệu cũ sau khi Phase 1 cập nhật.
-   Nếu filter làm phát sinh thay đổi lớn hoặc có vấn đề
    timestamp/timezone, báo cáo trước.

## Acceptance Criteria

-   [ ] Mặc định xem toàn bộ dữ liệu hiện có.
-   [ ] Filter đúng nếu được triển khai.
-   [ ] Nhãn thời gian rõ ràng.
-   [ ] Không có dữ liệu vẫn xử lý được.
-   [ ] Không sai lệch do cache/timezone.
-   [ ] Không thay đổi cơ chế Automatic Data Update.

------------------------------------------------------------------------

# 16. TASK 8 --- TÍCH HỢP VÀO DASHBOARD

Bố cục tham khảo:

``` text
Navigation / Filters
        ↓
KPI Overview
        ↓
Station Composite Map
        ↓
Demand Analysis
        ↓
Historical Prediction
        ↓
Future Forecast
        ↓
User & Bike Analysis
        ↓
Station Analysis
        ↓
Model Information
```

Đây là bố cục tham khảo, không bắt buộc di chuyển tất cả section nếu bố
cục hiện tại đã phù hợp.

## Quy tắc

-   Tái sử dụng style/component hiện có khi phù hợp.
-   Chỉ chỉnh bố cục cục bộ để bản đồ có đủ không gian.
-   Không redesign toàn bộ Dashboard.
-   Không xóa section hiện có.
-   Không đổi logic KPI/dự báo để phục vụ bản đồ.
-   Nếu bản đồ rỗng/lỗi, các section khác vẫn phải mở được.

## Acceptance Criteria

-   [ ] Dashboard mở bình thường.
-   [ ] Station Map tích hợp ở vị trí hợp lý.
-   [ ] Các section cũ vẫn hoạt động.
-   [ ] KPI/filter không bị sai.
-   [ ] Historical Prediction và Future Forecast vẫn hoạt động.
-   [ ] Dữ liệu bản đồ rỗng không làm Dashboard crash.

------------------------------------------------------------------------

# 17. TASK 9 --- KIỂM THỬ DỮ LIỆU TRẠM

## Test 1 --- Định danh

Trạm xuất hiện ở cả start và end không bị nhân thành hai trạm tổng hợp
nếu cùng định danh.

## Test 2 --- Activity Count

Với trạm mẫu, đối chiếu:

``` text
Activity Count = Start Count + End Count
```

với dữ liệu chuyến đi nguồn.

## Test 3 --- Tọa độ

Kiểm tra tọa độ hợp lệ, NULL, giá trị ngoài phạm vi và trạm có tọa độ
mâu thuẫn.

## Test 4 --- Dữ liệu rỗng

Kiểm tra không có trạm hợp lệ hoặc filter trả về 0 bản ghi.

## Test 5 --- Filter thời gian

Nếu filter được triển khai, chọn ít nhất hai phạm vi và đối chiếu count
với dữ liệu tương ứng.

## Acceptance Criteria

-   [ ] Count được đối chiếu với nguồn.
-   [ ] Không có trạm trùng do gộp start/end sai.
-   [ ] Tọa độ sai không được vẽ như hợp lệ.
-   [ ] Dữ liệu rỗng không làm Dashboard crash.
-   [ ] Filter được kiểm tra nếu có.

------------------------------------------------------------------------

# 18. TASK 10 --- KIỂM THỬ BẢN ĐỒ VÀ REGRESSION

## Station Map

-   [ ] Tên trạm hiển thị đúng.
-   [ ] Station ID tra cứu được.
-   [ ] Tọa độ marker đúng.
-   [ ] Activity Count đúng.
-   [ ] Kích thước marker phản ánh hoạt động.
-   [ ] Heatmap hiển thị và đủ mờ.
-   [ ] Tooltip hoạt động.
-   [ ] Filter đúng nếu có.
-   [ ] Không có `None`/`NaN` trên giao diện.

## Regression Phase 1

-   [ ] `trips` và `hourly_demand` truy cập được.
-   [ ] Automatic Data Update không bị sửa ngoài phạm vi.
-   [ ] Kafka/Spark/PostgreSQL pipeline không bị phá.
-   [ ] Không phát sinh duplicate.
-   [ ] Dữ liệu lịch sử không bị xóa.

## Regression Phase 2

-   [ ] Historical Prediction `Random Forest / 1.0` còn nguyên.
-   [ ] Future Forecast `Random Forest / future-v1` còn nguyên.
-   [ ] Quy tắc `actual_demand` của Future Forecast không bị đổi.
-   [ ] Loader/chart dự báo vẫn hoạt động.
-   [ ] Logic forecast không bị thay đổi.

## Regression Dashboard

-   [ ] Dashboard khởi động được.
-   [ ] KPI/filter cũ hoạt động.
-   [ ] Biểu đồ cũ hiển thị.
-   [ ] Lỗi bản đồ không làm hỏng toàn Dashboard.

Agent phải ghi lệnh test đã chạy, kết quả thực tế và test nào chưa chạy
được. Không đánh dấu PASS nếu chưa có bằng chứng kiểm thử tương ứng.

------------------------------------------------------------------------

# 19. TASK 11 --- DOCUMENTATION / HANDOVER

Bàn giao tối thiểu:

``` text
1. Files changed
2. Nguồn dữ liệu station thực tế
3. Các cột dữ liệu được sử dụng
4. Cách tính Activity Count
5. Thư viện bản đồ đã sử dụng
6. Cách chạy Dashboard
7. Cách sử dụng bản đồ/filter
8. Test results
9. Regression results
10. Dữ liệu thiếu và giới hạn
11. Git status / checkpoint
```

Cập nhật tài liệu phù hợp trong cấu trúc hiện có. Không tạo nhiều tài
liệu trùng lặp nếu đã có tài liệu tương đương.

------------------------------------------------------------------------

# 20. QUY TẮC STOP VÀ PHẠM VI

Agent phải STOP và hỏi người dùng nếu:

1.  Không tìm thấy tọa độ đủ dùng.
2.  Cần thay đổi schema PostgreSQL.
3.  Cần sửa Automatic Data Update.
4.  Cần sửa Future Forecast hoặc Historical Prediction.
5.  Cần xóa/sửa dữ liệu thật.
6.  Cần thêm dependency lớn/dịch vụ mới.
7.  Cần thay đổi kiến trúc Kafka/Spark/PostgreSQL.
8.  Có nguy cơ mất thay đổi Git hiện có.
9.  Phải redesign toàn bộ Dashboard mới làm được bản đồ.
10. Acceptance Criteria không thể đạt bằng thay đổi tối thiểu.

Không tự suy đoán để tiếp tục. Ghi nhận vấn đề, nêu ảnh hưởng và chờ
quyết định.

------------------------------------------------------------------------

# 21. BẢO VỆ DỮ LIỆU VÀ DESTRUCTIVE COMMAND

Agent không được tự ý chạy:

``` text
docker compose down -v
docker system prune
DROP TABLE
TRUNCATE
DELETE FROM predictions
DELETE FROM trips
DELETE FROM hourly_demand
```

Không reset/ghi đè thay đổi Git chưa kiểm tra. Không xóa hoặc apply
stash.

Nếu cần thao tác dữ liệu thật hoặc thay đổi schema, STOP và hỏi người
dùng trước.

------------------------------------------------------------------------

# 22. DEPENDENCY VÀ THƯ VIỆN BẢN ĐỒ

Trước khi thêm package:

1.  Kiểm tra dependency hiện có.
2.  Kiểm tra thư viện bản đồ đang dùng.
3.  Đánh giá khả năng dựng Point Map và Heatmap bằng công nghệ hiện tại.
4.  Báo cáo package, lý do và ảnh hưởng.
5.  Chờ chấp thuận nếu là thay đổi đáng kể.

Không mặc định dùng Folium, PyDeck, Plotly, Deck.gl hay thư viện khác
khi chưa khảo sát code hiện tại.

Ưu tiên giải pháp đơn giản, tương thích Streamlit và dễ kiểm thử.

------------------------------------------------------------------------

# 23. GIT / CHECKPOINT

Trước khi sửa code:

``` powershell
git status
git diff
```

Sau mỗi Task lớn:

1.  Kiểm tra file thay đổi.
2.  Đọc diff.
3.  Chạy test/check.
4.  Đối chiếu Acceptance Criteria.
5.  Báo cáo kết quả.
6.  Chỉ commit khi người dùng xác nhận hoặc theo workflow đã thống nhất.

Không dùng `git add .` mù quáng nếu có file không liên quan. Không
commit `.env`, credentials, secrets hoặc database dump.

Tên commit gợi ý:

``` text
feat(phase3): add station activity aggregation
feat(phase3): add station composite map
feat(phase3): add station activity heatmap
test(phase3): add station map validation
docs(phase3): document station map handover
```

------------------------------------------------------------------------

# 24. QUY TRÌNH LÀM VIỆC VỚI AI AGENT

## Trước mỗi Task

``` text
1. Đọc TASK_PHASE3.md.
2. Đọc file liên quan trong source code.
3. Xác định phạm vi Task hiện tại.
4. Kiểm tra code và dữ liệu.
5. Nêu kế hoạch ngắn và file dự kiến thay đổi.
6. Chỉ sửa code sau khi người dùng xác nhận kế hoạch.
```

Không tự động chạy liên tục qua nhiều Task.

## Prompt nguyên tắc

``` text
Bạn đang làm việc trên BikeDemand — Phase 3: Station Composite Map.

Đọc TASK_PHASE3.md và chỉ thực hiện đúng Task mà người dùng chỉ định.

Trước khi sửa code:
1. Khảo sát cấu trúc project và code liên quan.
2. Kiểm tra schema/dữ liệu thực tế.
3. Báo cáo kế hoạch ngắn và các file dự kiến thay đổi.
4. Không sửa code cho đến khi người dùng xác nhận kế hoạch.

Không thực hiện Task tiếp theo.
Không redesign toàn bộ Dashboard.
Không sửa Phase 1 hoặc Phase 2 nếu không trực tiếp bắt buộc.
Không đổi schema, xóa dữ liệu, thêm dependency lớn hoặc đổi kiến trúc khi chưa được chấp thuận.
Không tự giả định tên bảng/cột, thư viện bản đồ hoặc tọa độ.
Nếu thiếu dữ liệu hoặc có vấn đề ngoài phạm vi, STOP và báo cáo.

Sau Task được giao, báo cáo:
1. Files changed.
2. Changes.
3. Commands/tests đã chạy.
4. Kết quả PASS/FAIL.
5. Acceptance Criteria.
6. Remaining issues.
7. Out-of-scope findings.

Chờ người dùng kiểm tra trước khi chuyển Task tiếp theo.
```

## Báo cáo sau mỗi Task

``` text
## Task X — Completed / Blocked

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

Nếu có FAIL hoặc chưa đủ bằng chứng kiểm thử, không đánh dấu Task hoàn
thành.

------------------------------------------------------------------------

# 25. CHECKPOINT THEO TASK

  Task   Nội dung                             Trạng thái   Ghi chú
  ------ ------------------------------------ ------------ ---------
  0      Checkpoint trước khi code            ⬜           
  1      Khảo sát Dashboard và dữ liệu trạm   ⬜           
  2      Dữ liệu tổng hợp cấp trạm            ⬜           
  3      Tên trạm và tọa độ                   ⬜           
  4      Point/Proportional Symbol Map        ⬜           
  5      Heatmap mờ                           ⬜           
  6      Tooltip/thông tin trạm               ⬜           
  7      Bộ lọc thời gian                     ⬜           
  8      Tích hợp Dashboard                   ⬜           
  9      Kiểm thử dữ liệu trạm                ⬜           
  10     Map + regression tests               ⬜           
  11     Documentation/handover               ⬜           

Không chuyển Task khi Task hiện tại chưa đạt Acceptance Criteria hoặc
chưa được người dùng chấp thuận.

------------------------------------------------------------------------

# 26. ACCEPTANCE CRITERIA TOÀN PHASE 3

Chỉ đánh dấu:

``` text
🟢 PHASE 3 — COMPLETED
```

khi tất cả tiêu chí áp dụng đều đạt.

## Data

-   [ ] Nguồn dữ liệu station được xác minh.
-   [ ] Tên/định danh được xử lý nhất quán.
-   [ ] Tọa độ hợp lệ.
-   [ ] Activity Count = Start Count + End Count.
-   [ ] Dữ liệu tổng hợp đối chiếu được với nguồn.
-   [ ] Không tạo dữ liệu giả.

## Map

-   [ ] Point Map hiển thị vị trí trạm.
-   [ ] Kích thước marker phản ánh hoạt động.
-   [ ] Heatmap hiển thị và đủ mờ.
-   [ ] Tooltip có tên trạm và tổng hoạt động.
-   [ ] Dữ liệu thiếu được xử lý rõ ràng.
-   [ ] Không suy luận tồn kho/thiếu xe.

## Time Filter

-   [ ] Mặc định toàn bộ dữ liệu.
-   [ ] Filter đúng nếu được triển khai.
-   [ ] Marker, Heatmap và bảng dùng cùng phạm vi thời gian.

## Dashboard

-   [ ] Dashboard mở bình thường.
-   [ ] Station Map tích hợp phù hợp.
-   [ ] KPI/filter/biểu đồ cũ vẫn hoạt động.
-   [ ] Historical Prediction còn nguyên.
-   [ ] Future Forecast vẫn hoạt động.
-   [ ] Không redesign toàn bộ Dashboard trong Phase 3.

## Regression / Handover

-   [ ] Automatic Data Update không bị phá.
-   [ ] Future Forecast không bị phá.
-   [ ] Không destructive operation ngoài phê duyệt.
-   [ ] Test và regression results được ghi lại.
-   [ ] Giới hạn dữ liệu được ghi lại.
-   [ ] Git status/diff được kiểm tra.
-   [ ] Có tài liệu bàn giao.

------------------------------------------------------------------------

# 27. PHẠM VI SAU PHASE 3

Không đưa vào Phase 3:

``` text
Full Dashboard redesign
Global typography/spacing redesign
Navigation redesign toàn hệ thống
New forecasting model/horizon
Inventory / bike shortage prediction
Scheduler / Airflow / Kubernetes / Cloud
Kafka/Spark/PostgreSQL architecture rewrite
```

Sau khi Station Map hoạt động ổn định, người dùng và Bee sẽ bàn chi tiết
nâng cấp giao diện tổng thể. Khi đó mới chốt chi tiết design system và
triển khai đồng bộ toàn Dashboard.

------------------------------------------------------------------------

# 28. KẾT QUẢ BÀN GIAO PHASE 3

``` text
1. Station-level aggregation hoặc loader cập nhật
2. Station Composite Map
3. Heatmap mờ
4. Tooltip/thông tin trạm
5. Bộ lọc thời gian nếu được triển khai
6. Test results
7. Regression results
8. Documentation/handover
9. Git status/checkpoint
```

Thông tin bàn giao:

``` text
Station data source
Actual station fields
Valid station count
Missing/invalid coordinate count
Activity Count validation
Map library used
Time filter behavior
Tests passed/failed
Known limitations
Files changed
Git checkpoint
```

------------------------------------------------------------------------

# 29. NGUYÊN TẮC CUỐI CÙNG

> **Phase 3 chỉ làm Station Composite Map.**

> **Không redesign toàn bộ Dashboard trong Phase 3.**

> **Không tự giả định dữ liệu trạm hoặc thêm dependency trước khi khảo
> sát.**

> **Không phá Automatic Data Update, Future Forecast hoặc Historical
> Prediction.**

> **Không kết luận thiếu xe/hết xe từ dữ liệu chuyến đi.**

> **Không destructive operation nếu chưa được người dùng cho phép.**

> **Mỗi Task phải được kiểm tra trước khi chuyển Task tiếp theo.**

Ưu tiên:

``` text
Khảo sát đúng
    ↓
Tái sử dụng code hiện tại
    ↓
Dữ liệu trạm chính xác
    ↓
Bản đồ dễ đọc
    ↓
Kiểm thử
    ↓
Regression
    ↓
Bàn giao rõ ràng
```

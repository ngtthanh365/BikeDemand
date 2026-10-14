import sys
import unittest
from datetime import date, datetime
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))

from database.postgres import get_connection, load_station_activity_data, normalize_date_range
from dashboard.services.data_loader import (
    load_station_activity,
    prepare_station_display_data,
    get_station_by_id,
    format_date_range_label,
)
from dashboard.components.charts import show_station_symbol_map


class TestStationData(unittest.TestCase):
    """
    Bộ kiểm thử độc lập cho Task 9 — Kiểm thử dữ liệu trạm (Phase 3).
    Tuân thủ mục 17 trong docs/TASK_PHASE3.md:
      - Test 1: Định danh (không nhân bản trạm khi gộp start/end).
      - Test 2: Activity Count (đối chiếu công thức với truy vấn SQL nguồn thô trên trips).
      - Test 3: Tọa độ (hợp lệ, lọc bỏ NULL/rác ngoài vùng, tính trọng tâm gia quyền).
      - Test 4: Dữ liệu rỗng (xử lý an toàn khi không có trạm hoặc filter 0 bản ghi).
      - Test 5: Filter thời gian (đối chiếu 2 phạm vi với truy vấn SQL nguồn thô).
      - Test 6: Biên ngày tháng (ngày đảo ngược, ngày tương lai không crash).
    """

    @classmethod
    def setUpClass(cls):
        """Xác minh kết nối PostgreSQL trước khi chạy test suite. Báo lỗi rõ nếu không kết nối được."""
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT 1;")
            cur.fetchone()
            conn.close()
        except Exception as e:
            raise RuntimeError(f"LỖI KẾT NỐI DATABASE: Không thể kết nối đến PostgreSQL để kiểm thử: {e}")

    # =========================================================================
    # Test 1 — Định danh (Test 1 trong docs/TASK_PHASE3.md)
    # =========================================================================
    def test_01_station_identity_no_duplicate_on_start_end_merge(self):
        """
        Xác minh quy tắc định danh: trạm xuất hiện ở cả start và end không bị nhân
        đôi thành 2 trạm khi gộp; và các trạm end-only vẫn được bảo toàn.
        """
        conn = get_connection()
        try:
            cur = conn.cursor()

            # Lấy số trạm xuất phát hợp lệ duy nhất từ bảng trips nguồn
            cur.execute("""
                SELECT COUNT(DISTINCT start_station_id) 
                FROM trips 
                WHERE start_station_id IS NOT NULL 
                  AND start_station_id != '"NaN"' 
                  AND TRIM(start_station_id) != ''
                  AND start_lat IS NOT NULL AND start_lat != 'NaN'::double precision
                  AND start_lng IS NOT NULL AND start_lng != 'NaN'::double precision;
            """)
            expected_starts_count = cur.fetchone()[0]

            # Lấy số trạm kết thúc hợp lệ duy nhất từ bảng trips nguồn
            cur.execute("""
                SELECT COUNT(DISTINCT end_station_id) 
                FROM trips 
                WHERE end_station_id IS NOT NULL 
                  AND end_station_id != '"NaN"' 
                  AND TRIM(end_station_id) != ''
                  AND end_lat IS NOT NULL AND end_lat != 'NaN'::double precision
                  AND end_lng IS NOT NULL AND end_lng != 'NaN'::double precision;
            """)
            expected_ends_count = cur.fetchone()[0]

            # Lấy số trạm giao thoa xuất hiện ở CẢ start và end
            cur.execute("""
                SELECT COUNT(*) FROM (
                    SELECT start_station_id AS sid FROM trips 
                    WHERE start_station_id IS NOT NULL AND start_station_id != '"NaN"' AND TRIM(start_station_id) != ''
                      AND start_lat IS NOT NULL AND start_lat != 'NaN'::double precision
                      AND start_lng IS NOT NULL AND start_lng != 'NaN'::double precision
                    INTERSECT
                    SELECT end_station_id AS sid FROM trips 
                    WHERE end_station_id IS NOT NULL AND end_station_id != '"NaN"' AND TRIM(end_station_id) != ''
                      AND end_lat IS NOT NULL AND end_lat != 'NaN'::double precision
                      AND end_lng IS NOT NULL AND end_lng != 'NaN'::double precision
                ) t;
            """)
            expected_overlap_count = cur.fetchone()[0]

            # Lấy tổng số trạm hợp lệ duy nhất (hợp của start và end)
            cur.execute("""
                SELECT COUNT(*) FROM (
                    SELECT start_station_id AS sid FROM trips 
                    WHERE start_station_id IS NOT NULL AND start_station_id != '"NaN"' AND TRIM(start_station_id) != ''
                      AND start_lat IS NOT NULL AND start_lat != 'NaN'::double precision
                      AND start_lng IS NOT NULL AND start_lng != 'NaN'::double precision
                    UNION
                    SELECT end_station_id AS sid FROM trips 
                    WHERE end_station_id IS NOT NULL AND end_station_id != '"NaN"' AND TRIM(end_station_id) != ''
                      AND end_lat IS NOT NULL AND end_lat != 'NaN'::double precision
                      AND end_lng IS NOT NULL AND end_lng != 'NaN'::double precision
                ) t;
            """)
            expected_total_unique = cur.fetchone()[0]
        finally:
            conn.close()

        # Nạp dữ liệu qua hàm tổng hợp
        df = load_station_activity_data()

        # 1. Tổng số dòng phải bằng đúng số trạm hợp lệ duy nhất trong nguồn
        self.assertEqual(len(df), expected_total_unique, 
                         f"Tổng số trạm {len(df)} không khớp với nguồn {expected_total_unique}")

        # 2. Không có bất kỳ station_id nào bị trùng lặp
        self.assertEqual(df["station_id"].nunique(), len(df), 
                         "Phát hiện trạm bị trùng lặp station_id sau khi gộp start và end")

        # 3. Kiểm tra các trạm xuất hiện ở cả start và end chỉ có đúng 1 bản ghi
        self.assertGreater(expected_overlap_count, 0, "Phải có trạm xuất hiện ở cả 2 vai trò start và end")
        overlap_stations = df[(df["start_count"] > 0) & (df["end_count"] > 0)]
        self.assertEqual(len(overlap_stations), expected_overlap_count,
                         f"Số trạm hai vai trò ({len(overlap_stations)}) không khớp với giao ({expected_overlap_count})")

        # 4. Kiểm tra các trạm end-only (start_count == 0) được bảo toàn đầy đủ
        end_only_stations = df[df["start_count"] == 0]
        expected_end_only = expected_ends_count - expected_overlap_count
        self.assertEqual(len(end_only_stations), expected_end_only,
                         f"Số trạm end-only ({len(end_only_stations)}) không khớp dự kiến ({expected_end_only})")
        self.assertTrue((end_only_stations["end_count"] > 0).all())

    # =========================================================================
    # Test 2 — Activity Count (Test 2 trong docs/TASK_PHASE3.md)
    # =========================================================================
    def test_02_activity_count_reconciliation_with_source_trips(self):
        """
        Đối chiếu trực tiếp công thức Activity Count = Start Count + End Count
        với số liệu đếm độc lập từ bảng trips nguồn.
        """
        sample_station_id = "JC115"  # Trạm mẫu tiêu biểu (Grove St PATH)

        conn = get_connection()
        try:
            cur = conn.cursor()

            # Đếm số chuyến bắt đầu thực tế của trạm mẫu trên trips
            cur.execute("""
                SELECT COUNT(*) FROM trips 
                WHERE start_station_id = %s
                  AND start_lat IS NOT NULL AND start_lat != 'NaN'::double precision
                  AND start_lng IS NOT NULL AND start_lng != 'NaN'::double precision;
            """, (sample_station_id,))
            raw_starts = cur.fetchone()[0]

            # Đếm số chuyến kết thúc thực tế của trạm mẫu trên trips
            cur.execute("""
                SELECT COUNT(*) FROM trips 
                WHERE end_station_id = %s
                  AND end_lat IS NOT NULL AND end_lat != 'NaN'::double precision
                  AND end_lng IS NOT NULL AND end_lng != 'NaN'::double precision;
            """, (sample_station_id,))
            raw_ends = cur.fetchone()[0]
        finally:
            conn.close()

        # Nạp dữ liệu qua hàm tổng hợp
        df = load_station_activity_data()

        # Tìm trạm mẫu trong kết quả tổng hợp
        st_match = df[df["station_id"] == sample_station_id]
        self.assertEqual(len(st_match), 1, f"Không tìm thấy trạm mẫu {sample_station_id}")
        st_row = st_match.iloc[0]

        # 1. Đối chiếu Start Count của trạm mẫu
        self.assertEqual(int(st_row["start_count"]), raw_starts,
                         f"Start count của {sample_station_id} ({st_row['start_count']}) lệch với SQL nguồn ({raw_starts})")

        # 2. Đối chiếu End Count của trạm mẫu
        self.assertEqual(int(st_row["end_count"]), raw_ends,
                         f"End count của {sample_station_id} ({st_row['end_count']}) lệch với SQL nguồn ({raw_ends})")

        # 3. Đối chiếu Activity Count = Start Count + End Count
        expected_activity = raw_starts + raw_ends
        self.assertEqual(int(st_row["activity_count"]), expected_activity,
                         f"Activity count của {sample_station_id} lệch với tổng nguồn ({expected_activity})")

        # 4. Xác minh bất biến toán học trên 100% các trạm trong dữ liệu
        diff = df["activity_count"] - (df["start_count"] + df["end_count"])
        self.assertTrue((diff == 0).all(), "Phát hiện sai lệch activity_count != start_count + end_count")
        self.assertTrue((df["start_count"] >= 0).all(), "Phát hiện start_count âm")
        self.assertTrue((df["end_count"] >= 0).all(), "Phát hiện end_count âm")
        self.assertTrue((df["activity_count"] > 0).all(), "Phát hiện activity_count <= 0")

    # =========================================================================
    # Test 3 — Tọa độ (Test 3 trong docs/TASK_PHASE3.md)
    # =========================================================================
    def test_03_coordinates_validation_and_synthetic_dirty_filter(self):
        """
        Kiểm tra tính hợp lệ của tọa độ trạm thực tế và kiểm tra trong bộ nhớ
        việc loại bỏ tọa độ NULL, 'NaN', ngoài phạm vi NY/NJ; xác minh công thức
        trọng tâm gia quyền cho trạm mâu thuẫn vị trí dock.
        """
        # 1. Kiểm tra 100% tọa độ thực tế nạp lên bản đồ
        df_real = load_station_activity()
        self.assertFalse(df_real.empty, "Dữ liệu trạm thực tế không được rỗng")
        self.assertFalse(df_real["latitude"].isna().any(), "Tồn tại latitude NaN trong dữ liệu thực")
        self.assertFalse(df_real["longitude"].isna().any(), "Tồn tại longitude NaN trong dữ liệu thực")
        self.assertTrue((df_real["latitude"] >= 40.0).all() and (df_real["latitude"] <= 41.5).all(),
                        "Tồn tại latitude ngoài phạm vi NY/NJ")
        self.assertTrue((df_real["longitude"] >= -74.5).all() and (df_real["longitude"] <= -73.0).all(),
                        "Tồn tại longitude ngoài phạm vi NY/NJ")

        # 2. Kiểm tra bộ lọc tọa độ với dữ liệu bẩn nhân tạo trong bộ nhớ (KHÔNG ghi vào DB)
        synthetic_dirty_df = pd.DataFrame([
            {"station_id": "ST_VALID", "station_name": "Valid Station", "latitude": 40.7194, "longitude": -74.0431, "start_count": 10, "end_count": 5, "activity_count": 15},
            {"station_id": "ST_NULL_LAT", "station_name": "Null Lat", "latitude": None, "longitude": -74.0431, "start_count": 1, "end_count": 1, "activity_count": 2},
            {"station_id": "ST_STR_NAN", "station_name": "String NaN", "latitude": "NaN", "longitude": -74.0431, "start_count": 1, "end_count": 1, "activity_count": 2},
            {"station_id": "ST_NULL_LNG", "station_name": "Null Lng", "latitude": 40.7194, "longitude": None, "start_count": 1, "end_count": 1, "activity_count": 2},
            {"station_id": "ST_ZERO_ISLAND", "station_name": "Zero Island", "latitude": 0.0, "longitude": 0.0, "start_count": 1, "end_count": 1, "activity_count": 2},
            {"station_id": "ST_PARIS", "station_name": "Paris Station", "latitude": 48.8566, "longitude": 2.3522, "start_count": 1, "end_count": 1, "activity_count": 2},
            {"station_id": "ST_INVERTED", "station_name": "Inverted Coords", "latitude": -40.7194, "longitude": -74.0431, "start_count": 1, "end_count": 1, "activity_count": 2},
        ])

        cleaned_df = prepare_station_display_data(synthetic_dirty_df)

        # Chỉ có duy nhất ST_VALID được giữ lại
        self.assertEqual(len(cleaned_df), 1, "Lọc tọa độ sai chưa loại bỏ hết các trạm không hợp lệ")
        self.assertEqual(cleaned_df.iloc[0]["station_id"], "ST_VALID")

        # 3. Xác minh công thức trọng tâm gia quyền cho trạm 5772.05 (Morton St & Greenwich St)
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT AVG(start_lat), AVG(start_lng), COUNT(*) 
                FROM trips 
                WHERE start_station_id = '5772.05'
                  AND start_lat IS NOT NULL AND start_lat != 'NaN'::double precision
                  AND start_lng IS NOT NULL AND start_lng != 'NaN'::double precision;
            """)
            s_lat, s_lng, s_cnt = cur.fetchone()

            cur.execute("""
                SELECT AVG(end_lat), AVG(end_lng), COUNT(*) 
                FROM trips 
                WHERE end_station_id = '5772.05'
                  AND end_lat IS NOT NULL AND end_lat != 'NaN'::double precision
                  AND end_lng IS NOT NULL AND end_lng != 'NaN'::double precision;
            """)
            e_lat, e_lng, e_cnt = cur.fetchone()
        finally:
            conn.close()

        # Tính trọng tâm theo đúng công thức SQL CASE trong load_station_activity_data
        if s_lat is not None and e_lat is not None:
            expected_weighted_lat = round((s_lat * s_cnt + e_lat * e_cnt) / (s_cnt + e_cnt), 6)
            expected_weighted_lng = round((s_lng * s_cnt + e_lng * e_cnt) / (s_cnt + e_cnt), 6)
        elif s_lat is not None:
            expected_weighted_lat = round(s_lat, 6)
            expected_weighted_lng = round(s_lng, 6)
        else:
            expected_weighted_lat = round(e_lat, 6)
            expected_weighted_lng = round(e_lng, 6)

        st_5772 = df_real[df_real["station_id"] == "5772.05"]
        self.assertEqual(len(st_5772), 1)
        self.assertAlmostEqual(st_5772.iloc[0]["latitude"], expected_weighted_lat, places=5)
        self.assertAlmostEqual(st_5772.iloc[0]["longitude"], expected_weighted_lng, places=5)

    # =========================================================================
    # Test 4 — Dữ liệu rỗng (Test 4 trong docs/TASK_PHASE3.md)
    # =========================================================================
    def test_04_empty_data_and_zero_record_graceful_handling(self):
        """
        Kiểm tra xử lý an toàn khi không có trạm hợp lệ hoặc filter trả về 0 bản ghi,
        bảo đảm không crash Dashboard và các hàm tra cứu trả về an toàn.
        """
        # 1. DataFrame hoàn toàn rỗng
        empty_raw = pd.DataFrame()
        prepared_empty = prepare_station_display_data(empty_raw)
        self.assertTrue(prepared_empty.empty)
        expected_cols = [
            "station_id", "station_name", "display_label", "latitude",
            "longitude", "start_count", "end_count", "activity_count"
        ]
        for col in expected_cols:
            self.assertIn(col, prepared_empty.columns)

        # 2. DataFrame có các cột đúng nhưng 0 dòng
        empty_with_cols = pd.DataFrame(columns=expected_cols)
        prepared_empty_cols = prepare_station_display_data(empty_with_cols)
        self.assertTrue(prepared_empty_cols.empty)

        # 3. Tra cứu ID trên DataFrame rỗng trả về None mà không crash
        self.assertIsNone(get_station_by_id(prepared_empty, "JC115"))
        self.assertIsNone(get_station_by_id(prepared_empty, ""))

        # 4. Gọi show_station_symbol_map với DataFrame rỗng chạy an toàn không ném Exception
        try:
            show_station_symbol_map(prepared_empty, date_label="01/01/2099 — 31/01/2099")
        except Exception as e:
            self.fail(f"show_station_symbol_map bị crash khi nhận DataFrame rỗng: {e}")

    # =========================================================================
    # Test 5 — Filter thời gian (Test 5 trong docs/TASK_PHASE3.md)
    # =========================================================================
    def test_05_date_filter_reconciliation_two_ranges(self):
        """
        Đối chiếu kết quả của bộ lọc thời gian với truy vấn SQL nguồn thô
        trên bảng trips cho ít nhất 2 phạm vi thời gian độc lập.
        """
        ranges = [
            ("2026-07-15", "2026-07-15", "Ngày đơn lẻ 15/07/2026"),
            ("2026-07-01", "2026-07-31", "Tháng đầy đủ 07/2026"),
        ]

        conn = get_connection()
        try:
            cur = conn.cursor()

            for start_d, end_d, label in ranges:
                # Chuẩn hóa mốc thời gian đối chứng theo ngày
                start_ts = f"{start_d} 00:00:00"
                end_ts = f"{end_d} 23:59:59.999999"

                # Đếm lượt xuất phát độc lập trên trips
                cur.execute("""
                    SELECT COUNT(*) FROM trips 
                    WHERE started_at >= %s AND started_at <= %s
                      AND start_station_id IS NOT NULL AND start_station_id != '"NaN"' AND TRIM(start_station_id) != ''
                      AND start_lat IS NOT NULL AND start_lat != 'NaN'::double precision
                      AND start_lng IS NOT NULL AND start_lng != 'NaN'::double precision;
                """, (start_ts, end_ts))
                raw_starts = cur.fetchone()[0]

                # Đếm lượt kết thúc độc lập trên trips
                cur.execute("""
                    SELECT COUNT(*) FROM trips 
                    WHERE ended_at >= %s AND ended_at <= %s
                      AND end_station_id IS NOT NULL AND end_station_id != '"NaN"' AND TRIM(end_station_id) != ''
                      AND end_lat IS NOT NULL AND end_lat != 'NaN'::double precision
                      AND end_lng IS NOT NULL AND end_lng != 'NaN'::double precision;
                """, (start_ts, end_ts))
                raw_ends = cur.fetchone()[0]

                # Nạp dữ liệu qua hàm lọc
                df_filtered = load_station_activity_data(start_date=start_d, end_date=end_d)

                # Đối chiếu Start Count
                agg_starts = int(df_filtered["start_count"].sum()) if not df_filtered.empty else 0
                self.assertEqual(agg_starts, raw_starts,
                                 f"[{label}] Start count tổng hợp ({agg_starts}) lệch SQL nguồn ({raw_starts})")

                # Đối chiếu End Count
                agg_ends = int(df_filtered["end_count"].sum()) if not df_filtered.empty else 0
                self.assertEqual(agg_ends, raw_ends,
                                 f"[{label}] End count tổng hợp ({agg_ends}) lệch SQL nguồn ({raw_ends})")

                # Đối chiếu Activity Count
                agg_activity = int(df_filtered["activity_count"].sum()) if not df_filtered.empty else 0
                self.assertEqual(agg_activity, raw_starts + raw_ends,
                                 f"[{label}] Activity count tổng hợp ({agg_activity}) lệch tổng SQL nguồn ({raw_starts + raw_ends})")

                # Tính nhất quán cho từng trạm trong phạm vi lọc
                if not df_filtered.empty:
                    diff = df_filtered["activity_count"] - (df_filtered["start_count"] + df_filtered["end_count"])
                    self.assertTrue((diff == 0).all())
        finally:
            conn.close()

    # =========================================================================
    # Test 6 — Biên ngày tháng (Reversed & Future Dates)
    # =========================================================================
    def test_06_edge_case_reversed_date_and_future_date(self):
        """
        Kiểm tra hành vi thực tế khi khoảng thời gian bị đảo ngược (start_date > end_date)
        hoặc thời gian trong tương lai chưa có dữ liệu: trả về DataFrame rỗng an toàn,
        không ném ngoại lệ làm gián đoạn ứng dụng.
        """
        # 1. Ngày bắt đầu lớn hơn ngày kết thúc
        norm_start, norm_end, is_reversed = normalize_date_range("2026-07-31", "2026-07-01")
        self.assertTrue(is_reversed, "normalize_date_range phải nhận diện is_reversed=True")

        df_rev = load_station_activity_data(start_date="2026-07-31", end_date="2026-07-01")
        self.assertTrue(df_rev.empty, "Dữ liệu ngày đảo ngược phải rỗng")
        self.assertIn("station_id", df_rev.columns)

        df_loaded_rev = load_station_activity(start_date="2026-07-31", end_date="2026-07-01")
        self.assertTrue(df_loaded_rev.empty)
        self.assertIn("display_label", df_loaded_rev.columns)

        # 2. Ngày trong tương lai (không có chuyến đi nào)
        df_future = load_station_activity_data(start_date="2099-01-01", end_date="2099-01-31")
        self.assertTrue(df_future.empty, "Dữ liệu năm 2099 phải rỗng")
        self.assertIn("station_id", df_future.columns)

        df_loaded_future = load_station_activity(start_date="2099-01-01", end_date="2099-01-31")
        self.assertTrue(df_loaded_future.empty)
        self.assertIn("display_label", df_loaded_future.columns)


if __name__ == "__main__":
    unittest.main()

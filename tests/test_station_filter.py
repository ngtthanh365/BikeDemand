import sys
import unittest
from datetime import date, datetime
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))

from database.postgres import load_station_activity_data, normalize_date_range
from dashboard.services.data_loader import (
    load_station_activity,
    prepare_station_display_data,
    format_date_range_label
)
from dashboard.components.charts import show_station_symbol_map


class TestStationFilter(unittest.TestCase):
    """
    Bộ kiểm thử tự động cho Task 7 — Bộ lọc thời gian (Phase 3).
    Kiểm định:
      1. Mặc định toàn bộ dữ liệu khi chưa chọn khoảng thời gian.
      2. Lọc đúng theo khoảng ngày hợp lệ (tháng, ngày đơn lẻ) với nhiều định dạng (str, date, Timestamp).
      3. Xử lý an toàn khi khoảng ngày không có dữ liệu (out of range).
      4. Xử lý an toàn trường hợp ngày bắt đầu lớn hơn ngày kết thúc (start_date > end_date).
      5. Nhãn thời gian hiển thị rõ ràng, thân thiện.
      6. Cập nhật chính xác số lượt đi, lượt đến, tổng hoạt động và hiển thị an toàn trên bản đồ.
    """

    def test_01_default_all_data(self):
        """Mặc định khi start_date=None và end_date=None phải trả về toàn bộ 452 trạm."""
        df_raw = load_station_activity_data()
        self.assertEqual(len(df_raw), 452, "Mặc định phải tải đủ 452 trạm")
        self.assertEqual(df_raw["start_count"].sum(), 742614)
        self.assertEqual(df_raw["end_count"].sum(), 738752)
        self.assertEqual(df_raw["activity_count"].sum(), 1481366)

        # Kiểm tra loader có chuẩn hóa display_label
        df_loaded = load_station_activity(None, None)
        self.assertEqual(len(df_loaded), 452)
        self.assertIn("display_label", df_loaded.columns)

    def test_02_valid_date_range_monthly(self):
        """Khoảng ngày hợp lệ (Tháng 7/2026): số lượt tính toán chính xác, nhất quán giữa str và date."""
        # 1. Truy vấn bằng chuỗi YYYY-MM-DD
        df_str = load_station_activity_data(start_date="2026-07-01", end_date="2026-07-31")
        self.assertFalse(df_str.empty)
        self.assertEqual(len(df_str), 232, "Tháng 7/2026 phải có 232 trạm hoạt động")
        self.assertEqual(df_str["activity_count"].sum(), 217840)

        # 2. Truy vấn bằng đối tượng date
        df_date = load_station_activity_data(
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31)
        )
        self.assertEqual(len(df_date), 232)
        self.assertEqual(df_date["activity_count"].sum(), 217840)

        # 3. Tính nhất quán giữa các bộ đếm
        diff = df_str["activity_count"] - (df_str["start_count"] + df_str["end_count"])
        self.assertTrue((diff == 0).all(), "Phát hiện sai lệch activity_count != start_count + end_count")
        self.assertTrue((df_str["start_count"] >= 0).all())
        self.assertTrue((df_str["end_count"] >= 0).all())

        # Tọa độ hợp lệ
        self.assertFalse(df_str["latitude"].isna().any())
        self.assertFalse(df_str["longitude"].isna().any())

    def test_03_valid_date_range_single_day(self):
        """Lọc một ngày cụ thể (2026-07-15): bao hàm trọn vẹn cả ngày đến 23:59:59."""
        df_day = load_station_activity_data(start_date="2026-07-15", end_date="2026-07-15")
        self.assertEqual(len(df_day), 122, "Ngày 15/07/2026 phải có 122 trạm hoạt động")
        self.assertEqual(df_day["start_count"].sum(), 3508)
        self.assertEqual(df_day["end_count"].sum(), 3496)
        self.assertEqual(df_day["activity_count"].sum(), 7004)

        # Kiểm tra qua load_station_activity
        df_loaded = load_station_activity(start_date="2026-07-15", end_date="2026-07-15")
        self.assertEqual(len(df_loaded), 122)
        self.assertEqual(df_loaded["activity_count"].sum(), 7004)

    def test_04_out_of_range_no_data(self):
        """Khoảng thời gian không có dữ liệu (năm 2027) trả về DataFrame rỗng an toàn, đủ cấu trúc cột."""
        df_future = load_station_activity_data(start_date="2027-01-01", end_date="2027-01-31")
        self.assertTrue(df_future.empty)
        expected_cols = [
            "station_id", "station_name", "latitude", "longitude",
            "start_count", "end_count", "activity_count"
        ]
        for col in expected_cols:
            self.assertIn(col, df_future.columns)

        df_loaded = load_station_activity(start_date="2027-01-01", end_date="2027-01-31")
        self.assertTrue(df_loaded.empty)
        self.assertIn("display_label", df_loaded.columns)

    def test_05_reversed_date_range_start_after_end(self):
        """Trường hợp ngày bắt đầu > ngày kết thúc được xử lý an toàn, không ném exception và trả về empty df."""
        norm_start, norm_end, is_reversed = normalize_date_range("2026-07-31", "2026-07-01")
        self.assertTrue(is_reversed, "Phải phát hiện start_date > end_date")

        df_rev = load_station_activity_data(start_date="2026-07-31", end_date="2026-07-01")
        self.assertTrue(df_rev.empty)
        self.assertIn("station_id", df_rev.columns)

        df_loaded = load_station_activity(start_date="2026-07-31", end_date="2026-07-01")
        self.assertTrue(df_loaded.empty)
        self.assertIn("display_label", df_loaded.columns)

    def test_06_format_date_range_label(self):
        """Kiểm tra nhãn hiển thị khoảng thời gian thân thiện."""
        # Mặc định
        self.assertEqual(format_date_range_label(None, None), "Toàn bộ dữ liệu")

        # Khoảng ngày hợp lệ
        self.assertEqual(format_date_range_label("2026-07-01", "2026-07-31"), "01/07/2026 — 31/07/2026")
        self.assertEqual(format_date_range_label(date(2026, 7, 1), date(2026, 7, 31)), "01/07/2026 — 31/07/2026")

        # Một ngày đơn lẻ
        self.assertEqual(format_date_range_label("2026-07-15", "2026-07-15"), "15/07/2026 — 15/07/2026")

        # Ngày bắt đầu > ngày kết thúc
        self.assertIn("không hợp lệ", format_date_range_label("2026-07-31", "2026-07-01"))

        # Bán khoảng (chỉ start hoặc chỉ end)
        self.assertEqual(format_date_range_label("2026-07-01", None), "Từ 01/07/2026")
        self.assertEqual(format_date_range_label(None, "2026-07-31"), "Đến 31/07/2026")

    def test_07_safe_chart_rendering_with_filtered_and_empty_data(self):
        """Bản đồ hiển thị an toàn khi có date_label hoặc dữ liệu rỗng."""
        # 1. Dữ liệu rỗng với date_label
        empty_df = pd.DataFrame()
        try:
            show_station_symbol_map(empty_df, date_label="01/01/2027 — 31/01/2027")
        except Exception as e:
            self.fail(f"show_station_symbol_map gặp lỗi khi DataFrame rỗng: {e}")

        # 2. Dữ liệu hợp lệ với date_label
        df_july = load_station_activity("2026-07-15", "2026-07-15")
        try:
            show_station_symbol_map(df_july, date_label="15/07/2026 — 15/07/2026")
        except Exception as e:
            self.fail(f"show_station_symbol_map gặp lỗi khi hiển thị dữ liệu lọc: {e}")


if __name__ == "__main__":
    unittest.main()

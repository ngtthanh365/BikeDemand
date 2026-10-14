import sys
import unittest
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.postgres import load_station_activity_data


class TestStationAggregation(unittest.TestCase):
    """
    Bộ kiểm thử tự động cho Task 2 — Tổng hợp dữ liệu cấp trạm (Phase 3).
    Kiểm định: số lượng trạm, bộ đếm, dữ liệu rác, tọa độ khác nhau, hiệu quả truyền tải.
    """

    @classmethod
    def setUpClass(cls):
        # Tải dữ liệu tổng hợp toàn thời gian từ database
        cls.df = load_station_activity_data()

    def test_01_station_count_and_columns(self):
        """Kiểm tra số lượng trạm duy nhất và cấu trúc cột trả về."""
        # Đúng 452 trạm hợp lệ duy nhất
        self.assertEqual(len(self.df), 452)
        # Không có station_id trùng lặp
        self.assertEqual(self.df["station_id"].nunique(), 452)

        # Đầy đủ 7 trường mục tiêu theo đặc tả TASK_PHASE3.md
        expected_cols = [
            "station_id",
            "station_name",
            "latitude",
            "longitude",
            "start_count",
            "end_count",
            "activity_count",
        ]
        for col in expected_cols:
            self.assertIn(col, self.df.columns, f"Thiếu cột bắt buộc: {col}")

    def test_02_counters_integrity(self):
        """Kiểm tra tính toàn vẹn và quy tắc toán học của các bộ đếm."""
        # Không có số âm
        self.assertTrue((self.df["start_count"] >= 0).all())
        self.assertTrue((self.df["end_count"] >= 0).all())
        self.assertTrue((self.df["activity_count"] > 0).all())

        # Quy tắc: activity_count = start_count + end_count cho từng trạm
        diff = self.df["activity_count"] - (self.df["start_count"] + self.df["end_count"])
        self.assertTrue((diff == 0).all(), "Phát hiện sai lệch activity_count != start_count + end_count")

        # Đối chiếu tổng các chuyến đi nguồn (742,615 trips)
        # Start count: đúng 742,614 (chỉ loại 1 bản ghi start '"NaN"')
        self.assertEqual(self.df["start_count"].sum(), 742614)
        # End count: đúng 738,752 (loại 3,863 bản ghi không rõ trạm trả)
        self.assertEqual(self.df["end_count"].sum(), 738752)
        # Tổng activity count
        self.assertEqual(self.df["activity_count"].sum(), 1481366)

    def test_03_coordinates_validity(self):
        """Kiểm tra tính hợp lệ của tọa độ vĩ độ và kinh độ."""
        # Không có giá trị NULL hoặc NaN
        self.assertFalse(self.df["latitude"].isna().any())
        self.assertFalse(self.df["longitude"].isna().any())

        # Nằm trong phạm vi địa lý hợp lệ của vùng đô thị NY/NJ
        self.assertTrue((self.df["latitude"] >= 40.6).all())
        self.assertTrue((self.df["latitude"] <= 40.9).all())
        self.assertTrue((self.df["longitude"] >= -74.2).all())
        self.assertTrue((self.df["longitude"] <= -73.8).all())

    def test_04_junk_data_and_whitespace_cleaning(self):
        """Kiểm tra việc loại bỏ dữ liệu rác và chuẩn hóa khoảng trắng tên trạm."""
        # Không còn chuỗi "NaN", NaN, rỗng trong station_id
        junk_ids = ['"NaN"', "NaN", "nan", "null", "None", ""]
        self.assertFalse(self.df["station_id"].isin(junk_ids).any())

        # Không còn chuỗi "NaN", NaN, rỗng trong station_name
        self.assertFalse(self.df["station_name"].isin(junk_ids).any())

        # Trạm 6626.11 phải được chuẩn hóa khoảng trắng kép thành khoảng trắng đơn
        st_6626 = self.df[self.df["station_id"] == "6626.11"]
        self.assertEqual(len(st_6626), 1)
        self.assertEqual(st_6626.iloc[0]["station_name"], "W 48 St & Rockefeller Plaza")
        self.assertNotIn("  ", st_6626.iloc[0]["station_name"])

    def test_05_varying_coordinates_handling(self):
        """Kiểm tra xử lý trọng tâm tọa độ cho trạm có nhiều dock lệch nhau (ID 5772.05)."""
        st_5772 = self.df[self.df["station_id"] == "5772.05"]
        self.assertEqual(len(st_5772), 1)
        row = st_5772.iloc[0]

        # Tọa độ trọng tâm đại diện phải nằm giữa 2 vị trí dock
        self.assertAlmostEqual(row["latitude"], 40.731137, places=5)
        self.assertAlmostEqual(row["longitude"], -74.008231, places=5)
        self.assertEqual(row["activity_count"], 9)

    def test_06_data_volume_efficiency(self):
        """Xác nhận hiệu quả: ứng dụng chỉ nhận đúng 452 dòng tổng hợp thay vì 742,615 dòng."""
        # Số dòng trả về bằng đúng số trạm (452 dòng)
        self.assertEqual(len(self.df), 452)
        # Dung lượng RAM nhỏ gọn (< 100 KB)
        mem_kb = self.df.memory_usage(deep=True).sum() / 1024
        self.assertLess(mem_kb, 100.0, f"Dung lượng DataFrame quá lớn: {mem_kb:.2f} KB")

    def test_07_optional_date_filtering(self):
        """Kiểm tra hỗ trợ lọc theo khoảng thời gian tùy chọn (ví dụ tháng 6/2026)."""
        df_june = load_station_activity_data(
            start_date="2026-06-01 00:00:00",
            end_date="2026-06-30 23:59:59"
        )
        # Tháng 6 có 251 trạm hoạt động
        self.assertEqual(len(df_june), 251)
        self.assertTrue((df_june["activity_count"] > 0).all())
        # Toán tử count vẫn đảm bảo tính đúng đắn
        diff = df_june["activity_count"] - (df_june["start_count"] + df_june["end_count"])
        self.assertTrue((diff == 0).all())


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))

from dashboard.services.data_loader import (
    prepare_station_display_data,
    get_station_by_id,
    load_station_activity,
)


class TestStationDisplay(unittest.TestCase):
    """
    Bộ kiểm thử cho Task 3 — Hiển thị tên trạm và tọa độ (Phase 3).
    Kiểm định: tên trạm, tọa độ thực, tính duy nhất của Station ID và cơ chế tra cứu.
    """

    @classmethod
    def setUpClass(cls):
        # Tải dữ liệu hiển thị đã chuẩn bị qua data_loader
        cls.df = load_station_activity()

    def test_01_station_name_validity_and_normalization(self):
        """Xác minh tên trạm hiển thị đúng, không chứa lỗi định dạng."""
        # 100% tên trạm không rỗng
        self.assertTrue((self.df["station_name"].str.strip() != "").all())
        # Không có chuỗi 'None', 'nan', 'NaN', 'null'
        junk_strings = ["none", "nan", "null", "undefined"]
        self.assertFalse(self.df["station_name"].str.lower().isin(junk_strings).any())
        # Không có khoảng trắng kép
        self.assertFalse(self.df["station_name"].str.contains(r"\s{2,}").any())

        # Kiểm tra chuẩn hóa cụ thể trạm 6626.11
        st_6626 = get_station_by_id(self.df, "6626.11")
        self.assertIsNotNone(st_6626)
        self.assertEqual(st_6626["station_name"], "W 48 St & Rockefeller Plaza")

    def test_02_station_id_uniqueness(self):
        """Xác minh Station ID là duy nhất tuyệt đối, không trùng lặp."""
        self.assertEqual(len(self.df), 452)
        self.assertEqual(self.df["station_id"].nunique(), 452)
        # Không có station_id rỗng
        self.assertTrue((self.df["station_id"].str.strip() != "").all())

    def test_03_coordinates_numeric_and_realistic(self):
        """Xác minh tọa độ lấy từ dữ liệu thật, là số thực hợp lệ và nằm trong phạm vi."""
        # Tọa độ là kiểu float64
        self.assertTrue(pd.api.types.is_float_dtype(self.df["latitude"]))
        self.assertTrue(pd.api.types.is_float_dtype(self.df["longitude"]))

        # Không có NaN, Inf hay None
        self.assertFalse(self.df["latitude"].isna().any())
        self.assertFalse(self.df["longitude"].isna().any())
        self.assertFalse(np.isinf(self.df["latitude"]).any())
        self.assertFalse(np.isinf(self.df["longitude"]).any())

        # Phạm vi địa lý thực tế vùng NY/NJ
        self.assertTrue((self.df["latitude"] >= 40.6).all() and (self.df["latitude"] <= 40.9).all())
        self.assertTrue((self.df["longitude"] >= -74.2).all() and (self.df["longitude"] <= -73.8).all())

    def test_04_station_lookup_by_id(self):
        """Xác minh cơ chế tra cứu trạm theo Station ID hoạt động chính xác."""
        # Tra cứu trạm mẫu có hoạt động cao nhất (JC115 - Grove St PATH)
        st_info = get_station_by_id(self.df, "JC115")
        self.assertIsNotNone(st_info)
        self.assertEqual(st_info["station_id"], "JC115")
        self.assertEqual(st_info["station_name"], "Grove St PATH")
        self.assertEqual(st_info["display_label"], "Grove St PATH (JC115)")
        self.assertAlmostEqual(st_info["latitude"], 40.719410, places=4)
        self.assertAlmostEqual(st_info["longitude"], -74.043090, places=4)
        self.assertEqual(st_info["activity_count"], 68266)

        # Tra cứu mã không tồn tại trả về None
        self.assertIsNone(get_station_by_id(self.df, "NON_EXISTENT_STATION"))
        self.assertIsNone(get_station_by_id(self.df, ""))

    def test_05_display_label_distinguishes_duplicate_names(self):
        """Xác minh display_label kết hợp Station Name và Station ID giúp phân biệt trạm trùng tên."""
        self.assertIn("display_label", self.df.columns)
        # Kiểm tra các trạm có cùng tên vật lý nhưng khác sub-dock (e.g. 5073.07 và 5073.08)
        st_1 = get_station_by_id(self.df, "5073.07")
        st_2 = get_station_by_id(self.df, "5073.08")
        if st_1 and st_2:
            self.assertEqual(st_1["station_name"], st_2["station_name"])
            self.assertNotEqual(st_1["display_label"], st_2["display_label"])
            self.assertEqual(st_1["display_label"], f"{st_1['station_name']} (5073.07)")
            self.assertEqual(st_2["display_label"], f"{st_2['station_name']} (5073.08)")

    def test_06_edge_case_missing_name_fallback(self):
        """Kiểm tra xử lý biên: trạm thiếu tên được gán fallback minh bạch không bịa tên giả."""
        dummy_df = pd.DataFrame([
            {
                "station_id": "TEST_NO_NAME",
                "station_name": None,
                "latitude": 40.72,
                "longitude": -74.04,
                "start_count": 10,
                "end_count": 5,
                "activity_count": 15,
            },
            {
                "station_id": "TEST_NAN_NAME",
                "station_name": "NaN",
                "latitude": 40.73,
                "longitude": -74.03,
                "start_count": 5,
                "end_count": 5,
                "activity_count": 10,
            }
        ])
        processed = prepare_station_display_data(dummy_df)
        self.assertEqual(len(processed), 2)
        self.assertEqual(processed.iloc[0]["station_name"], "Station TEST_NO_NAME")
        self.assertEqual(processed.iloc[1]["station_name"], "Station TEST_NAN_NAME")
        self.assertEqual(processed.iloc[0]["display_label"], "Station TEST_NO_NAME (TEST_NO_NAME)")

    def test_07_edge_case_duplicate_id_deduplication(self):
        """Kiểm tra xử lý biên: trùng Station ID được loại bỏ an toàn."""
        dummy_df = pd.DataFrame([
            {"station_id": "DUP01", "station_name": "Dock A", "latitude": 40.71, "longitude": -74.04, "start_count": 1, "end_count": 0, "activity_count": 1},
            {"station_id": "DUP01", "station_name": "Dock A", "latitude": 40.71, "longitude": -74.04, "start_count": 1, "end_count": 0, "activity_count": 1},
        ])
        processed = prepare_station_display_data(dummy_df)
        self.assertEqual(len(processed), 1)


if __name__ == "__main__":
    unittest.main()

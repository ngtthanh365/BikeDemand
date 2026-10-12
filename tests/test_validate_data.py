import unittest
from pathlib import Path
import pandas as pd
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.validate_data import (
    validate_schema,
    validate_and_clean_data,
    ValidationError,
    REQUIRED_COLUMNS,
)


class TestDataValidation(unittest.TestCase):

    def setUp(self):
        self.sample_row = {
            "ride_id": "TEST_RIDE_001",
            "rideable_type": "classic_bike",
            "started_at": "2026-07-15 10:00:00.000",
            "ended_at": "2026-07-15 10:25:00.000",
            "start_station_name": "Newport Pkwy",
            "start_station_id": "JC042",
            "end_station_name": "Liberty Light Rail",
            "end_station_id": "JC052",
            "start_lat": 40.7287448,
            "start_lng": -74.0321082,
            "end_lat": 40.7112423,
            "end_lng": -74.0557013,
            "member_casual": "member",
        }

    def test_schema_valid(self):
        df = pd.DataFrame([self.sample_row])
        is_valid, missing = validate_schema(df)
        self.assertTrue(is_valid)
        self.assertEqual(len(missing), 0)

    def test_schema_missing_column(self):
        df = pd.DataFrame([self.sample_row]).drop(columns=["member_casual"])
        is_valid, missing = validate_schema(df)
        self.assertFalse(is_valid)
        self.assertIn("member_casual", missing)

        with self.assertRaises(ValidationError):
            validate_and_clean_data(df, check_db_duplicates=False)

    def test_invalid_datetime_dropped(self):
        row_invalid = self.sample_row.copy()
        row_invalid["ride_id"] = "TEST_INVALID_DT"
        row_invalid["started_at"] = "invalid-date-string"

        df = pd.DataFrame([self.sample_row, row_invalid])
        cleaned, stats = validate_and_clean_data(df, check_db_duplicates=False)

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned.iloc[0]["ride_id"], "TEST_RIDE_001")
        self.assertEqual(stats["invalid_datetime_dropped"], 1)

    def test_negative_duration_dropped(self):
        row_negative = self.sample_row.copy()
        row_negative["ride_id"] = "TEST_NEG_DUR"
        row_negative["started_at"] = "2026-07-15 10:30:00.000"
        row_negative["ended_at"] = "2026-07-15 10:00:00.000"

        df = pd.DataFrame([self.sample_row, row_negative])
        cleaned, stats = validate_and_clean_data(df, check_db_duplicates=False)

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(stats["negative_duration_dropped"], 1)

    def test_outside_period_dropped(self):
        row_june = self.sample_row.copy()
        row_june["ride_id"] = "TEST_JUNE"
        row_june["started_at"] = "2026-06-30 23:55:00.000"
        row_june["ended_at"] = "2026-07-01 00:10:00.000"

        df = pd.DataFrame([self.sample_row, row_june])
        cleaned, stats = validate_and_clean_data(
            df, target_month="202607", check_db_duplicates=False
        )

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned.iloc[0]["ride_id"], "TEST_RIDE_001")
        self.assertEqual(stats["outside_period_dropped"], 1)

    def test_internal_duplicate_ride_id_dropped(self):
        row_dup = self.sample_row.copy()
        df = pd.DataFrame([self.sample_row, row_dup])
        cleaned, stats = validate_and_clean_data(df, check_db_duplicates=False)

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(stats["internal_duplicate_ride_id_dropped"], 1)

    def test_invalid_coordinates_dropped(self):
        row_bad_coords = self.sample_row.copy()
        row_bad_coords["ride_id"] = "TEST_BAD_COORD"
        row_bad_coords["start_lat"] = 0.0  # Invalid for NYC
        row_bad_coords["start_lng"] = 0.0

        df = pd.DataFrame([self.sample_row, row_bad_coords])
        cleaned, stats = validate_and_clean_data(df, check_db_duplicates=False)

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(stats["invalid_coordinates_dropped"], 1)

    def test_invalid_category_dropped(self):
        row_bad_cat = self.sample_row.copy()
        row_bad_cat["ride_id"] = "TEST_BAD_CAT"
        row_bad_cat["member_casual"] = "vip_guest"

        df = pd.DataFrame([self.sample_row, row_bad_cat])
        cleaned, stats = validate_and_clean_data(df, check_db_duplicates=False)

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(stats["invalid_categories_dropped"], 1)


if __name__ == "__main__":
    unittest.main()

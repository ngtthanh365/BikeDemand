"""
tests/test_future_forecast_integration.py — Task 7: Integration Test (Phase 2)

Kiểm thử tích hợp toàn diện luồng Future Demand Forecast (168 giờ / 7 ngày):
  1. Test 1: Kiểm tra tính liên tục, phạm vi thời gian (2026-10-01 00:00 -> 2026-10-07 23:00) và 168 dòng dự báo.
  2. Test 2: Kiểm tra nguyên tắc No Data Leakage trong đệ quy (chỉ dùng buffer lịch sử + dự báo trước).
  3. Test 3: Kiểm tra tính an toàn khi chạy lại (Idempotency): future-v1 không nhân đôi, Random Forest 1.0 giữ nguyên 4,176 dòng.
  4. Test 4: Kiểm tra tính toàn vẹn cơ sở dữ liệu (trips, hourly_demand, predictions schema).
  5. Test 5: Kiểm tra tích hợp Dashboard: load_future_forecast_data() đủ 168 điểm, HTTP status 200 OK.
  6. Test 6: Kiểm tra xử lý an toàn (Graceful Handling) khi dữ liệu rỗng và lỗi database.
"""

import os
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Thêm dashboard vào sys.path để test data loader
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))

from database.postgres import get_connection, load_predictions
from dashboard.services.data_loader import load_future_forecast_data
from dashboard.components.charts import show_future_forecast_chart


class TestFutureForecastIntegration(unittest.TestCase):
    """Bộ kiểm thử tích hợp hoàn chỉnh cho Task 7 — Phase 2."""

    @classmethod
    def setUpClass(cls):
        """Khởi tạo và kiểm tra kết nối DB cơ bản."""
        cls.conn = get_connection()
        cls.output_csv = PROJECT_ROOT / "analysis" / "outputs" / "ml" / "future_forecast.csv"

    @classmethod
    def tearDownClass(cls):
        """Đóng kết nối DB khi hoàn tất bộ test."""
        if cls.conn and not cls.conn.closed:
            cls.conn.close()

    # ============================================================
    # TEST 1 — FORECAST HIỆN TẠI (168H RANGE & OUTPUT VALIDATION)
    # ============================================================
    def test_01_forecast_current_range_and_output(self):
        """
        Xác nhận chuỗi dự báo 168 giờ từ latest_actual hiện tại (2026-09-30 23:00):
        Expected: 2026-10-01 00:00 -> 2026-10-07 23:00, Rows = 168.
        """
        # 1. Kiểm tra file CSV đầu ra
        self.assertTrue(self.output_csv.exists(), f"File {self.output_csv} không tồn tại!")
        df_csv = pd.read_csv(self.output_csv)

        self.assertEqual(len(df_csv), 168, f"CSV phải có 168 dòng, thực tế: {len(df_csv)}")
        self.assertEqual(df_csv["target_time"].nunique(), 168, "CSV có timestamp trùng lặp!")

        dt_series = pd.to_datetime(df_csv["target_time"])
        self.assertEqual(
            dt_series.min(),
            pd.Timestamp("2026-10-01 00:00:00"),
            f"Mốc bắt đầu không khớp: {dt_series.min()}",
        )
        self.assertEqual(
            dt_series.max(),
            pd.Timestamp("2026-10-07 23:00:00"),
            f"Mốc kết thúc không khớp: {dt_series.max()}",
        )

        # Kiểm tra bước nhảy thời gian strictly 1 giờ
        diffs = dt_series.diff().dropna()
        self.assertTrue(
            (diffs == pd.Timedelta(hours=1)).all(),
            "Các mốc thời gian không cách nhau đúng 1 giờ!",
        )

        # Kiểm tra giá trị dự báo không NaN/Inf và không âm
        self.assertEqual(df_csv["predicted_demand"].isnull().sum(), 0, "predicted_demand chứa NULL/NaN")
        self.assertFalse(np.isinf(df_csv["predicted_demand"].to_numpy()).any(), "predicted_demand chứa Inf")
        self.assertTrue((df_csv["predicted_demand"] >= 0).all(), "predicted_demand có giá trị âm!")

        # Kiểm tra metadata
        self.assertTrue((df_csv["model_name"] == "Random Forest").all())
        self.assertTrue((df_csv["model_version"] == "future-v1").all())
        self.assertTrue(df_csv["actual_demand"].isnull().all(), "actual_demand phải là NULL cho future forecast")

    # ============================================================
    # TEST 2 — KHÔNG RÒ RỈ DỮ LIỆU TƯƠNG LAI (NO DATA LEAKAGE)
    # ============================================================
    def test_02_no_future_data_leakage(self):
        """
        Xác nhận mỗi bước dự báo t chỉ dùng buffer lịch sử + các giá trị dự báo trước đó.
        Không truy cập hay tham chiếu đến dữ liệu thực tế tương lai nào.
        """
        df_csv = pd.read_csv(self.output_csv)
        
        # Kiểm tra toàn bộ 168 dòng đều có actual_demand là NULL
        self.assertTrue(
            df_csv["actual_demand"].isna().all(),
            "Phát hiện actual_demand không phải NULL trong file kết quả dự báo tương lai!",
        )

        # Kiểm tra truy vấn bảng hourly_demand: latest_actual thực tế trong DB
        with self.conn.cursor() as cur:
            cur.execute("SELECT MAX(timestamp) FROM hourly_demand;")
            latest_actual = cur.fetchone()[0]

        self.assertEqual(
            latest_actual,
            datetime(2026, 9, 30, 23, 0, 0),
            f"Latest actual trong DB không khớp: {latest_actual}",
        )

        # Xác nhận mốc dự báo đầu tiên strictly bắt đầu sau latest_actual
        first_forecast = pd.to_datetime(df_csv["target_time"].iloc[0])
        self.assertEqual(
            first_forecast,
            latest_actual + pd.Timedelta(hours=1),
            "Điểm bắt đầu dự báo không phải latest_actual + 1h!",
        )

        # Xác nhận trong PostgreSQL không hề có bản ghi actual nào trong tháng 10/2026
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM hourly_demand WHERE timestamp >= '2026-10-01 00:00:00';")
            future_actual_count = cur.fetchone()[0]
        self.assertEqual(
            future_actual_count,
            0,
            "Có dữ liệu thực tế trong tương lai trong DB, vi phạm môi trường dự báo!",
        )

    # ============================================================
    # TEST 3 — RERUN AN TOÀN & BẢO TOÀN LỊCH SỬ (IDEMPOTENCY)
    # ============================================================
    def test_03_rerun_idempotency_and_history_preservation(self):
        """
        Xác nhận khi rerun:
        1. future-v1 được thay thế đúng scope, đúng 168 dòng, không bị duplicate.
        2. Random Forest / 1.0 giữ nguyên vẹn 4,176 dòng, không bị xóa và không bị NULL hóa actual_demand.
        """
        with self.conn.cursor() as cur:
            # Kiểm tra số lượng bản ghi của từng phiên bản
            cur.execute("""
                SELECT model_name, model_version, COUNT(*), COUNT(DISTINCT target_time),
                       COUNT(actual_demand), COUNT(*) - COUNT(actual_demand)
                FROM predictions
                GROUP BY model_name, model_version
                ORDER BY model_name, model_version;
            """)
            rows = cur.fetchall()

        stats = {f"{r[0]}/{r[1]}": {"total": r[2], "distinct": r[3], "non_null": r[4], "nulls": r[5]} for r in rows}

        # 1. Kiểm tra Random Forest / 1.0 (Phase 1)
        self.assertIn("Random Forest/1.0", stats, "Thiếu phiên bản Random Forest / 1.0 trong DB!")
        hist_stats = stats["Random Forest/1.0"]
        self.assertEqual(hist_stats["total"], 4176, f"Số dòng Random Forest / 1.0 bị thay đổi: {hist_stats['total']} != 4176")
        self.assertEqual(hist_stats["distinct"], 4176, "Random Forest / 1.0 có target_time trùng lặp!")
        self.assertEqual(hist_stats["non_null"], 4176, "Random Forest / 1.0 có actual_demand bị NULL hóa!")
        self.assertEqual(hist_stats["nulls"], 0, "Random Forest / 1.0 có bản ghi NULL actual_demand!")

        # 2. Kiểm tra Random Forest / future-v1 (Phase 2)
        self.assertIn("Random Forest/future-v1", stats, "Thiếu phiên bản Random Forest / future-v1 trong DB!")
        fut_stats = stats["Random Forest/future-v1"]
        self.assertEqual(fut_stats["total"], 168, f"Số dòng future-v1 không đúng 168: {fut_stats['total']}")
        self.assertEqual(fut_stats["distinct"], 168, "future-v1 bị duplicate target_time!")
        self.assertEqual(fut_stats["nulls"], 168, "future-v1 phải có 100% actual_demand là NULL!")
        self.assertEqual(fut_stats["non_null"], 0, "future-v1 không được có non-null actual_demand!")

        # 3. Kiểm tra tổng số dòng bảng predictions
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM predictions;")
            total_predictions = cur.fetchone()[0]
        self.assertEqual(total_predictions, 4344, f"Tổng số dòng predictions phải là 4,344, thực tế: {total_predictions}")

    # ============================================================
    # TEST 4 — TOÀN VẸN CƠ SỞ DỮ LIỆU (DATABASE INTEGRITY)
    # ============================================================
    def test_04_database_integrity(self):
        """
        Kiểm tra tính toàn vẹn của các bảng trong PostgreSQL:
        trips, hourly_demand, predictions schema.
        """
        with self.conn.cursor() as cur:
            # 1. Bảng trips
            cur.execute("SELECT COUNT(*) FROM trips;")
            trips_count = cur.fetchone()[0]
            self.assertEqual(trips_count, 742615, f"Bảng trips bị biến động: {trips_count} != 742,615")

            # 2. Bảng hourly_demand
            cur.execute("SELECT COUNT(*) FROM hourly_demand;")
            hd_count = cur.fetchone()[0]
            self.assertEqual(hd_count, 6459, f"Bảng hourly_demand bị biến động: {hd_count} != 6,459")

            # 3. Schema bảng predictions
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'predictions'
                ORDER BY ordinal_position;
            """)
            columns = {r[0]: {"type": r[1], "nullable": r[2]} for r in cur.fetchall()}

        expected_columns = [
            "prediction_time",
            "target_time",
            "predicted_demand",
            "actual_demand",
            "model_name",
            "model_version",
        ]
        for col in expected_columns:
            self.assertIn(col, columns, f"Cột bắt buộc {col} không có trong schema predictions!")

        # actual_demand phải cho phép NULL
        self.assertEqual(columns["actual_demand"]["nullable"], "YES")

    # ============================================================
    # TEST 5 — DASHBOARD INTEGRATION & HTTP STATUS
    # ============================================================
    def test_05_dashboard_integration_and_http_status(self):
        """
        Xác nhận Dashboard service đọc đúng dữ liệu từ PostgreSQL:
        - load_future_forecast_data() trả về đúng 168 điểm, sắp xếp tăng dần.
        - Streamlit server đang chạy và phản hồi HTTP 200 OK.
        """
        df_dash = load_future_forecast_data()
        self.assertFalse(df_dash.empty, "load_future_forecast_data() trả về rỗng!")
        self.assertEqual(len(df_dash), 168, f"Dashboard loader phải trả về đúng 168 dòng, thực tế: {len(df_dash)}")

        # Sắp xếp tăng dần theo target_time
        target_series = pd.to_datetime(df_dash["target_time"])
        self.assertTrue(target_series.is_monotonic_increasing, "Dữ liệu Dashboard không được sắp xếp tăng dần!")
        self.assertEqual(target_series.min(), pd.Timestamp("2026-10-01 00:00:00"))
        self.assertEqual(target_series.max(), pd.Timestamp("2026-10-07 23:00:00"))

        # Kiểm tra HTTP status của Streamlit server
        try:
            resp = requests.get("http://localhost:8501", timeout=5)
            self.assertEqual(resp.status_code, 200, f"Dashboard trả về HTTP status code: {resp.status_code}")
        except requests.exceptions.RequestException as e:
            self.fail(f"Không thể kết nối đến Dashboard Streamlit tại http://localhost:8501: {e}")

    # ============================================================
    # TEST 6 — XỬ LÝ AN TOÀN KHI DỮ LIỆU RỖNG VÀ LỖI DATABASE
    # ============================================================
    def test_06_safe_handling_empty_forecast_and_db_edge_cases(self):
        """
        Kiểm tra Dashboard và component charts xử lý an toàn:
        1. Khi dữ liệu future forecast rỗng: không crash, hiển thị warning/info an toàn.
        2. load_predictions() với phiên bản không tồn tại trả về DataFrame rỗng đúng cấu trúc.
        3. show_future_forecast_chart() với DataFrame rỗng không ném ngoại lệ.
        """
        # 1. Test load_predictions() với version không tồn tại
        df_empty = load_predictions(model_name="Random Forest", model_version="non-existent-v99")
        self.assertTrue(df_empty.empty, "load_predictions với version lạ phải trả về DataFrame rỗng")
        expected_cols = [
            "prediction_time",
            "target_time",
            "predicted_demand",
            "actual_demand",
            "model_name",
            "model_version",
        ]
        for col in expected_cols:
            self.assertIn(col, df_empty.columns, f"DataFrame rỗng vẫn phải giữ cấu trúc cột {col}")

        # 2. Test show_future_forecast_chart() khi df rỗng
        try:
            show_future_forecast_chart(pd.DataFrame())
        except Exception as e:
            self.fail(f"show_future_forecast_chart ném ngoại lệ khi input rỗng: {e}")

        # 3. Test mock data loader trả về rỗng trong môi trường Dashboard
        load_future_forecast_data.clear()
        with patch("dashboard.services.data_loader.load_predictions", return_value=pd.DataFrame()):
            res = load_future_forecast_data()
            self.assertTrue(res.empty, "Mock empty load_future_forecast_data phải trả về rỗng an toàn")
        load_future_forecast_data.clear()


if __name__ == "__main__":
    unittest.main(verbosity=2)

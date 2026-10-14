import sys
import unittest
from pathlib import Path
import requests
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))

from database.postgres import get_connection, load_predictions
from dashboard.services.data_loader import (
    load_prediction_data,
    load_future_forecast_data,
    load_model_metrics,
    load_station_activity,
    format_date_range_label,
)
from dashboard.components.charts import show_station_symbol_map


class TestDashboardIntegration(unittest.TestCase):
    """
    Bộ kiểm thử tự động cho Task 8 — Tích hợp vào Dashboard (Phase 3).
    Xác minh tất cả các Acceptance Criteria theo TASK_PHASE3.md:
      1. Dashboard mở bình thường và phản hồi HTTP 200 OK.
      2. Station Map được tích hợp đúng vị trí với đầy đủ luồng dữ liệu.
      3. Các section hiện có (KPI, Demand, ML, Future Forecast) vẫn hoạt động nguyên vẹn.
      4. KPI và filter không bị sai lệch do sự xuất hiện của Station Map.
      5. Historical Prediction và Future Forecast (168h) vẫn hoạt động.
      6. Dữ liệu bản đồ rỗng không làm Dashboard crash.
    """

    def test_01_dashboard_http_status_ok(self):
        """Dashboard Streamlit mở bình thường và trả về HTTP status 200 OK."""
        try:
            resp = requests.get("http://localhost:8501", timeout=5)
            self.assertEqual(resp.status_code, 200, f"Dashboard trả về mã HTTP {resp.status_code}")
            self.assertIn("root", resp.text, "Trang không chứa phần tử root của ứng dụng Streamlit")
        except requests.exceptions.RequestException as e:
            self.fail(f"Không thể kết nối đến Dashboard tại http://localhost:8501: {e}")

    def test_02_station_map_integration_in_app(self):
        """Xác minh app.py đã tích hợp Station Composite Map và import các hàm cần thiết."""
        app_file = DASHBOARD_DIR / "app.py"
        self.assertTrue(app_file.exists(), "Tệp dashboard/app.py không tồn tại!")
        app_content = app_file.read_text(encoding="utf-8")

        # Kiểm tra các import bắt buộc
        self.assertIn("load_station_activity", app_content, "app.py thiếu import load_station_activity")
        self.assertIn("format_date_range_label", app_content, "app.py thiếu import format_date_range_label")
        self.assertIn("show_station_symbol_map", app_content, "app.py thiếu import show_station_symbol_map")

        # Kiểm tra tiêu đề Section Station Composite Map
        self.assertIn("Station Composite Map", app_content, "app.py thiếu section Station Composite Map")
        self.assertIn("show_station_symbol_map(", app_content, "app.py chưa gọi show_station_symbol_map")

    def test_03_station_map_data_loading_and_filter_sync(self):
        """Xác minh dữ liệu bản đồ tải đúng và đồng bộ với bộ lọc thời gian."""
        # 1. Toàn bộ dữ liệu
        df_all = load_station_activity(None, None)
        self.assertEqual(len(df_all), 452, "Bản đồ mặc định phải có đủ 452 trạm")
        self.assertEqual(df_all["activity_count"].sum(), 1481366)

        # 2. Dữ liệu lọc tháng 7/2026
        df_july = load_station_activity("2026-07-01", "2026-07-31")
        self.assertEqual(len(df_july), 232, "Tháng 7/2026 phải có đúng 232 trạm")
        self.assertEqual(df_july["activity_count"].sum(), 217840)

        # 3. Label thời gian
        label_all = format_date_range_label(None, None)
        self.assertEqual(label_all, "Toàn bộ dữ liệu")

    def test_04_existing_sections_and_forecast_integrity(self):
        """Xác minh Historical Prediction (4,176 rows) và Future Forecast (168h) vẫn bảo toàn."""
        # 1. Historical prediction
        hist_df = load_prediction_data()
        self.assertFalse(hist_df.empty, "Historical prediction data bị rỗng!")
        self.assertEqual(len(hist_df), 4176, f"Historical prediction phải là 4,176 dòng, thực tế: {len(hist_df)}")

        # 2. Future forecast
        future_df = load_future_forecast_data()
        self.assertFalse(future_df.empty, "Future forecast data bị rỗng!")
        self.assertEqual(len(future_df), 168, f"Future forecast phải là đúng 168 dòng, thực tế: {len(future_df)}")

        # 3. Model metrics
        metrics = load_model_metrics()
        self.assertFalse(metrics.empty, "Model metrics bị rỗng!")

    def test_05_graceful_handling_empty_map_data(self):
        """Dữ liệu bản đồ rỗng hoặc ngoài phạm vi không làm Dashboard crash hay ném ngoại lệ."""
        df_empty = load_station_activity("2027-01-01", "2027-01-31")
        self.assertTrue(df_empty.empty)

        # Gọi hàm vẽ bản đồ với dữ liệu rỗng không được ném ngoại lệ
        try:
            show_station_symbol_map(df_empty, show_heatmap=True, date_label="01/01/2027 — 31/01/2027")
        except Exception as e:
            self.fail(f"show_station_symbol_map ném lỗi khi dữ liệu rỗng: {e}")


if __name__ == "__main__":
    unittest.main()

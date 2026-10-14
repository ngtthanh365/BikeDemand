import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
import pydeck as pdk

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))

from dashboard.services.data_loader import load_station_activity
from dashboard.components.charts import (
    compute_station_marker_sizes,
    create_station_symbol_layer,
    create_station_heatmap_layer,
    build_station_map_deck,
    show_station_symbol_map,
    format_station_tooltip_data,
    get_station_tooltip_config,
)


class TestStationMap(unittest.TestCase):
    """
    Bộ kiểm thử cho Task 4 — Point / Proportional Symbol Map (Phase 3).
    Kiểm định:
    - Bán kính marker và thuật toán căn bậc hai (Area Proportional)
    - Giới hạn min_radius / max_radius và pixel limits
    - Phân cấp màu sắc RGBA và ý nghĩa theo activity_count
    - Thuộc tính lớp PyDeck ScatterplotLayer
    - Xử lý biên (dữ liệu rỗng, dữ liệu thiếu cột, tọa độ ngoài phạm vi)
    - Tái sử dụng dữ liệu cấp trạm đã tổng hợp (452 trạm, không tải bảng trips)
    """

    @classmethod
    def setUpClass(cls):
        # Tải dữ liệu tổng hợp cấp trạm qua data_loader (Task 2-3)
        cls.df = load_station_activity()

    def test_01_marker_size_bounds(self):
        """Xác minh bán kính marker nằm chính xác trong khoảng [min_radius, max_radius]."""
        min_r = 25.0
        max_r = 220.0
        res_df = compute_station_marker_sizes(self.df, min_radius=min_r, max_radius=max_r)

        self.assertIn("radius", res_df.columns)
        self.assertTrue((res_df["radius"] >= min_r).all(), "Tồn tại marker nhỏ hơn min_radius")
        self.assertTrue((res_df["radius"] <= max_r).all(), "Tồn tại marker lớn hơn max_radius")

        # Kiểm tra với tham số tùy biến khác
        custom_min = 10.0
        custom_max = 100.0
        custom_df = compute_station_marker_sizes(self.df, min_radius=custom_min, max_radius=custom_max)
        self.assertTrue((custom_df["radius"] >= custom_min).all())
        self.assertTrue((custom_df["radius"] <= custom_max).all())

    def test_02_marker_size_monotonicity_and_sqrt_scaling(self):
        """Xác minh kích thước marker phản ánh đơn điệu tăng theo activity_count và scale theo căn bậc hai."""
        res_df = compute_station_marker_sizes(self.df)

        # Trạm có activity_count cao nhất phải có bán kính lớn nhất
        max_idx = res_df["activity_count"].idxmax()
        self.assertAlmostEqual(res_df.loc[max_idx, "radius"], 220.0, places=2)

        # Trạm có activity_count thấp nhất phải có bán kính nhỏ nhất
        min_idx = res_df["activity_count"].idxmin()
        self.assertAlmostEqual(res_df.loc[min_idx, "radius"], 25.0, places=2)

        # Kiểm tra tính đơn điệu: sắp xếp theo activity_count thì radius cũng phải không giảm
        sorted_df = res_df.sort_values("activity_count").reset_index(drop=True)
        is_monotonic = (sorted_df["radius"].diff().dropna() >= 0).all()
        self.assertTrue(is_monotonic, "Bán kính không tăng đơn điệu theo activity_count")

        # So sánh 2 trạm cụ thể: Grove St PATH (68,266) vs trạm ít hoạt động hơn
        grove_st = res_df[res_df["station_id"] == "JC115"].iloc[0]
        other_st = res_df[res_df["activity_count"] < 1000].iloc[0]
        self.assertGreater(grove_st["radius"], other_st["radius"])

    def test_03_color_tiers_and_valid_rgba(self):
        """Xác minh phân cấp màu sắc RGBA theo 4 ngưỡng hoạt động và giá trị kênh màu hợp lệ."""
        res_df = compute_station_marker_sizes(self.df)
        self.assertIn("fill_color", res_df.columns)

        for _, row in res_df.iterrows():
            color = row["fill_color"]
            act = row["activity_count"]
            self.assertEqual(len(color), 4, "Màu sắc phải có 4 kênh RGBA")
            # Kênh màu phải là int từ 0 đến 255
            for c in color:
                self.assertIsInstance(c, (int, np.integer))
                self.assertTrue(0 <= c <= 255)

            # Kiểm tra logic phân tầng màu
            if act >= 20000:
                self.assertEqual(color, [255, 65, 54, 220], "Tier >= 20,000 phải là Đỏ cam")
            elif act >= 10000:
                self.assertEqual(color, [255, 140, 0, 200], "Tier 10,000-19,999 phải là Cam")
            elif act >= 1000:
                self.assertEqual(color, [0, 160, 255, 180], "Tier 1,000-9,999 phải là Xanh dương")
            else:
                self.assertEqual(color, [0, 210, 210, 160], "Tier < 1,000 phải là Cyan")

    def test_04_scatterplot_layer_properties(self):
        """Xác minh thuộc tính ScatterplotLayer tuân thủ đúng đặc tả Task 4."""
        layer, plot_df = create_station_symbol_layer(self.df)

        self.assertIsInstance(layer, pdk.Layer)
        self.assertEqual(layer.type, "ScatterplotLayer")
        self.assertTrue("longitude" in str(layer.get_position) and "latitude" in str(layer.get_position))
        self.assertIn("radius", str(layer.get_radius))
        self.assertIn("fill_color", str(layer.get_fill_color))
        self.assertTrue(layer.pickable)
        self.assertTrue(layer.auto_highlight)
        self.assertEqual(layer.radius_min_pixels, 3)
        self.assertEqual(layer.radius_max_pixels, 18)
        self.assertEqual(layer.get_line_color, [255, 255, 255, 220])

        # plot_df phải chứa đầy đủ display_label và các cột cần thiết
        self.assertIn("display_label", plot_df.columns)
        self.assertIn("radius", plot_df.columns)
        self.assertIn("fill_color", plot_df.columns)

    def test_05_empty_and_edge_case_inputs(self):
        """Kiểm tra xử lý biên: dữ liệu rỗng, 1 dòng duy nhất, giá trị trùng nhau, số âm."""
        # DataFrame rỗng
        empty_df = pd.DataFrame(columns=["station_id", "station_name", "latitude", "longitude", "activity_count"])
        res_empty = compute_station_marker_sizes(empty_df)
        self.assertTrue(res_empty.empty)

        # 1 dòng duy nhất (min == max) không gây ZeroDivisionError
        single_df = pd.DataFrame([{
            "station_id": "ST1",
            "station_name": "Test Station",
            "latitude": 40.7,
            "longitude": -74.0,
            "activity_count": 500,
        }])
        res_single = compute_station_marker_sizes(single_df, min_radius=30.0, max_radius=150.0)
        self.assertEqual(len(res_single), 1)
        self.assertEqual(res_single.iloc[0]["radius"], 30.0)

        # Nhiều dòng nhưng tất cả activity_count bằng nhau
        tied_df = pd.DataFrame([
            {"station_id": "ST1", "activity_count": 100},
            {"station_id": "ST2", "activity_count": 100},
        ])
        res_tied = compute_station_marker_sizes(tied_df)
        self.assertEqual(res_tied.iloc[0]["radius"], res_tied.iloc[1]["radius"])

        # Số âm clip về 0 an toàn không lỗi căn bậc hai
        neg_df = pd.DataFrame([
            {"station_id": "ST1", "activity_count": -50},
            {"station_id": "ST2", "activity_count": 100},
        ])
        res_neg = compute_station_marker_sizes(neg_df)
        self.assertTrue(np.isfinite(res_neg["radius"]).all())

    def test_06_map_rendering_robustness(self):
        """Xác minh show_station_symbol_map chạy an toàn, không crash khi gặp dữ liệu bất thường."""
        # 1. DataFrame rỗng
        try:
            show_station_symbol_map(pd.DataFrame())
        except Exception as e:
            self.fail(f"show_station_symbol_map crash trên DataFrame rỗng: {e}")

        # 2. DataFrame thiếu cột tọa độ
        bad_cols_df = pd.DataFrame([{"station_id": "ST1", "activity_count": 100}])
        try:
            show_station_symbol_map(bad_cols_df)
        except Exception as e:
            self.fail(f"show_station_symbol_map crash khi thiếu cột tọa độ: {e}")

        # 3. Tọa độ nằm ngoài phạm vi thực tế (sẽ bị lọc sạch)
        out_of_bounds_df = pd.DataFrame([
            {"station_id": "BAD", "latitude": 0.0, "longitude": 0.0, "activity_count": 100}
        ])
        try:
            show_station_symbol_map(out_of_bounds_df)
        except Exception as e:
            self.fail(f"show_station_symbol_map crash khi tọa độ ngoài phạm vi: {e}")

        # 4. Chạy với dữ liệu trạm thực tế (452 trạm)
        try:
            show_station_symbol_map(self.df)
        except Exception as e:
            self.fail(f"show_station_symbol_map crash trên dữ liệu trạm thật: {e}")

    def test_07_aggregated_data_efficiency_and_display_identity(self):
        """Xác minh bản đồ sử dụng đúng dữ liệu tổng hợp cấp trạm (452 dòng) và display_label."""
        # Chỉ có 452 dòng tổng hợp, không tải bảng trips (742k dòng)
        self.assertEqual(len(self.df), 452)
        self.assertLess(len(self.df), 1000)

        # Định danh trạm qua display_label
        self.assertIn("display_label", self.df.columns)
        self.assertTrue(self.df["display_label"].str.contains(r"\(.+\)$").all())

        # Tọa độ 100% hợp lệ, không có dữ liệu giả
        self.assertTrue((self.df["latitude"] >= 40.0).all() and (self.df["latitude"] <= 41.5).all())
        self.assertTrue((self.df["longitude"] >= -74.5).all() and (self.df["longitude"] <= -73.0).all())

    def test_08_heatmap_layer_properties_and_weights(self):
        """Xác minh thuộc tính HeatmapLayer: vị trí, trọng số activity_count, độ mờ nền."""
        layer = create_station_heatmap_layer(self.df)

        self.assertIsInstance(layer, pdk.Layer)
        self.assertEqual(layer.type, "HeatmapLayer")
        self.assertTrue("longitude" in str(layer.get_position) and "latitude" in str(layer.get_position))
        self.assertIn("activity_count", str(layer.get_weight))
        self.assertAlmostEqual(layer.opacity, 0.50, places=2)
        self.assertEqual(layer.radius_pixels, 45)
        self.assertAlmostEqual(layer.threshold, 0.05, places=2)
        self.assertAlmostEqual(layer.intensity, 1.2, places=2)
        self.assertEqual(len(layer.color_range), 6)

    def test_09_heatmap_layer_empty_and_fallback_handling(self):
        """Kiểm tra xử lý biên HeatmapLayer: dữ liệu rỗng và thiếu cột trọng số."""
        # DataFrame rỗng
        empty_layer = create_station_heatmap_layer(pd.DataFrame())
        self.assertIsInstance(empty_layer, pdk.Layer)
        self.assertEqual(empty_layer.type, "HeatmapLayer")

        # DataFrame thiếu cột activity_count
        no_weight_df = pd.DataFrame([{"latitude": 40.7, "longitude": -74.0}])
        no_weight_layer = create_station_heatmap_layer(no_weight_df)
        self.assertIsInstance(no_weight_layer, pdk.Layer)
        self.assertIsNone(no_weight_layer.get_weight)

    def test_10_layer_stacking_order_composite_deck(self):
        """Xác minh thứ tự xếp lớp: HeatmapLayer nằm dưới, ScatterplotLayer nằm trên."""
        deck, plot_df = build_station_map_deck(self.df, show_heatmap=True)

        self.assertIsInstance(deck, pdk.Deck)
        self.assertEqual(len(deck.layers), 2, "Bản đồ composite phải có đúng 2 lớp")
        # Lớp 0: HeatmapLayer (lớp nền dưới cùng)
        self.assertEqual(deck.layers[0].type, "HeatmapLayer", "Lớp dưới cùng phải là HeatmapLayer")
        # Lớp 1: ScatterplotLayer (marker trên cùng)
        self.assertEqual(deck.layers[1].type, "ScatterplotLayer", "Lớp trên cùng phải là ScatterplotLayer")

        # Khi tắt Heatmap: chỉ còn ScatterplotLayer
        deck_no_hm, _ = build_station_map_deck(self.df, show_heatmap=False)
        self.assertEqual(len(deck_no_hm.layers), 1)
        self.assertEqual(deck_no_hm.layers[0].type, "ScatterplotLayer")

    def test_11_heatmap_rendering_robustness(self):
        """Xác minh show_station_symbol_map chạy trơn tru với cả show_heatmap=True và False."""
        try:
            show_station_symbol_map(self.df, show_heatmap=True)
            show_station_symbol_map(self.df, show_heatmap=False)
            show_station_symbol_map(pd.DataFrame(), show_heatmap=True)
        except Exception as e:
            self.fail(f"show_station_symbol_map gặp lỗi khi render với heatmap: {e}")

    def test_12_tooltip_configuration_all_fields(self):
        """Xác minh cấu hình tooltip hiển thị đầy đủ 7 trường thông tin theo đặc tả Task 6."""
        tooltip_cfg = get_station_tooltip_config()

        self.assertIsInstance(tooltip_cfg, dict)
        self.assertIn("html", tooltip_cfg)
        self.assertIn("style", tooltip_cfg)

        html_template = tooltip_cfg["html"]
        # Phải chứa đủ 7 trường: station_name, station_id, latitude, longitude, start_count, end_count, activity_count
        required_fields = [
            "station_name",
            "station_id",
            "latitude",
            "longitude",
            "start_count",
            "end_count",
            "activity_count",
        ]
        for field in required_fields:
            self.assertIn(
                f"{{{field}}}",
                html_template,
                f"Thiếu placeholder {{{field}}} trong template tooltip"
            )

        # Deck tạo bởi build_station_map_deck phải được gán tooltip này
        deck, _ = build_station_map_deck(self.df)
        self.assertEqual(deck._tooltip, tooltip_cfg)

    def test_13_tooltip_data_formatting_and_missing_handling(self):
        """Xác minh xử lý định dạng tooltip: dữ liệu thật, dữ liệu thiếu, phân biệt số 0 thực tế."""
        # 1. Trạm thực tế hợp lệ
        formatted_df = format_station_tooltip_data(self.df)
        grove_st = formatted_df[formatted_df["station_id"] == "JC115"].iloc[0]
        self.assertEqual(grove_st["station_name"], "Grove St PATH")
        self.assertEqual(grove_st["station_id"], "JC115")
        self.assertIn(",", grove_st["activity_count"])  # Định dạng phân cách hàng nghìn: 68,266

        # 2. Xử lý giá trị thiếu và phân biệt rõ số 0 thực tế
        test_edge_df = pd.DataFrame([
            {
                "station_id": "ST_ZERO",
                "station_name": "Zero Activity Station",
                "latitude": 40.71,
                "longitude": -74.02,
                "start_count": 0,
                "end_count": 0,
                "activity_count": 0,
            },
            {
                "station_id": "ST_MISSING",
                "station_name": None,
                "latitude": np.nan,
                "longitude": np.nan,
                "start_count": np.nan,
                "end_count": None,
                "activity_count": np.nan,
            },
        ])
        res_edge = format_station_tooltip_data(test_edge_df)

        # Trạm ST_ZERO: số 0 thực tế phải được giữ là '0', KHÔNG bị biến thành 'N/A'
        zero_row = res_edge[res_edge["station_id"] == "ST_ZERO"].iloc[0]
        self.assertEqual(zero_row["start_count"], "0")
        self.assertEqual(zero_row["end_count"], "0")
        self.assertEqual(zero_row["activity_count"], "0")

        # Trạm ST_MISSING: missing/NaN phải thành 'N/A', tên trạm fallback thành 'Station ST_MISSING'
        missing_row = res_edge[res_edge["station_id"] == "ST_MISSING"].iloc[0]
        self.assertEqual(missing_row["start_count"], "N/A")
        self.assertEqual(missing_row["end_count"], "N/A")
        self.assertEqual(missing_row["activity_count"], "N/A")
        self.assertEqual(missing_row["latitude"], "N/A")
        self.assertEqual(missing_row["longitude"], "N/A")
        self.assertEqual(missing_row["station_name"], "Station ST_MISSING")

    def test_14_no_unwanted_format_errors_or_inventory_claims(self):
        """Xác minh không có chuỗi rác NaN/None/null và không đưa tuyên bố sai về tồn kho xe."""
        formatted_df = format_station_tooltip_data(self.df)
        junk_strings = ["none", "nan", "null", "undefined", "inf"]

        for col in ["station_name", "station_id", "start_count", "end_count", "activity_count"]:
            val_strs = formatted_df[col].astype(str).str.lower()
            for junk in junk_strings:
                self.assertFalse(
                    (val_strs == junk).any(),
                    f"Cột {col} chứa chuỗi lỗi định dạng '{junk}'"
                )

        # Tooltip template không chứa tuyên bố sai về xe còn/hết
        tooltip_html = get_station_tooltip_config()["html"].lower()
        forbidden_phrases = ["còn xe", "hết xe", "tồn kho", "xe khả dụng", "thiếu xe"]
        for phrase in forbidden_phrases:
            self.assertNotIn(
                phrase,
                tooltip_html,
                f"Tooltip không được phép kết luận về tồn kho xe: '{phrase}'"
            )

    def test_15_empty_dataframe_tooltip_handling(self):
        """Kiểm tra format_station_tooltip_data với DataFrame rỗng không gây ngoại lệ."""
        empty_res = format_station_tooltip_data(pd.DataFrame())
        self.assertTrue(empty_res.empty)

    def test_16_basemap_style_and_view_state(self):
        """Xác minh cấu hình bản đồ nền địa lý thực (CARTO vector tiles) và ViewState."""
        # 1. Mặc định là CARTO Positron Light (không yêu cầu Mapbox token)
        deck_default, _ = build_station_map_deck(self.df)
        self.assertEqual(deck_default.map_style, pdk.map_styles.CARTO_LIGHT)
        self.assertTrue(
            str(deck_default.map_style).startswith("https://")
            or deck_default.map_style == pdk.map_styles.CARTO_LIGHT
        )

        # 2. ViewState zoom=11.0 và tâm nằm đúng cụm 452 trạm NYC/NJ
        vs = deck_default.initial_view_state
        self.assertEqual(vs.zoom, 11.0)
        self.assertTrue(40.65 <= vs.latitude <= 40.86, f"Vĩ độ tâm không hợp lệ: {vs.latitude}")
        self.assertTrue(-74.15 <= vs.longitude <= -73.80, f"Kinh độ tâm không hợp lệ: {vs.longitude}")

        # 3. Tùy biến map_style: CARTO Voyager & CARTO Dark
        deck_voyager, _ = build_station_map_deck(self.df, map_style=pdk.map_styles.CARTO_ROAD)
        self.assertEqual(deck_voyager.map_style, pdk.map_styles.CARTO_ROAD)

        deck_dark, _ = build_station_map_deck(self.df, map_style=pdk.map_styles.CARTO_DARK)
        self.assertEqual(deck_dark.map_style, pdk.map_styles.CARTO_DARK)

    def test_17_tooltip_bounds_and_heatmap_enhanced_config(self):
        """Xác minh cấu hình tooltip giới hạn kích thước, chống tràn mép và dải màu Heatmap nâng cao."""
        # 1. Tooltip style có đủ maxWidth, maxHeight, overflowY, pointerEvents: none
        tooltip_cfg = get_station_tooltip_config()
        style = tooltip_cfg["style"]
        self.assertEqual(style["pointerEvents"], "none")
        self.assertEqual(style["maxWidth"], "290px")
        self.assertEqual(style["maxHeight"], "240px")
        self.assertEqual(style["overflowY"], "auto")

        # 2. Dải màu chuyển tiếp từ vàng nhạt đến đỏ đậm
        layer = create_station_heatmap_layer(self.df)
        colors = layer.color_range
        self.assertEqual(len(colors), 6)
        # Điểm đầu vàng nhạt (red cao, green cao, blue tương đối cao)
        self.assertEqual(colors[0], [255, 255, 178])
        # Điểm cuối đỏ đậm
        self.assertEqual(colors[-1], [128, 0, 38])

        # 3. Tùy biến tham số heatmap trong build_station_map_deck
        custom_deck, _ = build_station_map_deck(
            self.df,
            show_heatmap=True,
            heatmap_radius_pixels=50,
            heatmap_opacity=0.6,
            heatmap_threshold=0.03,
            heatmap_intensity=1.5,
        )
        hm_layer = custom_deck.layers[0]
        self.assertEqual(hm_layer.radius_pixels, 50)
        self.assertAlmostEqual(hm_layer.opacity, 0.6, places=2)
        self.assertAlmostEqual(hm_layer.threshold, 0.03, places=2)
        self.assertAlmostEqual(hm_layer.intensity, 1.5, places=2)


if __name__ == "__main__":
    unittest.main()

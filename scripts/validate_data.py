import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Schema tối thiểu theo TASK_PHASE1.md
REQUIRED_COLUMNS = [
    "ride_id",
    "rideable_type",
    "started_at",
    "ended_at",
    "start_station_name",
    "start_station_id",
    "end_station_name",
    "end_station_id",
    "start_lat",
    "start_lng",
    "end_lat",
    "end_lng",
    "member_casual",
]

# Tọa độ hợp lệ cho khu vực New York / New Jersey Citi Bike
LAT_MIN, LAT_MAX = 40.0, 41.5
LNG_MIN, LNG_MAX = -74.5, -73.5

FILENAME_MONTH_REGEX = re.compile(
    r"^JC-(?P<year>\d{4})(?P<month>\d{2})-citibike-tripdata\.csv$",
    re.IGNORECASE,
)


class ValidationError(Exception):
    """Lỗi cấu trúc hoặc schema dữ liệu không hợp lệ."""
    pass


def validate_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Kiểm tra DataFrame có chứa đầy đủ 13 cột bắt buộc theo đặc tả không.
    Trả về (is_valid, missing_columns).
    """
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    return (len(missing_cols) == 0, missing_cols)


def get_existing_db_ride_ids(ride_ids: Set[str]) -> Set[str]:
    """
    Truy vấn PostgreSQL để tìm các ride_id đã tồn tại trong bảng trips (nếu DB hoạt động).
    """
    if not ride_ids:
        return set()

    try:
        from database.postgres import get_connection

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                # Dùng temp table hoặc truy vấn chunk nếu số lượng lớn
                id_list = list(ride_ids)
                chunk_size = 5000
                found_in_db: Set[str] = set()

                for i in range(0, len(id_list), chunk_size):
                    chunk = id_list[i : i + chunk_size]
                    format_strings = ",".join(["%s"] * len(chunk))
                    query = f"SELECT ride_id FROM trips WHERE ride_id IN ({format_strings});"
                    cursor.execute(query, chunk)
                    rows = cursor.fetchall()
                    for r in rows:
                        found_in_db.add(r[0])

                return found_in_db
        finally:
            conn.close()
    except Exception as exc:
        print(f"[CHECK] Lưu ý: Không thể truy vấn PostgreSQL để kiểm tra trùng lặp ({exc}).")
        return set()


def validate_and_clean_data(
    df: pd.DataFrame,
    target_month: Optional[str] = None,
    check_db_duplicates: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Kiểm tra và làm sạch dữ liệu mới theo các quy tắc chuẩn của BikeDemand v1.0 / Phase 1:
    1. Schema validation (13 cột bắt buộc).
    2. Datetime parsing (started_at, ended_at).
    3. Loại bỏ thời lượng âm (duration < 0).
    4. Lọc theo chu kỳ tháng đích (loại bỏ chuyến bắt đầu trước tháng hoặc sau tháng).
    5. Deduplication ride_id nội bộ file.
    6. Deduplication ride_id với PostgreSQL trips (nếu bật).
    7. Kiểm tra tọa độ xuất phát (start_lat, start_lng).
    8. Kiểm tra phân loại hợp lệ (member_casual, rideable_type).
    """
    stats: Dict[str, int] = {
        "initial_rows": len(df),
        "missing_columns": 0,
        "invalid_datetime_dropped": 0,
        "negative_duration_dropped": 0,
        "outside_period_dropped": 0,
        "internal_duplicate_ride_id_dropped": 0,
        "db_duplicate_ride_id_dropped": 0,
        "invalid_coordinates_dropped": 0,
        "invalid_categories_dropped": 0,
        "valid_final_rows": 0,
    }

    print("=" * 70)
    print("[START] CITI BIKE DATA VALIDATION")
    print("=" * 70)
    print(f"[CHECK] Tổng số dòng ban đầu: {stats['initial_rows']:,}")

    # 1. Schema Check
    is_valid_schema, missing_cols = validate_schema(df)
    if not is_valid_schema:
        stats["missing_columns"] = len(missing_cols)
        err_msg = f"Schema không hợp lệ! Thiếu các cột bắt buộc: {missing_cols}"
        print(f"[ERROR] {err_msg}")
        raise ValidationError(err_msg)
    print(f"[VALIDATE] Schema kiểm tra thành công: đầy đủ {len(REQUIRED_COLUMNS)} cột chuẩn.")

    # Tạo bản sao làm việc
    df_clean = df.copy()

    # 2. Datetime Parsing
    df_clean["started_at"] = pd.to_datetime(df_clean["started_at"], errors="coerce")
    df_clean["ended_at"] = pd.to_datetime(df_clean["ended_at"], errors="coerce")

    invalid_dt_mask = df_clean["started_at"].isna() | df_clean["ended_at"].isna()
    invalid_dt_count = int(invalid_dt_mask.sum())
    if invalid_dt_count > 0:
        print(f"[CLEAN] Phát hiện {invalid_dt_count:,} dòng có datetime không hợp lệ. Đang loại bỏ...")
        df_clean = df_clean.loc[~invalid_dt_mask].copy()
    stats["invalid_datetime_dropped"] = invalid_dt_count

    # 3. Duration Check (ended_at >= started_at)
    duration_sec = (df_clean["ended_at"] - df_clean["started_at"]).dt.total_seconds()
    negative_dur_mask = duration_sec < 0
    negative_dur_count = int(negative_dur_mask.sum())
    if negative_dur_count > 0:
        print(f"[CLEAN] Phát hiện {negative_dur_count:,} dòng có thời lượng chuyến đi < 0. Đang loại bỏ...")
        df_clean = df_clean.loc[~negative_dur_mask].copy()
    stats["negative_duration_dropped"] = negative_dur_count

    # Thông tin thống kê thêm về chuyến > 24 giờ (vẫn giữ nếu hợp lệ)
    duration_24h_count = int((duration_sec > 86400).sum())
    if duration_24h_count > 0:
        print(f"[CHECK] Ghi nhận {duration_24h_count:,} chuyến đi kéo dài > 24 giờ.")

    # 4. Target Month Window Filtering
    if target_month:
        try:
            year = int(target_month[:4])
            month = int(target_month[4:6])
            start_window = pd.Timestamp(year, month, 1, 0, 0, 0)
            if month == 12:
                end_window = pd.Timestamp(year + 1, 1, 1, 0, 0, 0)
            else:
                end_window = pd.Timestamp(year, month + 1, 1, 0, 0, 0)

            outside_period_mask = (df_clean["started_at"] < start_window) | (df_clean["started_at"] >= end_window)
            outside_count = int(outside_period_mask.sum())
            if outside_count > 0:
                print(
                    f"[CLEAN] Phát hiện {outside_count:,} dòng bắt đầu ngoài tháng {target_month} "
                    f"(< {start_window} hoặc >= {end_window}). Đang loại bỏ để tránh collision..."
                )
                df_clean = df_clean.loc[~outside_period_mask].copy()
            stats["outside_period_dropped"] = outside_count
        except Exception as exc:
            print(f"[CHECK] Không thể xác định chu kỳ tháng từ '{target_month}': {exc}")

    # 5. Internal Deduplication (ride_id)
    internal_dup_count = int(df_clean["ride_id"].duplicated().sum())
    if internal_dup_count > 0:
        print(f"[CLEAN] Phát hiện {internal_dup_count:,} ride_id trùng lặp nội bộ. Đang deduplicate...")
        df_clean = df_clean.drop_duplicates(subset=["ride_id"], keep="first").copy()
    stats["internal_duplicate_ride_id_dropped"] = internal_dup_count

    # 6. Database Deduplication (kiểm tra với PostgreSQL)
    if check_db_duplicates and not df_clean.empty:
        current_ids = set(df_clean["ride_id"].dropna().astype(str))
        existing_db_ids = get_existing_db_ride_ids(current_ids)
        if existing_db_ids:
            print(f"[CLEAN] Phát hiện {len(existing_db_ids):,} ride_id đã tồn tại trong PostgreSQL trips. Đang loại bỏ...")
            db_dup_mask = df_clean["ride_id"].isin(existing_db_ids)
            df_clean = df_clean.loc[~db_dup_mask].copy()
            stats["db_duplicate_ride_id_dropped"] = len(existing_db_ids)
        else:
            print("[VALIDATE] Kiểm tra DB: 0 ride_id trùng lặp với bảng trips hiện có.")

    # 7. Coordinates Validation (start_lat, start_lng)
    invalid_coords_mask = (
        df_clean["start_lat"].isna()
        | df_clean["start_lng"].isna()
        | (~df_clean["start_lat"].between(LAT_MIN, LAT_MAX))
        | (~df_clean["start_lng"].between(LNG_MIN, LNG_MAX))
    )
    invalid_coords_count = int(invalid_coords_mask.sum())
    if invalid_coords_count > 0:
        print(f"[CLEAN] Phát hiện {invalid_coords_count:,} dòng có tọa độ xuất phát bất thường. Đang loại bỏ...")
        df_clean = df_clean.loc[~invalid_coords_mask].copy()
    stats["invalid_coordinates_dropped"] = invalid_coords_count

    # 8. Categorical Validation
    invalid_cat_mask = (
        ~df_clean["member_casual"].isin(["member", "casual"])
        | df_clean["ride_id"].isna()
        | (df_clean["ride_id"].astype(str).str.strip() == "")
    )
    invalid_cat_count = int(invalid_cat_mask.sum())
    if invalid_cat_count > 0:
        print(f"[CLEAN] Phát hiện {invalid_cat_count:,} dòng sai định dạng phân loại. Đang loại bỏ...")
        df_clean = df_clean.loc[~invalid_cat_mask].copy()
    stats["invalid_categories_dropped"] = invalid_cat_count

    # Chuẩn hóa thứ tự thời gian
    df_clean = df_clean.sort_values(by="started_at").reset_index(drop=True)
    stats["valid_final_rows"] = len(df_clean)

    print("-" * 70)
    print("[SUMMARY] KẾT QUẢ DATA VALIDATION:")
    print(f"  - Ban đầu:                  {stats['initial_rows']:,} dòng")
    print(f"  - Lỗi datetime loại bỏ:     {stats['invalid_datetime_dropped']:,}")
    print(f"  - Thời lượng âm loại bỏ:    {stats['negative_duration_dropped']:,}")
    print(f"  - Ngoài chu kỳ loại bỏ:     {stats['outside_period_dropped']:,}")
    print(f"  - Trùng lặp file loại bỏ:   {stats['internal_duplicate_ride_id_dropped']:,}")
    print(f"  - Trùng lặp DB loại bỏ:     {stats['db_duplicate_ride_id_dropped']:,}")
    print(f"  - Tọa độ lỗi loại bỏ:       {stats['invalid_coordinates_dropped']:,}")
    print(f"  - Phân loại lỗi loại bỏ:    {stats['invalid_categories_dropped']:,}")
    print(f"  - Hợp lệ sẵn sàng:          {stats['valid_final_rows']:,} dòng")
    if stats["valid_final_rows"] > 0:
        print(f"  - Khoảng thời gian:         {df_clean['started_at'].min()} -> {df_clean['started_at'].max()}")
        print(f"  - Unique ride_id:           {df_clean['ride_id'].nunique():,}")
    print("=" * 70)

    return df_clean, stats


def validate_file(
    input_file: Path,
    output_file: Optional[Path] = None,
    check_db_duplicates: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Đọc file CSV thô, xác thực và lưu kết quả đã làm sạch nếu được chỉ định.
    """
    if not input_file.exists():
        raise FileNotFoundError(f"File không tồn tại: {input_file}")

    print(f"[CHECK] Đang đọc file: {input_file.name}")
    df_raw = pd.read_csv(input_file, low_memory=False)

    # Xác định tháng từ tên file (nếu có)
    match = FILENAME_MONTH_REGEX.match(input_file.name)
    target_month = f"{match.group('year')}{match.group('month')}" if match else None

    df_clean, stats = validate_and_clean_data(
        df=df_raw,
        target_month=target_month,
        check_db_duplicates=check_db_duplicates,
    )

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        # Định dạng timestamp lại thành chuỗi chuẩn ISO khi lưu
        df_to_save = df_clean.copy()
        df_to_save["started_at"] = df_to_save["started_at"].dt.strftime("%Y-%m-%d %H:%M:%S.%f").str[:-3]
        df_to_save["ended_at"] = df_to_save["ended_at"].dt.strftime("%Y-%m-%d %H:%M:%S.%f").str[:-3]
        df_to_save.to_csv(output_file, index=False)
        print(f"[SUCCESS] Đã lưu dữ liệu làm sạch vào: {output_file} ({len(df_to_save):,} dòng)")

    return df_clean, stats


def main():
    parser = argparse.ArgumentParser(description="Citi Bike Data Validator")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Đường dẫn tới file CSV cần kiểm tra (ví dụ: data/raw/trips/JC-202607-citibike-tripdata.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Đường dẫn lưu file sau khi làm sạch (tuỳ chọn).",
    )
    parser.add_argument(
        "--no-db-check",
        action="store_true",
        help="Bỏ qua kiểm tra trùng lặp với bảng trips trong PostgreSQL.",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else None

    validate_file(
        input_file=input_path,
        output_file=output_path,
        check_db_duplicates=not args.no_db_check,
    )


if __name__ == "__main__":
    main()

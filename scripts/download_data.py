import argparse
import io
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Set

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw" / "trips"
S3_BUCKET_URL = "https://s3.amazonaws.com/tripdata"
S3_XML_NAMESPACE = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}

REMOTE_KEY_REGEX = re.compile(
    r"^JC-(?P<year>\d{4})(?P<month>\d{2})-citibike-tripdata(?:\.csv)?\.zip$",
    re.IGNORECASE,
)
LOCAL_CSV_REGEX = re.compile(
    r"^JC-(?P<year>\d{4})(?P<month>\d{2})-citibike-tripdata\.csv$",
    re.IGNORECASE,
)


def fetch_available_remote_months(
    bucket_url: str = S3_BUCKET_URL,
    timeout: int = 20,
) -> Dict[str, str]:
    """
    Quét danh sách file từ S3 bucket XML và trích xuất các tháng JC khả dụng.
    Trả về dict: { 'YYYYMM': 'Key-name-on-S3', ... }
    """
    response = requests.get(bucket_url, timeout=timeout)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    remote_months: Dict[str, str] = {}

    for elem in root.findall(".//s3:Key", S3_XML_NAMESPACE):
        key = (elem.text or "").strip()
        match = REMOTE_KEY_REGEX.match(key)
        if match:
            month_id = f"{match.group('year')}{match.group('month')}"
            remote_months[month_id] = key

    return remote_months


def get_local_months(raw_dir: Path = DEFAULT_RAW_DIR) -> Set[str]:
    """
    Quét thư mục raw_dir và trích xuất các tháng JC đã có file CSV.
    """
    if not raw_dir.exists():
        return set()

    local_months: Set[str] = set()
    for file in raw_dir.iterdir():
        if file.is_file():
            match = LOCAL_CSV_REGEX.match(file.name)
            if match:
                month_id = f"{match.group('year')}{match.group('month')}"
                local_months.add(month_id)

    return local_months


def find_new_months(
    raw_dir: Path = DEFAULT_RAW_DIR,
    bucket_url: str = S3_BUCKET_URL,
) -> Dict[str, str]:
    """
    So sánh nguồn remote và dữ liệu local để tìm các tháng mới (lớn hơn tháng mới nhất hiện có).
    Trả về dict sorted theo tháng: { 'YYYYMM': 'Key-name', ... }
    """
    remote_map = fetch_available_remote_months(bucket_url=bucket_url)
    local_set = get_local_months(raw_dir=raw_dir)

    if local_set:
        max_local = max(local_set)
        new_months = {
            m: key
            for m, key in remote_map.items()
            if m > max_local
        }
    else:
        new_months = remote_map

    # Sắp xếp tăng dần theo thời gian
    sorted_new_months = dict(sorted(new_months.items(), key=lambda item: item[0]))
    return sorted_new_months


def download_and_extract_month(
    month_id: str,
    s3_key: str,
    target_dir: Path = DEFAULT_RAW_DIR,
    bucket_url: str = S3_BUCKET_URL,
    chunk_size: int = 1024 * 1024,
    timeout: int = 60,
) -> Path:
    """
    Tải file zip từ S3, kiểm tra tính toàn vẹn và giải nén file CSV vào target_dir.
    Sử dụng file tạm để đảm bảo an toàn nếu quá trình tải bị gián đoạn.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    expected_csv_name = f"JC-{month_id}-citibike-tripdata.csv"
    final_csv_path = target_dir / expected_csv_name

    if final_csv_path.exists():
        print(f"[CHECK] File {expected_csv_name} đã tồn tại. Bỏ qua tải lại.")
        return final_csv_path

    download_url = f"{bucket_url}/{s3_key}"
    temp_zip_path = target_dir / f"temp_{month_id}_{os.getpid()}.zip.tmp"

    print(f"[DOWNLOAD] Đang tải {s3_key} từ {download_url}...")
    try:
        with requests.get(download_url, stream=True, timeout=timeout) as resp:
            resp.raise_for_status()
            total_bytes = int(resp.headers.get("Content-Length", 0))
            downloaded_bytes = 0

            with open(temp_zip_path, "wb") as f_out:
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f_out.write(chunk)
                        downloaded_bytes += len(chunk)

        if total_bytes > 0 and downloaded_bytes != total_bytes:
            raise IOError(
                f"Tải file chưa hoàn tất: nhận {downloaded_bytes}/{total_bytes} bytes"
            )

        print(f"[DOWNLOAD] Tải thành công {downloaded_bytes:,} bytes. Đang kiểm tra file zip...")

        with zipfile.ZipFile(temp_zip_path, "r") as zip_ref:
            test_result = zip_ref.testzip()
            if test_result is not None:
                raise zipfile.BadZipFile(f"File zip bị hỏng tại entry: {test_result}")

            # Tìm file CSV hợp lệ trong zip (bỏ qua __MACOSX và file ẩn)
            csv_candidates = [
                name for name in zip_ref.namelist()
                if name.lower().endswith(".csv")
                and not name.startswith("__MACOSX")
                and not os.path.basename(name).startswith("._")
            ]

            if not csv_candidates:
                raise ValueError(f"Không tìm thấy file CSV hợp lệ trong {s3_key}")

            chosen_entry = csv_candidates[0]
            print(f"[EXTRACT] Đang giải nén: {chosen_entry} -> {final_csv_path.name}")

            # Giải nén an toàn sang file tạm trước khi đổi tên
            temp_csv_path = target_dir / f"temp_{expected_csv_name}.tmp"
            with zip_ref.open(chosen_entry) as source, open(temp_csv_path, "wb") as target:
                while True:
                    data = source.read(1024 * 1024)
                    if not data:
                        break
                    target.write(data)

            # Atomic rename / replace
            if final_csv_path.exists():
                final_csv_path.unlink()
            temp_csv_path.rename(final_csv_path)

        csv_size = final_csv_path.stat().st_size
        print(f"[SUCCESS] Đã lưu {final_csv_path.name} ({csv_size:,} bytes)")
        return final_csv_path

    finally:
        # Dọn dẹp file zip tạm
        if temp_zip_path.exists():
            try:
                temp_zip_path.unlink()
            except OSError:
                pass


def download_new_data(
    target_dir: Path = DEFAULT_RAW_DIR,
    specific_month: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Path]:
    """
    Quy trình tự động phát hiện và tải dữ liệu Citi Bike tháng mới.
    """
    print("=" * 70)
    print("[START] AUTOMATIC CITI BIKE DATA DOWNLOADER")
    print("=" * 70)

    print(f"[CHECK] Kiểm tra nguồn Citi Bike: {S3_BUCKET_URL}")
    try:
        new_months = find_new_months(raw_dir=target_dir)
    except Exception as exc:
        print(f"[ERROR] Không thể kết nối hoặc quét danh sách dữ liệu: {exc}")
        raise

    local_existing = get_local_months(raw_dir=target_dir)
    print(f"[CHECK] Tháng đã có tại local ({len(local_existing)}): {sorted(list(local_existing))}")
    print(f"[CHECK] Tháng mới phát hiện ({len(new_months)}): {list(new_months.keys())}")

    if not new_months:
        print("[CHECK] Không có dữ liệu tháng mới. Hệ thống ở trạng thái cập nhật nhất.")
        print("-" * 70)
        print("[SUMMARY] Downloaded: 0 files | New data: None")
        print("=" * 70)
        return []

    # Lọc nếu có yêu cầu tháng cụ thể
    months_to_download: Dict[str, str] = {}
    if specific_month:
        clean_month = specific_month.replace("-", "").strip()
        if clean_month in new_months:
            months_to_download[clean_month] = new_months[clean_month]
        else:
            if clean_month in local_existing:
                print(f"[CHECK] Tháng {specific_month} đã tồn tại tại local. Bỏ qua.")
            else:
                print(f"[ERROR] Tháng {specific_month} không có trên nguồn remote.")
            print("-" * 70)
            print("[SUMMARY] Downloaded: 0 files")
            print("=" * 70)
            return []
    else:
        months_to_download = new_months

    if limit is not None and limit > 0:
        months_to_download = dict(list(months_to_download.items())[:limit])

    print(f"[START] Chuẩn bị tải {len(months_to_download)} tháng: {list(months_to_download.keys())}")
    print("-" * 70)

    downloaded_files: List[Path] = []
    error_count = 0

    for month_id, s3_key in months_to_download.items():
        try:
            print(f"[CHECK] Bắt đầu xử lý tháng {month_id} (key: {s3_key})")
            csv_path = download_and_extract_month(
                month_id=month_id,
                s3_key=s3_key,
                target_dir=target_dir,
            )
            downloaded_files.append(csv_path)
        except Exception as exc:
            error_count += 1
            print(f"[ERROR] Lỗi khi tải tháng {month_id}: {exc}")

    print("-" * 70)
    print("[SUMMARY] KẾT QUẢ TẢI DỮ LIỆU:")
    print(f"  - Thành công: {len(downloaded_files)} file")
    print(f"  - Lỗi:       {error_count} file")
    for f in downloaded_files:
        print(f"    * {f.name} ({f.stat().st_size:,} bytes)")
    print("=" * 70)

    return downloaded_files


def main():
    parser = argparse.ArgumentParser(
        description="Automatic Citi Bike Trip Data Downloader",
    )
    parser.add_argument(
        "--month",
        type=str,
        default=None,
        help="Tháng cụ thể cần tải (định dạng YYYYMM hoặc YYYY-MM). Mặc định: tự động tải tháng mới.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Giới hạn số tháng tải về trong lần chạy này (ví dụ: --limit 1).",
    )
    parser.add_argument(
        "--target-dir",
        type=str,
        default=str(DEFAULT_RAW_DIR),
        help=f"Thư mục lưu file CSV (mặc định: {DEFAULT_RAW_DIR})",
    )

    args = parser.parse_args()

    download_new_data(
        target_dir=Path(args.target_dir),
        specific_month=args.month,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()

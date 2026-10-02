from pathlib import Path
import pandas as pd


DATA_DIR = Path("data/raw/trips")


def inspect_file(file):
    print("=" * 80)
    print(f"FILE: {file.name}")
    print("=" * 80)

    df = pd.read_csv(file)

    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    # ---------------------------------------------------------
    # 1. COLUMNS
    # ---------------------------------------------------------
    print("\n[1] COLUMNS")
    for col in df.columns:
        print(f"  - {col}")

    # ---------------------------------------------------------
    # 2. DATA TYPES
    # ---------------------------------------------------------
    print("\n[2] DATA TYPES")
    print(df.dtypes.to_string())

    # ---------------------------------------------------------
    # 3. MISSING VALUES
    # ---------------------------------------------------------
    print("\n[3] MISSING VALUES")

    missing = df.isna().sum()
    missing = missing[missing > 0]

    if missing.empty:
        print("  No missing values.")
    else:
        for col, count in missing.items():
            percentage = count / len(df) * 100
            print(f"  {col}: {count:,} ({percentage:.2f}%)")

    # ---------------------------------------------------------
    # 4. DUPLICATE ride_id
    # ---------------------------------------------------------
    print("\n[4] DUPLICATE ride_id")

    if "ride_id" in df.columns:
        duplicate_count = df["ride_id"].duplicated().sum()
        print(f"  Duplicate ride_id: {duplicate_count:,}")

    # ---------------------------------------------------------
    # 5. DATETIME RANGE
    # ---------------------------------------------------------
    print("\n[5] DATETIME RANGE")

    df["started_at"] = pd.to_datetime(
        df["started_at"],
        errors="coerce"
    )

    df["ended_at"] = pd.to_datetime(
        df["ended_at"],
        errors="coerce"
    )

    print(f"  started_at MIN: {df['started_at'].min()}")
    print(f"  started_at MAX: {df['started_at'].max()}")

    print(f"  ended_at   MIN: {df['ended_at'].min()}")
    print(f"  ended_at   MAX: {df['ended_at'].max()}")

    # ---------------------------------------------------------
    # 6. INVALID DATETIME
    # ---------------------------------------------------------
    print("\n[6] INVALID DATETIME")

    invalid_started = df["started_at"].isna().sum()
    invalid_ended = df["ended_at"].isna().sum()

    print(f"  Invalid started_at: {invalid_started:,}")
    print(f"  Invalid ended_at:   {invalid_ended:,}")

    # ---------------------------------------------------------
    # 7. RIDE DURATION
    # ---------------------------------------------------------
    print("\n[7] RIDE DURATION")

    duration = (
        df["ended_at"] - df["started_at"]
    ).dt.total_seconds() / 60

    print(f"  Minimum duration: {duration.min():.2f} minutes")
    print(f"  Maximum duration: {duration.max():.2f} minutes")
    print(f"  Average duration: {duration.mean():.2f} minutes")

    invalid_duration = (duration <= 0).sum()

    print(f"  Duration <= 0: {invalid_duration:,}")

    # Các chuyến quá dài
    over_24h = (duration > 24 * 60).sum()

    print(f"  Duration > 24 hours: {over_24h:,}")

    # ---------------------------------------------------------
    # 8. RIDEABLE TYPE
    # ---------------------------------------------------------
    print("\n[8] RIDEABLE TYPE")

    if "rideable_type" in df.columns:
        print(df["rideable_type"].value_counts(dropna=False).to_string())

    # ---------------------------------------------------------
    # 9. MEMBER / CASUAL
    # ---------------------------------------------------------
    print("\n[9] MEMBER / CASUAL")

    if "member_casual" in df.columns:
        print(df["member_casual"].value_counts(dropna=False).to_string())

    # ---------------------------------------------------------
    # 10. MONTH DISTRIBUTION
    # ---------------------------------------------------------
    print("\n[10] STARTED_AT MONTH DISTRIBUTION")

    month_distribution = (
        df["started_at"]
        .dt.to_period("M")
        .value_counts()
        .sort_index()
    )

    print(month_distribution.to_string())

    # ---------------------------------------------------------
    # 11. OUTSIDE TARGET PERIOD
    # ---------------------------------------------------------
    print("\n[11] OUTSIDE TARGET PERIOD")

    target_start = pd.Timestamp("2026-01-01 00:00:00")
    target_end = pd.Timestamp("2026-07-01 00:00:00")

    outside = (
        (df["started_at"] < target_start)
        | (df["started_at"] >= target_end)
    )

    print(
        f"  Outside 2026-01-01 -> 2026-07-01: "
        f"{outside.sum():,}"
    )


def main():
    files = sorted(DATA_DIR.glob("*.csv"))

    print("=" * 80)
    print("CITI BIKE DATA QUALITY INSPECTION")
    print("=" * 80)

    print(f"\nFound {len(files)} CSV files.")

    if not files:
        print("No CSV files found.")
        return

    # ---------------------------------------------------------
    # 12. DUPLICATE GIỮA CÁC FILE
    # ---------------------------------------------------------
    print("\n" + "=" * 80)
    print("[GLOBAL CHECK] DUPLICATE ride_id BETWEEN FILES")
    print("=" * 80)

    all_ids = []
    file_id_counts = {}

    for file in files:
        df = pd.read_csv(
            file,
            usecols=["ride_id"]
        )

        ids = df["ride_id"].dropna()

        all_ids.extend(ids.tolist())

        file_id_counts[file.name] = len(ids)

    all_ids_series = pd.Series(all_ids)

    global_duplicates = all_ids_series.duplicated().sum()

    print(f"Total ride_id records: {len(all_ids_series):,}")
    print(f"Duplicate ride_id across files: {global_duplicates:,}")

    # ---------------------------------------------------------
    # INSPECT EACH FILE
    # ---------------------------------------------------------
    for file in files:
        inspect_file(file)

    print("\n" + "=" * 80)
    print("INSPECTION COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()
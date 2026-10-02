from pathlib import Path
import pandas as pd


RAW_DIR = Path("data/raw/trips")
PROCESSED_DIR = Path("data/processed")

OUTPUT_FILE = PROCESSED_DIR / "citibike_2026_H1.csv"

TARGET_START = pd.Timestamp("2026-01-01 00:00:00")
TARGET_END = pd.Timestamp("2026-07-01 00:00:00")


def main():
    print("=" * 80)
    print("CREATE OFFICIAL CITI BIKE DATASET - 2026 H1")
    print("=" * 80)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(RAW_DIR.glob("JC-2026*.csv"))

    print(f"\nFound {len(files)} CSV files.")

    if len(files) != 6:
        raise RuntimeError(
            f"Expected 6 CSV files, but found {len(files)}."
        )

    for file in files:
        print(f"  - {file.name}")

    # ------------------------------------------------------------------
    # 1. READ AND COMBINE
    # ------------------------------------------------------------------

    dataframes = []

    print("\n[1] READING FILES")

    for file in files:
        print(f"Reading: {file.name}")

        df = pd.read_csv(file)

        print(f"  Rows: {len(df):,}")

        dataframes.append(df)

    combined = pd.concat(
        dataframes,
        ignore_index=True
    )

    print(f"\nCombined rows: {len(combined):,}")

    # ------------------------------------------------------------------
    # 2. CONVERT DATETIME
    # ------------------------------------------------------------------

    print("\n[2] CONVERT DATETIME")

    combined["started_at"] = pd.to_datetime(
        combined["started_at"],
        errors="coerce"
    )

    combined["ended_at"] = pd.to_datetime(
        combined["ended_at"],
        errors="coerce"
    )

    invalid_started = combined["started_at"].isna().sum()
    invalid_ended = combined["ended_at"].isna().sum()

    print(f"Invalid started_at: {invalid_started:,}")
    print(f"Invalid ended_at:   {invalid_ended:,}")

    # ------------------------------------------------------------------
    # 3. FILTER TARGET PERIOD
    # ------------------------------------------------------------------

    print("\n[3] FILTER TARGET PERIOD")

    outside_mask = (
        (combined["started_at"] < TARGET_START)
        | (combined["started_at"] >= TARGET_END)
    )

    outside_count = outside_mask.sum()

    print(f"Records outside target period: {outside_count:,}")

    filtered = combined.loc[
        ~outside_mask
    ].copy()

    print(
        f"Rows after time filtering: "
        f"{len(filtered):,}"
    )

    # ------------------------------------------------------------------
    # 4. REMOVE DUPLICATE ride_id
    # ------------------------------------------------------------------

    print("\n[4] REMOVE DUPLICATE ride_id")

    duplicate_count = filtered["ride_id"].duplicated().sum()

    print(f"Duplicate ride_id: {duplicate_count:,}")

    filtered = filtered.drop_duplicates(
        subset=["ride_id"],
        keep="first"
    ).copy()

    print(
        f"Rows after deduplication: "
        f"{len(filtered):,}"
    )

    # ------------------------------------------------------------------
    # 5. SORT
    # ------------------------------------------------------------------

    print("\n[5] SORT DATA")

    filtered = filtered.sort_values(
        by="started_at"
    ).reset_index(drop=True)

    # ------------------------------------------------------------------
    # 6. SAVE
    # ------------------------------------------------------------------

    print("\n[6] SAVE OFFICIAL DATASET")

    filtered.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(f"Output: {OUTPUT_FILE}")
    print(f"Final rows: {len(filtered):,}")
    print(f"Final columns: {len(filtered.columns)}")

    # ------------------------------------------------------------------
    # 7. FINAL VALIDATION
    # ------------------------------------------------------------------

    print("\n[7] FINAL VALIDATION")

    print(
        f"started_at MIN: "
        f"{filtered['started_at'].min()}"
    )

    print(
        f"started_at MAX: "
        f"{filtered['started_at'].max()}"
    )

    print(
        f"Unique ride_id: "
        f"{filtered['ride_id'].nunique():,}"
    )

    print(
        f"Duplicate ride_id remaining: "
        f"{filtered['ride_id'].duplicated().sum():,}"
    )

    print("\n" + "=" * 80)
    print("OFFICIAL DATASET CREATED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()
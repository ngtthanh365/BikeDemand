from pathlib import Path
import pandas as pd


DATASET = Path("data/processed/citibike_2026_H1.csv")


def main():
    print("=" * 80)
    print("CITI BIKE 2026 H1 - DATA OVERVIEW")
    print("=" * 80)

    # ---------------------------------------------------------------
    # 1. LOAD DATASET
    # ---------------------------------------------------------------

    print("\n[1] LOAD DATASET")

    if not DATASET.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET}"
        )

    df = pd.read_csv(DATASET)

    print(f"Rows:    {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    # ---------------------------------------------------------------
    # 2. DATETIME
    # ---------------------------------------------------------------

    print("\n[2] DATETIME CONVERSION")

    df["started_at"] = pd.to_datetime(
        df["started_at"],
        errors="coerce"
    )

    df["ended_at"] = pd.to_datetime(
        df["ended_at"],
        errors="coerce"
    )

    print(f"started_at dtype: {df['started_at'].dtype}")
    print(f"ended_at dtype:   {df['ended_at'].dtype}")

    # ---------------------------------------------------------------
    # 3. MISSING VALUES
    # ---------------------------------------------------------------

    print("\n[3] MISSING VALUES")

    missing = df.isna().sum()

    for column, count in missing.items():
        if count > 0:
            percentage = count / len(df) * 100
            print(
                f"{column}: {count:,} "
                f"({percentage:.2f}%)"
            )

    # ---------------------------------------------------------------
    # 4. USER TYPE
    # ---------------------------------------------------------------

    print("\n[4] MEMBER / CASUAL")

    user_counts = df["member_casual"].value_counts()

    for user_type, count in user_counts.items():
        percentage = count / len(df) * 100

        print(
            f"{user_type}: "
            f"{count:,} "
            f"({percentage:.2f}%)"
        )

    # ---------------------------------------------------------------
    # 5. BIKE TYPE
    # ---------------------------------------------------------------

    print("\n[5] RIDEABLE TYPE")

    bike_counts = df["rideable_type"].value_counts()

    for bike_type, count in bike_counts.items():
        percentage = count / len(df) * 100

        print(
            f"{bike_type}: "
            f"{count:,} "
            f"({percentage:.2f}%)"
        )

    # ---------------------------------------------------------------
    # 6. STATIONS
    # ---------------------------------------------------------------

    print("\n[6] STATIONS")

    print(
        f"Unique start stations: "
        f"{df['start_station_id'].nunique():,}"
    )

    print(
        f"Unique end stations: "
        f"{df['end_station_id'].nunique():,}"
    )

    # ---------------------------------------------------------------
    # 7. RIDE DURATION
    # ---------------------------------------------------------------

    print("\n[7] RIDE DURATION")

    duration = (
        df["ended_at"] - df["started_at"]
    ).dt.total_seconds() / 60

    print(f"Minimum: {duration.min():.2f} minutes")
    print(f"Maximum: {duration.max():.2f} minutes")
    print(f"Average: {duration.mean():.2f} minutes")
    print(f"Median:  {duration.median():.2f} minutes")

    print(
        f"Duration > 24 hours: "
        f"{(duration > 24 * 60).sum():,}"
    )

    # ---------------------------------------------------------------
    # 8. NUMERIC SUMMARY
    # ---------------------------------------------------------------

    print("\n[8] NUMERIC SUMMARY")

    print(
        df[
            [
                "start_lat",
                "start_lng",
                "end_lat",
                "end_lng",
            ]
        ].describe()
    )

    print("\n" + "=" * 80)
    print("DATA OVERVIEW COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()
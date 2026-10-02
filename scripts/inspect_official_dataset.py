from pathlib import Path
import pandas as pd


DATASET = Path("data/processed/citibike_2026_H1.csv")


def main():
    print("=" * 80)
    print("OFFICIAL CITI BIKE DATASET - FINAL INSPECTION")
    print("=" * 80)

    if not DATASET.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET}"
        )

    # ==============================================================
    # 1. LOAD DATA
    # ==============================================================

    print("\n[1] LOAD DATASET")

    df = pd.read_csv(DATASET)

    print(f"Rows:    {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    # ==============================================================
    # 2. COLUMNS
    # ==============================================================

    print("\n[2] COLUMNS")

    for col in df.columns:
        print(f"  - {col}")

    # ==============================================================
    # 3. DATA TYPES
    # ==============================================================

    print("\n[3] DATA TYPES")

    print(df.dtypes.to_string())

    # ==============================================================
    # 4. DATETIME
    # ==============================================================

    print("\n[4] DATETIME")

    df["started_at"] = pd.to_datetime(
        df["started_at"],
        errors="coerce"
    )

    df["ended_at"] = pd.to_datetime(
        df["ended_at"],
        errors="coerce"
    )

    print(f"started_at MIN: {df['started_at'].min()}")
    print(f"started_at MAX: {df['started_at'].max()}")

    print(f"ended_at   MIN: {df['ended_at'].min()}")
    print(f"ended_at   MAX: {df['ended_at'].max()}")

    print(
        f"Invalid started_at: "
        f"{df['started_at'].isna().sum():,}"
    )

    print(
        f"Invalid ended_at:   "
        f"{df['ended_at'].isna().sum():,}"
    )

    # ==============================================================
    # 5. DUPLICATE
    # ==============================================================

    print("\n[5] DUPLICATE ride_id")

    print(
        f"Duplicate ride_id: "
        f"{df['ride_id'].duplicated().sum():,}"
    )

    print(
        f"Unique ride_id: "
        f"{df['ride_id'].nunique():,}"
    )

    # ==============================================================
    # 6. MISSING VALUES
    # ==============================================================

    print("\n[6] MISSING VALUES")

    missing = df.isna().sum()
    missing = missing[missing > 0]

    if missing.empty:
        print("No missing values.")
    else:
        for col, count in missing.items():
            percentage = count / len(df) * 100

            print(
                f"  {col}: "
                f"{count:,} "
                f"({percentage:.2f}%)"
            )

    # ==============================================================
    # 7. RIDEABLE TYPE
    # ==============================================================

    print("\n[7] RIDEABLE TYPE")

    rideable = df["rideable_type"].value_counts(
        dropna=False
    )

    for value, count in rideable.items():
        percentage = count / len(df) * 100

        print(
            f"  {value}: "
            f"{count:,} "
            f"({percentage:.2f}%)"
        )

    # ==============================================================
    # 8. MEMBER / CASUAL
    # ==============================================================

    print("\n[8] MEMBER / CASUAL")

    users = df["member_casual"].value_counts(
        dropna=False
    )

    for value, count in users.items():
        percentage = count / len(df) * 100

        print(
            f"  {value}: "
            f"{count:,} "
            f"({percentage:.2f}%)"
        )

    # ==============================================================
    # 9. DURATION
    # ==============================================================

    print("\n[9] RIDE DURATION")

    duration = (
        df["ended_at"] - df["started_at"]
    ).dt.total_seconds() / 60

    print(f"Minimum: {duration.min():.2f} minutes")
    print(f"Maximum: {duration.max():.2f} minutes")
    print(f"Average: {duration.mean():.2f} minutes")
    print(f"Median:  {duration.median():.2f} minutes")

    print(
        f"Duration <= 0: "
        f"{(duration <= 0).sum():,}"
    )

    print(
        f"Duration > 24 hours: "
        f"{(duration > 24 * 60).sum():,}"
    )

    # ==============================================================
    # 10. MONTHLY DEMAND
    # ==============================================================

    print("\n[10] TRIPS BY MONTH")

    df["month"] = df["started_at"].dt.to_period("M")

    monthly = (
        df.groupby("month")
        .size()
        .sort_index()
    )

    for month, count in monthly.items():
        print(f"  {month}: {count:,}")

    # ==============================================================
    # 11. DAILY DEMAND
    # ==============================================================

    print("\n[11] DAILY DEMAND")

    df["date"] = df["started_at"].dt.date

    daily = (
        df.groupby("date")
        .size()
    )

    print(f"Number of days: {len(daily):,}")
    print(f"Minimum trips/day: {daily.min():,}")
    print(f"Maximum trips/day: {daily.max():,}")
    print(f"Average trips/day: {daily.mean():,.2f}")
    print(f"Median trips/day: {daily.median():,.2f}")

    print("\nTop 10 busiest days:")

    top_days = daily.sort_values(
        ascending=False
    ).head(10)

    for date, count in top_days.items():
        print(f"  {date}: {count:,}")

    # ==============================================================
    # 12. HOURLY DEMAND
    # ==============================================================

    print("\n[12] HOURLY DEMAND")

    df["hour"] = df["started_at"].dt.hour

    hourly = (
        df.groupby("hour")
        .size()
        .sort_index()
    )

    for hour, count in hourly.items():
        print(
            f"  {hour:02d}:00 - "
            f"{count:,}"
        )

    busiest_hour = hourly.idxmax()
    busiest_hour_count = hourly.max()

    print(
        f"\nBusiest hour: "
        f"{busiest_hour:02d}:00 "
        f"({busiest_hour_count:,} trips)"
    )

    # ==============================================================
    # 13. DAY OF WEEK
    # ==============================================================

    print("\n[13] DAY OF WEEK")

    df["day_of_week"] = df["started_at"].dt.dayofweek

    day_names = {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday",
    }

    weekday = (
        df.groupby("day_of_week")
        .size()
        .sort_index()
    )

    for day, count in weekday.items():
        print(
            f"  {day_names[day]}: "
            f"{count:,}"
        )

    # ==============================================================
    # 14. START STATIONS
    # ==============================================================

    print("\n[14] START STATIONS")

    start_station_count = (
        df["start_station_id"]
        .nunique(dropna=True)
    )

    print(
        f"Unique start stations: "
        f"{start_station_count:,}"
    )

    print("\nTop 10 start stations:")

    top_start = (
        df["start_station_id"]
        .value_counts()
        .head(10)
    )

    for station, count in top_start.items():
        print(f"  {station}: {count:,}")

    # ==============================================================
    # 15. END STATIONS
    # ==============================================================

    print("\n[15] END STATIONS")

    end_station_count = (
        df["end_station_id"]
        .nunique(dropna=True)
    )

    print(
        f"Unique end stations: "
        f"{end_station_count:,}"
    )

    print("\nTop 10 end stations:")

    top_end = (
        df["end_station_id"]
        .value_counts()
        .head(10)
    )

    for station, count in top_end.items():
        print(f"  {station}: {count:,}")

    # ==============================================================
    # 16. COORDINATES
    # ==============================================================

    print("\n[16] COORDINATES")

    coordinate_columns = [
        "start_lat",
        "start_lng",
        "end_lat",
        "end_lng",
    ]

    for col in coordinate_columns:
        print(
            f"  {col}: "
            f"MIN={df[col].min()}, "
            f"MAX={df[col].max()}"
        )

    # ==============================================================
    # 17. FINAL SUMMARY
    # ==============================================================

    print("\n" + "=" * 80)
    print("FINAL DATASET SUMMARY")
    print("=" * 80)

    print(f"Total trips:       {len(df):,}")
    print(f"Columns:            {len(df.columns) - 3}")
    print(f"Unique ride_id:    {df['ride_id'].nunique():,}")
    print(f"Unique start stations: {start_station_count:,}")
    print(f"Unique end stations:   {end_station_count:,}")

    print(
        f"Time range: "
        f"{df['started_at'].min()} "
        f"→ "
        f"{df['started_at'].max()}"
    )

    print("\nInspection completed.")


if __name__ == "__main__":
    main()
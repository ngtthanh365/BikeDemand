from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# ================================================================
# CONFIG
# ================================================================

DATASET = Path("data/processed/citibike_2026_H1.csv")

OUTPUT_DIR = Path("analysis/outputs")
FIGURES_DIR = OUTPUT_DIR / "figures"
TABLES_DIR = OUTPUT_DIR / "tables"


# ================================================================
# HELPER FUNCTIONS
# ================================================================

def save_table(df, filename):
    """Save analysis table as CSV."""
    output_file = TABLES_DIR / filename
    df.to_csv(output_file, index=False)
    print(f"Saved table: {output_file}")


def save_figure(filename):
    """Save current matplotlib figure."""
    output_file = FIGURES_DIR / filename
    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    plt.close()
    print(f"Saved figure: {output_file}")


# ================================================================
# MAIN
# ================================================================

def main():

    print("=" * 80)
    print("CITI BIKE 2026 H1 - TIME ANALYSIS")
    print("=" * 80)

    # ------------------------------------------------------------
    # 1. CREATE OUTPUT DIRECTORIES
    # ------------------------------------------------------------

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------
    # 2. LOAD DATASET
    # ------------------------------------------------------------

    print("\n[1] LOAD DATASET")

    if not DATASET.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET}"
        )

    df = pd.read_csv(DATASET)

    df["started_at"] = pd.to_datetime(
        df["started_at"],
        errors="coerce"
    )

    print(f"Rows: {len(df):,}")

    # ------------------------------------------------------------
    # 3. CREATE TIME FEATURES
    # ------------------------------------------------------------

    print("\n[2] CREATE TIME FEATURES")

    df["date"] = df["started_at"].dt.date
    df["hour"] = df["started_at"].dt.hour
    df["day_of_week"] = df["started_at"].dt.dayofweek
    df["day_name"] = df["started_at"].dt.day_name()
    df["month"] = df["started_at"].dt.month
    df["month_name"] = df["started_at"].dt.month_name()

    # ============================================================
    # 4. MONTHLY ANALYSIS
    # ============================================================

    print("\n[3] MONTHLY ANALYSIS")

    monthly = (
        df.groupby(["month", "month_name"])
        .size()
        .reset_index(name="total_trips")
        .sort_values("month")
    )

    print(monthly.to_string(index=False))

    save_table(
        monthly,
        "time_monthly_demand.csv"
    )

    plt.figure(figsize=(10, 5))

    plt.plot(
        monthly["month_name"],
        monthly["total_trips"],
        marker="o"
    )

    plt.title("Citi Bike Trips by Month - 2026 H1")
    plt.xlabel("Month")
    plt.ylabel("Total Trips")
    plt.xticks(rotation=45)

    save_figure(
        "time_monthly_demand.png"
    )

    # ============================================================
    # 5. DAILY ANALYSIS
    # ============================================================

    print("\n[4] DAILY ANALYSIS")

    daily = (
        df.groupby("date")
        .size()
        .reset_index(name="total_trips")
    )

    daily["date"] = pd.to_datetime(daily["date"])

    print("\nDaily statistics:")

    print(
        f"Minimum: {daily['total_trips'].min():,} trips"
    )

    print(
        f"Maximum: {daily['total_trips'].max():,} trips"
    )

    print(
        f"Average: {daily['total_trips'].mean():,.2f} trips"
    )

    print(
        f"Median: {daily['total_trips'].median():,.2f} trips"
    )

    print("\nTop 10 busiest days:")

    top_days = (
        daily
        .sort_values("total_trips", ascending=False)
        .head(10)
    )

    print(top_days.to_string(index=False))

    save_table(
        daily,
        "time_daily_demand.csv"
    )

    save_table(
        top_days,
        "time_top_10_busiest_days.csv"
    )

    plt.figure(figsize=(12, 5))

    plt.plot(
        daily["date"],
        daily["total_trips"]
    )

    plt.title("Daily Citi Bike Demand - 2026 H1")
    plt.xlabel("Date")
    plt.ylabel("Total Trips")

    save_figure(
        "time_daily_demand.png"
    )

    # ============================================================
    # 6. HOURLY ANALYSIS
    # ============================================================

    print("\n[5] HOURLY ANALYSIS")

    hourly = (
        df.groupby("hour")
        .size()
        .reset_index(name="total_trips")
        .sort_values("hour")
    )

    print(hourly.to_string(index=False))

    busiest_hour = hourly.loc[
        hourly["total_trips"].idxmax()
    ]

    print(
        f"\nBusiest hour: "
        f"{int(busiest_hour['hour']):02d}:00 "
        f"with {int(busiest_hour['total_trips']):,} trips"
    )

    save_table(
        hourly,
        "time_hourly_demand.csv"
    )

    plt.figure(figsize=(10, 5))

    plt.plot(
        hourly["hour"],
        hourly["total_trips"],
        marker="o"
    )

    plt.title("Citi Bike Trips by Hour - 2026 H1")
    plt.xlabel("Hour of Day")
    plt.ylabel("Total Trips")
    plt.xticks(range(24))

    save_figure(
        "time_hourly_demand.png"
    )

    # ============================================================
    # 7. DAY OF WEEK ANALYSIS
    # ============================================================

    print("\n[6] DAY OF WEEK ANALYSIS")

    weekday_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday"
    ]

    weekday = (
        df.groupby(
            ["day_of_week", "day_name"]
        )
        .size()
        .reset_index(name="total_trips")
        .sort_values("day_of_week")
    )

    print(weekday.to_string(index=False))

    save_table(
        weekday,
        "time_day_of_week_demand.csv"
    )

    plt.figure(figsize=(10, 5))

    plt.bar(
        weekday["day_name"],
        weekday["total_trips"]
    )

    plt.title("Citi Bike Trips by Day of Week - 2026 H1")
    plt.xlabel("Day of Week")
    plt.ylabel("Total Trips")

    plt.xticks(
        range(7),
        weekday_order,
        rotation=45
    )

    save_figure(
        "time_day_of_week_demand.png"
    )

    # ============================================================
    # 8. SUMMARY
    # ============================================================

    print("\n[7] TIME ANALYSIS SUMMARY")

    print(
        f"Total trips: {len(df):,}"
    )

    print(
        f"Date range: "
        f"{df['started_at'].min()} "
        f"to "
        f"{df['started_at'].max()}"
    )

    max_month = monthly.loc[
        monthly["total_trips"].idxmax()
    ]

    min_month = monthly.loc[
        monthly["total_trips"].idxmin()
    ]

    max_weekday = weekday.loc[
        weekday["total_trips"].idxmax()
    ]

    min_weekday = weekday.loc[
        weekday["total_trips"].idxmin()
    ]

    print(
        f"Highest-demand month: "
        f"{max_month['month_name']} "
        f"({int(max_month['total_trips']):,} trips)"
    )

    print(
        f"Lowest-demand month: "
        f"{min_month['month_name']} "
        f"({int(min_month['total_trips']):,} trips)"
    )

    print(
        f"Highest-demand weekday: "
        f"{max_weekday['day_name']} "
        f"({int(max_weekday['total_trips']):,} trips)"
    )

    print(
        f"Lowest-demand weekday: "
        f"{min_weekday['day_name']} "
        f"({int(min_weekday['total_trips']):,} trips)"
    )

    print(
        f"Busiest hour: "
        f"{int(busiest_hour['hour']):02d}:00 "
        f"({int(busiest_hour['total_trips']):,} trips)"
    )

    print("\n" + "=" * 80)
    print("TIME ANALYSIS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()
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
    output_file = TABLES_DIR / filename
    df.to_csv(output_file, index=False)
    print(f"Saved table: {output_file}")


def save_figure(filename):
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
    print("CITI BIKE 2026 H1 - BIKE ANALYSIS")
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

    df["month"] = df["started_at"].dt.month
    df["month_name"] = df["started_at"].dt.month_name()

    df["hour"] = df["started_at"].dt.hour

    df["day_of_week"] = df["started_at"].dt.dayofweek
    df["day_name"] = df["started_at"].dt.day_name()

    bike_order = [
        "electric_bike",
        "classic_bike"
    ]

    # ============================================================
    # 4. BIKE TYPE - OVERALL
    # ============================================================

    print("\n[3] BIKE TYPE - OVERALL")

    bike_counts = (
        df["rideable_type"]
        .value_counts()
        .reindex(bike_order)
        .fillna(0)
        .astype(int)
        .reset_index()
    )

    bike_counts.columns = [
        "rideable_type",
        "total_trips"
    ]

    bike_counts["percentage"] = (
        bike_counts["total_trips"]
        / bike_counts["total_trips"].sum()
        * 100
    )

    print(
        bike_counts.to_string(index=False)
    )

    save_table(
        bike_counts,
        "bike_overall_demand.csv"
    )

    plt.figure(figsize=(7, 7))

    plt.pie(
        bike_counts["total_trips"],
        labels=bike_counts["rideable_type"],
        autopct="%1.2f%%"
    )

    plt.title(
        "Citi Bike Trips - Electric vs Classic Bike"
    )

    save_figure(
        "bike_electric_vs_classic.png"
    )

    # ============================================================
    # 5. BIKE TYPE BY MONTH
    # ============================================================

    print("\n[4] BIKE TYPE BY MONTH")

    monthly_bike = (
        df.groupby(
            [
                "month",
                "month_name",
                "rideable_type"
            ]
        )
        .size()
        .reset_index(name="total_trips")
        .sort_values(
            [
                "month",
                "rideable_type"
            ]
        )
    )

    print(
        monthly_bike.to_string(index=False)
    )

    save_table(
        monthly_bike,
        "bike_monthly_demand.csv"
    )

    monthly_pivot = (
        monthly_bike
        .pivot(
            index=["month", "month_name"],
            columns="rideable_type",
            values="total_trips"
        )
        .reset_index()
    )

    monthly_pivot.columns.name = None

    save_table(
        monthly_pivot,
        "bike_monthly_comparison.csv"
    )

    plt.figure(figsize=(10, 5))

    for bike_type in bike_order:

        if bike_type in monthly_pivot.columns:

            plt.plot(
                monthly_pivot["month_name"],
                monthly_pivot[bike_type],
                marker="o",
                label=bike_type
            )

    plt.title(
        "Electric vs Classic Bike Trips by Month - 2026 H1"
    )

    plt.xlabel("Month")
    plt.ylabel("Total Trips")
    plt.legend()

    save_figure(
        "bike_monthly_comparison.png"
    )

    # ============================================================
    # 6. BIKE TYPE BY HOUR
    # ============================================================

    print("\n[5] BIKE TYPE BY HOUR")

    hourly_bike = (
        df.groupby(
            [
                "hour",
                "rideable_type"
            ]
        )
        .size()
        .reset_index(name="total_trips")
        .sort_values(
            [
                "hour",
                "rideable_type"
            ]
        )
    )

    print(
        hourly_bike.to_string(index=False)
    )

    save_table(
        hourly_bike,
        "bike_hourly_demand.csv"
    )

    hourly_pivot = (
        hourly_bike
        .pivot(
            index="hour",
            columns="rideable_type",
            values="total_trips"
        )
        .reset_index()
    )

    hourly_pivot.columns.name = None

    save_table(
        hourly_pivot,
        "bike_hourly_comparison.csv"
    )

    plt.figure(figsize=(11, 5))

    for bike_type in bike_order:

        if bike_type in hourly_pivot.columns:

            plt.plot(
                hourly_pivot["hour"],
                hourly_pivot[bike_type],
                marker="o",
                label=bike_type
            )

    plt.title(
        "Electric vs Classic Bike Trips by Hour - 2026 H1"
    )

    plt.xlabel("Hour of Day")
    plt.ylabel("Total Trips")
    plt.xticks(range(24))
    plt.legend()

    save_figure(
        "bike_hourly_comparison.png"
    )

    # ============================================================
    # 7. BIKE TYPE BY DAY OF WEEK
    # ============================================================

    print("\n[6] BIKE TYPE BY DAY OF WEEK")

    weekday_bike = (
        df.groupby(
            [
                "day_of_week",
                "day_name",
                "rideable_type"
            ]
        )
        .size()
        .reset_index(name="total_trips")
        .sort_values(
            [
                "day_of_week",
                "rideable_type"
            ]
        )
    )

    print(
        weekday_bike.to_string(index=False)
    )

    save_table(
        weekday_bike,
        "bike_day_of_week_demand.csv"
    )

    weekday_pivot = (
        weekday_bike
        .pivot(
            index=["day_of_week", "day_name"],
            columns="rideable_type",
            values="total_trips"
        )
        .reset_index()
        .sort_values("day_of_week")
    )

    weekday_pivot.columns.name = None

    save_table(
        weekday_pivot,
        "bike_day_of_week_comparison.csv"
    )

    plt.figure(figsize=(10, 5))

    for bike_type in bike_order:

        if bike_type in weekday_pivot.columns:

            plt.plot(
                weekday_pivot["day_name"],
                weekday_pivot[bike_type],
                marker="o",
                label=bike_type
            )

    plt.title(
        "Electric vs Classic Bike Trips by Day of Week - 2026 H1"
    )

    plt.xlabel("Day of Week")
    plt.ylabel("Total Trips")
    plt.legend()

    plt.xticks(rotation=45)

    save_figure(
        "bike_day_of_week_comparison.png"
    )

    # ============================================================
    # 8. SUMMARY
    # ============================================================

    print("\n[7] BIKE ANALYSIS SUMMARY")

    electric_total = int(
        bike_counts.loc[
            bike_counts["rideable_type"] == "electric_bike",
            "total_trips"
        ].iloc[0]
    )

    classic_total = int(
        bike_counts.loc[
            bike_counts["rideable_type"] == "classic_bike",
            "total_trips"
        ].iloc[0]
    )

    electric_percentage = (
        electric_total
        / len(df)
        * 100
    )

    classic_percentage = (
        classic_total
        / len(df)
        * 100
    )

    print(
        f"Electric bike: {electric_total:,} "
        f"({electric_percentage:.2f}%)"
    )

    print(
        f"Classic bike: {classic_total:,} "
        f"({classic_percentage:.2f}%)"
    )

    # Electric busiest hour
    electric_hour = (
        hourly_bike[
            hourly_bike["rideable_type"] == "electric_bike"
        ]
        .sort_values(
            "total_trips",
            ascending=False
        )
        .iloc[0]
    )

    # Classic busiest hour
    classic_hour = (
        hourly_bike[
            hourly_bike["rideable_type"] == "classic_bike"
        ]
        .sort_values(
            "total_trips",
            ascending=False
        )
        .iloc[0]
    )

    print(
        f"Electric bike busiest hour: "
        f"{int(electric_hour['hour']):02d}:00 "
        f"({int(electric_hour['total_trips']):,} trips)"
    )

    print(
        f"Classic bike busiest hour: "
        f"{int(classic_hour['hour']):02d}:00 "
        f"({int(classic_hour['total_trips']):,} trips)"
    )

    # Electric busiest weekday
    electric_day = (
        weekday_bike[
            weekday_bike["rideable_type"] == "electric_bike"
        ]
        .sort_values(
            "total_trips",
            ascending=False
        )
        .iloc[0]
    )

    # Classic busiest weekday
    classic_day = (
        weekday_bike[
            weekday_bike["rideable_type"] == "classic_bike"
        ]
        .sort_values(
            "total_trips",
            ascending=False
        )
        .iloc[0]
    )

    print(
        f"Electric bike busiest weekday: "
        f"{electric_day['day_name']} "
        f"({int(electric_day['total_trips']):,} trips)"
    )

    print(
        f"Classic bike busiest weekday: "
        f"{classic_day['day_name']} "
        f"({int(classic_day['total_trips']):,} trips)"
    )

    print("\n" + "=" * 80)
    print("BIKE ANALYSIS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()
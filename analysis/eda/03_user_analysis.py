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
    print("CITI BIKE 2026 H1 - USER ANALYSIS")
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

    # ============================================================
    # 4. MEMBER VS CASUAL - OVERALL
    # ============================================================

    print("\n[3] MEMBER VS CASUAL - OVERALL")

    user_order = ["member", "casual"]

    user_counts = (
        df["member_casual"]
        .value_counts()
        .reindex(user_order)
        .fillna(0)
        .astype(int)
        .reset_index()
    )

    user_counts.columns = [
        "member_casual",
        "total_trips"
    ]

    user_counts["percentage"] = (
        user_counts["total_trips"]
        / user_counts["total_trips"].sum()
        * 100
    )

    print(user_counts.to_string(index=False))

    save_table(
        user_counts,
        "user_overall_demand.csv"
    )

    # Pie chart
    plt.figure(figsize=(7, 7))

    plt.pie(
        user_counts["total_trips"],
        labels=user_counts["member_casual"],
        autopct="%1.2f%%"
    )

    plt.title(
        "Citi Bike Trips - Member vs Casual"
    )

    save_figure(
        "user_member_vs_casual.png"
    )

    # ============================================================
    # 5. MEMBER VS CASUAL BY MONTH
    # ============================================================

    print("\n[4] MEMBER VS CASUAL BY MONTH")

    monthly_user = (
        df.groupby(
            ["month", "month_name", "member_casual"]
        )
        .size()
        .reset_index(name="total_trips")
        .sort_values(
            ["month", "member_casual"]
        )
    )

    print(monthly_user.to_string(index=False))

    save_table(
        monthly_user,
        "user_monthly_demand.csv"
    )

    monthly_pivot = (
        monthly_user
        .pivot(
            index=["month", "month_name"],
            columns="member_casual",
            values="total_trips"
        )
        .reset_index()
    )

    monthly_pivot.columns.name = None

    print("\nMonthly comparison:")

    print(
        monthly_pivot.to_string(index=False)
    )

    save_table(
        monthly_pivot,
        "user_monthly_comparison.csv"
    )

    plt.figure(figsize=(10, 5))

    for user_type in user_order:
        subset = monthly_pivot

        if user_type in subset.columns:
            plt.plot(
                subset["month_name"],
                subset[user_type],
                marker="o",
                label=user_type
            )

    plt.title(
        "Member vs Casual Trips by Month - 2026 H1"
    )

    plt.xlabel("Month")
    plt.ylabel("Total Trips")
    plt.legend()

    save_figure(
        "user_monthly_comparison.png"
    )

    # ============================================================
    # 6. MEMBER VS CASUAL BY HOUR
    # ============================================================

    print("\n[5] MEMBER VS CASUAL BY HOUR")

    hourly_user = (
        df.groupby(
            ["hour", "member_casual"]
        )
        .size()
        .reset_index(name="total_trips")
        .sort_values(
            ["hour", "member_casual"]
        )
    )

    print(hourly_user.to_string(index=False))

    save_table(
        hourly_user,
        "user_hourly_demand.csv"
    )

    hourly_pivot = (
        hourly_user
        .pivot(
            index="hour",
            columns="member_casual",
            values="total_trips"
        )
        .reset_index()
    )

    hourly_pivot.columns.name = None

    save_table(
        hourly_pivot,
        "user_hourly_comparison.csv"
    )

    plt.figure(figsize=(11, 5))

    for user_type in user_order:

        if user_type in hourly_pivot.columns:

            plt.plot(
                hourly_pivot["hour"],
                hourly_pivot[user_type],
                marker="o",
                label=user_type
            )

    plt.title(
        "Member vs Casual Trips by Hour - 2026 H1"
    )

    plt.xlabel("Hour of Day")
    plt.ylabel("Total Trips")
    plt.xticks(range(24))
    plt.legend()

    save_figure(
        "user_hourly_comparison.png"
    )

    # ============================================================
    # 7. MEMBER VS CASUAL BY DAY OF WEEK
    # ============================================================

    print("\n[6] MEMBER VS CASUAL BY DAY OF WEEK")

    weekday_user = (
        df.groupby(
            [
                "day_of_week",
                "day_name",
                "member_casual"
            ]
        )
        .size()
        .reset_index(name="total_trips")
        .sort_values(
            [
                "day_of_week",
                "member_casual"
            ]
        )
    )

    print(
        weekday_user.to_string(index=False)
    )

    save_table(
        weekday_user,
        "user_day_of_week_demand.csv"
    )

    weekday_pivot = (
        weekday_user
        .pivot(
            index=["day_of_week", "day_name"],
            columns="member_casual",
            values="total_trips"
        )
        .reset_index()
        .sort_values("day_of_week")
    )

    weekday_pivot.columns.name = None

    save_table(
        weekday_pivot,
        "user_day_of_week_comparison.csv"
    )

    plt.figure(figsize=(10, 5))

    for user_type in user_order:

        if user_type in weekday_pivot.columns:

            plt.plot(
                weekday_pivot["day_name"],
                weekday_pivot[user_type],
                marker="o",
                label=user_type
            )

    plt.title(
        "Member vs Casual Trips by Day of Week - 2026 H1"
    )

    plt.xlabel("Day of Week")
    plt.ylabel("Total Trips")
    plt.legend()

    plt.xticks(rotation=45)

    save_figure(
        "user_day_of_week_comparison.png"
    )

    # ============================================================
    # 8. SUMMARY
    # ============================================================

    print("\n[7] USER ANALYSIS SUMMARY")

    member_total = int(
        user_counts.loc[
            user_counts["member_casual"] == "member",
            "total_trips"
        ].iloc[0]
    )

    casual_total = int(
        user_counts.loc[
            user_counts["member_casual"] == "casual",
            "total_trips"
        ].iloc[0]
    )

    member_percentage = (
        member_total
        / len(df)
        * 100
    )

    casual_percentage = (
        casual_total
        / len(df)
        * 100
    )

    print(
        f"Member: {member_total:,} "
        f"({member_percentage:.2f}%)"
    )

    print(
        f"Casual: {casual_total:,} "
        f"({casual_percentage:.2f}%)"
    )

    # Member busiest hour
    member_hour = (
        hourly_user[
            hourly_user["member_casual"] == "member"
        ]
        .sort_values(
            "total_trips",
            ascending=False
        )
        .iloc[0]
    )

    # Casual busiest hour
    casual_hour = (
        hourly_user[
            hourly_user["member_casual"] == "casual"
        ]
        .sort_values(
            "total_trips",
            ascending=False
        )
        .iloc[0]
    )

    print(
        f"Member busiest hour: "
        f"{int(member_hour['hour']):02d}:00 "
        f"({int(member_hour['total_trips']):,} trips)"
    )

    print(
        f"Casual busiest hour: "
        f"{int(casual_hour['hour']):02d}:00 "
        f"({int(casual_hour['total_trips']):,} trips)"
    )

    # Member busiest weekday
    member_day = (
        weekday_user[
            weekday_user["member_casual"] == "member"
        ]
        .sort_values(
            "total_trips",
            ascending=False
        )
        .iloc[0]
    )

    # Casual busiest weekday
    casual_day = (
        weekday_user[
            weekday_user["member_casual"] == "casual"
        ]
        .sort_values(
            "total_trips",
            ascending=False
        )
        .iloc[0]
    )

    print(
        f"Member busiest weekday: "
        f"{member_day['day_name']} "
        f"({int(member_day['total_trips']):,} trips)"
    )

    print(
        f"Casual busiest weekday: "
        f"{casual_day['day_name']} "
        f"({int(casual_day['total_trips']):,} trips)"
    )

    print("\n" + "=" * 80)
    print("USER ANALYSIS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()
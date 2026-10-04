import os
import pandas as pd
import matplotlib.pyplot as plt


# =========================
# 1. CONFIG
# =========================

INPUT_FILE = "data/processed/citibike_2026_H1.csv"

OUTPUT_TABLE_DIR = "analysis/outputs/tables"
OUTPUT_FIGURE_DIR = "analysis/outputs/figures"

os.makedirs(OUTPUT_TABLE_DIR, exist_ok=True)
os.makedirs(OUTPUT_FIGURE_DIR, exist_ok=True)


# =========================
# 2. LOAD DATA
# =========================

print("=" * 70)
print("EDA 05 - STATION ANALYSIS")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

print(f"\nRows: {len(df):,}")


# =========================
# 3. TOP START STATIONS
# =========================

start_station = (
    df.dropna(subset=["start_station_id"])
      .groupby(
          ["start_station_id", "start_station_name"],
          dropna=False
      )
      .size()
      .reset_index(name="total_trips")
      .sort_values("total_trips", ascending=False)
)

top_start = start_station.head(10).copy()

print("\n" + "=" * 70)
print("TOP 10 START STATIONS")
print("=" * 70)

print(top_start.to_string(index=False))

top_start.to_csv(
    f"{OUTPUT_TABLE_DIR}/station_top_10_start.csv",
    index=False
)


# =========================
# 4. TOP END STATIONS
# =========================

end_station = (
    df.dropna(subset=["end_station_id"])
      .groupby(
          ["end_station_id", "end_station_name"],
          dropna=False
      )
      .size()
      .reset_index(name="total_trips")
      .sort_values("total_trips", ascending=False)
)

top_end = end_station.head(10).copy()

print("\n" + "=" * 70)
print("TOP 10 END STATIONS")
print("=" * 70)

print(top_end.to_string(index=False))

top_end.to_csv(
    f"{OUTPUT_TABLE_DIR}/station_top_10_end.csv",
    index=False
)


# =========================
# 5. START / END COMPARISON
# =========================

start_compare = (
    df.dropna(subset=["start_station_id"])
      .groupby("start_station_id")
      .size()
      .reset_index(name="start_trips")
)

end_compare = (
    df.dropna(subset=["end_station_id"])
      .groupby("end_station_id")
      .size()
      .reset_index(name="end_trips")
)

station_compare = pd.merge(
    start_compare,
    end_compare,
    left_on="start_station_id",
    right_on="end_station_id",
    how="outer"
)

station_compare["station_id"] = (
    station_compare["start_station_id"]
    .fillna(station_compare["end_station_id"])
)

station_compare["start_trips"] = station_compare["start_trips"].fillna(0)
station_compare["end_trips"] = station_compare["end_trips"].fillna(0)

station_compare["total_station_activity"] = (
    station_compare["start_trips"]
    + station_compare["end_trips"]
)

station_compare = station_compare[
    [
        "station_id",
        "start_trips",
        "end_trips",
        "total_station_activity"
    ]
].sort_values(
    "total_station_activity",
    ascending=False
)

print("\n" + "=" * 70)
print("TOP 10 STATIONS BY TOTAL ACTIVITY")
print("=" * 70)

print(
    station_compare.head(10).to_string(index=False)
)

station_compare.to_csv(
    f"{OUTPUT_TABLE_DIR}/station_start_end_comparison.csv",
    index=False
)


# =========================
# 6. TOP 10 STATIONS CHART
# =========================

top_10_activity = station_compare.head(10).copy()

plt.figure(figsize=(12, 7))

plt.barh(
    top_10_activity["station_id"].astype(str),
    top_10_activity["total_station_activity"]
)

plt.xlabel("Number of trips")
plt.ylabel("Station ID")
plt.title("Top 10 Stations by Total Activity")

plt.gca().invert_yaxis()

plt.tight_layout()

plt.savefig(
    f"{OUTPUT_FIGURE_DIR}/station_top_10_activity.png",
    dpi=150
)

plt.close()


# =========================
# 7. TOP START STATIONS CHART
# =========================

plt.figure(figsize=(12, 7))

plt.barh(
    top_start["start_station_id"].astype(str),
    top_start["total_trips"]
)

plt.xlabel("Number of trips")
plt.ylabel("Start Station ID")
plt.title("Top 10 Start Stations")

plt.gca().invert_yaxis()

plt.tight_layout()

plt.savefig(
    f"{OUTPUT_FIGURE_DIR}/station_top_10_start.png",
    dpi=150
)

plt.close()


# =========================
# 8. TOP END STATIONS CHART
# =========================

plt.figure(figsize=(12, 7))

plt.barh(
    top_end["end_station_id"].astype(str),
    top_end["total_trips"]
)

plt.xlabel("Number of trips")
plt.ylabel("End Station ID")
plt.title("Top 10 End Stations")

plt.gca().invert_yaxis()

plt.tight_layout()

plt.savefig(
    f"{OUTPUT_FIGURE_DIR}/station_top_10_end.png",
    dpi=150
)

plt.close()


# =========================
# 9. SUMMARY
# =========================

print("\n" + "=" * 70)
print("STATION ANALYSIS SUMMARY")
print("=" * 70)

print(
    f"Unique start stations: "
    f"{df['start_station_id'].nunique():,}"
)

print(
    f"Unique end stations: "
    f"{df['end_station_id'].nunique():,}"
)

print("\nTop start station:")
print(
    f"  {top_start.iloc[0]['start_station_id']} "
    f"- {top_start.iloc[0]['start_station_name']}"
    f" ({top_start.iloc[0]['total_trips']:,} trips)"
)

print("\nTop end station:")
print(
    f"  {top_end.iloc[0]['end_station_id']} "
    f"- {top_end.iloc[0]['end_station_name']}"
    f" ({top_end.iloc[0]['total_trips']:,} trips)"
)

print("\nTop station by total activity:")
print(
    f"  {top_10_activity.iloc[0]['station_id']}"
    f" ({top_10_activity.iloc[0]['total_station_activity']:,} trips)"
)

print("\nOutput tables:")
print(f"  {OUTPUT_TABLE_DIR}/station_top_10_start.csv")
print(f"  {OUTPUT_TABLE_DIR}/station_top_10_end.csv")
print(f"  {OUTPUT_TABLE_DIR}/station_start_end_comparison.csv")

print("\nOutput figures:")
print(f"  {OUTPUT_FIGURE_DIR}/station_top_10_activity.png")
print(f"  {OUTPUT_FIGURE_DIR}/station_top_10_start.png")
print(f"  {OUTPUT_FIGURE_DIR}/station_top_10_end.png")

print("\nEDA 05 completed successfully.")
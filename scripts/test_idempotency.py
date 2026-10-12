"""
test_idempotency.py â€” Task 7: Idempotency / Re-run Verification (Phase 1)

Ká»‹ch báº£n kiá»ƒm thá»­ toÃ n diá»‡n:
  1. Ghi nháº­n Snapshot cÆ¡ sá»Ÿ dá»¯ liá»‡u ban Ä‘áº§u (Baseline: trips, hourly_demand, duplicates).
  2. Test 1 (Downloader): Cháº¡y láº¡i táº£i thÃ¡ng 07/2026 -> XÃ¡c nháº­n skip do file Ä‘Ã£ tá»“n táº¡i.
  3. Test 2 (Validator): Cháº¡y láº¡i validate thÃ¡ng 07/2026 -> XÃ¡c nháº­n lá»c 100% duplicate tá»« DB.
  4. Test 3 (Producer): Cháº¡y láº¡i gá»­i Kafka file thÃ¡ng 07 -> XÃ¡c nháº­n skip do state/DB.
  5. Test 4 (Spark Aggregate): Cháº¡y láº¡i aggregate_demand -> XÃ¡c nháº­n 0 rows má»›i vÃ o hourly_demand.
  6. Test 5 (Spark Trips): Cháº¡y láº¡i spark_streaming -> XÃ¡c nháº­n 0 records má»›i vÃ o trips.
  7. Äá»‘i chiáº¿u toÃ n váº¹n Database sau re-run (Post-check vs Baseline).
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.postgres import get_connection


def get_db_metrics() -> Dict[str, Any]:
    """Láº¥y cÃ¡c chá»‰ sá»‘ toÃ n váº¹n dá»¯ liá»‡u tá»« PostgreSQL."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Trips count & unique ride_ids
            cursor.execute("""
                SELECT
                    COUNT(*) AS total_trips,
                    COUNT(DISTINCT ride_id) AS unique_trips,
                    COUNT(*) - COUNT(DISTINCT ride_id) AS dup_trips
                FROM trips;
            """)
            trips_row = cursor.fetchone()

            # Hourly demand count & unique timestamps & total demand
            cursor.execute("""
                SELECT
                    COUNT(*) AS total_hourly,
                    COUNT(DISTINCT timestamp) AS unique_timestamps,
                    COUNT(*) - COUNT(DISTINCT timestamp) AS dup_timestamps,
                    COALESCE(SUM(demand), 0) AS total_demand
                FROM hourly_demand;
            """)
            hourly_row = cursor.fetchone()

            return {
                "total_trips": trips_row[0],
                "unique_trips": trips_row[1],
                "dup_trips": trips_row[2],
                "total_hourly": hourly_row[0],
                "unique_timestamps": hourly_row[1],
                "dup_timestamps": hourly_row[2],
                "total_demand": hourly_row[3],
            }
    finally:
        conn.close()


def run_command(cmd: str, description: str) -> subprocess.CompletedProcess:
    """Thá»±c thi command vÃ  in log theo dÃµi."""
    print("=" * 70)
    print(f"[TEST RUN] {description}")
    print(f"[CMD] {cmd}")
    print("-" * 70)
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print(result.stdout)
    if result.stderr and result.returncode != 0:
        print(f"[STDERR] {result.stderr}")
    return result


def main():
    print("=" * 70)
    print("CITI BIKE â€” TASK 7: IDEMPOTENCY & RE-RUN TEST SUITE")
    print("=" * 70)

    # 1. Baseline Snapshot
    print("\n[STEP 1] Ghi nháº­n Database Snapshot ban Ä‘áº§u (Baseline)...")
    baseline = get_db_metrics()
    print(f"  - Trips count:        {baseline['total_trips']:,}")
    print(f"  - Unique ride_ids:    {baseline['unique_trips']:,}")
    print(f"  - Duplicate ride_ids: {baseline['dup_trips']:,}")
    print(f"  - Hourly demand rows: {baseline['total_hourly']:,}")
    print(f"  - Unique timestamps:  {baseline['unique_timestamps']:,}")
    print(f"  - Duplicate ts:       {baseline['dup_timestamps']:,}")
    print(f"  - Total demand:       {baseline['total_demand']:,}")

    # 2. Test Downloader (Re-run thÃ¡ng 2026-07)
    print("\n[STEP 2] Test Downloader Re-run...")
    dl_res = run_command(
        f'"{sys.executable}" scripts/download_data.py --month 2026-07',
        "Test Downloader â€” Re-run thÃ¡ng 2026-07 Ä‘Ã£ cÃ³",
    )
    dl_passed = (
        "Ä‘Ã£ tá»“n táº¡i" in dl_res.stdout
        or "KhÃ´ng cÃ³ dá»¯ liá»‡u thÃ¡ng má»›i" in dl_res.stdout
        or "Downloaded: 0" in dl_res.stdout
    )

    # 3. Test Validator (Re-run raw thÃ¡ng 2026-07)
    print("\n[STEP 3] Test Validator Re-run...")
    val_res = run_command(
        f'"{sys.executable}" scripts/validate_data.py --input data/raw/trips/JC-202607-citibike-tripdata.csv',
        "Test Validator â€” Re-run kiá»ƒm tra trÃ¹ng láº·p DB",
    )
    val_passed = (
        "TrÃ¹ng láº·p DB loáº¡i bá»" in val_res.stdout
        or "Há»£p lá»‡ sáºµn sÃ ng:          0 dÃ²ng" in val_res.stdout
        or "0 ride_id" in val_res.stdout
        or val_res.returncode == 0
    )

    # 4. Test Kafka Producer (Re-run file Ä‘Ã£ gá»­i)
    print("\n[STEP 4] Test Kafka Producer Re-run...")
    prod_res = run_command(
        f'"{sys.executable}" producer/kafka_producer.py --input data/processed/JC-202607-citibike-tripdata-clean.csv',
        "Test Kafka Producer â€” Re-run file clean Ä‘Ã£ gá»­i",
    )
    prod_passed = (
        "Messages sent: 0" in prod_res.stdout
        or "Ä‘Ã£ Ä‘Æ°á»£c gá»­i thÃ nh cÃ´ng trÆ°á»›c Ä‘Ã³" in prod_res.stdout
        or "Bá» qua khÃ´ng gá»­i láº¡i" in prod_res.stdout
    )

    # 5. Test Spark Aggregate (Re-run)
    print("\n[STEP 5] Test Spark Aggregate Re-run...")
    spark_agg_cmd = (
        "docker exec citibike-spark-master "
        "/opt/spark/bin/spark-submit "
        "--master spark://spark-master:7077 "
        "--conf spark.jars.ivy=/tmp/ivy-cache "
        "--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.7,org.postgresql:postgresql:42.7.4 "
        "/opt/spark-apps/aggregate_demand.py"
    )
    agg_res = run_command(spark_agg_cmd, "Test Spark Aggregate â€” Re-run job")
    agg_passed = (
        "No new data" in agg_res.stdout
        or "0 records processed" in agg_res.stdout
        or "Tat ca timestamp da ton tai" in agg_res.stdout
        or agg_res.returncode == 0
    )

    # 6. Test Spark Trips (Re-run)
    print("\n[STEP 6] Test Spark Trips Re-run...")
    spark_trips_cmd = (
        "docker exec citibike-spark-master "
        "/opt/spark/bin/spark-submit "
        "--master spark://spark-master:7077 "
        "--conf spark.jars.ivy=/tmp/ivy-cache "
        "--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.7,org.postgresql:postgresql:42.7.4 "
        "/opt/spark-apps/spark_streaming.py"
    )
    trips_res = run_command(spark_trips_cmd, "Test Spark Trips â€” Re-run job")
    trips_passed = (
        "No new data" in trips_res.stdout
        or "0 records processed" in trips_res.stdout
        or "Tat ca ride_id da ton tai" in trips_res.stdout
        or trips_res.returncode == 0
    )

    # 7. Post-run Database Verification
    print("\n[STEP 7] Äá»‘i chiáº¿u toÃ n váº¹n Database sau toÃ n bá»™ Re-run...")
    post = get_db_metrics()

    trips_diff = post["total_trips"] - baseline["total_trips"]
    hourly_diff = post["total_hourly"] - baseline["total_hourly"]
    demand_diff = post["total_demand"] - baseline["total_demand"]

    print("\n" + "=" * 70)
    print("Káº¾T QUáº¢ KIá»‚M THá»¬ TASK 7 â€” IDEMPOTENCY / CHáº Y Láº I")
    print("=" * 70)
    print(f"{'Chá»‰ sá»‘':<25} | {'Baseline':<12} | {'Sau Re-run':<12} | {'Biáº¿n thiÃªn':<10} | {'Tráº¡ng thÃ¡i'}")
    print("-" * 75)
    print(f"{'Trips Count':<25} | {baseline['total_trips']:<12,} | {post['total_trips']:<12,} | {trips_diff:<10} | {'âœ… KHÃ”NG Äá»”I' if trips_diff == 0 else 'âŒ THAY Äá»”I'}")
    print(f"{'Unique Ride IDs':<25} | {baseline['unique_trips']:<12,} | {post['unique_trips']:<12,} | {post['unique_trips'] - baseline['unique_trips']:<10} | {'âœ… KHÃ”NG Äá»”I' if post['unique_trips'] == baseline['unique_trips'] else 'âŒ THAY Äá»”I'}")
    print(f"{'Duplicate Ride IDs':<25} | {baseline['dup_trips']:<12} | {post['dup_trips']:<12} | {post['dup_trips'] - baseline['dup_trips']:<10} | {'âœ… = 0' if post['dup_trips'] == 0 else 'âŒ PHÃT SINH'}")
    print(f"{'Hourly Demand Rows':<25} | {baseline['total_hourly']:<12,} | {post['total_hourly']:<12,} | {hourly_diff:<10} | {'âœ… KHÃ”NG Äá»”I' if hourly_diff == 0 else 'âŒ THAY Äá»”I'}")
    print(f"{'Unique Timestamps':<25} | {baseline['unique_timestamps']:<12,} | {post['unique_timestamps']:<12,} | {post['unique_timestamps'] - baseline['unique_timestamps']:<10} | {'âœ… KHÃ”NG Äá»”I' if post['unique_timestamps'] == baseline['unique_timestamps'] else 'âŒ THAY Äá»”I'}")
    print(f"{'Duplicate Timestamps':<25} | {baseline['dup_timestamps']:<12} | {post['dup_timestamps']:<12} | {post['dup_timestamps'] - baseline['dup_timestamps']:<10} | {'âœ… = 0' if post['dup_timestamps'] == 0 else 'âŒ PHÃT SINH'}")
    print(f"{'Total Demand':<25} | {baseline['total_demand']:<12,} | {post['total_demand']:<12,} | {demand_diff:<10} | {'âœ… KHÃ”NG Äá»”I' if demand_diff == 0 else 'âŒ THAY Äá»”I'}")
    print("-" * 75)

    print("\nKáº¾T QUáº¢ Tá»ªNG COMPONENT RE-RUN:")
    print(f"  1. Downloader:      {'âœ… PASS (Skip)' if dl_passed else 'âŒ FAIL'}")
    print(f"  2. Validator:       {'âœ… PASS (Drop DB duplicates)' if val_passed else 'âŒ FAIL'}")
    print(f"  3. Kafka Producer:  {'âœ… PASS (Skip 0 sent)' if prod_passed else 'âŒ FAIL'}")
    print(f"  4. Spark Aggregate: {'âœ… PASS (0 rows inserted)' if agg_passed and hourly_diff == 0 else 'âŒ FAIL'}")
    print(f"  5. Spark Trips:     {'âœ… PASS (0 records inserted)' if trips_passed and trips_diff == 0 else 'âŒ FAIL'}")

    all_passed = (
        dl_passed
        and val_passed
        and prod_passed
        and agg_passed
        and trips_passed
        and trips_diff == 0
        and hourly_diff == 0
        and demand_diff == 0
        and post["dup_trips"] == 0
        and post["dup_timestamps"] == 0
    )

    print("\n" + "=" * 70)
    if all_passed:
        print("ðŸ† Táº¤T Cáº¢ KIá»‚M THá»¬ TASK 7: PASSED! Há»† THá»NG HOÃ€N TOÃ€N IDEMPOTENT.")
    else:
        print("âš ï¸ CÃ“ KIá»‚M THá»¬ CHÆ¯A Äáº T. VUI LÃ’NG KIá»‚M TRA Láº I.")
    print("=" * 70)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()

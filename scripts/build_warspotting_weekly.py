#!/usr/bin/env python3
import csv
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path


INPUT = Path("warspotting_losses.csv")
OUT_DIR = Path("tables")


def parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def week_start(day):
    return day - timedelta(days=day.weekday())


def write_csv(path, fieldnames, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUT_DIR.mkdir(exist_ok=True)

    records = []
    with INPUT.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("date"):
                continue
            row["date"] = parse_date(row["date"])
            row["week_start"] = week_start(row["date"])
            row["type"] = row["type"].strip()
            row["status"] = row["status"].strip()
            row["lost_by"] = row["lost_by"].strip()
            records.append(row)

    if not records:
        raise SystemExit("no dated records found")

    min_date = min(r["date"] for r in records)
    max_date = max(r["date"] for r in records)
    first_week = week_start(min_date)
    last_week = week_start(max_date)

    all_weeks = []
    current = first_week
    while current <= last_week:
        all_weeks.append(current)
        current += timedelta(days=7)

    weekly_total = Counter()
    weekly_type = Counter()
    weekly_status = Counter()
    type_total = Counter()

    for row in records:
        wk = row["week_start"]
        typ = row["type"]
        status = row["status"]
        weekly_total[wk] += 1
        weekly_type[(wk, typ)] += 1
        weekly_status[(wk, status)] += 1
        type_total[typ] += 1

    weekly_rows = []
    for wk in all_weeks:
        end = wk + timedelta(days=6)
        count = weekly_total[wk]
        weekly_rows.append(
            {
                "week_start": wk.isoformat(),
                "week_end": end.isoformat(),
                "loss_count": count,
                "rate_per_day": round(count / 7, 6),
                "rate_per_30_days": round(count / 7 * 30, 6),
            }
        )

    write_csv(
        OUT_DIR / "warspotting_weekly_total.csv",
        ["week_start", "week_end", "loss_count", "rate_per_day", "rate_per_30_days"],
        weekly_rows,
    )

    weekly_type_rows = []
    for wk in all_weeks:
        for typ in sorted(type_total):
            count = weekly_type[(wk, typ)]
            weekly_type_rows.append(
                {
                    "week_start": wk.isoformat(),
                    "type": typ,
                    "loss_count": count,
                    "rate_per_day": round(count / 7, 6),
                    "rate_per_30_days": round(count / 7 * 30, 6),
                }
            )
    write_csv(
        OUT_DIR / "warspotting_weekly_by_type.csv",
        ["week_start", "type", "loss_count", "rate_per_day", "rate_per_30_days"],
        weekly_type_rows,
    )

    weekly_status_rows = []
    statuses = sorted({r["status"] for r in records})
    for wk in all_weeks:
        for status in statuses:
            count = weekly_status[(wk, status)]
            weekly_status_rows.append(
                {
                    "week_start": wk.isoformat(),
                    "status": status,
                    "loss_count": count,
                    "rate_per_day": round(count / 7, 6),
                    "rate_per_30_days": round(count / 7 * 30, 6),
                }
            )
    write_csv(
        OUT_DIR / "warspotting_weekly_by_status.csv",
        ["week_start", "status", "loss_count", "rate_per_day", "rate_per_30_days"],
        weekly_status_rows,
    )

    type_rows = []
    total_count = len(records)
    for typ, count in sorted(type_total.items(), key=lambda item: (-item[1], item[0])):
        type_rows.append(
            {
                "type": typ,
                "loss_count": count,
                "share": round(count / total_count, 6),
            }
        )
    write_csv(OUT_DIR / "warspotting_type_summary.csv", ["type", "loss_count", "share"], type_rows)

    print(f"records: {len(records)}")
    print(f"date range: {min_date} to {max_date}")
    print(f"weeks: {len(all_weeks)}")
    print("wrote tables/warspotting_weekly_total.csv")
    print("wrote tables/warspotting_weekly_by_type.csv")
    print("wrote tables/warspotting_weekly_by_status.csv")
    print("wrote tables/warspotting_type_summary.csv")


if __name__ == "__main__":
    main()

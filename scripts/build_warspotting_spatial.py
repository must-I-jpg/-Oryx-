#!/usr/bin/env python3
import csv
import math
from collections import Counter
from pathlib import Path


INPUT = Path("warspotting_losses.csv")
OUT_DIR = Path("tables")


def parse_float(value):
    try:
        if value == "":
            return None
        return float(value)
    except ValueError:
        return None


def macro_region(lat, lon):
    # Transparent coordinate-based bins, not official administrative regions.
    if lat is None or lon is None:
        return "Missing coordinates"
    if lon >= 36:
        return "East"
    if lon < 28:
        return "West"
    if lat >= 50:
        return "North"
    if lat < 47.5:
        return "South"
    return "Central"


def one_degree_grid(lat, lon):
    if lat is None or lon is None:
        return "Missing coordinates"
    lat_floor = math.floor(lat)
    lon_floor = math.floor(lon)
    return f"lat[{lat_floor},{lat_floor + 1})_lon[{lon_floor},{lon_floor + 1})"


def location_area(value):
    if not value:
        return "Missing location"
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if not parts:
        return "Missing location"
    return parts[-1]


def write_csv(path, fieldnames, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def pct(value, total):
    return round(value / total, 6) if total else ""


def main():
    OUT_DIR.mkdir(exist_ok=True)

    rows = []
    with INPUT.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lat = parse_float(row.get("latitude", ""))
            lon = parse_float(row.get("longitude", ""))
            has_coords = lat is not None and lon is not None
            rows.append(
                {
                    "id": row["id"],
                    "date": row["date"],
                    "type": row["type"].strip(),
                    "status": row["status"].strip(),
                    "nearest_location": row["nearest_location"].strip(),
                    "location_area": location_area(row["nearest_location"]),
                    "latitude": lat,
                    "longitude": lon,
                    "has_coordinates": has_coords,
                    "macro_region": macro_region(lat, lon),
                    "grid_1deg": one_degree_grid(lat, lon),
                }
            )

    total = len(rows)
    with_coords = sum(1 for row in rows if row["has_coordinates"])
    with_location = sum(1 for row in rows if row["nearest_location"])

    quality = [
        {
            "total_records": total,
            "records_with_coordinates": with_coords,
            "records_missing_coordinates": total - with_coords,
            "coordinate_coverage": pct(with_coords, total),
            "records_with_nearest_location": with_location,
            "nearest_location_coverage": pct(with_location, total),
        }
    ]
    write_csv(
        OUT_DIR / "warspotting_coordinate_quality.csv",
        list(quality[0].keys()),
        quality,
    )

    region_counter = Counter(row["macro_region"] for row in rows)
    region_rows = []
    for region, count in sorted(region_counter.items(), key=lambda item: (-item[1], item[0])):
        region_rows.append(
            {
                "macro_region": region,
                "loss_count": count,
                "share_all_records": pct(count, total),
                "share_coordinate_records": pct(count, with_coords)
                if region != "Missing coordinates"
                else "",
            }
        )
    write_csv(
        OUT_DIR / "warspotting_spatial_macro_region_summary.csv",
        ["macro_region", "loss_count", "share_all_records", "share_coordinate_records"],
        region_rows,
    )

    region_type_counter = Counter((row["macro_region"], row["type"]) for row in rows)
    region_type_rows = []
    for (region, typ), count in sorted(region_type_counter.items(), key=lambda item: (item[0][0], -item[1], item[0][1])):
        region_type_rows.append(
            {
                "macro_region": region,
                "type": typ,
                "loss_count": count,
                "share_within_region": pct(count, region_counter[region]),
            }
        )
    write_csv(
        OUT_DIR / "warspotting_spatial_macro_region_by_type.csv",
        ["macro_region", "type", "loss_count", "share_within_region"],
        region_type_rows,
    )

    grid_counter = Counter(row["grid_1deg"] for row in rows)
    grid_rows = []
    for grid, count in sorted(grid_counter.items(), key=lambda item: (-item[1], item[0])):
        if grid == "Missing coordinates":
            continue
        grid_members = [row for row in rows if row["grid_1deg"] == grid]
        common_area = Counter(row["location_area"] for row in grid_members).most_common(1)[0][0]
        grid_rows.append(
            {
                "grid_1deg": grid,
                "loss_count": count,
                "share_coordinate_records": pct(count, with_coords),
                "most_common_location_area": common_area,
            }
        )
    write_csv(
        OUT_DIR / "warspotting_spatial_grid_1deg_summary.csv",
        ["grid_1deg", "loss_count", "share_coordinate_records", "most_common_location_area"],
        grid_rows,
    )

    area_counter = Counter(row["location_area"] for row in rows)
    area_rows = []
    for area, count in sorted(area_counter.items(), key=lambda item: (-item[1], item[0])):
        area_rows.append(
            {
                "location_area": area,
                "loss_count": count,
                "share_all_records": pct(count, total),
            }
        )
    write_csv(
        OUT_DIR / "warspotting_location_area_summary.csv",
        ["location_area", "loss_count", "share_all_records"],
        area_rows,
    )

    print(f"records: {total}")
    print(f"coordinate coverage: {with_coords}/{total} ({with_coords / total:.3%})")
    print("wrote tables/warspotting_coordinate_quality.csv")
    print("wrote tables/warspotting_spatial_macro_region_summary.csv")
    print("wrote tables/warspotting_spatial_macro_region_by_type.csv")
    print("wrote tables/warspotting_spatial_grid_1deg_summary.csv")
    print("wrote tables/warspotting_location_area_summary.csv")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import csv
from pathlib import Path


INPUT = Path("tables/category_comparison_russia_ukraine.csv")
OUT_DIR = Path("tables")
EXPOSURE_DAYS = 1555

# Sensitivity grid for observation probabilities.
# Values are assumptions, not estimates from the data.
RUSSIA_OBS_PROBS = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
UKRAINE_OBS_PROBS = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]


def write_csv(path, fieldnames, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sensitivity_rows(category, russia_count, ukraine_count):
    rows = []
    observed_rr = russia_count / ukraine_count if ukraine_count else ""
    for p_russia in RUSSIA_OBS_PROBS:
        for p_ukraine in UKRAINE_OBS_PROBS:
            corrected_russia_count = russia_count / p_russia if p_russia else ""
            corrected_ukraine_count = ukraine_count / p_ukraine if p_ukraine else ""
            corrected_rr = (
                (corrected_russia_count / corrected_ukraine_count)
                if corrected_ukraine_count
                else ""
            )
            rows.append(
                {
                    "category": category,
                    "russia_observed_count": russia_count,
                    "ukraine_observed_count": ukraine_count,
                    "observed_rate_ratio": round(observed_rr, 6) if observed_rr != "" else "",
                    "p_observed_russia_assumed": p_russia,
                    "p_observed_ukraine_assumed": p_ukraine,
                    "corrected_russia_count": round(corrected_russia_count, 6),
                    "corrected_ukraine_count": round(corrected_ukraine_count, 6),
                    "corrected_russia_rate_per_day": round(corrected_russia_count / EXPOSURE_DAYS, 6),
                    "corrected_ukraine_rate_per_day": round(corrected_ukraine_count / EXPOSURE_DAYS, 6),
                    "corrected_rate_ratio": round(corrected_rr, 6) if corrected_rr != "" else "",
                    "rr_still_above_1": bool(corrected_rr != "" and corrected_rr > 1),
                }
            )
    return rows


def main():
    OUT_DIR.mkdir(exist_ok=True)
    category_rows = []
    total_russia = 0
    total_ukraine = 0

    with INPUT.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            russia_count = int(row["russia_item_count"])
            ukraine_count = int(row["ukraine_item_count"])
            total_russia += russia_count
            total_ukraine += ukraine_count
            category_rows.extend(sensitivity_rows(row["category"], russia_count, ukraine_count))

    overall_rows = sensitivity_rows("All categories", total_russia, total_ukraine)

    fields = [
        "category",
        "russia_observed_count",
        "ukraine_observed_count",
        "observed_rate_ratio",
        "p_observed_russia_assumed",
        "p_observed_ukraine_assumed",
        "corrected_russia_count",
        "corrected_ukraine_count",
        "corrected_russia_rate_per_day",
        "corrected_ukraine_rate_per_day",
        "corrected_rate_ratio",
        "rr_still_above_1",
    ]
    write_csv(OUT_DIR / "observation_probability_sensitivity_overall.csv", fields, overall_rows)
    write_csv(OUT_DIR / "observation_probability_sensitivity_by_category.csv", fields, category_rows)

    print(f"overall observed Russia count: {total_russia}")
    print(f"overall observed Ukraine count: {total_ukraine}")
    print("wrote tables/observation_probability_sensitivity_overall.csv")
    print("wrote tables/observation_probability_sensitivity_by_category.csv")


if __name__ == "__main__":
    main()

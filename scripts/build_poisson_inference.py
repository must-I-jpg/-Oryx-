#!/usr/bin/env python3
import csv
import math
from datetime import date
from pathlib import Path

from scipy.stats import binomtest, chi2, norm


INPUT = Path("tables/category_comparison_russia_ukraine.csv")
OUT_DIR = Path("tables")
START_DATE = date(2022, 2, 24)
END_DATE = date(2026, 5, 28)
ALPHA = 0.05


def poisson_exact_rate_ci(count, exposure, alpha=ALPHA):
    if count == 0:
        lower = 0.0
    else:
        lower = 0.5 * chi2.ppf(alpha / 2, 2 * count) / exposure
    upper = 0.5 * chi2.ppf(1 - alpha / 2, 2 * (count + 1)) / exposure
    return lower, upper


def poisson_wald_rate_ci(count, exposure, alpha=ALPHA):
    rate = count / exposure
    z = norm.ppf(1 - alpha / 2)
    se = math.sqrt(count) / exposure if count > 0 else 0.0
    return max(0.0, rate - z * se), rate + z * se


def poisson_score_rate_ci(count, exposure, alpha=ALPHA):
    z = norm.ppf(1 - alpha / 2)
    center = count + (z**2) / 2
    half_width = z * math.sqrt(count + (z**2) / 4)
    lower = max(0.0, center - half_width) / exposure
    upper = (center + half_width) / exposure
    return lower, upper


def rate_ratio_ci(count1, exposure1, count2, exposure2, alpha=ALPHA):
    if count1 == 0 or count2 == 0:
        return "", "", ""
    rr = (count1 / exposure1) / (count2 / exposure2)
    z = norm.ppf(1 - alpha / 2)
    se_log = math.sqrt(1 / count1 + 1 / count2)
    lower = math.exp(math.log(rr) - z * se_log)
    upper = math.exp(math.log(rr) + z * se_log)
    return rr, lower, upper


def conditional_poisson_pvalue(count1, count2, exposure1, exposure2):
    total = count1 + count2
    if total == 0:
        return ""
    p = exposure1 / (exposure1 + exposure2)
    return binomtest(count1, total, p=p, alternative="two-sided").pvalue


def fmt(x, digits=6):
    if x == "":
        return ""
    return round(float(x), digits)


def inference_row(label, russia_count, ukraine_count, exposure_days):
    r_rate = russia_count / exposure_days
    u_rate = ukraine_count / exposure_days
    r_exact = poisson_exact_rate_ci(russia_count, exposure_days)
    u_exact = poisson_exact_rate_ci(ukraine_count, exposure_days)
    r_wald = poisson_wald_rate_ci(russia_count, exposure_days)
    u_wald = poisson_wald_rate_ci(ukraine_count, exposure_days)
    r_score = poisson_score_rate_ci(russia_count, exposure_days)
    u_score = poisson_score_rate_ci(ukraine_count, exposure_days)
    rr, rr_low, rr_high = rate_ratio_ci(russia_count, exposure_days, ukraine_count, exposure_days)
    p_value = conditional_poisson_pvalue(russia_count, ukraine_count, exposure_days, exposure_days)

    return {
        "category": label,
        "exposure_days": exposure_days,
        "russia_count": russia_count,
        "ukraine_count": ukraine_count,
        "russia_rate_per_day": fmt(r_rate),
        "ukraine_rate_per_day": fmt(u_rate),
        "russia_rate_per_30_days": fmt(r_rate * 30),
        "ukraine_rate_per_30_days": fmt(u_rate * 30),
        "russia_exact_ci_low_per_day": fmt(r_exact[0]),
        "russia_exact_ci_high_per_day": fmt(r_exact[1]),
        "ukraine_exact_ci_low_per_day": fmt(u_exact[0]),
        "ukraine_exact_ci_high_per_day": fmt(u_exact[1]),
        "russia_wald_ci_low_per_day": fmt(r_wald[0]),
        "russia_wald_ci_high_per_day": fmt(r_wald[1]),
        "ukraine_wald_ci_low_per_day": fmt(u_wald[0]),
        "ukraine_wald_ci_high_per_day": fmt(u_wald[1]),
        "russia_score_ci_low_per_day": fmt(r_score[0]),
        "russia_score_ci_high_per_day": fmt(r_score[1]),
        "ukraine_score_ci_low_per_day": fmt(u_score[0]),
        "ukraine_score_ci_high_per_day": fmt(u_score[1]),
        "rate_ratio_russia_over_ukraine": fmt(rr),
        "rate_ratio_ci_low": fmt(rr_low),
        "rate_ratio_ci_high": fmt(rr_high),
        "conditional_poisson_p_value": fmt(p_value, 10),
        "significant_0_05": bool(p_value != "" and p_value < ALPHA),
    }


def write_csv(path, rows):
    fieldnames = [
        "category",
        "exposure_days",
        "russia_count",
        "ukraine_count",
        "russia_rate_per_day",
        "ukraine_rate_per_day",
        "russia_rate_per_30_days",
        "ukraine_rate_per_30_days",
        "russia_exact_ci_low_per_day",
        "russia_exact_ci_high_per_day",
        "ukraine_exact_ci_low_per_day",
        "ukraine_exact_ci_high_per_day",
        "russia_wald_ci_low_per_day",
        "russia_wald_ci_high_per_day",
        "ukraine_wald_ci_low_per_day",
        "ukraine_wald_ci_high_per_day",
        "russia_score_ci_low_per_day",
        "russia_score_ci_high_per_day",
        "ukraine_score_ci_low_per_day",
        "ukraine_score_ci_high_per_day",
        "rate_ratio_russia_over_ukraine",
        "rate_ratio_ci_low",
        "rate_ratio_ci_high",
        "conditional_poisson_p_value",
        "significant_0_05",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    exposure_days = (END_DATE - START_DATE).days + 1
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
            category_rows.append(
                inference_row(row["category"], russia_count, ukraine_count, exposure_days)
            )

    category_rows.sort(key=lambda x: int(x["russia_count"]) + int(x["ukraine_count"]), reverse=True)
    total_row = inference_row("All categories", total_russia, total_ukraine, exposure_days)

    write_csv(OUT_DIR / "poisson_inference_by_category.csv", category_rows)
    write_csv(OUT_DIR / "poisson_inference_overall.csv", [total_row])

    print(f"exposure_days: {exposure_days}")
    print(f"overall Russia count: {total_russia}")
    print(f"overall Ukraine count: {total_ukraine}")
    print("wrote tables/poisson_inference_by_category.csv")
    print("wrote tables/poisson_inference_overall.csv")


if __name__ == "__main__":
    main()

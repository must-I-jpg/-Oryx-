#!/usr/bin/env python3
import csv
import math
import random
from pathlib import Path


INPUT = Path("tables/warspotting_weekly_total.csv")
OUT_DIR = Path("tables")
BOOTSTRAP_REPS = 10000
SEED = 20260528
ALPHA = 0.05


def read_weekly_counts():
    rows = []
    with INPUT.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                {
                    "week_start": row["week_start"],
                    "week_end": row["week_end"],
                    "loss_count": int(row["loss_count"]),
                }
            )
    return rows


def statistic(counts):
    return sum(counts) / (7 * len(counts))


def normal_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def normal_ppf(p):
    # Peter J. Acklam's inverse-normal approximation.
    if not 0 < p < 1:
        raise ValueError("p must be in (0, 1)")

    a = [
        -3.969683028665376e01,
        2.209460984245205e02,
        -2.759285104469687e02,
        1.383577518672690e02,
        -3.066479806614716e01,
        2.506628277459239e00,
    ]
    b = [
        -5.447609879822406e01,
        1.615858368580409e02,
        -1.556989798598866e02,
        6.680131188771972e01,
        -1.328068155288572e01,
    ]
    c = [
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e00,
        -2.549732539343734e00,
        4.374664141464968e00,
        2.938163982698783e00,
    ]
    d = [
        7.784695709041462e-03,
        3.224671290700398e-01,
        2.445134137142996e00,
        3.754408661907416e00,
    ]

    plow = 0.02425
    phigh = 1 - plow
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (
            (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
            / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
        )
    if p <= phigh:
        q = p - 0.5
        r = q * q
        return (
            (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5])
            * q
            / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
        )

    q = math.sqrt(-2 * math.log(1 - p))
    return -(
        (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
        / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    )


def quantile(values, prob):
    ordered = sorted(values)
    if prob <= 0:
        return ordered[0]
    if prob >= 1:
        return ordered[-1]
    pos = prob * (len(ordered) - 1)
    lower = math.floor(pos)
    upper = math.ceil(pos)
    if lower == upper:
        return ordered[lower]
    weight = pos - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def mean(values):
    return sum(values) / len(values)


def sample_sd(values):
    avg = mean(values)
    return math.sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1))


def bca_interval(theta_hat, boot_stats, jack_stats, alpha=ALPHA):
    prop_less = sum(1 for value in boot_stats if value < theta_hat) / len(boot_stats)
    eps = 1 / (2 * len(boot_stats))
    prop_less = min(max(prop_less, eps), 1 - eps)
    z0 = normal_ppf(prop_less)

    jack_mean = mean(jack_stats)
    diffs = [jack_mean - value for value in jack_stats]
    numerator = sum(value**3 for value in diffs)
    denominator = 6 * (sum(value**2 for value in diffs) ** 1.5)
    acceleration = 0.0 if denominator == 0 else numerator / denominator

    def adjusted_quantile(prob):
        z = normal_ppf(prob)
        adjusted = normal_cdf(z0 + (z0 + z) / (1 - acceleration * (z0 + z)))
        return min(max(adjusted, 0.0), 1.0)

    q_low = adjusted_quantile(alpha / 2)
    q_high = adjusted_quantile(1 - alpha / 2)
    return (
        quantile(boot_stats, q_low),
        quantile(boot_stats, q_high),
        z0,
        acceleration,
        q_low,
        q_high,
    )


def write_csv(path, fieldnames, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUT_DIR.mkdir(exist_ok=True)
    weekly_rows = read_weekly_counts()
    counts = [row["loss_count"] for row in weekly_rows]
    n_weeks = len(counts)

    rng = random.Random(SEED)
    boot_rate_per_day = []
    for _ in range(BOOTSTRAP_REPS):
        total = sum(counts[rng.randrange(n_weeks)] for _ in range(n_weeks))
        boot_rate_per_day.append(total / (7 * n_weeks))

    theta_hat = statistic(counts)
    percentile_low = quantile(boot_rate_per_day, ALPHA / 2)
    percentile_high = quantile(boot_rate_per_day, 1 - ALPHA / 2)

    jack_stats = [statistic(counts[:i] + counts[i + 1 :]) for i in range(n_weeks)]
    bca_low, bca_high, z0, acceleration, q_low, q_high = bca_interval(
        theta_hat, boot_rate_per_day, jack_stats
    )

    summary = [
        {
            "statistic": "weekly_block_bootstrap_rate_per_day",
            "source": str(INPUT),
            "n_weeks": n_weeks,
            "bootstrap_reps": BOOTSTRAP_REPS,
            "seed": SEED,
            "theta_hat_rate_per_day": round(theta_hat, 6),
            "theta_hat_rate_per_30_days": round(theta_hat * 30, 6),
            "bootstrap_mean_rate_per_day": round(mean(boot_rate_per_day), 6),
            "bootstrap_sd_rate_per_day": round(sample_sd(boot_rate_per_day), 6),
            "percentile_ci_low_per_day": round(percentile_low, 6),
            "percentile_ci_high_per_day": round(percentile_high, 6),
            "bca_ci_low_per_day": round(bca_low, 6),
            "bca_ci_high_per_day": round(bca_high, 6),
            "bca_z0": round(z0, 6),
            "bca_acceleration": round(acceleration, 6),
            "bca_adjusted_quantile_low": round(q_low, 6),
            "bca_adjusted_quantile_high": round(q_high, 6),
        }
    ]
    write_csv(
        OUT_DIR / "warspotting_weekly_block_bootstrap_bca.csv",
        list(summary[0].keys()),
        summary,
    )

    distribution_rows = [
        {
            "replicate": i + 1,
            "rate_per_day": round(value, 6),
            "rate_per_30_days": round(value * 30, 6),
        }
        for i, value in enumerate(boot_rate_per_day)
    ]
    write_csv(
        OUT_DIR / "warspotting_weekly_bootstrap_distribution.csv",
        ["replicate", "rate_per_day", "rate_per_30_days"],
        distribution_rows,
    )

    jack_rows = [
        {
            "omitted_week_start": weekly_rows[i]["week_start"],
            "omitted_week_end": weekly_rows[i]["week_end"],
            "omitted_loss_count": counts[i],
            "jackknife_rate_per_day": round(jack_stats[i], 6),
        }
        for i in range(n_weeks)
    ]
    write_csv(
        OUT_DIR / "warspotting_weekly_jackknife_rates.csv",
        ["omitted_week_start", "omitted_week_end", "omitted_loss_count", "jackknife_rate_per_day"],
        jack_rows,
    )

    print(f"n_weeks: {n_weeks}")
    print(f"theta_hat_rate_per_day: {theta_hat:.6f}")
    print(f"percentile_ci: [{percentile_low:.6f}, {percentile_high:.6f}]")
    print(f"bca_ci: [{bca_low:.6f}, {bca_high:.6f}]")
    print("wrote tables/warspotting_weekly_block_bootstrap_bca.csv")
    print("wrote tables/warspotting_weekly_bootstrap_distribution.csv")
    print("wrote tables/warspotting_weekly_jackknife_rates.csv")


if __name__ == "__main__":
    main()

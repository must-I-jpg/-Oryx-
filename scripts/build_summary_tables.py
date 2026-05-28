#!/usr/bin/env python3
import csv
from collections import Counter, defaultdict
from pathlib import Path


INPUT = Path("oryx_losses_combined.csv")
OUT_DIR = Path("tables")

CATEGORY_ALIASES = {
    "Radars": "Radars And Communications Equipment",
    "Radars And Communications Equipment": "Radars And Communications Equipment",
    "Naval Ships": "Naval Ships and Submarines",
    "Naval Ships and Submarines": "Naval Ships and Submarines",
}


def normalize_category(category):
    return CATEGORY_ALIASES.get(category, category)


def read_rows():
    with INPUT.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["item_count"] = int(row["item_count"] or 0)
            row["side"] = row["side"].strip()
            row["original_category"] = row["category"].strip()
            row["category"] = normalize_category(row["original_category"])
            row["model"] = row["model"].strip()
            row["status"] = row["status"].strip()
            yield row


def write_csv(path, fieldnames, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def pct(value, total):
    return round(value / total, 6) if total else ""


def ratio(num, den):
    return round(num / den, 6) if den else ""


def main():
    OUT_DIR.mkdir(exist_ok=True)
    rows = list(read_rows())

    total_items = sum(r["item_count"] for r in rows)
    total_evidence_rows = len(rows)

    # Cleaned detail table: keep only analysis-ready fields.
    cleaned_fields = [
        "side",
        "category",
        "original_category",
        "model",
        "status",
        "status_raw",
        "item_count",
        "evidence_url",
        "source_url",
        "source_sequence",
    ]
    write_csv(
        OUT_DIR / "cleaned_oryx_loss_records.csv",
        cleaned_fields,
        [{k: r[k] for k in cleaned_fields} for r in rows],
    )

    side_items = Counter()
    side_evidence = Counter()
    side_category_items = Counter()
    side_category_evidence = Counter()
    side_status_items = Counter()
    side_status_evidence = Counter()
    side_category_status_items = Counter()
    model_items = Counter()
    model_evidence = Counter()

    for r in rows:
        side = r["side"]
        category = r["category"]
        status = r["status"]
        model = r["model"]
        n = r["item_count"]

        side_items[side] += n
        side_evidence[side] += 1
        side_category_items[(side, category)] += n
        side_category_evidence[(side, category)] += 1
        side_status_items[(side, status)] += n
        side_status_evidence[(side, status)] += 1
        side_category_status_items[(side, category, status)] += n
        model_items[(side, category, model)] += n
        model_evidence[(side, category, model)] += 1

    by_side = []
    for side in sorted(side_items):
        by_side.append(
            {
                "side": side,
                "evidence_rows": side_evidence[side],
                "item_count": side_items[side],
                "share_of_all_items": pct(side_items[side], total_items),
                "share_of_all_evidence_rows": pct(side_evidence[side], total_evidence_rows),
            }
        )
    write_csv(
        OUT_DIR / "summary_by_side.csv",
        ["side", "evidence_rows", "item_count", "share_of_all_items", "share_of_all_evidence_rows"],
        by_side,
    )

    by_category = []
    side_totals = dict(side_items)
    for (side, category), n in sorted(side_category_items.items()):
        by_category.append(
            {
                "side": side,
                "category": category,
                "evidence_rows": side_category_evidence[(side, category)],
                "item_count": n,
                "share_within_side": pct(n, side_totals[side]),
            }
        )
    write_csv(
        OUT_DIR / "summary_by_side_category.csv",
        ["side", "category", "evidence_rows", "item_count", "share_within_side"],
        by_category,
    )

    by_status = []
    for (side, status), n in sorted(side_status_items.items()):
        by_status.append(
            {
                "side": side,
                "status": status,
                "evidence_rows": side_status_evidence[(side, status)],
                "item_count": n,
                "share_within_side": pct(n, side_totals[side]),
            }
        )
    write_csv(
        OUT_DIR / "summary_by_side_status.csv",
        ["side", "status", "evidence_rows", "item_count", "share_within_side"],
        by_status,
    )

    by_category_status = []
    category_totals = dict(side_category_items)
    for (side, category, status), n in sorted(side_category_status_items.items()):
        by_category_status.append(
            {
                "side": side,
                "category": category,
                "status": status,
                "item_count": n,
                "share_within_side_category": pct(n, category_totals[(side, category)]),
            }
        )
    write_csv(
        OUT_DIR / "summary_by_side_category_status.csv",
        ["side", "category", "status", "item_count", "share_within_side_category"],
        by_category_status,
    )

    categories = sorted({category for _, category in side_category_items})
    comparison = []
    for category in categories:
        russia = side_category_items.get(("Russia", category), 0)
        ukraine = side_category_items.get(("Ukraine", category), 0)
        total = russia + ukraine
        comparison.append(
            {
                "category": category,
                "russia_item_count": russia,
                "ukraine_item_count": ukraine,
                "combined_item_count": total,
                "russia_share_in_category": pct(russia, total),
                "ukraine_share_in_category": pct(ukraine, total),
                "russia_to_ukraine_count_ratio": ratio(russia, ukraine),
                "russia_share_within_side": pct(russia, side_totals.get("Russia", 0)),
                "ukraine_share_within_side": pct(ukraine, side_totals.get("Ukraine", 0)),
            }
        )
    comparison.sort(key=lambda x: x["combined_item_count"], reverse=True)
    write_csv(
        OUT_DIR / "category_comparison_russia_ukraine.csv",
        [
            "category",
            "russia_item_count",
            "ukraine_item_count",
            "combined_item_count",
            "russia_share_in_category",
            "ukraine_share_in_category",
            "russia_to_ukraine_count_ratio",
            "russia_share_within_side",
            "ukraine_share_within_side",
        ],
        comparison,
    )

    model_rows = []
    for (side, category, model), n in sorted(model_items.items(), key=lambda x: (-x[1], x[0])):
        model_rows.append(
            {
                "side": side,
                "category": category,
                "model": model,
                "evidence_rows": model_evidence[(side, category, model)],
                "item_count": n,
                "share_within_side_category": pct(n, category_totals[(side, category)]),
            }
        )
    write_csv(
        OUT_DIR / "summary_by_side_category_model.csv",
        ["side", "category", "model", "evidence_rows", "item_count", "share_within_side_category"],
        model_rows,
    )

    print(f"source rows: {len(rows)}")
    print(f"source item_count total: {total_items}")
    print(f"wrote tables to {OUT_DIR}")


if __name__ == "__main__":
    main()

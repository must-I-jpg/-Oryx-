#!/usr/bin/env python3
import argparse
import csv
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


SOURCES = {
    "Russia": {
        "url": "https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-equipment.html",
        "html": "oryx_russia.html",
    },
    "Ukraine": {
        "url": "https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-ukrainian.html",
        "html": "oryx_ukraine.html",
    },
}

STATUSES = ("destroyed", "damaged", "abandoned", "captured")


def fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def clean_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_category(h3) -> tuple[str, int | None]:
    text = clean_space(h3.get_text(" ", strip=True))
    match = re.match(r"^(?P<name>.+?)\s*\((?P<count>\d+)(?:,|\))", text)
    if match:
        return match.group("name").strip(), int(match.group("count"))
    text = re.sub(r"\s*\([^)]*of which[^)]*\)\s*$", "", text, flags=re.I)
    match = re.match(r"^(?P<name>.+?)\s*\((?P<count>\d+)\)\s*$", text)
    if match:
        return match.group("name").strip(), int(match.group("count"))
    return text.strip(), None


def parse_model(summary) -> tuple[str, int | None]:
    for img in summary.find_all("img"):
        img.extract()
    text = clean_space(summary.get_text(" ", strip=True)).rstrip(":")
    match = re.match(r"^(?P<count>\d+)\s+(?P<model>.+)$", text)
    if match:
        return match.group("model").strip(), int(match.group("count"))
    return text.strip(), None


def infer_item_count(label: str) -> int:
    first_part = label.strip("() ").split(",", 1)[0].lower()
    numbers = [int(n) for n in re.findall(r"\d+", first_part)]
    if re.search(r"\bto\b|-", first_part) and len(numbers) >= 2:
        start, end = numbers[0], numbers[1]
        if end >= start:
            return end - start + 1
    if re.search(r"\band\b|&|\+", first_part) and numbers:
        return len(numbers)
    return 1


def parse_status(label: str) -> tuple[str, str]:
    lowered = label.lower()
    present = [status for status in STATUSES if status in lowered]
    if not present:
        return "", clean_space(label.strip("() "))
    return "+".join(present), clean_space(label.strip("() "))


def parse_page(side: str, html: str, source_url: str) -> list[dict[str, str | int]]:
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    sequence = 0

    for h3 in soup.find_all("h3"):
        ul = h3.find_next_sibling("ul", class_="collapsible")
        if ul is None:
            continue

        category, category_total = parse_category(h3)
        if not category or "losses of " in category.lower():
            continue

        for details in ul.find_all("details"):
            summary = details.find("summary")
            if summary is None:
                continue
            model, model_total = parse_model(summary)

            for link in details.find_all("a"):
                label = clean_space(link.get_text(" ", strip=True))
                if not label.startswith("("):
                    continue
                status, status_raw = parse_status(label)
                if not status:
                    continue
                sequence += 1
                rows.append(
                    {
                        "side": side,
                        "category": category,
                        "category_total_reported": category_total or "",
                        "model": model,
                        "model_total_reported": model_total or "",
                        "status": status,
                        "status_raw": status_raw,
                        "item_count": infer_item_count(label),
                        "evidence_text": label,
                        "evidence_url": link.get("href", ""),
                        "source_url": source_url,
                        "source_sequence": sequence,
                    }
                )

    return rows


def write_csv(path: Path, rows: list[dict[str, str | int]]) -> None:
    fieldnames = [
        "side",
        "category",
        "category_total_reported",
        "model",
        "model_total_reported",
        "status",
        "status_raw",
        "item_count",
        "evidence_text",
        "evidence_url",
        "source_url",
        "source_sequence",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="oryx_losses_combined.csv")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    all_rows = []
    for side, config in SOURCES.items():
        html_path = Path(config["html"])
        if args.refresh or not html_path.exists():
            html_path.write_text(fetch(config["url"]), encoding="utf-8")
        html = html_path.read_text(encoding="utf-8", errors="replace")
        all_rows.extend(parse_page(side, html, config["url"]))

    write_csv(Path(args.out), all_rows)
    print(f"wrote {len(all_rows)} evidence rows to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
import csv
from pathlib import Path


INPUT = Path("tables/observation_probability_sensitivity_overall.csv")
OUT = Path("tables/observation_probability_sensitivity_heatmap.svg")


def read_rows():
    with INPUT.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def color_for(value, min_value, max_value):
    if max_value == min_value:
        t = 0.5
    else:
        t = (value - min_value) / (max_value - min_value)
    # Light blue -> white -> red, centered roughly around RR=1 when possible.
    if value < 1:
        local = max(0.0, min(1.0, value / 1.0))
        r = int(69 + (245 - 69) * local)
        g = int(117 + (245 - 117) * local)
        b = int(180 + (245 - 180) * local)
    else:
        local = max(0.0, min(1.0, (value - 1) / (max_value - 1)))
        r = int(245 + (178 - 245) * local)
        g = int(245 + (24 - 245) * local)
        b = int(245 + (43 - 245) * local)
    return f"#{r:02x}{g:02x}{b:02x}"


def main():
    rows = read_rows()
    p_r_values = sorted({float(r["p_observed_russia_assumed"]) for r in rows})
    p_u_values = sorted({float(r["p_observed_ukraine_assumed"]) for r in rows}, reverse=True)
    values = {
        (
            float(r["p_observed_russia_assumed"]),
            float(r["p_observed_ukraine_assumed"]),
        ): float(r["corrected_rate_ratio"])
        for r in rows
    }

    observed_rr = float(rows[0]["observed_rate_ratio"])
    reversal_boundary = 1 / observed_rr
    min_rr = min(values.values())
    max_rr = max(values.values())

    cell = 78
    left = 120
    top = 95
    width = left + cell * len(p_r_values) + 260
    height = top + cell * len(p_u_values) + 115

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="30" y="36" font-family="Arial, sans-serif" font-size="22" font-weight="700">Observation Probability Sensitivity Heatmap</text>',
        f'<text x="30" y="64" font-family="Arial, sans-serif" font-size="14" fill="#444">Corrected Russia/Ukraine rate ratio; reversal boundary p_U / p_R = 1 / {observed_rr:.6f} ≈ {reversal_boundary:.3f}</text>',
    ]

    # Axis labels.
    parts.append(
        f'<text x="{left + cell * len(p_r_values) / 2}" y="{height - 30}" text-anchor="middle" font-family="Arial, sans-serif" font-size="15" font-weight="700">Assumed p_observed Russia (p_R)</text>'
    )
    parts.append(
        f'<text x="24" y="{top + cell * len(p_u_values) / 2}" transform="rotate(-90 24 {top + cell * len(p_u_values) / 2})" text-anchor="middle" font-family="Arial, sans-serif" font-size="15" font-weight="700">Assumed p_observed Ukraine (p_U)</text>'
    )

    for i, p_r in enumerate(p_r_values):
        x = left + i * cell + cell / 2
        parts.append(
            f'<text x="{x}" y="{top - 16}" text-anchor="middle" font-family="Arial, sans-serif" font-size="13">{p_r:.1f}</text>'
        )

    for j, p_u in enumerate(p_u_values):
        y = top + j * cell + cell / 2 + 5
        parts.append(
            f'<text x="{left - 18}" y="{y}" text-anchor="end" font-family="Arial, sans-serif" font-size="13">{p_u:.1f}</text>'
        )

    for j, p_u in enumerate(p_u_values):
        for i, p_r in enumerate(p_r_values):
            rr = values[(p_r, p_u)]
            x = left + i * cell
            y = top + j * cell
            fill = color_for(rr, min_rr, max_rr)
            text_color = "#111111" if rr < 3.2 else "#ffffff"
            stroke = "#111111" if rr <= 1 else "#d9d9d9"
            stroke_width = 2 if rr <= 1 else 1
            parts.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'
            )
            parts.append(
                f'<text x="{x + cell / 2}" y="{y + cell / 2 + 5}" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" font-weight="700" fill="{text_color}">{rr:.2f}</text>'
            )

    # Boundary guide: p_U = boundary * p_R. The y axis is reversed.
    line_points = []
    for p_r in p_r_values:
        p_u = reversal_boundary * p_r
        if min(p_u_values) <= p_u <= max(p_u_values):
            x = left + p_r_values.index(p_r) * cell + cell / 2
            y_pos = top + (max(p_u_values) - p_u) / 0.1 * cell + cell / 2
            line_points.append((x, y_pos))
    if len(line_points) >= 2:
        path = " ".join(f"{x:.1f},{y:.1f}" for x, y in line_points)
        parts.append(
            f'<polyline points="{path}" fill="none" stroke="#111111" stroke-width="3" stroke-dasharray="7,5"/>'
        )

    legend_x = left + cell * len(p_r_values) + 45
    legend_y = top
    parts.extend(
        [
            f'<text x="{legend_x}" y="{legend_y}" font-family="Arial, sans-serif" font-size="14" font-weight="700">Notes</text>',
            f'<text x="{legend_x}" y="{legend_y + 28}" font-family="Arial, sans-serif" font-size="13" fill="#333">RR &gt; 1: Russia higher</text>',
            f'<text x="{legend_x}" y="{legend_y + 50}" font-family="Arial, sans-serif" font-size="13" fill="#333">RR ≤ 1: reversal</text>',
            f'<text x="{legend_x}" y="{legend_y + 72}" font-family="Arial, sans-serif" font-size="13" fill="#333">Dashed line:</text>',
            f'<text x="{legend_x}" y="{legend_y + 94}" font-family="Arial, sans-serif" font-size="13" fill="#333">p_U / p_R ≈ {reversal_boundary:.3f}</text>',
            f'<text x="{legend_x}" y="{legend_y + 128}" font-family="Arial, sans-serif" font-size="12" fill="#555">Cells show corrected RR</text>',
            f'<text x="{legend_x}" y="{legend_y + 148}" font-family="Arial, sans-serif" font-size="12" fill="#555">using observed_count / p</text>',
        ]
    )
    parts.append("</svg>")

    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"observed_rr: {observed_rr:.6f}")
    print(f"reversal_boundary_pu_over_pr: {reversal_boundary:.6f}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

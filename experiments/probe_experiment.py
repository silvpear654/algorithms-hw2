"""Measure separate-chaining search probes and compare them with theory."""

from pathlib import Path
import random

from src.hash_table import HashTable

CAPACITY = 4000
LOAD_FACTORS = tuple(step / 4 for step in range(1, 17))
OUTPUT = Path(__file__).resolve().parent


def measure(load_factor: float) -> tuple[float, float]:
    key_count = round(CAPACITY * load_factor)
    table = HashTable(CAPACITY)
    stored_random = random.Random(2026)
    stored_occupancy = [0] * CAPACITY
    keys = []
    for _ in range(key_count):
        bucket = stored_random.randrange(CAPACITY)
        repetition = stored_occupancy[bucket]
        stored_occupancy[bucket] += 1
        keys.append(chr(0x10000 + bucket + repetition * CAPACITY))
    for index, key in enumerate(keys):
        table.insert(key, index)

    successful = 0
    successful_queries = list(keys)
    random.Random(2027).shuffle(successful_queries)
    for key in successful_queries:
        table.search(key)
        successful += table.last_probes

    unsuccessful = 0
    absent_random = random.Random(2028)
    absent_occupancy = [0] * CAPACITY
    for _ in range(key_count):
        bucket = absent_random.randrange(CAPACITY)
        repetition = absent_occupancy[bucket]
        absent_occupancy[bucket] += 1
        key = chr(0x30000 + bucket + repetition * CAPACITY)
        table.search(key)
        unsuccessful += table.last_probes

    return successful / key_count, unsuccessful / key_count


def svg_chart(rows: list[tuple[float, float, float]]) -> str:
    width, height = 900, 520
    left, right, top, bottom = 75, 30, 55, 75
    plot_width = width - left - right
    plot_height = height - top - bottom
    max_y = 5.0

    def point(alpha: float, probes: float) -> tuple[float, float]:
        x = left + alpha / 4 * plot_width
        y = top + (max_y - probes) / max_y * plot_height
        return x, y

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<title>Separate chaining search probes by load factor</title>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="450" y="28" text-anchor="middle" font-family="sans-serif" font-size="18">Separate chaining: measured and theoretical probes</text>',
    ]
    for probe in range(6):
        y = point(0, probe)[1]
        parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" stroke="#ddd"/>'
        )
        parts.append(
            f'<text x="{left-12}" y="{y+4:.1f}" text-anchor="end" font-family="sans-serif" font-size="12">{probe}</text>'
        )
    for alpha in range(5):
        x = point(alpha, 0)[0]
        parts.append(
            f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{height-bottom}" stroke="#eee"/>'
        )
        parts.append(
            f'<text x="{x:.1f}" y="{height-bottom+24}" text-anchor="middle" font-family="sans-serif" font-size="12">{alpha}</text>'
        )
    parts.extend(
        [
            f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#222"/>',
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#222"/>',
            f'<text x="{left+plot_width/2:.1f}" y="{height-18}" text-anchor="middle" font-family="sans-serif" font-size="14">Load factor α</text>',
            f'<text x="18" y="{top+plot_height/2:.1f}" transform="rotate(-90 18 {top+plot_height/2:.1f})" text-anchor="middle" font-family="sans-serif" font-size="14">Average inspected nodes</text>',
        ]
    )

    series = (
        ("Measured success", [success for _, success, _ in rows], "#1769aa", False),
        (
            "Theory success 1 + α/2",
            [1 + alpha / 2 for alpha, _, _ in rows],
            "#1769aa",
            True,
        ),
        ("Measured failure", [failure for _, _, failure in rows], "#d1495b", False),
        ("Theory failure α", [alpha for alpha, _, _ in rows], "#d1495b", True),
    )
    for _, probes_by_load, color, dashed in series:
        values = []
        for (alpha, _, _), probes in zip(rows, probes_by_load):
            x, y = point(alpha, probes)
            values.append(f"{x:.1f},{y:.1f}")
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        parts.append(
            f'<polyline points="{" ".join(values)}" fill="none" stroke="{color}" stroke-width="2.5"{dash}/>'
        )

    legend = (
        ("Measured success", "#1769aa", False),
        ("Theory success 1 + α/2", "#1769aa", True),
        ("Measured failure", "#d1495b", False),
        ("Theory failure α", "#d1495b", True),
    )
    for index, (label, color, dashed) in enumerate(legend):
        x = left + (index % 2) * 350
        y = top + plot_height + 50 + (index // 2) * 18
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        parts.append(
            f'<line x1="{x}" y1="{y-4}" x2="{x+25}" y2="{y-4}" stroke="{color}" stroke-width="2.5"{dash}/>'
        )
        parts.append(
            f'<text x="{x+32}" y="{y}" font-family="sans-serif" font-size="12">{label}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> None:
    rows = []
    for alpha in LOAD_FACTORS:
        successful, unsuccessful = measure(alpha)
        rows.append((alpha, successful, unsuccessful))

    lines = [
        "# Separate-chaining probe experiment",
        "",
        f"Capacity: {CAPACITY}. Each row averages α × capacity successful and unsuccessful searches. Seeded independent bucket assignments give reproducible, approximately uniform key and query distributions.",
        "",
        "| α | successful measured | successful theory (1 + α/2) | unsuccessful measured | unsuccessful theory (α) |",
        "|---:|---:|---:|---:|---:|",
    ]
    for alpha, successful, unsuccessful in rows:
        lines.append(
            f"| {alpha:.2f} | {successful:.3f} | {1 + alpha / 2:.3f} | {unsuccessful:.3f} | {alpha:.3f} |"
        )
    lines.extend(
        [
            "",
            "The theoretical expressions assume uniformly distributed keys and, for successful searches, a uniformly selected stored key. Independent seeded bucket assignments approximate these assumptions; finite table size and the realized bucket occupancy cause small deviations. An empty bucket costs zero probes, which is included in the unsuccessful-search average.",
            "",
            "![Measured and theoretical probe counts](probe_experiment.svg)",
        ]
    )
    (OUTPUT / "probe_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUTPUT / "probe_experiment.svg").write_text(svg_chart(rows), encoding="utf-8")
    print(f"Wrote {OUTPUT / 'probe_results.md'} and {OUTPUT / 'probe_experiment.svg'}")


if __name__ == "__main__":
    main()

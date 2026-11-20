"""Measure separate-chaining probes for random URLs and compare with theory."""

import csv
import random
import string
from pathlib import Path
from xml.sax.saxutils import escape

from src.hash_table import HashTable

CAPACITY = 4093
TRIALS = 5
LOAD_FACTORS = tuple(step / 4 for step in range(1, 17))
OUTPUT = Path(__file__).resolve().parent
URL_CHARACTERS = string.ascii_lowercase + string.digits


def random_urls(count: int, seed: int, namespace: str) -> list[str]:
    generator = random.Random(seed)
    urls = []
    for index in range(count):
        hostname = "".join(generator.choices(URL_CHARACTERS, k=12))
        path = "".join(generator.choices(URL_CHARACTERS, k=24))
        urls.append(f"https://{hostname}.example/{namespace}-{index}-{path}")
    return urls


def measure_trial(load_factor: float, seed: int) -> tuple[float, float]:
    item_count = round(CAPACITY * load_factor)
    table = HashTable(CAPACITY, max_load=None)
    urls = random_urls(item_count, seed, "stored")
    for index, url in enumerate(urls):
        table.insert(url, index)

    successful_queries = list(urls)
    random.Random(seed + 1).shuffle(successful_queries)
    successful_probes = 0
    for url in successful_queries:
        table.search(url)
        successful_probes += table.last_probes

    unsuccessful_queries = random_urls(item_count, seed + 2, "absent")
    unsuccessful_probes = 0
    for url in unsuccessful_queries:
        table.search(url)
        unsuccessful_probes += table.last_probes

    return (
        successful_probes / item_count,
        unsuccessful_probes / item_count,
    )


def measure(load_factor: float) -> tuple[float, float]:
    trials = [
        measure_trial(load_factor, 202600 + trial * 100 + round(load_factor * 100))
        for trial in range(TRIALS)
    ]
    return (
        sum(successful for successful, _ in trials) / TRIALS,
        sum(unsuccessful for _, unsuccessful in trials) / TRIALS,
    )


def svg_chart(rows: list[tuple[float, float, float]]) -> str:
    width, height = 900, 520
    left, right, top, bottom = 75, 30, 55, 75
    plot_width = width - left - right
    plot_height = height - top - bottom
    max_probes = 5.0

    def point(alpha: float, probes: float) -> tuple[float, float]:
        x = left + alpha / 4 * plot_width
        y = top + (max_probes - probes) / max_probes * plot_height
        return x, y

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<title>Average chaining probes by load factor</title>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="450" y="28" text-anchor="middle" font-family="sans-serif" font-size="18">Random URL searches: measured and theoretical probes</text>',
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
        points = []
        for (alpha, _, _), probes in zip(rows, probes_by_load):
            x, y = point(alpha, probes)
            points.append(f"{x:.1f},{y:.1f}")
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        parts.append(
            f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2.5"{dash}/>'
        )

    for index, (label, color, dashed) in enumerate(
        (
            ("Measured success", "#1769aa", False),
            ("Theory success 1 + α/2", "#1769aa", True),
            ("Measured failure", "#d1495b", False),
            ("Theory failure α", "#d1495b", True),
        )
    ):
        x = left + (index % 2) * 350
        y = top + plot_height + 50 + (index // 2) * 18
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        parts.append(
            f'<line x1="{x}" y1="{y-4}" x2="{x+25}" y2="{y-4}" stroke="{color}" stroke-width="2.5"{dash}/>'
        )
        parts.append(
            f'<text x="{x+32}" y="{y}" font-family="sans-serif" font-size="12">{escape(label)}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def write_results(
    rows: list[tuple[float, float, float]], output_dir: Path = OUTPUT
) -> tuple[Path, Path]:
    results_path = output_dir / "results.csv"
    with results_path.open("w", newline="", encoding="utf-8") as results_file:
        writer = csv.writer(results_file, lineterminator="\n")
        writer.writerow(
            (
                "load_factor",
                "capacity",
                "items",
                "trials",
                "successful_measured",
                "successful_theory",
                "unsuccessful_measured",
                "unsuccessful_theory",
            )
        )
        for load_factor, successful, unsuccessful in rows:
            writer.writerow(
                (
                    f"{load_factor:.2f}",
                    CAPACITY,
                    round(CAPACITY * load_factor),
                    TRIALS,
                    f"{successful:.6f}",
                    f"{1 + load_factor / 2:.6f}",
                    f"{unsuccessful:.6f}",
                    f"{load_factor:.6f}",
                )
            )

    graph_path = output_dir / "probe_experiment.svg"
    graph_path.write_text(svg_chart(rows), encoding="utf-8")
    return results_path, graph_path


def main() -> None:
    rows = []
    for load_factor in LOAD_FACTORS:
        successful, unsuccessful = measure(load_factor)
        rows.append((load_factor, successful, unsuccessful))

    results_path, graph_path = write_results(rows)
    print(f"Wrote {results_path} and {graph_path}")


if __name__ == "__main__":
    main()

"""Compare separate chaining and linear probing on identical key sets."""

import random
from pathlib import Path

from src.hash_table import HashTable, LinearProbingHashTable

CAPACITY = 2000
TRIALS = 20
LOAD_FACTORS = tuple(step / 10 for step in range(1, 10))
OUTPUT = Path(__file__).resolve().parent

Result = tuple[float, float, float, float, float]


def _keys(count: int, seed: int, base: int) -> list[str]:
    generator = random.Random(seed)
    occupancy = [0] * CAPACITY
    result = []
    for _ in range(count):
        bucket = generator.randrange(CAPACITY)
        repetition = occupancy[bucket]
        occupancy[bucket] += 1
        result.append(chr(base + bucket + repetition * CAPACITY))
    return result


def _average_probes(table: HashTable, keys: list[str]) -> float:
    total = 0
    queries = list(keys)
    random.Random(2027).shuffle(queries)
    for key in queries:
        table.search(key)
        total += table.last_probes
    return total / len(queries)


def measure(load_factor: float) -> Result:
    key_count = round(CAPACITY * load_factor)
    totals = [0.0, 0.0, 0.0, 0.0]
    for trial in range(TRIALS):
        keys = _keys(key_count, 2026 + trial, 0x10000)
        absent_keys = _keys(key_count, 3026 + trial, 0x30000)
        chaining = HashTable(CAPACITY)
        linear = LinearProbingHashTable(CAPACITY)
        for index, key in enumerate(keys):
            chaining.insert(key, index)
            linear.insert(key, index)

        totals[0] += _average_probes(chaining, keys)
        totals[1] += _average_probes(chaining, absent_keys)
        totals[2] += _average_probes(linear, keys)
        totals[3] += _average_probes(linear, absent_keys)

    averages = [total / TRIALS for total in totals]
    return (load_factor, *averages)


def theory(load_factor: float) -> tuple[float, float, float, float]:
    return (
        1 + load_factor / 2,
        load_factor,
        0.5 * (1 + 1 / (1 - load_factor)),
        0.5 * (1 + 1 / (1 - load_factor) ** 2),
    )


def svg_chart(rows: list[Result]) -> str:
    width, height = 1000, 800
    left, right = 90, 35
    plot_width = width - left - right
    panels = (
        ("Successful searches", 65, 340, 6, (0, 1, 2, 3, 4, 5, 6), 1, 3, 0, 2),
        ("Unsuccessful searches", 410, 685, 55, (0, 10, 20, 30, 40, 50), 2, 4, 1, 3),
    )

    def x_position(alpha: float) -> float:
        return left + (alpha - 0.1) / 0.8 * plot_width

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<title>Chaining and linear probing search costs</title>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="500" y="30" text-anchor="middle" font-family="sans-serif" font-size="20">Measured and theoretical probe counts</text>',
    ]
    for (
        title,
        top,
        bottom,
        max_y,
        ticks,
        measured_column,
        linear_column,
        chaining_theory_column,
        linear_theory_column,
    ) in panels:
        plot_height = bottom - top

        def y_position(probes: float) -> float:
            return bottom - probes / max_y * plot_height

        parts.append(
            f'<text x="{left}" y="{top-12}" font-family="sans-serif" font-size="15">{title}</text>'
        )
        for tick in ticks:
            y = y_position(tick)
            parts.append(
                f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" stroke="#ddd"/>'
            )
            parts.append(
                f'<text x="{left-12}" y="{y+4:.1f}" text-anchor="end" font-family="sans-serif" font-size="11">{tick}</text>'
            )
        for step in range(1, 10):
            alpha = step / 10
            x = x_position(alpha)
            parts.append(
                f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{bottom}" stroke="#eee"/>'
            )
            parts.append(
                f'<text x="{x:.1f}" y="{bottom+18}" text-anchor="middle" font-family="sans-serif" font-size="10">{alpha:.1f}</text>'
            )
        parts.append(
            f'<text x="{left+plot_width/2:.1f}" y="{bottom+34}" text-anchor="middle" font-family="sans-serif" font-size="12">Load factor alpha</text>'
        )
        series = (
            ("Chaining measured", measured_column, None, "#1769aa", False),
            ("Chaining theory", None, chaining_theory_column, "#1769aa", True),
            ("Linear measured", linear_column, None, "#d1495b", False),
            ("Linear theory", None, linear_theory_column, "#d1495b", True),
        )
        for _, row_column, theory_column, color, dashed in series:
            points = []
            for row in rows:
                alpha = row[0]
                if theory_column is not None:
                    probes = theory(alpha)[theory_column]
                else:
                    probes = row[row_column]
                points.append(
                    f"{x_position(alpha):.1f},{y_position(probes):.1f}"
                )
            dash = ' stroke-dasharray="6 4"' if dashed else ""
            parts.append(
                f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2.5"{dash}/>'
            )

    legend = (
        ("Chaining measured", "#1769aa", False),
        ("Chaining theory", "#1769aa", True),
        ("Linear measured", "#d1495b", False),
        ("Linear theory", "#d1495b", True),
    )
    for index, (label, color, dashed) in enumerate(legend):
        x = left + (index % 2) * 400
        y = 735 + (index // 2) * 22
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        parts.append(
            f'<line x1="{x}" y1="{y-4}" x2="{x+25}" y2="{y-4}" stroke="{color}" stroke-width="2.5"{dash}/>'
        )
        parts.append(
            f'<text x="{x+32}" y="{y}" font-family="sans-serif" font-size="12">{label}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _pdf_text(x: float, y: float, size: float, text: str, font: str = "F1") -> str:
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return (
        f"BT /{font} {size} Tf 1 0 0 1 {x:.2f} {y:.2f} Tm "
        f"({escaped}) Tj ET"
    )


def _pdf_panel(
    commands: list[str],
    rows: list[Result],
    title: str,
    top: float,
    bottom: float,
    max_y: float,
    y_ticks: tuple[int, ...],
    measured_column: int,
    linear_column: int,
) -> None:
    left, right = 80, 560
    plot_width = right - left
    plot_height = top - bottom

    def x_position(alpha: float) -> float:
        return left + (alpha - 0.1) / 0.8 * plot_width

    def y_position(probes: float) -> float:
        return bottom + probes / max_y * plot_height

    commands.append(_pdf_text(left, top + 18, 12, title))
    for tick in y_ticks:
        y = y_position(tick)
        commands.extend(
            [
                "0.85 G 0.5 w",
                f"{left} {y:.2f} m {right} {y:.2f} l S",
                "0 G",
                _pdf_text(left - 24, y - 3, 8, str(tick)),
            ]
        )
    for step in range(1, 10):
        alpha = step / 10
        x = x_position(alpha)
        commands.extend(
            [
                "0.92 G 0.4 w",
                f"{x:.2f} {bottom} m {x:.2f} {top} l S",
                "0 G",
                _pdf_text(x - 8, bottom - 15, 7, f"{alpha:.1f}"),
            ]
        )
    commands.extend(
        [
            "0 G 0.8 w",
            f"{left} {bottom} m {right} {bottom} l S",
            f"{left} {bottom} m {left} {top} l S",
        ]
    )
    series = (
        (measured_column, "chaining", False),
        (measured_column, "chaining", True),
        (linear_column, "linear", False),
        (linear_column, "linear", True),
    )
    for column, strategy, is_theory in series:
        color = "0.09 0.41 0.67" if strategy == "chaining" else "0.82 0.29 0.35"
        commands.append(f"{color} RG 1.6 w")
        commands.append("[4 3] 0 d" if is_theory else "[] 0 d")
        coordinates = []
        for row in rows:
            alpha = row[0]
            if is_theory:
                estimates = theory(alpha)
                theory_column = (
                    0 if measured_column == 1 else 1
                ) if strategy == "chaining" else (
                    2 if measured_column == 1 else 3
                )
                probes = estimates[theory_column]
            else:
                probes = row[column]
            coordinates.append((x_position(alpha), y_position(probes)))
        if coordinates:
            first_x, first_y = coordinates[0]
            commands.append(f"{first_x:.2f} {first_y:.2f} m")
            commands.extend(
                f"{x:.2f} {y:.2f} l" for x, y in coordinates[1:]
            )
            commands.append("S")
    commands.append("[] 0 d 0 G")
    commands.append(
        _pdf_text(left + plot_width / 2 - 35, bottom - 29, 9, "Load factor alpha")
    )


def _pdf_document(rows: list[Result]) -> bytes:
    page_one = [
        _pdf_text(50, 750, 18, "Hash table probe comparison"),
        _pdf_text(50, 728, 10, "Chaining vs. linear probing at load factors 0.1 through 0.9"),
        _pdf_text(50, 704, 9, "Method: fixed capacity 2,000; 20 seeded trials use identical keys for both tables"),
        _pdf_text(50, 690, 9, "and Horner hash (multiplier 31). Entries are inserted once; counts are average"),
        _pdf_text(50, 676, 9, "nodes inspected (chaining) or slots inspected (linear probing)."),
        _pdf_text(50, 650, 9, "Theory: chaining success 1+alpha/2, failure alpha; linear success"),
        _pdf_text(50, 636, 9, "0.5*(1+1/(1-alpha)), failure 0.5*(1+1/(1-alpha)^2)."),
        _pdf_text(50, 600, 9, "alpha | chain S obs/theory | chain U obs/theory | linear S obs/theory | linear U obs/theory", "F2"),
        _pdf_text(50, 584, 9, "------+--------------------+--------------------+----------------------+----------------------", "F2"),
    ]
    for index, row in enumerate(rows):
        alpha, chain_success, chain_failure, linear_success, linear_failure = row
        chain_success_theory, chain_failure_theory, linear_success_theory, linear_failure_theory = theory(alpha)
        line = (
            f"{alpha:.1f}   | {chain_success:.2f}/{chain_success_theory:.2f}"
            f"          | {chain_failure:.2f}/{chain_failure_theory:.2f}"
            f"          | {linear_success:.2f}/{linear_success_theory:.2f}"
            f"            | {linear_failure:.2f}/{linear_failure_theory:.2f}"
        )
        page_one.append(_pdf_text(50, 564 - index * 17, 8, line, "F2"))
    page_one.extend(
        [
            _pdf_text(50, 385, 9, "Observed values differ slightly from theory because the table is finite and"),
            _pdf_text(50, 371, 9, "the seeded bucket assignments have a realized, rather than perfectly uniform,"),
            _pdf_text(50, 357, 9, "occupancy distribution. The same keys isolate the collision strategy effect."),
        ]
    )

    page_two = [
        _pdf_text(50, 750, 17, "Results and interpretation"),
        _pdf_text(50, 728, 9, "Solid lines are measured; dashed lines are theory. Blue is chaining, red is linear."),
    ]
    _pdf_panel(page_two, rows, "Successful searches", 680, 460, 6, (0, 1, 2, 3, 4, 5, 6), 1, 3)
    _pdf_panel(page_two, rows, "Unsuccessful searches", 390, 170, 55, (0, 10, 20, 30, 40, 50), 2, 4)
    page_two.extend(
        [
            _pdf_text(50, 105, 9, "At moderate load, measured values track the estimates. As alpha approaches 1,"),
            _pdf_text(50, 91, 9, "linear probing rises sharply: long occupied runs cause primary clustering."),
            _pdf_text(50, 77, 9, "Chaining grows much more gradually. The comparison uses identical keys and capacity."),
        ]
    )

    content_one = "\n".join(page_one).encode("ascii")
    content_two = "\n".join(page_two).encode("ascii")

    def stream(content: bytes) -> bytes:
        return (
            f"<< /Length {len(content)} >>\nstream\n".encode("ascii")
            + content
            + b"\nendstream"
        )

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> /Contents 7 0 R >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> /Contents 8 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
        stream(content_one),
        stream(content_two),
    ]
    document = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, item in enumerate(objects, start=1):
        offsets.append(len(document))
        document.extend(f"{number} 0 obj\n".encode("ascii"))
        document.extend(item)
        document.extend(b"\nendobj\n")
    xref_offset = len(document)
    document.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    document.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        document.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    document.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(document)


def main() -> None:
    rows = [measure(alpha) for alpha in LOAD_FACTORS]
    lines = [
        "# Chaining vs. linear probing",
        "",
        f"Both implementations use capacity {CAPACITY} and the identical keys and absent queries within each of {TRIALS} seeded trials at every load factor. Successful averages query each stored key once in shuffled order; unsuccessful averages query the same number of absent keys.",
        "",
        "Theoretical estimates: chaining success `1 + α/2`, failure `α`; linear probing success `0.5 × (1 + 1/(1−α))`, failure `0.5 × (1 + 1/(1−α)^2)`.",
        "",
        "| α | Chaining success | Theory | Chaining failure | Theory | Linear success | Theory | Linear failure | Theory |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        alpha, chain_success, chain_failure, linear_success, linear_failure = row
        chain_success_theory, chain_failure_theory, linear_success_theory, linear_failure_theory = theory(alpha)
        lines.append(
            f"| {alpha:.1f} | {chain_success:.3f} | {chain_success_theory:.3f} | {chain_failure:.3f} | {chain_failure_theory:.3f} | {linear_success:.3f} | {linear_success_theory:.3f} | {linear_failure:.3f} | {linear_failure_theory:.3f} |"
        )
    lines.extend(
        [
            "",
            "The SVG separates successful and unsuccessful search scales so both strategies remain readable. Finite seeded trials and realized bucket layouts cause deviations from theory. Linear probing's costs rise sharply near load 1 because primary clustering creates long runs; chaining grows more gradually.",
            "",
            "![Measured and theoretical probe counts](comparison.svg)",
            "",
            "The two-page summary is in [report.pdf](report.pdf).",
        ]
    )
    (OUTPUT / "comparison_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUTPUT / "comparison.svg").write_text(svg_chart(rows), encoding="utf-8")
    (OUTPUT / "report.pdf").write_bytes(_pdf_document(rows))
    print(
        f"Wrote {OUTPUT / 'comparison_results.md'}, "
        f"{OUTPUT / 'comparison.svg'}, and {OUTPUT / 'report.pdf'}"
    )


if __name__ == "__main__":
    main()

import csv
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit

from experiments.probe_experiment import (
    CAPACITY,
    TRIALS,
    measure_trial,
    random_urls,
    write_results,
)


class ProbeExperimentTests(unittest.TestCase):
    def test_random_urls_are_reproducible_and_distinct(self):
        first = random_urls(20, seed=1234, namespace="stored")
        repeated = random_urls(20, seed=1234, namespace="stored")

        self.assertEqual(first, repeated)
        self.assertEqual(len(set(first)), len(first))
        for index, url in enumerate(first):
            parsed = urlsplit(url)
            self.assertEqual(parsed.scheme, "https")
            self.assertTrue(parsed.hostname.endswith(".example"))
            self.assertIn(f"stored-{index}-", parsed.path)

    def test_trial_returns_reproducible_success_and_failure_averages(self):
        first = measure_trial(0.25, seed=202625)
        repeated = measure_trial(0.25, seed=202625)

        self.assertEqual(first, repeated)
        successful, unsuccessful = first
        self.assertGreaterEqual(successful, 1.0)
        self.assertLess(successful, 2.0)
        self.assertGreaterEqual(unsuccessful, 0.0)
        self.assertLess(unsuccessful, 1.0)

    def test_results_writer_emits_csv_theory_columns_and_svg(self):
        rows = [(0.25, 1.125, 0.25), (4.0, 3.0, 4.0)]
        with tempfile.TemporaryDirectory() as directory:
            csv_path, svg_path = write_results(rows, Path(directory))

            with csv_path.open(newline="", encoding="utf-8") as results_file:
                written_rows = list(csv.DictReader(results_file))
            self.assertEqual(len(written_rows), 2)
            self.assertEqual(int(written_rows[0]["capacity"]), CAPACITY)
            self.assertEqual(int(written_rows[0]["trials"]), TRIALS)
            self.assertEqual(written_rows[0]["successful_theory"], "1.125000")
            self.assertEqual(written_rows[0]["unsuccessful_theory"], "0.250000")
            self.assertEqual(written_rows[1]["successful_theory"], "3.000000")
            self.assertEqual(written_rows[1]["unsuccessful_theory"], "4.000000")

            svg_root = ET.parse(svg_path).getroot()
            namespace = {"svg": "http://www.w3.org/2000/svg"}
            curves = svg_root.findall(".//svg:polyline", namespace)
            self.assertEqual(len(curves), 4)
            self.assertTrue(all(len(curve.attrib["points"].split()) == 2 for curve in curves))


if __name__ == "__main__":
    unittest.main()

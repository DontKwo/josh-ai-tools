import csv
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Insert scripts dir to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import benchmark_runner

class TestBenchmarkRunner(unittest.TestCase):
    def test_calculate_metrics(self) -> None:
        """Tests that metrics are calculated correctly."""
        times = [1.0, 2.0, 3.0, 4.0, 5.0]
        memories = [100.0, 200.0, 150.0, 300.0, 250.0]
        metrics = benchmark_runner.calculate_metrics(times, memories)
        self.assertEqual(metrics["mean"], 3.0)
        self.assertEqual(metrics["median"], 3.0)
        self.assertAlmostEqual(metrics["stdev"], 1.5811388300841898)
        self.assertEqual(metrics["min"], 1.0)
        self.assertEqual(metrics["max"], 5.0)
        self.assertEqual(metrics["peak_memory"], 300.0)

    def test_calculate_metrics_empty(self) -> None:
        """Tests that empty inputs return empty metrics."""
        metrics = benchmark_runner.calculate_metrics([], [])
        self.assertEqual(metrics, {})

    @patch("benchmark_runner.run_iteration")
    def test_main_stdout(self, mock_run: MagicMock) -> None:
        """Tests main entry point outputting to stdout."""
        mock_run.side_effect = [(1.0, 100.0), (2.0, 200.0)]
        args = ["-n", "2", "--", "echo", "hello"]
        with patch("sys.stdout") as mock_stdout:
            benchmark_runner.main(args)
            self.assertEqual(mock_run.call_count, 2)

    @patch("benchmark_runner.run_iteration")
    def test_main_csv(self, mock_run: MagicMock) -> None:
        """Tests main entry point outputting to a CSV file."""
        mock_run.side_effect = [(1.0, 100.0), (3.0, 200.0)]
        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str).resolve()
            csv_path = temp_dir / "out.csv"
            args = ["-n", "2", "--csv", str(csv_path), "--", "echo", "test"]
            benchmark_runner.main(args)

            self.assertTrue(csv_path.exists())
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                self.assertEqual(len(rows), 1)
                self.assertEqual(float(rows[0]["mean"]), 2.0)
                self.assertEqual(float(rows[0]["peak_memory"]), 200.0)

if __name__ == "__main__":
    unittest.main()

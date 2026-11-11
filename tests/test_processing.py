import tempfile
import unittest
from pathlib import Path

import pandas as pd

from data_chart_assistant.cli import main
from data_chart_assistant.processing import clean_dataset, plot_dataset


class ProcessingTests(unittest.TestCase):
    def test_clean_removes_empty_rows_and_fills_numeric_median(self):
        data = pd.DataFrame({"label": ["a", "b", None], "value": [1.0, None, None]})

        cleaned = clean_dataset(data)

        self.assertEqual(len(cleaned), 2)
        self.assertEqual(cleaned["value"].tolist(), [1.0, 1.0])

    def test_cli_writes_cleaned_output_and_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.csv"
            output = Path(directory) / "cleaned.csv"
            summary = Path(directory) / "summary.json"
            pd.DataFrame({"label": ["a", "b", "c"], "value": [1, None, 3]}).to_csv(source, index=False)

            result = main(["clean", str(source), "--output", str(output), "--summary", str(summary)])

            self.assertEqual(result, 0)
            self.assertTrue(output.is_file())
            self.assertTrue(summary.is_file())
            self.assertEqual(pd.read_csv(output)["value"].tolist(), [1.0, 2.0, 3.0])

    def test_scatter_chart_is_created(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "scatter.png"
            data = pd.DataFrame({"x": [1, 2], "y": [3, 5]})

            result = plot_dataset(data, "scatter", output)

            self.assertEqual(result, output.resolve())
            self.assertTrue(output.is_file())


if __name__ == "__main__":
    unittest.main()
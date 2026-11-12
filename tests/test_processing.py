import tempfile
import unittest
import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pandas as pd

from data_chart_assistant.cli import main
from data_chart_assistant.eda import profile_dataset
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

    def test_eda_sample_has_at_least_50_rows_and_10_fields(self):
        sample_path = Path(__file__).parents[1] / "examples" / "eda_sample.csv"

        sample = pd.read_csv(sample_path)

        self.assertGreaterEqual(len(sample), 50)
        self.assertGreaterEqual(len(sample.columns), 10)
        self.assertIn("customer_id", sample.columns)
        self.assertIn("region", sample.columns)

    def test_profile_infers_types_and_excludes_raw_values(self):
        data = pd.DataFrame({
            "customer_id": ["A001", "A002", "A003"],
            "signup_date": ["2025-01-01", "2025-02-01", "2025-03-01"],
            "region": ["West", "East", "West"],
            "spend": [10.0, None, 30.0],
        })

        profile = profile_dataset(data)
        columns = {item["name"]: item for item in profile["column_profiles"]}

        self.assertEqual(profile["rows"], 3)
        self.assertEqual(columns["customer_id"]["type"], "identifier")
        self.assertEqual(columns["signup_date"]["type"], "datetime")
        self.assertEqual(columns["region"]["type"], "categorical")
        self.assertEqual(columns["spend"]["statistics"]["p99"], 29.8)
        self.assertNotIn("West", json.dumps(profile))

        location_profile = profile_dataset(
            pd.DataFrame({"postal_code": [94103, 10001, 60601]}),
            max_categories=2,
        )
        location_column = location_profile["column_profiles"][0]
        self.assertEqual(location_column["type"], "categorical")
        self.assertTrue(location_column["high_cardinality"])

        weekly_profile = profile_dataset(data, time_frequency="week")
        time_recommendation = next(
            item for item in weekly_profile["recommendations"]
            if item.get("chart") == "time_series"
        )
        self.assertIn("week", time_recommendation["reason"])

        quarterly_profile = profile_dataset(data, time_frequency="quarter")
        quarterly_recommendation = next(
            item for item in quarterly_profile["recommendations"]
            if item.get("chart") == "time_series"
        )
        self.assertIn("quarter", quarterly_recommendation["reason"])

    def test_eda_cli_creates_self_contained_report(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.csv"
            report = Path(directory) / "report.html"
            pd.DataFrame({
                "date": ["2025-01-01", "2025-02-01", "2025-03-01"],
                "group": ["a", "b", "a"],
                "x": [1, 2, 3],
                "y": [4, 3, 5],
            }).to_csv(source, index=False)

            plan_output = StringIO()
            with redirect_stdout(plan_output):
                plan_result = main(["eda", str(source), "--plan-only"])
            report_output = StringIO()
            with redirect_stdout(report_output):
                report_result = main(["eda", str(source), "--output", str(report)])

            plan = json.loads(plan_output.getvalue())
            self.assertEqual(plan_result, 0)
            self.assertIn("scatter", [item.get("chart") for item in plan["recommendations"]])
            self.assertEqual(report_result, 0)
            self.assertTrue(report.is_file())
            report_html = report.read_text(encoding="utf-8")
            self.assertIn("Plotly.newPlot", report_html)
            self.assertIn("Column profile", report_html)
            self.assertIn("Numeric summary", report_html)
            self.assertNotRegex(report_html, r'<script[^>]+src="https?://')


if __name__ == "__main__":
    unittest.main()
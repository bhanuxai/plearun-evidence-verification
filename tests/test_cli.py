
import json
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO

from plearun_cli import main, run


class CLITests(unittest.TestCase):

    def test_run_returns_findings(self):
        result = run(
            "reports/report_fictional_02.txt",
            "records"
        )

        self.assertEqual(set(result.keys()), {"findings"})
        self.assertIsInstance(result["findings"], list)
        self.assertGreater(len(result["findings"]), 0)

    def test_main_rejects_missing_arguments(self):
        stderr = StringIO()

        with redirect_stderr(stderr):
            result = main([])

        self.assertEqual(result, 2)
        self.assertIn("Usage:", stderr.getvalue())

    def test_main_rejects_missing_report(self):
        stderr = StringIO()

        with redirect_stderr(stderr):
            result = main([
                "missing_report.txt",
                "records"
            ])

        self.assertEqual(result, 2)
        self.assertIn("Report file not found", stderr.getvalue())

    def test_main_rejects_missing_records_directory(self):
        stderr = StringIO()

        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report.txt"
            report.write_text("A test report.", encoding="utf-8")

            with redirect_stderr(stderr):
                result = main([
                    str(report),
                    str(Path(directory) / "missing_records")
                ])

        self.assertEqual(result, 2)
        self.assertIn("Records directory not found", stderr.getvalue())

    def test_main_outputs_valid_json(self):
        stdout = StringIO()

        with redirect_stdout(stdout):
            result = main([
                "reports/report_fictional_02.txt",
                "records"
            ])

        self.assertEqual(result, 0)

        output = json.loads(stdout.getvalue())

        self.assertEqual(set(output.keys()), {"findings"})
        self.assertIsInstance(output["findings"], list)


if __name__ == "__main__":
    unittest.main()

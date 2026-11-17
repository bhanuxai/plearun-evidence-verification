
import json
import unittest

from parsers import load_records


class OutputSchemaTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open("findings.json", encoding="utf-8") as file:
            cls.output = json.load(file)

        cls.records = load_records("records")

    def test_top_level_schema(self):
        self.assertEqual(set(self.output.keys()), {"findings"})
        self.assertIsInstance(self.output["findings"], list)

    def test_finding_schema(self):
        for finding in self.output["findings"]:
            self.assertIn(
                finding["finding"],
                {"match", "conflict", "not_settled", "not_checkable"}
            )

            self.assertIsInstance(finding["claim"], str)

            if finding["finding"] in {"match", "conflict"}:
                self.assertEqual(
                    set(finding.keys()),
                    {"claim", "finding", "cite", "quote"}
                )
            else:
                self.assertEqual(
                    set(finding.keys()),
                    {"claim", "finding"}
                )

    def test_all_citations_reference_real_records(self):
        for finding in self.output["findings"]:
            if finding["finding"] not in {"match", "conflict"}:
                continue

            matching_records = [
                record for record in self.records
                if (
                    record["file"] == finding["cite"]["file"]
                    and record["row"] == finding["cite"]["row"]
                )
            ]

            self.assertEqual(len(matching_records), 1)

            self.assertIn(
                finding["quote"],
                matching_records[0]["raw"]
            )


if __name__ == "__main__":
    unittest.main()

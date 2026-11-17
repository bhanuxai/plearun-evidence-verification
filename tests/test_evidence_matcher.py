
import unittest

from evidence_matcher import (
    normalize_text,
    extract_terms,
    score_record,
    find_candidate_evidence
)


class EvidenceMatcherTests(unittest.TestCase):



    def test_valid_exact_citation(self):
        from evidence_matcher import validate_citation

        record = self.records[0]
        quote = "Vehicle observed"

        self.assertTrue(validate_citation(record, quote))

    def test_invalid_quote_is_rejected(self):
        from evidence_matcher import validate_citation

        record = self.records[0]

        self.assertFalse(
            validate_citation(record, "Vehicle was speeding")
        )

    def test_invalid_match_is_downgraded(self):
        from evidence_matcher import build_finding

        result = build_finding(
            "Vehicle was speeding",
            "match",
            self.records[0],
            "Vehicle was speeding"
        )

        self.assertEqual(result["finding"], "not_settled")
        self.assertNotIn("cite", result)
        self.assertNotIn("quote", result)

    def test_valid_match_contains_exact_citation(self):
        from evidence_matcher import build_finding

        result = build_finding(
            "Vehicle was observed",
            "match",
            self.records[0],
            "Vehicle observed"
        )

        self.assertEqual(result["finding"], "match")
        self.assertEqual(result["cite"]["file"], "notes.csv")
        self.assertEqual(result["cite"]["row"], 2)
        self.assertEqual(result["quote"], "Vehicle observed")


    def setUp(self):
        self.records = [
            {
                "id": "notes.csv:2",
                "file": "notes.csv",
                "row": 2,
                "raw": "N-1,Officer Lee,Vehicle observed, plate unknown,21:15",
                "fields": {},
                "type": "csv"
            },
            {
                "id": "bodycam.vtt:cue:1",
                "file": "bodycam.vtt",
                "row": 1,
                "raw": "00:00:00.000 --> 00:00:04.000\nOfficer Lee: 58 in a 45.",
                "fields": {},
                "type": "vtt"
            }
        ]

    def test_normalize_text(self):
        self.assertEqual(
            normalize_text("Officer Lee: 58 MPH!"),
            "officer lee 58 mph"
        )

    def test_extract_terms_removes_stop_words(self):
        self.assertEqual(
            extract_terms("The vehicle was observed at 21:15"),
            ["vehicle", "observed", "21", "15"]
        )

    def test_relevant_record_scores_higher(self):
        self.assertGreater(
            score_record("Officer Lee observed vehicle", self.records[0]),
            score_record("Officer Lee observed vehicle", self.records[1])
        )

    def test_candidates_preserve_original_record(self):
        results = find_candidate_evidence(
            "Officer Lee observed vehicle",
            self.records
        )

        self.assertTrue(results)
        self.assertEqual(
            results[0]["record"]["raw"],
            self.records[0]["raw"]
        )

    def test_empty_claim_returns_no_candidates(self):
        self.assertEqual(
            find_candidate_evidence("", self.records),
            []
        )

    def test_invalid_claim_rejected(self):
        with self.assertRaises(TypeError):
            find_candidate_evidence(None, self.records)

    def test_invalid_limit_rejected(self):
        with self.assertRaises(ValueError):
            find_candidate_evidence("vehicle", self.records, limit=0)

    def test_boolean_row_number_is_rejected(self):
        from evidence_matcher import validate_citation

        record = dict(self.records[0])
        record["row"] = True

        self.assertFalse(
            validate_citation(record, "Vehicle observed")
        )

    def test_non_positive_row_number_is_rejected(self):
        from evidence_matcher import validate_citation

        for row in [0, -1]:
            with self.subTest(row=row):
                record = dict(self.records[0])
                record["row"] = row

                self.assertFalse(
                    validate_citation(record, "Vehicle observed")
                )

    def test_empty_filename_is_rejected(self):
        from evidence_matcher import validate_citation

        record = dict(self.records[0])
        record["file"] = "   "

        self.assertFalse(
            validate_citation(record, "Vehicle observed")
        )

    def test_unhashable_finding_status_is_rejected(self):
        from evidence_matcher import build_finding

        with self.assertRaises(ValueError):
            build_finding(
                "Vehicle was observed",
                ["match"]
            )


if __name__ == "__main__":
    unittest.main()

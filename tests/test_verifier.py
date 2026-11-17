
import unittest

from claim_extractor import extract_claims_from_file
from parsers import load_records
from verifier import verify_claim, verify_claims


class VerifierTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.records = load_records("records")

    def test_speed_claim_matches_transcript(self):
        result = verify_claim("travelling 58 mph", self.records)

        self.assertEqual(result["finding"], "match")
        self.assertEqual(result["quote"], "58 in a 45")

    def test_speed_limit_is_not_independently_established(self):
        result = verify_claim("posted 45 zone", self.records)

        self.assertEqual(result["finding"], "not_settled")

    def test_stop_time_matches_note(self):
        result = verify_claim("and stopped around 21:16.", self.records)

        self.assertEqual(result["finding"], "match")
        self.assertIn("Stopped at lot", result["quote"])

    def test_vehicle_identity_remains_unsettled(self):
        result = verify_claim(
            "Officer Lee first observed the blue sedan at about 21:14 near mile marker 4",
            self.records
        )

        self.assertEqual(result["finding"], "not_settled")

    def test_harbor_gas_location_remains_unsettled(self):
        result = verify_claim(
            "The driver pulled into the Harbor Gas lot",
            self.records
        )

        self.assertEqual(result["finding"], "not_settled")

    def test_lane_occupancy_is_not_checkable(self):
        result = verify_claim(
            "Officer Lee states the vehicle was the only car in the lane.",
            self.records
        )

        self.assertEqual(result["finding"], "not_checkable")

    def test_all_report_claims_are_processed(self):
        claims = extract_claims_from_file(
            "reports/report_fictional_02.txt"
        )

        results = verify_claims(claims, self.records)

        self.assertEqual(len(results), len(claims))

    def test_citations_are_exact_source_substrings(self):
        claims = extract_claims_from_file(
            "reports/report_fictional_02.txt"
        )

        results = verify_claims(claims, self.records)

        for result in results:
            if result["finding"] in {"match", "conflict"}:
                cited_record = next(
                    record for record in self.records
                    if (
                        record["file"] == result["cite"]["file"]
                        and record["row"] == result["cite"]["row"]
                    )
                )

                self.assertIn(result["quote"], cited_record["raw"])



    def test_compound_speed_claim_requires_both_values(self):
        records = [{
            "id": "bodycam:1",
            "file": "bodycam_transcript.vtt",
            "row": 1,
            "raw": "00:00:00.000 --> 00:00:04.000\nOfficer Lee: 58 in a 50.",
            "fields": {
                "text": "Officer Lee: 58 in a 50."
            },
            "type": "vtt"
        }]

        result = verify_claim(
            "travelling 58 mph in posted 45 zone",
            records
        )

        self.assertEqual(result["finding"], "not_settled")

    def test_stop_note_from_wrong_author_is_rejected(self):
        records = [{
            "id": "notes:1",
            "file": "notes.csv",
            "row": 2,
            "raw": "N-1,Dispatch,Stopped at lot ~21:16,21:16",
            "fields": {
                "ID": "N-1",
                "Author": "Dispatch",
                "Note": "Stopped at lot ~21:16",
                "Time": "21:16"
            },
            "type": "csv"
        }]

        result = verify_claim(
            "stopped around 21:16",
            records
        )

        self.assertEqual(result["finding"], "not_settled")

    def test_matching_speed_statement_has_exact_citation(self):
        records = [{
            "id": "bodycam:1",
            "file": "bodycam_transcript.vtt",
            "row": 1,
            "raw": "00:00:00.000 --> 00:00:04.000\nOfficer Lee: 58 in a 45.",
            "fields": {
                "text": "Officer Lee: 58 in a 45."
            },
            "type": "vtt"
        }]

        result = verify_claim("travelling 58 mph", records)

        self.assertEqual(result["finding"], "match")
        self.assertEqual(result["cite"]["file"], "bodycam_transcript.vtt")
        self.assertEqual(result["cite"]["row"], 1)
        self.assertIn(result["quote"], records[0]["raw"])

    def test_unidentified_camera_speed_does_not_match_vehicle(self):
        records = [{
            "id": "camera:1",
            "file": "camera_log.csv",
            "row": 3,
            "raw": "2026-03-02T21:15:18-05:00,CAM-03,58,45",
            "fields": {
                "timestamp": "2026-03-02T21:15:18-05:00",
                "device": "CAM-03",
                "speed_mph": "58",
                "zone_mph": "45"
            },
            "type": "csv"
        }]

        result = verify_claim(
            "The blue sedan was travelling 58 mph",
            records
        )

        self.assertEqual(result["finding"], "not_settled")



if __name__ == "__main__":
    unittest.main()

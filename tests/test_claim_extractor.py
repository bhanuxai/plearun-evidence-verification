
import unittest

from claim_extractor import extract_claims


class ClaimExtractorTests(unittest.TestCase):

    def test_claims_are_exact_source_substrings(self):
        report = (
            "Officer Lee observed the sedan, "
            "travelling 58 mph in a posted 45 zone."
        )

        claims = extract_claims(report)

        for claim in claims:
            self.assertIn(claim, report)

    def test_extracts_incident_claims(self):
        report = """
        SYNTHETIC - FICTIONAL CASE.
        Officer Lee first observed the blue sedan at about 21:14 near mile marker 4, travelling 58 mph in a posted 45 zone.
        The driver pulled into the Harbor Gas lot and stopped around 21:16.
        A 911 call reporting the incident was logged at 21:11.
        Dispatch records show a unit on scene roughly 2 minutes after the stop.
        Officer Lee states the vehicle was the only car in the lane.
        """

        claims = extract_claims(report)

        self.assertEqual(len(claims), 6)

        self.assertTrue(
            any(
                "blue sedan" in claim
                and "travelling 58 mph" in claim
                and "posted 45 zone" in claim
                for claim in claims
            )
        )

    def test_preserves_original_wording(self):
        report = "The driver stopped around 21:16."

        claims = extract_claims(report)

        self.assertEqual(
            claims,
            ["The driver stopped around 21:16."]
        )

    def test_ignores_empty_report(self):
        self.assertEqual(extract_claims(""), [])

    def test_rejects_non_string_input(self):
        with self.assertRaises(TypeError):
            extract_claims(None)


if __name__ == "__main__":
    unittest.main()


import unittest

from clock_sync import analyze_clock_alignment


class ClockAlignmentIntegrationTests(unittest.TestCase):


    def test_duplicate_anchor_is_rejected(self):
        records = [
            {
                "file": "camera_a.csv",
                "fields": {
                    "anchor_id": "EVENT-1",
                    "timestamp": "2026-03-02T21:00:00+00:00",
                    "device": "CAM-A"
                }
            },
            {
                "file": "camera_a.csv",
                "fields": {
                    "anchor_id": "EVENT-1",
                    "timestamp": "2026-03-02T21:00:05+00:00",
                    "device": "CAM-A"
                }
            },
            {
                "file": "camera_a.csv",
                "fields": {
                    "anchor_id": "EVENT-2",
                    "timestamp": "2026-03-02T21:10:00+00:00",
                    "device": "CAM-A"
                }
            },
            {
                "file": "camera_b.csv",
                "fields": {
                    "anchor_id": "EVENT-1",
                    "timestamp": "2026-03-02T21:00:03+00:00",
                    "device": "CAM-B"
                }
            },
            {
                "file": "camera_b.csv",
                "fields": {
                    "anchor_id": "EVENT-2",
                    "timestamp": "2026-03-02T21:10:03+00:00",
                    "device": "CAM-B"
                }
            }
        ]

        result = analyze_clock_alignment(records)

        self.assertEqual(
            result["ambiguous_anchors"]["CAM-A"],
            ["EVENT-1"]
        )
        self.assertFalse(result["reliable"])
        self.assertEqual(result["offsets"], {})


    def test_sample_records_have_no_invented_anchors(self):
        records = [
            {
                "file": "dispatch.json",
                "fields": {
                    "id": "D-1001",
                    "type": "911_call",
                    "logged": "2026-03-02 21:10:19"
                }
            },
            {
                "file": "notes.csv",
                "fields": {
                    "Author": "Officer Lee",
                    "Note": "Caller described vehicle weaving",
                    "Time": "21:11"
                }
            }
        ]

        result = analyze_clock_alignment(records)

        self.assertFalse(result["reliable"])
        self.assertEqual(result["offsets"], {})
        self.assertEqual(result["comparisons"], {})

    def test_explicit_shared_anchors_produce_offset(self):
        records = [
            {
                "file": "camera_a.csv",
                "fields": {
                    "anchor_id": "EVENT-1",
                    "timestamp": "2026-03-02T21:00:00+00:00",
                    "device": "CAM-A"
                }
            },
            {
                "file": "camera_a.csv",
                "fields": {
                    "anchor_id": "EVENT-2",
                    "timestamp": "2026-03-02T21:10:00+00:00",
                    "device": "CAM-A"
                }
            },
            {
                "file": "camera_b.csv",
                "fields": {
                    "anchor_id": "EVENT-1",
                    "timestamp": "2026-03-02T21:00:03+00:00",
                    "device": "CAM-B"
                }
            },
            {
                "file": "camera_b.csv",
                "fields": {
                    "anchor_id": "EVENT-2",
                    "timestamp": "2026-03-02T21:10:03+00:00",
                    "device": "CAM-B"
                }
            }
        ]

        result = analyze_clock_alignment(records)

        self.assertTrue(result["reliable"])
        self.assertAlmostEqual(
            result["offsets"]["CAM-A->CAM-B"],
            3.0
        )


if __name__ == "__main__":
    unittest.main()

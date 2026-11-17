
import unittest
from datetime import datetime, timezone

from clock_sync import (
    normalize_timestamp,
    estimate_clock_offset,
    apply_clock_offset
)


class ClockSyncTests(unittest.TestCase):

    def test_unix_milliseconds(self):
        result = normalize_timestamp(1772504118000)

        self.assertIsNotNone(result)
        self.assertEqual(result.tzinfo, timezone.utc)

    def test_timezone_aware_iso_timestamp(self):
        result = normalize_timestamp("2026-03-02T21:15:18-05:00")

        self.assertIsNotNone(result)
        self.assertEqual(result.hour, 2)
        self.assertEqual(result.minute, 15)
        self.assertEqual(result.day, 3)

    def test_timezone_naive_timestamp_is_rejected(self):
        result = normalize_timestamp("2026-03-02 21:10:19")

        self.assertIsNone(result)

    def test_invalid_timestamp_is_rejected(self):
        self.assertIsNone(normalize_timestamp("not-a-timestamp"))

    def test_consistent_clock_offset(self):
        anchors = [
            (
                "2026-03-02T21:00:00+00:00",
                "2026-03-02T21:02:00+00:00"
            ),
            (
                "2026-03-02T21:10:00+00:00",
                "2026-03-02T21:12:01+00:00"
            )
        ]

        result = estimate_clock_offset(anchors)

        self.assertTrue(result["reliable"])
        self.assertEqual(result["anchor_count"], 2)
        self.assertEqual(result["offset_seconds"], 120.5)

    def test_insufficient_anchors_are_unreliable(self):
        anchors = [
            (
                "2026-03-02T21:00:00+00:00",
                "2026-03-02T21:02:00+00:00"
            )
        ]

        result = estimate_clock_offset(anchors)

        self.assertFalse(result["reliable"])
        self.assertIsNone(result["offset_seconds"])

    def test_inconsistent_anchors_are_rejected(self):
        anchors = [
            (
                "2026-03-02T21:00:00+00:00",
                "2026-03-02T21:02:00+00:00"
            ),
            (
                "2026-03-02T21:10:00+00:00",
                "2026-03-02T21:20:00+00:00"
            )
        ]

        result = estimate_clock_offset(anchors)

        self.assertFalse(result["reliable"])
        self.assertIsNone(result["offset_seconds"])

    def test_apply_clock_offset(self):
        result = apply_clock_offset(
            "2026-03-02T21:00:00+00:00",
            120
        )

        self.assertEqual(result.minute, 2)


if __name__ == "__main__":
    unittest.main()

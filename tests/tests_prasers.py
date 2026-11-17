
import unittest
from pathlib import Path

from parsers import load_records


class ParserTests(unittest.TestCase):

    def test_csv_preserves_physical_line_numbers(self):
        from parsers import parse_csv
        from pathlib import Path
        import tempfile

        content = (
            "#PLEARUN test marker\n"
            "ID,Note,Time\n"
            'N-1,"First line\nsecond line",21:15\n'
            "N-2,Normal note,21:16\n"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.csv"
            path.write_text(content, encoding="utf-8")

            records = parse_csv(path)

        self.assertEqual(records[0]["row"], 3)
        self.assertIn(
        "First line\nsecond line",
        records[0]["raw"].replace("\r\n", "\n")
)
        self.assertEqual(records[1]["row"], 5)
        self.assertIn("Normal note", records[1]["raw"])

    def setUp(self):
        self.records = load_records("records")

    def test_all_formats_are_loaded(self):
        formats = {record["type"] for record in self.records}

        self.assertEqual(formats, {"csv", "json", "vtt"})

    def test_camera_marker_is_not_a_record(self):
        camera = [
            r for r in self.records
            if r["file"] == "camera_log.csv"
        ]

        self.assertEqual(len(camera), 34)

    def test_dispatch_events(self):
        dispatch = [
            r for r in self.records
            if r["file"] == "dispatch.json"
        ]

        self.assertEqual(len(dispatch), 3)

    def test_transcript_overlapping_cues(self):
        cues = [
            r for r in self.records
            if r["file"] == "bodycam_transcript.vtt"
        ]

        self.assertEqual(len(cues), 3)

    def test_original_camera_text_preserved(self):
        camera = [
            r for r in self.records
            if r["file"] == "camera_log.csv"
        ]

        self.assertTrue(
            any("CAM-03" in record["raw"] for record in camera)
        )



if __name__ == "__main__":
    unittest.main()

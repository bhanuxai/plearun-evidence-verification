
import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))


class SampleData(unittest.TestCase):

    def test_camera_log_has_marker_and_header(self):
        path = os.path.join(ROOT, "records", "camera_log.csv")

        with open(path, encoding="utf-8-sig") as file:
            raw = file.read().splitlines()

        self.assertTrue(raw[0].startswith("#PLEARUN"))
        self.assertIn("timestamp,device,speed_mph,zone_mph", raw)

    def test_dispatch_json_parses(self):
        path = os.path.join(ROOT, "records", "dispatch.json")

        with open(path, encoding="utf-8") as file:
            data = json.load(file)

        self.assertIn("events", data["export"])

    def test_notes_decode_as_cp1252(self):
        path = os.path.join(ROOT, "records", "notes_cp1252.csv")

        with open(path, "rb") as file:
            raw = file.read()

        decoded = raw.decode("cp1252")
        self.assertIn("Officer Lee", decoded)

    def test_transcript_is_webvtt(self):
        path = os.path.join(ROOT, "records", "bodycam_transcript.vtt")

        with open(path, encoding="utf-8") as file:
            content = file.read()

        self.assertTrue(content.startswith("WEBVTT"))


if __name__ == "__main__":
    unittest.main()

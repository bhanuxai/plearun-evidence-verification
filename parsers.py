
import csv
import json
import re
import io
from pathlib import Path


def read_text_with_fallback(path):
    """Read text while supporting UTF-8 BOM and Windows-1252."""
    raw = path.read_bytes()

    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252")


def extract_json_objects(source):
    """Extract original JSON event object text using source positions."""
    decoder = json.JSONDecoder()
    events = []

    # Locate the events array.
    match = re.search(r'"events"\s*:\s*\[', source)
    if not match:
        return events

    pos = match.end()

    while pos < len(source):
        while pos < len(source) and source[pos] in " \t\r\n,":
            pos += 1

        if pos >= len(source) or source[pos] == "]":
            break

        event, end = decoder.raw_decode(source, pos)

        if isinstance(event, dict):
            events.append((event, source[pos:end]))

        pos = end

    return events


def parse_csv(path):
    """Parse CSV records while preserving exact source text and line numbers."""
    source = read_text_with_fallback(path)
    physical_lines = source.splitlines(keepends=True)

    start_index = 0

    if physical_lines and physical_lines[0].startswith("#PLEARUN"):
        start_index = 1

    csv_source = "".join(physical_lines[start_index:])
    reader = csv.DictReader(io.StringIO(csv_source, newline=""))

    # Read the header first so line tracking starts after it.
    _ = reader.fieldnames
    previous_end_line = reader.line_num

    records = []

    for row in reader:
        end_line = reader.line_num

        start_line = previous_end_line + 1 + start_index
        physical_end_line = end_line + start_index

        raw = "".join(
            physical_lines[start_line - 1:physical_end_line]
        ).rstrip("\r\n")

        previous_end_line = end_line

        if not row or not any(value for value in row.values() if value):
            continue

        records.append({
            "id": f"{path.name}:{start_line}",
            "file": path.name,
            "row": start_line,
            "raw": raw,
            "fields": row,
            "type": "csv"
        })

    return records


def parse_json(path):
    """Parse nested JSON events while preserving their original text."""
    source = read_text_with_fallback(path)
    data = json.loads(source)

    records = []

    for index, (event, raw) in enumerate(
        extract_json_objects(source), start=1
    ):
        records.append({
            "id": f"{path.name}:{event.get('id', index)}",
            "file": path.name,
            "row": index,
            "raw": raw,
            "fields": event,
            "type": "json"
        })

    return records


def parse_vtt(path):
    """Parse WebVTT cues, preserving overlapping cues separately."""
    source = read_text_with_fallback(path)
    lines = source.splitlines()

    records = []
    index = 0
    cue_number = 0

    while index < len(lines):
        line = lines[index].strip()

        if "-->" not in line:
            index += 1
            continue

        timing = line
        cue_number += 1
        index += 1

        text_lines = []

        while index < len(lines) and lines[index].strip():
            text_lines.append(lines[index])
            index += 1

        cue_text = "\n".join(text_lines)

        records.append({
            "id": f"{path.name}:cue:{cue_number}",
            "file": path.name,
            "row": cue_number,
            "raw": timing + "\n" + cue_text,
            "fields": {
                "timing": timing,
                "text": cue_text
            },
            "type": "vtt"
        })

    return records


def load_records(records_dir):
    """Load all supported evidence files from a directory."""
    directory = Path(records_dir)
    records = []

    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue

        suffix = path.suffix.lower()

        try:
            if suffix == ".csv":
                records.extend(parse_csv(path))

            elif suffix == ".json":
                records.extend(parse_json(path))

            elif suffix == ".vtt":
                records.extend(parse_vtt(path))

        except (OSError, UnicodeError, csv.Error, json.JSONDecodeError,
                ValueError) as error:
            raise ValueError(
                f"Could not parse {path.name}: {error}"
            ) from error

    return records

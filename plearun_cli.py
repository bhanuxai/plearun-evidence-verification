
"""Command-line interface for the Plearun evidence verifier."""

import json
import sys
from pathlib import Path

from claim_extractor import extract_claims
from parsers import load_records
from verifier import verify_claims
from clock_sync import analyze_clock_alignment

def read_report(path):
    """Read a report with UTF-8 BOM and Windows-1252 fallback."""

    raw = Path(path).read_bytes()

    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252")


def run(report_path, records_dir):
    """Run the complete claim-verification pipeline."""

    report_text = read_report(report_path)

    claims = extract_claims(report_text)

    records = load_records(records_dir)

    clock_alignment = analyze_clock_alignment(records)

    findings = verify_claims(
        claims,
        records,
        clock_alignment
    )

    return {
        "findings": findings
    }


def main(argv=None):
    """Execute the CLI."""

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 2:
        print(
            "Usage: python plearun_cli.py REPORT RECORDS_DIR",
            file=sys.stderr
        )
        return 2

    report_path, records_dir = argv

    try:
        if not Path(report_path).is_file():
            raise FileNotFoundError(
                f"Report file not found: {report_path}"
            )

        if not Path(records_dir).is_dir():
            raise NotADirectoryError(
                f"Records directory not found: {records_dir}"
            )

        result = run(report_path, records_dir)

        print(json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        ))

        return 0

    except (OSError, UnicodeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

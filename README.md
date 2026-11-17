# Plearun – Evidence Verification CLI

## Overview

A deterministic, offline Python CLI that extracts factual claims from an incident report, retrieves relevant records, and assigns one of four findings: `match`, `conflict`, `not_settled`, or `not_checkable`.

The system prioritizes traceable evidence and avoids unsupported conclusions. Every `match` requires an exact source citation. Unsupported or invalid citations are downgraded to `not_settled`.

## Run

```bash
python plearun_cli.py reports/report_fictional_02.txt records > findings.json
```

Run the test suite:

```bash
make test
```

On Windows without GNU Make:

```bash
python -m unittest discover -s tests -v
```

The implementation uses Python's standard library and works offline.

## How It Works

1. **Parsing (`parsers.py`)** – Loads CSV, nested JSON and WebVTT records. Handles UTF-8 BOM, Windows-1252 encoding, marker lines, multiline CSV fields and overlapping transcript cues. Preserves original evidence text and source row or cue numbers.
2. **Claim extraction (`claim_extractor.py`)** – Extracts factual claims while preserving their original wording and source substrings.
3. **Candidate retrieval (`evidence_matcher.py`)** – Uses normalized lexical overlap to identify potentially relevant records. Retrieval scores do not establish truth.
4. **Clock synchronization (`clock_sync.py`)** – Normalizes supported timestamps and estimates offsets only from repeated, explicitly identified events. Requires multiple consistent anchors and rejects ambiguous duplicate anchors. Unreliable clocks are not aligned.
5. **Verification (`verifier.py`)** – Applies conservative, source-specific checks. Unsupported claims remain `not_settled`; claims that cannot be evaluated from available record types may be `not_checkable`.
6. **Citation validation** – Before a `match` or `conflict` is emitted, the source record, filename, positive row number and exact quote are validated. Invalid citations are downgraded.
7. **CLI (`plearun_cli.py`)** – Connects the pipeline and writes the required JSON structure to standard output.

## Three Hardest Decisions

1. **Evidence versus similarity:** Lexical overlap is used only for candidate retrieval. A relevant-looking record is not automatically proof of a claim.
2. **Vehicle identity and clock uncertainty:** Camera speed readings without a reliable vehicle identifier cannot establish the speed of a particular vehicle. Timestamp similarity alone is not sufficient to infer clock offsets.
3. **Citation integrity:** Original record text and physical row or cue references are preserved. Unsupported evidence is not converted into a confident finding.

## Limitations

- Claim extraction is deterministic and pattern-based; complex, unusual or heavily compound sentences may be missed or split imperfectly.
- Verification rules cover specific evidence patterns rather than every possible factual claim.
- The current implementation does not provide general-purpose contradiction detection. It avoids inventing conflicts when identity, event association or timing is uncertain.
- Naive timestamps and relative transcript timestamps cannot safely be aligned without reliable anchors.
- Lexical retrieval may miss paraphrases, indirect references, negation and domain-specific wording.

## What Would Break First on Real Records?

The biggest risks are ambiguous entity identity, inconsistent device clocks, incomplete metadata, unfamiliar export formats and conflicting or poorly structured records. Larger datasets may also require indexed retrieval and more efficient parsing. Additional source-specific verification rules and stronger entity resolution would be needed before production use.

## Tools Used

- **Python:** Core implementation using the standard library.
- **unittest:** Writing and running automated tests.
- **Git:** Version control.
- **ChatGPT:** Used occasionally as a supporting tool for debugging errors, understanding issues, and reviewing potential edge cases during development. The implementation, code integration, and final decisions were handled by me.

The application runs entirely offline and does not use an LLM or external API at runtime.

No LLM or network service is used at runtime.
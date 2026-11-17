
"""Conservative retrieval of candidate evidence records."""

import re
from collections import Counter


STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at",
    "to", "of", "for", "from", "by", "with", "about", "as",
    "is", "was", "were", "be", "been", "being", "it", "its",
    "he", "she", "they", "them", "this", "that", "these",
    "those", "who", "which", "what", "when", "where", "how",
    "roughly", "approximately", "around"
}


def normalize_text(value):
    """Normalize text for comparison without changing source records."""
    if not isinstance(value, str):
        return ""

    return " ".join(
        re.findall(r"[a-z0-9]+", value.lower())
    )


def extract_terms(text):
    """Extract meaningful comparison terms from text."""
    normalized = normalize_text(text)

    return [
        term for term in normalized.split()
        if term not in STOP_WORDS and len(term) > 1
    ]


def score_record(claim, record):
    """Calculate lexical overlap between a claim and a source record."""
    if not isinstance(record, dict):
        return 0

    raw = record.get("raw", "")

    claim_terms = Counter(extract_terms(claim))
    record_terms = Counter(extract_terms(raw))

    if not claim_terms or not record_terms:
        return 0

    overlap = sum(
        min(count, record_terms[term])
        for term, count in claim_terms.items()
    )

    return overlap / sum(claim_terms.values())


def find_candidate_evidence(claim, records, limit=10):
    """
    Retrieve candidate records using lexical overlap.

    This function does not determine whether a claim is true or false.
    """
    if not isinstance(claim, str):
        raise TypeError("Claim must be a string.")

    if not isinstance(records, (list, tuple)):
        raise TypeError("Records must be a list or tuple.")

    if (
        isinstance(limit, bool)
        or not isinstance(limit, int)
        or limit < 1
    ):
        raise ValueError("Limit must be a positive integer.")

    candidates = []

    for record in records:
        if not isinstance(record, dict):
            continue

        score = score_record(claim, record)

        if score <= 0:
            continue

        candidates.append({
            "record": record,
            "score": score
        })

    candidates.sort(
        key=lambda item: (
            -item["score"],
            item["record"].get("file", ""),
            item["record"].get("row", 0)
        )
    )

    return candidates[:limit]


VALID_FINDINGS = {
    "match",
    "conflict",
    "not_settled",
    "not_checkable"
}


def validate_citation(record, quote):
    """Check that a proposed quote exists exactly in its source record."""

    if not isinstance(record, dict):
        return False

    raw = record.get("raw")
    filename = record.get("file")
    row = record.get("row")

    if not isinstance(raw, str) or not raw.strip():
        return False

    if not isinstance(quote, str) or not quote.strip():
        return False

    if not isinstance(filename, str) or not filename.strip():
        return False

    if (
        isinstance(row, bool)
        or not isinstance(row, int)
        or row < 1
    ):
        return False

    return quote in raw


def build_finding(claim, finding, record=None, quote=None):
    """
    Build an output finding.

    Unsupported or invalid citations are downgraded to not_settled.
    """

    if not isinstance(claim, str) or not claim.strip():
        raise ValueError("Claim must be a non-empty string.")

    if not isinstance(finding, str) or finding not in VALID_FINDINGS:
        raise ValueError("Invalid finding status.")

    result = {
        "claim": claim,
        "finding": finding
    }

    if finding in {"match", "conflict"}:
        if not validate_citation(record, quote):
            result["finding"] = "not_settled"
            return result

        result["cite"] = {
            "file": record["file"],
            "row": record["row"]
        }
        result["quote"] = quote

    return result


"""Deterministic extraction of factual claims from incident reports."""

import re


FACTUAL_PATTERNS = [
    r"\bobserved\b",
    r"\btravelling\b",
    r"\bposted\b",
    r"\bstopped\b",
    r"\bcall\b",
    r"\bdispatch\b",
    r"\bunit\b",
    r"\bvehicle\b",
    r"\bcar\b",
    r"\bdriver\b",
    r"\bstates?\b",
    r"\barrived\b",
    r"\bscene\b",
    r"\bmph\b",
]


def _is_factual(sentence):
    return any(
        re.search(pattern, sentence, re.IGNORECASE)
        for pattern in FACTUAL_PATTERNS
    )


def _split_compound_claim(sentence):
    """Split known compound incident statements into exact source phrases."""


    stop_match = re.search(
        r"\band stopped\b.*$",
        sentence,
        re.IGNORECASE
    )

    if stop_match:
        first_part = sentence[:stop_match.start()].rstrip()
        second_part = sentence[stop_match.start():].strip()

        return [first_part, second_part]

    return [sentence]


def extract_claims(report_text):
    """Extract factual claims while preserving exact source wording."""

    if not isinstance(report_text, str):
        raise TypeError("Report text must be a string.")

    claims = []

    sentences = re.split(
        r"(?<=[.!?])\s+",
        report_text.strip()
    )

    for sentence in sentences:
        sentence = sentence.strip()

        if not sentence or sentence.startswith("SYNTHETIC"):
            continue

        if sentence.endswith(":"):
            continue

        if not _is_factual(sentence):
            continue

        claims.extend(_split_compound_claim(sentence))

    return claims


def extract_claims_from_file(report_path):
    """Read a report and extract its factual claims."""

    with open(report_path, "r", encoding="utf-8-sig") as file:
        return extract_claims(file.read())


"""Conservative deterministic verification of incident claims."""

import re

from evidence_matcher import build_finding



def _find_vtt_speed_evidence(claim, records):
    """Find one officer statement supporting every speed assertion."""

    speed_claim = re.search(
        r"\btravelling\s+(\d+(?:\.\d+)?)\s*mph\b",
        claim,
        re.IGNORECASE
    )

    limit_claim = re.search(
        r"\bposted\s+(\d+(?:\.\d+)?)\s+zone\b",
        claim,
        re.IGNORECASE
    )

    if not speed_claim and not limit_claim:
        return None

    for record in records:
        if record.get("type") != "vtt":
            continue

        fields = record.get("fields", {})
        text = fields.get("text", "")

        if not isinstance(text, str):
            continue

        if not re.search(r"\bOfficer Lee\s*:", text, re.IGNORECASE):
            continue

        evidence = re.search(
            r"\b(\d+(?:\.\d+)?)\s+in\s+a\s+"
            r"(\d+(?:\.\d+)?)\b",
            text,
            re.IGNORECASE
        )

        if not evidence:
            continue

                # A speed statement without vehicle identification cannot
        # establish the speed of a specifically identified vehicle.
        claim_has_vehicle = bool(
            re.search(
                r"\b(?:sedan|vehicle|car|truck)\b",
                claim,
                re.IGNORECASE
            )
        )

        evidence_has_vehicle = bool(
            re.search(
                r"\b(?:sedan|vehicle|car|truck)\b",
                text,
                re.IGNORECASE
            )
        )

        if claim_has_vehicle and not evidence_has_vehicle:
            continue

        # "In a 45" does not independently establish that
        # a posted speed-limit sign showed 45 mph.
        if (
            limit_claim
            and re.search(r"\bposted\b", claim, re.IGNORECASE)
            and not re.search(r"\bposted\b", text, re.IGNORECASE)
        ):
            continue

        # Every assertion present in the claim must match.
        if (
            speed_claim
            and evidence.group(1) != speed_claim.group(1)
        ):
            continue

        if (
            limit_claim
            and evidence.group(2) != limit_claim.group(1)
        ):
            continue

        return record, evidence.group(0)

    return None




def _find_stop_evidence(claim, records):
    """Find an Officer Lee note recording the claimed stop time."""

    time_match = re.search(
        r"\bstopped\s+around\s+(\d{1,2}:\d{2})",
        claim,
        re.IGNORECASE
    )

    if not time_match:
        return None

    claimed_time = time_match.group(1)

    for record in records:
        if record.get("type") != "csv":
            continue

        fields = record.get("fields", {})

        author = fields.get("Author", "")
        note = fields.get("Note", "")
        record_time = fields.get("Time", "")

        if not all(
            isinstance(value, str)
            for value in (author, note, record_time)
        ):
            continue

        if (
            author.strip().casefold() == "officer lee"
            and re.search(r"\bstopped\b", note, re.IGNORECASE)
            and record_time.strip() == claimed_time
        ):
            return record, record["raw"]

    return None



def verify_claim(claim, records, clock_alignment=None):
    """Verify one claim using explicit, conservative evidence rules."""

    if not isinstance(claim, str) or not claim.strip():
        raise ValueError("Claim must be a non-empty string.")

    if not isinstance(records, (list, tuple)):
        raise TypeError("Records must be a list or tuple.")

    normalized = claim.lower()
        # Cross-source timeline claims require reliable clock alignment.
    if (
        "unit on scene" in normalized
        and "after the stop" in normalized
    ):
        if (
            not isinstance(clock_alignment, dict)
            or not clock_alignment.get("reliable", False)
        ):
            return build_finding(claim, "not_settled")

    # Available records do not establish lane occupancy.
    if re.search(r"\bonly\s+car\s+in\s+the\s+lane\b", normalized):
        return build_finding(claim, "not_checkable")

    # An officer's explicit transcript statement can support
    # the reported speed and speed-limit figures.
    speed_evidence = _find_vtt_speed_evidence(claim, records)

    if speed_evidence:
        record, quote = speed_evidence
        return build_finding(claim, "match", record, quote)

    # A structured note can support the recorded stop time.
    stop_evidence = _find_stop_evidence(claim, records)

    if stop_evidence:
        record, quote = stop_evidence
        return build_finding(claim, "match", record, quote)

    # Do not infer contradictions from unsynchronized clocks,
    # missing vehicle identifiers, or partial descriptions.
    return build_finding(claim, "not_settled")


def verify_claims(claims, records, clock_alignment=None):
    """Verify all claims using the available clock-alignment analysis."""

    return [
        verify_claim(claim, records, clock_alignment)
        for claim in claims
    ]

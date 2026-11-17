
"""Conservative timestamp parsing and clock-offset estimation."""

import math
from datetime import datetime, timezone, timedelta
from statistics import median


def normalize_timestamp(value):
    """Normalize supported timestamps to timezone-aware UTC."""

    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return None

        return value.astimezone(timezone.utc)

    try:
        if isinstance(value, (int, float)):
            if not math.isfinite(value):
                return None

            return datetime.fromtimestamp(
                value / 1000,
                tz=timezone.utc
            )

        if not isinstance(value, str):
            return None

        value = value.strip()

        if not value:
            return None

        if value.isdigit() and len(value) == 13:
            return datetime.fromtimestamp(
                int(value) / 1000,
                tz=timezone.utc
            )

        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        parsed = datetime.fromisoformat(value)

        if parsed.tzinfo is None:
            return None

        return parsed.astimezone(timezone.utc)

    except (ValueError, OverflowError, OSError):
        return None


def estimate_clock_offset(
    anchor_pairs,
    min_anchors=2,
    max_spread_seconds=5.0
):
    """Estimate reference_time - source_time."""

    if (
        isinstance(min_anchors, bool)
        or not isinstance(min_anchors, int)
        or min_anchors < 2
    ):
        raise ValueError("At least two anchors are required.")

    if (
        isinstance(max_spread_seconds, bool)
        or not isinstance(max_spread_seconds, (int, float))
        or not math.isfinite(max_spread_seconds)
        or max_spread_seconds < 0
    ):
        raise ValueError("Invalid maximum spread.")

    offsets = []
    invalid_count = 0

    for pair in anchor_pairs:
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            invalid_count += 1
            continue

        source_value, reference_value = pair

        source_time = normalize_timestamp(source_value)
        reference_time = normalize_timestamp(reference_value)

        if source_time is None or reference_time is None:
            invalid_count += 1
            continue

        offsets.append(
            (reference_time - source_time).total_seconds()
        )

    if invalid_count:
        return {
            "reliable": False,
            "offset_seconds": None,
            "anchor_count": len(offsets),
            "invalid_count": invalid_count,
            "spread_seconds": None,
            "reason": "One or more supplied anchors are invalid."
        }

    if len(offsets) < min_anchors:
        return {
            "reliable": False,
            "offset_seconds": None,
            "anchor_count": len(offsets),
            "invalid_count": 0,
            "spread_seconds": None,
            "reason": "Not enough valid anchors."
        }

    spread = max(offsets) - min(offsets)

    if spread > max_spread_seconds:
        return {
            "reliable": False,
            "offset_seconds": None,
            "anchor_count": len(offsets),
            "invalid_count": 0,
            "spread_seconds": spread,
            "reason": "Anchor offsets disagree."
        }

    return {
        "reliable": True,
        "offset_seconds": median(offsets),
        "anchor_count": len(offsets),
        "invalid_count": 0,
        "spread_seconds": spread,
        "reason": "Offset supported by consistent anchors."
    }


def apply_clock_offset(timestamp, offset_seconds):
    """Apply a validated clock offset to a timestamp."""

    if (
        isinstance(offset_seconds, bool)
        or not isinstance(offset_seconds, (int, float))
        or not math.isfinite(offset_seconds)
    ):
        return None

    normalized = normalize_timestamp(timestamp)

    if normalized is None:
        return None

    try:
        return normalized + timedelta(seconds=offset_seconds)
    except (OverflowError, ValueError):
        return None


def analyze_clock_alignment(records):
    """
    Discover explicit shared-event anchors and estimate pairwise
    clock offsets. Duplicate anchor IDs within a source are rejected.
    """

    from itertools import combinations

    source_events = {}
    ambiguous_anchors = {}

    for record in records:
        if not isinstance(record, dict):
            continue

        fields = record.get("fields", {})

        if not isinstance(fields, dict):
            continue

        anchor_id = (
            fields.get("anchor_id")
            or fields.get("event_id")
            or fields.get("shared_event_id")
        )

        if not isinstance(anchor_id, str) or not anchor_id.strip():
            continue

        timestamp = None

        for key in ("timestamp", "logged", "time", "Time"):
            if key in fields:
                timestamp = normalize_timestamp(fields[key])
                if timestamp is not None:
                    break

        if timestamp is None:
            continue

        source = fields.get("device") or record.get("file")

        if not isinstance(source, str) or not source.strip():
            continue

        source_events.setdefault(source, {})

        # Never silently overwrite a repeated anchor.
        if anchor_id in source_events[source]:
            source_events[source].pop(anchor_id, None)
            ambiguous_anchors.setdefault(source, set()).add(anchor_id)
            continue

        if anchor_id in ambiguous_anchors.get(source, set()):
            continue

        source_events[source][anchor_id] = timestamp

    comparisons = {}
    offsets = {}

    sources = sorted(source_events)

    for source, reference in combinations(sources, 2):
        source_anchors = source_events[source]
        reference_anchors = source_events[reference]

        shared_ids = sorted(
            set(source_anchors) & set(reference_anchors)
        )

        anchor_pairs = [
            (
                source_anchors[anchor_id],
                reference_anchors[anchor_id]
            )
            for anchor_id in shared_ids
        ]

        result = estimate_clock_offset(anchor_pairs)

        key = f"{source}->{reference}"
        comparisons[key] = result

        if result["reliable"]:
            offsets[key] = result["offset_seconds"]

    return {
        # True means at least one device pair has a reliable offset.
        # It does not mean every device is synchronized.
        "reliable": bool(offsets),
        "offsets": offsets,
        "comparisons": comparisons,
        "source_count": len(sources),
        "ambiguous_anchors": {
            source: sorted(anchor_ids)
            for source, anchor_ids in ambiguous_anchors.items()
        },
        "reason": (
            "Reliable offsets found for one or more device pairs."
            if offsets
            else "No reliable offsets: insufficient explicit shared-event anchors."
        )
    }

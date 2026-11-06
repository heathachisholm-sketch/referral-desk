"""Tool: route_case — assign a generic administrative queue. Deterministic.

This is administrative triage only. It contains NONE of Mended Skin's provider
matching or ranking logic — cases are sorted into generic queues a human team
would already have. Ambiguous cases go to General Navigation rather than being
forced into a clinical queue.
"""
from __future__ import annotations

from ..models import QUEUES

# Ordered keyword rules. First match wins; order encodes priority.
_RULES: list[tuple[str, list[str]]] = [
    ("camouflage_tattoo", ["camouflage", "tattoo", "cover-up", "cover up",
                           "makeup", "conceal"]),
    ("clinical_consultation", ["consult", "specialist", "dermatolog", "surgeon",
                               "clinician", "see someone", "who should i see",
                               "professional"]),
    ("post_procedure", ["post-procedure", "post procedure", "post-op", "post op",
                        "after surgery", "recovery", "healing", "just had",
                        "aftercare"]),
    ("scar_therapy", ["therapy", "silicone", "massage", "soften", "flatten",
                      "reduce", "support", "treatment options"]),
]

_AMBIGUOUS = ["not sure", "don't know", "dont know", "no idea", "unsure",
              "where to start", "where do i start"]


def route_case(desired_support: str | None, raw_text: str = "") -> dict:
    """Return {"queue_id", "queue_name"} for the case.

    Args:
        desired_support: Structured "type of help wanted" (may be None).
        raw_text: Original enquiry text, used as a secondary signal.
    """
    blob = f"{desired_support or ''} {raw_text}".lower()

    if any(k in blob for k in _AMBIGUOUS) or not (desired_support or "").strip():
        # No clear ask -> navigate the person, don't invent a clinical route.
        if not any(any(k in blob for k in kws) for _, kws in _RULES):
            return _q("general_navigation")

    for queue_id, keywords in _RULES:
        if any(k in blob for k in keywords):
            return _q(queue_id)

    return _q("manual_review")


def _q(queue_id: str) -> dict:
    return {"queue_id": queue_id, "queue_name": QUEUES[queue_id]}

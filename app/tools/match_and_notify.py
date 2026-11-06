"""Tool: match_and_notify — availability-only front-office handoff (simulated).

A generic operational step: shortlist clinics that are currently accepting
enquiries and simulate notifying their front office. Deliberately
availability-only — no scar-type or provider-matching logic (that stays in the
private production system). No real message is sent; the notification is
recorded so the action is auditable.
"""
from __future__ import annotations

from ..clinics import CLINICS


def match_and_notify(area: str, queue_name: str, case_id: str) -> dict:
    """Shortlist available clinics and simulate notifying their front office.

    Args:
        area: The patient's location (for the note text only; not a filter).
        queue_name: The administrative queue the case was routed to.
        case_id: The case reference to include in the note.

    Returns:
        {"notified": [{"name","area","note"}], "skipped": [{"name","area"}]}
    """
    notified, skipped = [], []
    for c in CLINICS:
        if c.get("accepting_enquiries"):
            note = (
                f"Case {case_id} ready for review — {queue_name}"
                + (f", enquiry from {area}" if area else "")
                + ". Please confirm capacity to take this referral."
            )
            notified.append({"name": c["name"], "area": c["area"], "note": note})
        else:
            skipped.append({"name": c["name"], "area": c["area"]})
    return {"notified": notified, "skipped": skipped}

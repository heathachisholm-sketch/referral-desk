"""Tool: create_referral_packet — human-readable summary (Gemini + template)."""
from __future__ import annotations

from .. import gemini_client


def create_referral_packet(case_id: str, structured: dict, image_status: str,
                           queue_name: str) -> str:
    """Produce a formatted referral packet for an administrator to action.

    The narrative summary is written by Gemini; the packet envelope (IDs,
    status, queue) is assembled deterministically so key facts can't drift.
    """
    body = gemini_client.summarise_packet(structured, image_status, queue_name)
    return (
        f"REFERRAL PACKET #{case_id}\n"
        f"{'-' * 44}\n"
        f"{body}\n"
        f"{'-' * 44}\n"
        f"Status: READY FOR REFERRAL\n"
        f"Queue: {queue_name}\n"
        f"Note: administrative preparation only — no diagnosis or treatment "
        f"recommendation has been made."
    )


def create_follow_up(missing: list[str]) -> str:
    """Deterministic follow-up request when information is missing."""
    asks = {
        "location": "your location (town or postcode)",
        "approximate scar age": "roughly how long you have had the scar",
        "a clearer photo": "another photo taken in good light with the area "
                           "clearly visible",
    }
    parts = [asks.get(m, m) for m in missing]
    if len(parts) == 1:
        needed = parts[0]
    else:
        needed = ", ".join(parts[:-1]) + f" and {parts[-1]}"
    return (
        f"Thanks for getting in touch. To prepare your enquiry we just need "
        f"{needed}. Once you add that, we'll get it ready for the right team."
    )

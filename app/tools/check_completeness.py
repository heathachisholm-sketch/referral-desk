"""Tool: check_completeness — deterministic gate. No LLM. Rules control here."""
from __future__ import annotations

from ..models import ImageStatus


def check_completeness(structured: dict, image_status: str,
                       has_photo: bool) -> dict:
    """Decide whether the case has enough information to be referral-ready.

    This is pure Python on purpose: the workflow decision must be auditable and
    reproducible, not a probabilistic model output.

    Required for a referral-ready case:
      - geographic_location present
      - scar_age present
      - if a photo was supplied, it must be USABLE
    (desired_support may be absent — that routes to General Navigation rather
    than blocking, so the system never forces a clinical choice.)

    Returns a dict with per-field booleans, a `missing` list, and `ready` bool.
    """
    location_ok = bool(structured.get("geographic_location"))
    scar_age_ok = bool(structured.get("scar_age"))
    photo_ok = (not has_photo) or (image_status == ImageStatus.USABLE.value)
    support_present = bool(structured.get("desired_support"))

    missing: list[str] = []
    if not location_ok:
        missing.append("location")
    if not scar_age_ok:
        missing.append("approximate scar age")
    if has_photo and not photo_ok:
        missing.append("a clearer photo")

    return {
        "location_supplied": location_ok,
        "scar_age_supplied": scar_age_ok,
        "photo_usable": photo_ok,
        "desired_support_supplied": support_present,
        "missing": missing,
        "ready": len(missing) == 0,
    }

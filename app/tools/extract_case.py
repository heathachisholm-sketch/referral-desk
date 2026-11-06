"""Tool: extract_case — turn free text into structured intake JSON (Gemini)."""
from __future__ import annotations

from .. import gemini_client


def extract_case(raw_text: str, location_hint: str = "",
                 support_hint: str = "") -> dict:
    """Extract structured intake fields from a free-text scar-care enquiry.

    Uses Gemini for interpretation only. Never diagnoses or infers scar type.

    Args:
        raw_text: The patient's unstructured description.
        location_hint: Optional location supplied via a form field.
        support_hint: Optional "type of help wanted" supplied via a form field.

    Returns:
        A dict with keys: scar_location, cause_context, scar_age, previous_care,
        desired_support, geographic_location, preferences, missing_information.
    """
    return gemini_client.extract_structured(raw_text, location_hint, support_hint)

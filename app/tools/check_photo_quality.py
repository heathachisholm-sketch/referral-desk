"""Tool: check_photo_quality — is the photo USABLE for referral prep? (Gemini)."""
from __future__ import annotations

from typing import Optional

from .. import gemini_client


def check_photo_quality(image_bytes: Optional[bytes] = None,
                        mime_type: str = "image/jpeg",
                        mock_status: Optional[str] = None) -> dict:
    """Assess whether an uploaded photo is usable for referral preparation.

    Deliberately NON-clinical: judges lighting, focus, distance and framing
    only. Never assesses diagnosis, malignancy, severity or treatment.

    Args:
        image_bytes: Raw image bytes, or None if no photo was supplied.
        mime_type: MIME type of the image.
        mock_status: Force a result in mock mode ("USABLE"/"RETAKE_REQUIRED").

    Returns:
        {"status": "USABLE"|"RETAKE_REQUIRED", "reason": str}
    """
    return gemini_client.assess_image(image_bytes, mime_type, mock_status)

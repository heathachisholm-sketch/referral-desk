"""
Thin wrapper around the Google GenAI SDK (google-genai).

Two responsibilities:
  1. Structured text extraction (Gemini, JSON output).
  2. Multimodal image usability assessment (Gemini, image + prompt).

In MOCK mode every call is served locally with deterministic logic, so the
workflow — and the demo — runs with no credentials and no network. The real
and mock code paths return identical shapes, so nothing downstream cares which
one ran.
"""
from __future__ import annotations

import json
import re
from typing import Optional

from . import config

_client = None


def _get_client():
    """Lazily construct the GenAI client so mock runs need no google deps."""
    global _client
    if _client is not None:
        return _client
    from google import genai  # imported lazily on purpose

    if config.USE_VERTEX:
        _client = genai.Client(
            vertexai=True,
            project=config.GCP_PROJECT,
            location=config.GCP_LOCATION,
        )
    else:
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client


# --------------------------------------------------------------------------- #
# Structured extraction
# --------------------------------------------------------------------------- #
EXTRACTION_SYSTEM = """You are an intake assistant for a scar-care referral desk.
Extract ONLY what the patient explicitly states. Do not diagnose, do not infer a
scar type, do not suggest treatment. If a field is not stated, use null.
Return STRICT JSON with exactly these keys:
scar_location, cause_context, scar_age, previous_care, desired_support,
geographic_location, preferences, missing_information (array of strings).
"""


def extract_structured(raw_text: str, location_hint: str = "",
                       support_hint: str = "") -> dict:
    if config.MOCK_MODE:
        return _mock_extract(raw_text, location_hint, support_hint)
    try:
        client = _get_client()
        prompt = (
            f"{EXTRACTION_SYSTEM}\n\nPatient enquiry:\n\"\"\"{raw_text}\"\"\"\n"
            f"Location field (may be blank): {location_hint}\n"
            f"Desired support field (may be blank): {support_hint}\n"
            "Return only the JSON object."
        )
        resp = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        data = _loads(resp.text)
        # Prefer explicit form fields when the model left them blank.
        if location_hint and not data.get("geographic_location"):
            data["geographic_location"] = location_hint
        if support_hint and not data.get("desired_support"):
            data["desired_support"] = support_hint
        return data
    except Exception as exc:  # graceful degradation, never crash the pipeline
        fallback = _mock_extract(raw_text, location_hint, support_hint)
        fallback["_degraded"] = f"gemini_extract_failed: {exc}"
        return fallback


# --------------------------------------------------------------------------- #
# Multimodal image usability (NON-clinical: framing/lighting only)
# --------------------------------------------------------------------------- #
IMAGE_SYSTEM = """You assess whether a photo is USABLE for administrative referral
preparation. Judge ONLY framing and clarity: lighting, focus, distance, whether
the described area is visible. Do NOT diagnose, grade, or comment on any medical
feature. Return STRICT JSON: {"status": "USABLE"|"RETAKE_REQUIRED", "reason": str}.
"""


def assess_image(image_bytes: Optional[bytes], mime_type: str = "image/jpeg",
                 mock_status: Optional[str] = None) -> dict:
    if config.MOCK_MODE or image_bytes is None:
        return _mock_image(mock_status)
    try:
        from google.genai import types
        client = _get_client()
        resp = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                IMAGE_SYSTEM,
            ],
            config={"response_mime_type": "application/json"},
        )
        return _loads(resp.text)
    except Exception as exc:
        out = _mock_image(mock_status)
        out["reason"] = f"{out['reason']} (image check degraded: {exc})"
        return out


# --------------------------------------------------------------------------- #
# Referral summary
# --------------------------------------------------------------------------- #
PACKET_SYSTEM = """Write a concise, neutral referral summary for an administrator.
Use only the provided structured facts. Do not add clinical opinion, diagnosis or
treatment advice. Plain professional English, no marketing language.
"""


def summarise_packet(structured: dict, image_status: str, queue_name: str) -> str:
    if config.MOCK_MODE:
        return _mock_packet(structured, image_status, queue_name)
    try:
        client = _get_client()
        prompt = (
            f"{PACKET_SYSTEM}\n\nStructured facts (JSON):\n"
            f"{json.dumps(structured, indent=2)}\n"
            f"Image quality: {image_status}\nRouted queue: {queue_name}\n"
            "Write 3-5 short lines."
        )
        resp = client.models.generate_content(
            model=config.GEMINI_MODEL, contents=prompt
        )
        return (resp.text or "").strip() or _mock_packet(
            structured, image_status, queue_name
        )
    except Exception:
        return _mock_packet(structured, image_status, queue_name)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _loads(text: str) -> dict:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*", "", text).rstrip("`").strip()
    return json.loads(text)


# ------------------------------- MOCK LOGIC -------------------------------- #
_LOCATIONS = [
    "london", "manchester", "birmingham", "leeds", "glasgow", "edinburgh",
    "bristol", "liverpool", "cardiff", "sheffield", "newcastle", "nottingham",
]
_BODY = ["shoulder", "face", "cheek", "arm", "leg", "chest", "back", "abdomen",
         "neck", "hand", "knee", "forehead", "chin"]


_WORD_NUM = {
    "a": "1", "an": "1", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "ten": "10", "eleven": "11", "twelve": "12", "eighteen": "18",
}


def _parse_age(low: str) -> Optional[str]:
    # digit form: "2 years", "6 months ago"
    m = re.search(r"(\d+)\s*(year|yr|month|week)s?", low)
    if m:
        return f"approximately {m.group(1)} {m.group(2)}s"
    # word form: "six months ago", "a year ago"
    m = re.search(r"\b(" + "|".join(_WORD_NUM) + r")\s+(year|month|week)s?", low)
    if m:
        return f"approximately {_WORD_NUM[m.group(1)]} {m.group(2)}s"
    if "years ago" in low or "year ago" in low:
        return "approximately a year or more"
    return None


def _find(words: list[str], text: str) -> Optional[str]:
    low = text.lower()
    for w in words:
        if w in low:
            return w
    return None


def _mock_extract(raw_text: str, location_hint: str, support_hint: str) -> dict:
    low = raw_text.lower()
    loc = location_hint or _find(_LOCATIONS, raw_text)
    body = _find(_BODY, raw_text)

    age = _parse_age(low)

    prev = None
    for care in ["silicone", "steroid", "laser", "massage", "cream", "gel",
                 "pressure garment", "surgery"]:
        if care in low:
            prev = care
            break

    support = support_hint or None
    if support is None:
        if any(k in low for k in ["camouflage", "tattoo", "cover up", "makeup"]):
            support = "camouflage or cover-up"
        elif any(k in low for k in ["consult", "specialist", "dermatolog",
                                     "surgeon", "see someone", "who should i see"]):
            support = "clinical consultation"
        elif any(k in low for k in ["therapy", "silicone", "massage", "reduce",
                                     "soften", "flatten"]):
            support = "scar therapy or support"
        elif any(k in low for k in ["after surgery", "post-op", "post op",
                                     "recovery", "healing", "just had"]):
            support = "post-procedure information"
        elif any(k in low for k in ["not sure", "don't know", "dont know",
                                     "no idea", "unsure", "where to start"]):
            support = None  # deliberately ambiguous -> navigation

    cause = None
    if "surgery" in low or "operation" in low or "op " in low:
        cause = "following surgery"
    elif "burn" in low:
        cause = "following a burn"
    elif "acne" in low:
        cause = "acne-related"
    elif "accident" in low or "injury" in low:
        cause = "following an injury"

    missing = []
    if not loc:
        missing.append("geographic_location")
    if not age:
        missing.append("scar_age")
    if support is None:
        missing.append("desired_support")

    return {
        "scar_location": body,
        "cause_context": cause,
        "scar_age": age,
        "previous_care": prev,
        "desired_support": support,
        "geographic_location": loc.title() if loc else None,
        "preferences": None,
        "missing_information": missing,
    }


def _mock_image(mock_status: Optional[str]) -> dict:
    if mock_status == "RETAKE_REQUIRED":
        return {"status": "RETAKE_REQUIRED",
                "reason": "Image is too dark and the area is not clearly visible."}
    return {"status": "USABLE",
            "reason": "Area is in focus, well lit and clearly framed."}


def _mock_packet(structured: dict, image_status: str, queue_name: str) -> str:
    g = structured
    lines = [
        f"Reason for enquiry: {g.get('cause_context') or 'Scar-care enquiry'}; "
        f"patient seeking {g.get('desired_support') or 'guidance on next steps'}.",
        f"Scar location: {g.get('scar_location') or 'not specified'}.",
        f"Patient-provided history: age {g.get('scar_age') or 'not stated'}; "
        f"previous care {g.get('previous_care') or 'none stated'}.",
        f"Geographic location: {g.get('geographic_location') or 'not stated'}.",
        f"Image quality: {image_status}.",
        f"Suggested administrative queue: {queue_name}.",
    ]
    return "\n".join(lines)

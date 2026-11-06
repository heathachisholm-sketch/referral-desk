"""
Google ADK agent for The Referral Desk.

This is a genuine second implementation of the workflow using Google's Agent
Development Kit. The FastAPI app runs the deterministic pipeline (reliable for a
live demo); this ADK agent exposes the SAME tools to an LlmAgent so the agent's
reasoning/tool-calls can be shown in the ADK dev UI during the demo.

Run it:
    pip install google-adk
    export GEMINI_API_KEY=...            # or configure Vertex (see README)
    adk web        # visual dev UI at http://localhost:8000
    # or: adk run agent

If ADK setup is not available, nothing is lost — the pipeline path already
satisfies every hackathon requirement (Gemini 3.5 + GenAI SDK + Cloud Run +
Firestore).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make the sibling `app` package importable when ADK loads this module.
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import config                                    # noqa: E402
from app.tools import (                                   # noqa: E402
    check_completeness as _check_completeness,
    create_referral_packet as _create_packet,
    extract_case as _extract_case,
    match_and_notify as _match_and_notify,
    route_case as _route_case,
)


# --- ADK-friendly tool wrappers (JSON-serialisable args only) --------------- #
def extract_case(raw_text: str, location_hint: str = "",
                 support_hint: str = "") -> dict:
    """Extract structured intake fields from a free-text scar-care enquiry.

    Interpretation only — never diagnoses or infers a scar type.
    Returns keys: scar_location, cause_context, scar_age, previous_care,
    desired_support, geographic_location, preferences, missing_information.
    """
    return _extract_case(raw_text, location_hint, support_hint)


def assess_photo_status(has_photo: bool, described_quality: str = "usable") -> dict:
    """Record whether a supplied photo is usable for referral preparation.

    Non-clinical: framing/lighting only. The real multimodal check runs in the
    pipeline; here the agent records the outcome.
    Returns {"status": "USABLE"|"RETAKE_REQUIRED"|"NOT_PROVIDED"}.
    """
    if not has_photo:
        return {"status": "NOT_PROVIDED"}
    bad = any(w in described_quality.lower()
              for w in ["dark", "blur", "far", "obscure", "unclear", "retake"])
    return {"status": "RETAKE_REQUIRED" if bad else "USABLE"}


def check_completeness(structured: dict, image_status: str,
                       has_photo: bool) -> dict:
    """Deterministically decide whether a case is referral-ready.

    Returns per-field booleans, a `missing` list, and `ready` (bool).
    """
    return _check_completeness(structured, image_status, has_photo)


def route_case(desired_support: str = "", raw_text: str = "") -> dict:
    """Assign a generic administrative queue. Returns {queue_id, queue_name}."""
    return _route_case(desired_support or None, raw_text)


def create_referral_packet(case_id: str, structured: dict, image_status: str,
                           queue_name: str) -> str:
    """Produce a human-readable referral packet for an administrator."""
    return _create_packet(case_id, structured, image_status, queue_name)


def match_and_notify(area: str = "", queue_name: str = "",
                     case_id: str = "") -> dict:
    """Shortlist clinics currently accepting enquiries and simulate notifying
    their front office. Availability only — no scar-type/matching logic.
    Returns {"notified": [...], "skipped": [...]}.
    """
    return _match_and_notify(area, queue_name, case_id)


INSTRUCTION = """You are the Referral Desk agent for a scar-care service.
Follow this standard operating procedure exactly, calling one tool per step:

1. Call extract_case on the enquiry text (pass any location/support hints).
2. Call assess_photo_status with whether a photo was provided.
3. Call check_completeness with the structured data, image status and has_photo.
4. If completeness.ready is false: STOP and tell the user, in one short warm
   sentence, exactly what is missing. Do not route or create a packet.
5. If ready: call route_case, then create_referral_packet, then
   match_and_notify to shortlist available clinics and notify their front
   office, then report the queue and which clinics were notified.

Hard rules:
- You interpret and summarise. You never diagnose, grade, or recommend treatment.
- You never invent facts the user did not provide.
- Deterministic tools own the ready/route decision — respect their output.
- The handoff is availability-only; never claim a clinical match.
"""

try:
    from google.adk.agents import Agent

    root_agent = Agent(
        name="referral_desk",
        model=config.GEMINI_MODEL,
        description="Turns a patient's scar-care enquiry into a referral-ready case.",
        instruction=INSTRUCTION,
        tools=[
            extract_case,
            assess_photo_status,
            check_completeness,
            route_case,
            create_referral_packet,
            match_and_notify,
        ],
    )
except Exception as _exc:  # ADK not installed — import-safe for pipeline users
    root_agent = None
    _ADK_IMPORT_ERROR = _exc

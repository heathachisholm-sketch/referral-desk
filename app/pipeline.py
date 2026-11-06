"""
The orchestrator.

A deterministic sequence controls the workflow; Gemini is invoked only inside
individual tools for interpretation. This is the "rules control, AI interprets"
boundary made concrete. Every transition is logged and persisted, so the audit
trail is real operational evidence rather than generated prose.

The workflow is a closed loop: when information is missing the agent drafts a
follow-up and waits; when the patient replies, `resume_with_reply` merges the
new information and re-runs the case from extraction until it is referral-ready.

The same five tools are also registered with an ADK agent in agent/agent.py.
"""
from __future__ import annotations

from typing import Optional

from . import store
from .models import Case, CaseState, ImageStatus, StructuredCase
from .tools import (
    check_completeness,
    check_photo_quality,
    create_referral_packet,
    extract_case,
    match_and_notify,
    route_case,
)
from .tools.create_referral_packet import create_follow_up


def run_pipeline(case: Case, image_bytes: Optional[bytes] = None,
                 mime_type: str = "image/jpeg",
                 mock_image_status: Optional[str] = None) -> Case:
    """Create a new case and process it from the top."""
    case.set_state(CaseState.NEW)
    case.log("CASE_CREATED", f"Intake received (photo: {case.has_photo}).")
    store.save(case)
    return _process(case, image_bytes, mime_type, mock_image_status,
                    reassess_image=True)


def resume_with_reply(case: Case, new_text: str = "", new_location: str = "",
                      new_support: str = "", image_bytes: Optional[bytes] = None,
                      mime_type: str = "image/jpeg",
                      mock_image_status: Optional[str] = None) -> Case:
    """Merge a patient's reply into an existing case and re-process it.

    This closes the loop: an incomplete case that produced a follow-up can be
    completed by the patient and carried through to referral without starting
    over.
    """
    if new_text.strip():
        prefix = "\n\n" if case.raw_text else ""
        case.raw_text = f"{case.raw_text}{prefix}[Patient reply] {new_text.strip()}"
    if new_location.strip():
        case.location_input = new_location.strip()
    if new_support.strip():
        case.desired_support_input = new_support.strip()

    new_photo = image_bytes is not None or mock_image_status is not None
    if new_photo:
        case.has_photo = True

    # Clear the transient follow-up; a fresh decision will be made.
    case.follow_up_message = None
    case.log("INFORMATION_RECEIVED", "Patient supplied additional information.")
    store.save(case)
    return _process(case, image_bytes, mime_type, mock_image_status,
                    reassess_image=new_photo)


def _process(case: Case, image_bytes: Optional[bytes], mime_type: str,
             mock_image_status: Optional[str], reassess_image: bool) -> Case:
    """Shared core: extract -> image -> completeness -> branch -> route/packet."""
    try:
        # 1) Extract structured intake (Gemini) --------------------------------
        raw = extract_case(case.raw_text, case.location_input,
                           case.desired_support_input)
        degraded = raw.pop("_degraded", None)
        case.structured = StructuredCase(
            scar_location=raw.get("scar_location"),
            cause_context=raw.get("cause_context"),
            scar_age=raw.get("scar_age"),
            previous_care=raw.get("previous_care"),
            desired_support=raw.get("desired_support"),
            geographic_location=raw.get("geographic_location"),
            preferences=raw.get("preferences"),
            missing_information=raw.get("missing_information") or [],
        )
        case.set_state(CaseState.EXTRACTED)
        detail = "Structured intake extracted."
        if degraded:
            detail += f" [degraded->mock: {degraded}]"
        case.log("EXTRACTED", detail)
        store.save(case)

        # 2) Photo usability (Gemini multimodal) -------------------------------
        if reassess_image:
            if case.has_photo:
                result = check_photo_quality(image_bytes, mime_type,
                                             mock_status=mock_image_status)
                case.image_status = ImageStatus(result.get("status", "USABLE"))
                case.image_reason = result.get("reason")
            else:
                case.image_status = ImageStatus.NOT_PROVIDED
            image_detail = f"Image status: {case.image_status.value}" + (
                f" — {case.image_reason}" if case.image_reason else "")
        else:
            image_detail = (f"Image status: {case.image_status.value} "
                            f"(carried over).")
        case.set_state(CaseState.IMAGE_CHECKED)
        case.log("IMAGE_CHECKED", image_detail)
        store.save(case)

        # 3) Completeness (deterministic) --------------------------------------
        structured_dict = case.structured.__dict__
        completeness = check_completeness(structured_dict,
                                          case.image_status.value, case.has_photo)
        case.completeness = completeness
        case.set_state(CaseState.COMPLETENESS_CHECKED)
        case.log("COMPLETENESS_CHECKED",
                 f"Ready: {completeness['ready']}; "
                 f"missing: {completeness['missing'] or 'none'}.")
        store.save(case)

        # 4a) Missing info -> autonomous follow-up, then wait for a reply ------
        if not completeness["ready"]:
            case.follow_up_message = create_follow_up(completeness["missing"])
            case.set_state(CaseState.NEEDS_INFORMATION)
            case.log("NEEDS_INFORMATION",
                     "Generated a follow-up request and paused for the "
                     "patient's reply.")
            store.save(case)
            return case

        # 4b) Route (deterministic) --------------------------------------------
        routed = route_case(case.structured.desired_support, case.raw_text)
        case.queue_id = routed["queue_id"]
        case.queue_name = routed["queue_name"]
        case.set_state(CaseState.REFERRAL_READY)
        case.log("REFERRAL_READY", f"Routed to queue: {case.queue_name}.")
        store.save(case)

        # 5) Referral packet (Gemini summary + deterministic envelope) ---------
        case.referral_packet = create_referral_packet(
            case.id, structured_dict, case.image_status.value, case.queue_name)
        case.set_state(CaseState.ROUTED)
        case.log("ROUTED",
                 f"Referral packet created and dispatched to {case.queue_name}. "
                 f"Confirmation sent to the patient.")
        store.save(case)

        # 6) Front-office handoff (availability only; simulated notification) ---
        # Non-breaking: a failure here leaves the case ROUTED, never FAILED.
        try:
            area = case.structured.geographic_location or case.location_input
            handoff = match_and_notify(area, case.queue_name, case.id)
            case.handoff = handoff
            notified = handoff.get("notified", [])
            skipped = handoff.get("skipped", [])
            names = ", ".join(n["name"] for n in notified) or "none"
            case.set_state(CaseState.HANDED_OFF)
            case.log("HANDED_OFF",
                     f"Notified {len(notified)} available clinic(s): {names}; "
                     f"skipped {len(skipped)} not accepting new enquiries.")
            store.save(case)
        except Exception as exc:
            case.log("HANDOFF_SKIPPED",
                     f"Handoff step skipped ({exc}); case remains routed.")
            store.save(case)
        return case

    except Exception as exc:  # explicit failure state — nothing silently dies
        case.error = str(exc)
        case.set_state(CaseState.FAILED)
        case.log("FAILED", f"Pipeline error: {exc}")
        store.save(case)
        return case

"""Tests for deterministic logic and the mock end-to-end workflow."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.models import Case, CaseState, ImageStatus            # noqa: E402
from app.pipeline import run_pipeline                          # noqa: E402
from app.tools import check_completeness, route_case           # noqa: E402
from data.synthetic_cases import (                             # noqa: E402
    CASE_A_COMPLETE, CASE_B_INCOMPLETE, CASE_C_AMBIGUOUS)


def _run(spec):
    case = Case(
        raw_text=spec["text"],
        location_input=spec["location"],
        desired_support_input=spec["desired_support"],
        has_photo=bool(spec["simulate_photo"]),
        consent=True,
    )
    return run_pipeline(case, mock_image_status=spec["simulate_photo"])


# --- completeness (deterministic) ------------------------------------------ #
def test_completeness_ready():
    s = {"geographic_location": "Leeds", "scar_age": "2 years",
         "desired_support": "consultation"}
    r = check_completeness(s, ImageStatus.USABLE.value, has_photo=True)
    assert r["ready"] is True and r["missing"] == []


def test_completeness_missing_location_and_age():
    s = {"geographic_location": None, "scar_age": None, "desired_support": None}
    r = check_completeness(s, ImageStatus.NOT_PROVIDED.value, has_photo=False)
    assert r["ready"] is False
    assert "location" in r["missing"] and "approximate scar age" in r["missing"]


def test_completeness_bad_photo_blocks():
    s = {"geographic_location": "London", "scar_age": "1 year"}
    r = check_completeness(s, ImageStatus.RETAKE_REQUIRED.value, has_photo=True)
    assert r["ready"] is False and "a clearer photo" in r["missing"]


def test_support_not_required_for_ready():
    s = {"geographic_location": "York", "scar_age": "6 months",
         "desired_support": None}
    r = check_completeness(s, ImageStatus.NOT_PROVIDED.value, has_photo=False)
    assert r["ready"] is True


# --- routing (deterministic) ----------------------------------------------- #
def test_route_clinical():
    assert route_case("clinical consultation")["queue_id"] == "clinical_consultation"


def test_route_camouflage():
    assert route_case("camouflage")["queue_id"] == "camouflage_tattoo"


def test_route_ambiguous_to_navigation():
    assert route_case(None, "not sure who I should see")["queue_id"] == \
        "general_navigation"


# --- end to end (mock) ----------------------------------------------------- #
def test_case_a_routes_ready():
    case = _run(CASE_A_COMPLETE)
    assert case.state == CaseState.HANDED_OFF
    assert case.queue_name == "Clinical Consultation Requested"
    assert case.referral_packet and "REFERRAL PACKET" in case.referral_packet
    assert case.handoff["notified"]  # at least one clinic notified


def test_case_b_needs_information():
    case = _run(CASE_B_INCOMPLETE)
    assert case.state == CaseState.NEEDS_INFORMATION
    assert case.follow_up_message and case.referral_packet is None


def test_case_c_navigation():
    case = _run(CASE_C_AMBIGUOUS)
    assert case.state == CaseState.HANDED_OFF
    assert case.queue_name == "General Navigation"


def test_audit_trail_written():
    case = _run(CASE_A_COMPLETE)
    steps = [a.step for a in case.actions]
    for expected in ["CASE_CREATED", "EXTRACTED", "IMAGE_CHECKED",
                     "COMPLETENESS_CHECKED", "REFERRAL_READY", "ROUTED"]:
        assert expected in steps


def test_no_diagnosis_language_in_packet():
    """Packet must not assert a diagnosis. The safety disclaimer may still use
    the word 'diagnosis' to state that none was made — that's expected."""
    case = _run(CASE_A_COMPLETE)
    lowered = case.referral_packet.lower()
    # no diagnosis label, no specific scar-type classification
    for banned in ["diagnosis:", "hypertrophic", "keloid", "malignant",
                   "atrophic scar", "diagnosed"]:
        assert banned not in lowered
    # the safety disclaimer should be present
    assert "no diagnosis or treatment" in lowered


# --- closed loop: reply resolves an incomplete case ------------------------ #
def test_reply_resolves_incomplete_case():
    from app.pipeline import resume_with_reply
    case = _run(CASE_B_INCOMPLETE)          # NEEDS_INFORMATION (no loc/age/photo)
    assert case.state == CaseState.NEEDS_INFORMATION
    case = resume_with_reply(
        case,
        new_text="I'm in Bristol and I've had it about three years.",
        mock_image_status="USABLE",
    )
    assert case.state == CaseState.HANDED_OFF
    assert case.structured.geographic_location == "Bristol"
    assert case.completeness["ready"] is True
    assert case.referral_packet and "REFERRAL PACKET" in case.referral_packet


def test_reply_still_missing_stays_needs_info():
    from app.pipeline import resume_with_reply
    case = _run(CASE_B_INCOMPLETE)
    case = resume_with_reply(
        case, new_text="I'm in Bristol, had it about three years.")
    assert case.state == CaseState.NEEDS_INFORMATION
    assert "a clearer photo" in case.completeness["missing"]


def test_reply_preserves_audit_trail():
    from app.pipeline import resume_with_reply
    case = _run(CASE_B_INCOMPLETE)
    case = resume_with_reply(case, new_text="Bristol, three years ago",
                             mock_image_status="USABLE")
    steps = [a.step for a in case.actions]
    assert "NEEDS_INFORMATION" in steps
    assert "INFORMATION_RECEIVED" in steps
    assert steps.count("EXTRACTED") == 2
    assert steps[-1] == "HANDED_OFF"


def test_case_from_dict_roundtrip():
    case = _run(CASE_A_COMPLETE)
    rebuilt = Case.from_dict(case.to_dict())
    assert rebuilt.id == case.id
    assert rebuilt.state == case.state
    assert rebuilt.queue_name == case.queue_name
    assert len(rebuilt.actions) == len(case.actions)


# --- front-office handoff (availability only, simulated) -------------------- #
def test_match_and_notify_filters_by_availability():
    from app.tools import match_and_notify
    r = match_and_notify("Manchester", "Clinical Consultation Requested", "MS-TEST")
    assert len(r["notified"]) >= 1 and len(r["skipped"]) >= 1
    # notified entries carry a simulated note; skipped ones do not
    assert all("note" in n for n in r["notified"])


def test_handoff_recorded_on_completed_case():
    case = _run(CASE_A_COMPLETE)
    assert case.handoff["notified"] and case.handoff["skipped"]
    steps = [a.step for a in case.actions]
    assert steps[-1] == "HANDED_OFF"


def test_incomplete_case_has_no_handoff():
    case = _run(CASE_B_INCOMPLETE)
    assert case.state == CaseState.NEEDS_INFORMATION
    assert not case.handoff  # no handoff before a case is routed

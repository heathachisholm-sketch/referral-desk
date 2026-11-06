"""
Domain models for The Referral Desk.

The state machine is intentionally explicit. State is data the system owns and
persists — not something the language model is trusted to track.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class CaseState(str, Enum):
    NEW = "NEW"
    EXTRACTED = "EXTRACTED"
    IMAGE_CHECKED = "IMAGE_CHECKED"
    COMPLETENESS_CHECKED = "COMPLETENESS_CHECKED"
    NEEDS_INFORMATION = "NEEDS_INFORMATION"
    REFERRAL_READY = "REFERRAL_READY"
    ROUTED = "ROUTED"
    HANDED_OFF = "HANDED_OFF"
    FAILED = "FAILED"


class ImageStatus(str, Enum):
    NOT_PROVIDED = "NOT_PROVIDED"
    USABLE = "USABLE"
    RETAKE_REQUIRED = "RETAKE_REQUIRED"


# Generic administrative queues only. No provider matching, no ranking — those
# stay in Mended Skin's private layer (see README "Prototype scope / IP").
QUEUES = {
    "clinical_consultation": "Clinical Consultation Requested",
    "camouflage_tattoo": "Camouflage / Tattoo Enquiry",
    "scar_therapy": "Scar Therapy / Support Enquiry",
    "post_procedure": "Post-Procedure Information",
    "general_navigation": "General Navigation",
    "manual_review": "Manual Review",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class StructuredCase:
    """What Gemini is allowed to infer from free text. Interpretation only."""
    scar_location: Optional[str] = None
    cause_context: Optional[str] = None
    scar_age: Optional[str] = None
    previous_care: Optional[str] = None
    desired_support: Optional[str] = None
    geographic_location: Optional[str] = None
    preferences: Optional[str] = None
    missing_information: list[str] = field(default_factory=list)


@dataclass
class Action:
    """One entry in the audit trail — proof the agent did operational work."""
    step: str
    detail: str
    at: str = field(default_factory=_now)


@dataclass
class Case:
    id: str = field(default_factory=lambda: f"MS-{uuid.uuid4().hex[:8].upper()}")
    state: CaseState = CaseState.NEW
    raw_text: str = ""
    location_input: str = ""
    desired_support_input: str = ""
    has_photo: bool = False
    consent: bool = False

    structured: StructuredCase = field(default_factory=StructuredCase)
    image_status: ImageStatus = ImageStatus.NOT_PROVIDED
    image_reason: Optional[str] = None

    completeness: dict = field(default_factory=dict)
    queue_id: Optional[str] = None
    queue_name: Optional[str] = None
    follow_up_message: Optional[str] = None
    referral_packet: Optional[str] = None
    handoff: dict = field(default_factory=dict)
    error: Optional[str] = None

    actions: list[Action] = field(default_factory=list)
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def log(self, step: str, detail: str) -> None:
        self.actions.append(Action(step=step, detail=detail))
        self.updated_at = _now()

    def set_state(self, state: CaseState) -> None:
        self.state = state
        self.updated_at = _now()

    def to_dict(self) -> dict:
        d = asdict(self)
        d["state"] = self.state.value
        d["image_status"] = self.image_status.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Case":
        """Rebuild a Case from a stored dict (Firestore or in-memory)."""
        s = d.get("structured") or {}
        case = cls(
            id=d["id"],
            state=CaseState(d.get("state", "NEW")),
            raw_text=d.get("raw_text", ""),
            location_input=d.get("location_input", ""),
            desired_support_input=d.get("desired_support_input", ""),
            has_photo=d.get("has_photo", False),
            consent=d.get("consent", False),
            structured=StructuredCase(
                scar_location=s.get("scar_location"),
                cause_context=s.get("cause_context"),
                scar_age=s.get("scar_age"),
                previous_care=s.get("previous_care"),
                desired_support=s.get("desired_support"),
                geographic_location=s.get("geographic_location"),
                preferences=s.get("preferences"),
                missing_information=s.get("missing_information") or [],
            ),
            image_status=ImageStatus(d.get("image_status", "NOT_PROVIDED")),
            image_reason=d.get("image_reason"),
            completeness=d.get("completeness") or {},
            queue_id=d.get("queue_id"),
            queue_name=d.get("queue_name"),
            follow_up_message=d.get("follow_up_message"),
            referral_packet=d.get("referral_packet"),
            handoff=d.get("handoff") or {},
            error=d.get("error"),
            actions=[Action(step=a["step"], detail=a["detail"], at=a.get("at", ""))
                     for a in d.get("actions", [])],
            created_at=d.get("created_at", _now()),
            updated_at=d.get("updated_at", _now()),
        )
        return case

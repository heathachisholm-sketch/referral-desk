"""
Synthetic demo cases. Entirely fictional — no real patients, clinicians,
partners or hospitals. Used by scripts/run_demo.py and the test suite.
"""

CASE_A_COMPLETE = {
    "label": "Case A — Complete",
    "text": ("I have a raised scar on my shoulder following surgery two years "
             "ago. I've tried silicone. I'm in Manchester and I'd like a "
             "clinical consultation."),
    "location": "Manchester",
    "desired_support": "clinical consultation",
    "simulate_photo": "USABLE",
    "expect_state": "HANDED_OFF",
    "expect_queue": "Clinical Consultation Requested",
}

CASE_B_INCOMPLETE = {
    "label": "Case B — Incomplete",
    "text": "I've got a scar on my cheek and I really want to reduce how it looks.",
    "location": "",
    "desired_support": "",
    "simulate_photo": "RETAKE_REQUIRED",
    "expect_state": "NEEDS_INFORMATION",
    "expect_queue": None,
}

CASE_C_AMBIGUOUS = {
    "label": "Case C — Ambiguous",
    "text": ("I had an operation on my arm about six months ago and honestly "
             "I'm not sure who I should see or what I need. I'm in Leeds."),
    "location": "Leeds",
    "desired_support": "",
    "simulate_photo": None,
    "expect_state": "HANDED_OFF",
    "expect_queue": "General Navigation",
}

ALL_CASES = [CASE_A_COMPLETE, CASE_B_INCOMPLETE, CASE_C_AMBIGUOUS]

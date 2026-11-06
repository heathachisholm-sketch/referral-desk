"""
Run the three synthetic demo cases end to end and print the workflow.

    python -m scripts.run_demo

Runs in MOCK mode by default (no credentials needed). Set GEMINI_API_KEY to run
the real Gemini path.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import config                       # noqa: E402
from app.models import Case                  # noqa: E402
from app.pipeline import run_pipeline, resume_with_reply  # noqa: E402
from data.synthetic_cases import ALL_CASES   # noqa: E402


def run_one(spec: dict) -> Case:
    case = Case(
        raw_text=spec["text"],
        location_input=spec["location"],
        desired_support_input=spec["desired_support"],
        has_photo=bool(spec["simulate_photo"]),
        consent=True,
    )
    return run_pipeline(case, mock_image_status=spec["simulate_photo"])


def main() -> None:
    print(f"\nConfig: {config.summary()}\n" + "=" * 60)
    for spec in ALL_CASES:
        print(f"\n{spec['label']}  ({spec['text'][:56]}…)")
        print("-" * 60)
        case = run_one(spec)
        for a in case.actions:
            print(f"  {a.step:<22} {a.detail}")
        print(f"\n  FINAL STATE: {case.state.value}")
        if case.queue_name:
            print(f"  QUEUE:       {case.queue_name}")
        if case.follow_up_message:
            print(f"  FOLLOW-UP:   {case.follow_up_message}")
        if case.referral_packet:
            print("\n" + "\n".join("  " + ln
                  for ln in case.referral_packet.splitlines()))
        # lightweight self-check against expectations
        ok_state = case.state.value == spec["expect_state"]
        ok_queue = (case.queue_name == spec["expect_queue"])
        print(f"\n  CHECK: state {'OK' if ok_state else 'MISMATCH'}, "
              f"queue {'OK' if ok_queue else 'MISMATCH'}")
        print("=" * 60)

    # Closed loop: take the incomplete case and let the patient reply.
    print("\nCLOSED LOOP — patient replies to the incomplete case (B)")
    print("-" * 60)
    from data.synthetic_cases import CASE_B_INCOMPLETE
    case = run_one(CASE_B_INCOMPLETE)
    print(f"  before reply: {case.state.value} "
          f"(missing: {case.completeness['missing']})")
    case = resume_with_reply(
        case,
        new_text="I'm in Bristol and I've had it about three years.",
        mock_image_status="USABLE",
    )
    print("  patient reply merged; case re-processed:")
    for a in case.actions[-6:]:
        print(f"    {a.step:<22} {a.detail}")
    print(f"\n  after reply:  {case.state.value}  ->  {case.queue_name}")
    print("=" * 60)


if __name__ == "__main__":
    main()

# Devpost submission — paste-ready copy

**Project name:** The Referral Desk
**Tagline:** Turns a patient's scar-care enquiry into a referral-ready case.
**Category / track:** The Taskmaster
**Also entering:** Startup Excellence (incorporated org, corporate email) ·
Individual/Hobbyist (Best Solo Build)

---

## Inspiration

I run Mended Skin, a directory connecting patients with dermatology specialists
for scar treatment. The same friction shows up constantly: patients describe a
scar in a sentence or two and maybe attach a photo, but they don't know what a
practitioner actually needs to help them. Clinics receive half-formed enquiries
and spend time chasing the rest. I wanted an agent that does that
administrative legwork autonomously — without ever stepping into clinical
territory.

## What it does

The Referral Desk takes an unstructured patient enquiry (free text, an optional
photo, a location) and runs a complete workflow:

- **Structures** the enquiry into clean fields with Gemini (interpretation only).
- **Checks the photo** is usable for referral prep with a non-clinical
  multimodal check.
- **Decides completeness** with deterministic rules and, if anything is missing,
  autonomously drafts a follow-up and pauses.
- **Closes the loop:** when the patient replies, it merges the new information
  and re-runs the case to referral without starting over.
- **Routes** the case to a generic administrative queue.
- **Generates a referral packet** and persists every state transition to
  Firestore as an audit trail.

It's a workflow, not a chatbot: the model interprets, but deterministic code
owns every decision and the workflow state.

## How we built it

- **Gemini 3.5 Flash** via the **Google GenAI SDK** for extraction, image
  usability, and summarisation.
- A **deterministic orchestrator** driving an explicit state machine
  (`NEW → EXTRACTED → IMAGE_CHECKED → COMPLETENESS_CHECKED →
  NEEDS_INFORMATION | REFERRAL_READY → ROUTED`, plus `FAILED`).
- Five narrow tools: two Gemini-backed (extract, packet), one multimodal
  (photo), two deterministic (completeness, routing). The same tools are also
  exposed through a **Google ADK** agent.
- **Firestore** for persistent case state and audit trail; **Cloud Run** to host
  the FastAPI service. Secrets via environment variables only.

## Features and functionality

- Autonomous multi-step workflow with a live, animated state timeline.
- **Closed patient-feedback loop:** incomplete cases pause, ask for exactly
  what's missing, and resolve automatically when the patient replies.
- **Front-office handoff:** once routed, shortlists clinics currently accepting
  enquiries and records a simulated notification to each (availability only — no
  matching logic).
- Multimodal, non-clinical photo-usability check.
- Automatic follow-up generation for incomplete cases.
- Deterministic routing to generic queues; ambiguous cases go to navigation
  rather than a forced clinical route.
- Full audit trail persisted per case.
- Offline `MOCK_MODE` for a demo that can't be broken by a network hiccup.

## Technologies used

Gemini 3.5 Flash, Google GenAI SDK, Google ADK, Google Cloud Run, Google Cloud
Firestore, FastAPI, Python.

## Other data sources used

Synthetic, fictional cases only. No real patients, clinicians, partners or
hospitals; no production Mended Skin data or logic.

## Findings and learnings

Splitting responsibilities — LLM for interpretation, deterministic code for
decisions and state — produced an agent that is both genuinely useful and
reliable enough to demo live. Persisting each transition turns "the agent did
something" into visible evidence, which is exactly what matters for a
health-adjacent product where trust and auditability are the whole game.

## What's next

The Referral Desk is deliberately the administrative layer only. The private
Mended Skin roadmap — provider matching, clinical decision-support — sits behind
a clean boundary, so this hackathon build is an infrastructure experiment, not a
disclosure of core IP.

---

## Submission checklist
- [ ] Category selected: The Taskmaster
- [ ] Startup Excellence ticked + corporate email provided
- [ ] Hosted URL (Cloud Run) — optional but included
- [ ] Text description (above)
- [ ] Repo URL; if private, shared with testing@devpost.com and
      cloudhackathons@google.com
- [ ] Spin-up instructions in README.md
- [ ] Architecture diagram (docs/architecture.png)
- [ ] Demo video < 4 min, live, shows Google Cloud backend
- [ ] Bonus (optional): LinkedIn post with #AllThingsAgenticHackathon

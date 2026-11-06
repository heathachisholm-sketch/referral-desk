# Demo video script — The Referral Desk (~4:00)

Judging weights: Innovation & Operational Utility 40% · Architecture 30% ·
Demo & Production Readiness 30%. The demo must be **live and unedited** and must
**show the backend on Google Cloud**. Record the live demo in one take.

**Before you record**
- Deploy to Cloud Run (`./deploy.sh`) so you have a real `*.run.app` URL and
  Firestore is receiving writes.
- Open three tabs: (1) the live app, (2) the Cloud Run dashboard, (3) the
  Firestore `referral_cases` collection. Have the ADK dev UI ready if you want
  the optional agent shot.
- Keep it screen-recorded with voiceover; talk while it runs.

---

## 0:00–0:30 — Problem
*(Screen: the app's intake page.)*

> "Scar-care enquiries arrive incomplete and unstructured. A patient describes their
> scar in a sentence or two, maybe adds a photo — but they don't know what a
> practitioner actually needs. So clinics get half-formed enquiries and someone
> has to chase the rest by hand. I'm building Mended Skin, and this is the
> friction I wanted an agent to remove."

## 0:30–0:50 — Solution / value
> "The Referral Desk is an autonomous agent that turns that unstructured enquiry
> into a referral-ready case — it structures it, checks the photo, works out
> what's missing, routes it, and writes a referral packet. It takes action; it
> doesn't just chat. And it never makes a clinical decision."

## 0:50–2:30 — Live demo (the core; one take)
*(Load the "Complete case" example, or type it live, then click Prepare my referral.)*

> "Here's a real enquiry: raised shoulder scar, two years post-surgery, tried
> silicone, in Manchester, wants a consultation — plus a photo."

*(As the timeline animates, narrate each state — this is the money-shot.)*

> "Watch the workflow run. **Extracted** — Gemini pulls out location, scar age,
> previous care. **Image checked** — a non-clinical multimodal check confirms
> the photo is usable. **Completeness** — deterministic rules confirm nothing's
> missing. **Referral ready**, then **Routed** to the Clinical Consultation
> queue — and here's the generated referral packet."

*(Now load "Missing info".)*

> "Different case — no location, no scar age, a dark photo. The agent stops at
> **Needs information** and autonomously drafts a follow-up asking for exactly
> what's missing. It won't route an incomplete case."

*(Type a reply in the box — "I'm in Bristol, I've had it about three years" —
tick "Attach a clear photo", click Send reply.)*

> "And here's the part I care about most — it's a closed loop. The patient
> answers, the agent merges the new details, re-checks, and carries the same case
> all the way to **Routed** with a referral packet. No human re-keyed anything."

*(Now load "Not sure what's needed".)*

> "And when the patient doesn't know what help they need, it routes to General
> Navigation rather than forcing a clinical choice."

*(Point at the final timeline entry and the Front-office handoff panel.)*

> "And it doesn't stop at a queue — the last step is a real handoff. The agent
> shortlists the clinics currently accepting enquiries, notifies their front
> office, and skips the one that isn't taking new cases. That's the agent
> sending the right information to the right place — availability only, no
> clinical matching."

## 2:30–3:10 — Architecture
*(Screen: docs/architecture.png.)*

> "The design principle is: AI interprets, deterministic rules decide, clinicians
> retain care. Gemini 3.5 Flash handles interpretation — extraction, the image
> check, the summary. Deterministic Python owns the completeness gate, routing,
> and the workflow state machine, so the workflow is auditable and reproducible.
> It's built on the Google GenAI SDK, with the same tools also exposed through a
> Google ADK agent."

*(Optional 8-sec shot: ADK dev UI showing the agent calling the tools.)*

## 3:10–3:35 — Safety
> "Because this is health-adjacent, the boundaries are strict. It never
> diagnoses, grades, or recommends treatment. The photo check is framing and
> lighting only. Every packet states that no clinical decision was made — and
> the test suite enforces it."

## 3:35–4:00 — Cloud proof + close
*(Screen: Cloud Run dashboard, then the Firestore collection updating.)*

> "It's deployed on Google Cloud Run — here's the service — and every state
> transition is persisted to Firestore, so 'the agent did the work' is visible
> evidence, not a claim. For Mended Skin, this is the first autonomous piece of a
> larger referral workflow — and it already removes real administrative friction.
> Thanks for watching."

---

**Shot checklist (for Demo & Production Readiness):**
- [ ] Live app running (not slides) — full workflow, one take
- [ ] Cloud Run dashboard / `*.run.app` URL on screen
- [ ] Firestore `referral_cases` document(s) visible
- [ ] Architecture diagram
- [ ] Under 4:00

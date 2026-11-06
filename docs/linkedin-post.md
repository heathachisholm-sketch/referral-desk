# LinkedIn post (bonus points)

Rules: must be public (not unlisted), include the hashtag
**#AllThingsAgenticHackathon**, and state it was created for the hackathon.

---

I spent the weekend building an AI agent for the #AllThingsAgenticHackathon —
and it solved a real problem from my own company.

At Mended Skin we connect patients with dermatology specialists for scar
treatment. The recurring friction: enquiries arrive incomplete and unstructured.
Patients describe a scar in a sentence, maybe add a photo — but they don't know
what a clinician actually needs. So someone has to chase the rest by hand.

So I built **The Referral Desk**: an autonomous agent that turns an unstructured enquiry
into a referral-ready case. It structures the information, runs a non-clinical
check on the photo, works out what's missing, routes the case, and writes a
referral packet — persisting every step to Google Cloud as an audit trail. When
something's missing, it drafts the follow-up itself.

The part I'm most pleased with is the discipline: **AI interprets, deterministic
rules decide, clinicians retain care.** Gemini 3.5 Flash handles the language and
the image; plain Python owns the decisions and the workflow state. In a
health-adjacent product, that boundary is the whole game — and it makes the agent
reliable enough to demo live.

Built on Gemini 3.5 Flash, the Google ADK / GenAI SDK, Cloud Run and Firestore.

Created for the All Things Agentic Hackathon. #AllThingsAgenticHackathon

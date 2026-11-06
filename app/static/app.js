"use strict";

const DEMOS = {
  A: {
    text: "I have a raised scar on my shoulder following surgery two years ago. I've tried silicone. I'm in Manchester and I'd like a clinical consultation.",
    location: "Manchester",
    desired_support: "clinical consultation",
    simulate_photo: "USABLE",
  },
  B: {
    text: "I've got a scar on my cheek and I really want to reduce how it looks.",
    location: "",
    desired_support: "",
    simulate_photo: "RETAKE_REQUIRED",
  },
  C: {
    text: "I had an operation on my arm about six months ago and honestly I'm not sure who I should see or what I actually need. I'm in Leeds.",
    location: "Leeds",
    desired_support: "",
    simulate_photo: null,
  },
};

const $ = (id) => document.getElementById(id);
const CURRENT = { id: null };

// Load a demo into the form.
document.querySelectorAll(".chip").forEach((btn) => {
  btn.addEventListener("click", () => {
    const d = DEMOS[btn.dataset.demo];
    $("text").value = d.text;
    $("location").value = d.location;
    $("desired_support").value = d.desired_support;
    $("consent").checked = true;
    clearPhoto();
    // stash the simulated photo status on the form for this submission
    $("case-form").dataset.simPhoto = d.simulate_photo || "";
  });
});

// --- Photo upload: validation, preview, replace/remove --------------------
const MAX_BYTES = 10 * 1024 * 1024; // 10 MB
const OK_TYPES = ["image/jpeg", "image/png", "image/webp", "image/heic",
                  "image/heif"];
let previewURL = null;

function showUploadError(msg) {
  const el = $("upload-error");
  el.textContent = msg;
  el.hidden = false;
}
function clearUploadError() {
  $("upload-error").hidden = true;
}
function clearPhoto() {
  $("photo").value = "";
  if (previewURL) { URL.revokeObjectURL(previewURL); previewURL = null; }
  $("preview-img").removeAttribute("src");
  $("preview").hidden = true;
  $("upload-trigger").hidden = false;
  clearUploadError();
}

$("upload-trigger").addEventListener("click", () => $("photo").click());
$("replace-photo").addEventListener("click", () => $("photo").click());
$("remove-photo").addEventListener("click", clearPhoto);

$("photo").addEventListener("change", () => {
  const file = $("photo").files[0];
  if (!file) return;
  // Validate. HEIC can report an empty type on some browsers, so also allow
  // an image-looking extension as a fallback.
  const looksImage = OK_TYPES.includes(file.type) ||
    /\.(jpe?g|png|webp|heic|heif)$/i.test(file.name);
  if (!looksImage) {
    clearPhoto();
    showUploadError("That doesn't look like an image. Please choose a JPG, PNG or WEBP.");
    return;
  }
  if (file.size > MAX_BYTES) {
    clearPhoto();
    showUploadError("That image is over 10 MB. Please choose a smaller one.");
    return;
  }
  // A real photo overrides any simulated demo photo.
  $("case-form").dataset.simPhoto = "";
  try {
    if (previewURL) URL.revokeObjectURL(previewURL);
    previewURL = URL.createObjectURL(file);
    $("preview-img").src = previewURL;
    $("preview-name").textContent = file.name;
    $("preview").hidden = false;
    $("upload-trigger").hidden = true;
    clearUploadError();
  } catch (err) {
    clearPhoto();
    showUploadError("Couldn't preview that image. Please try another.");
    console.error(err);
  }
});

$("case-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = $("submit-btn");
  btn.disabled = true;
  btn.textContent = "Preparing…";

  const fd = new FormData();
  fd.append("text", $("text").value);
  fd.append("location", $("location").value);
  fd.append("desired_support", $("desired_support").value);
  fd.append("consent", $("consent").checked ? "true" : "false");

  const file = $("photo").files[0];
  if (file) {
    fd.append("photo", file);
  } else if ($("case-form").dataset.simPhoto) {
    fd.append("mock_image_status", $("case-form").dataset.simPhoto);
  }

  try {
    const res = await fetch("/cases", { method: "POST", body: fd });
    const data = await res.json();
    await render(data);
  } catch (err) {
    alert("Something went wrong preparing the case. Please try again.");
    console.error(err);
  } finally {
    btn.disabled = false;
    btn.textContent = "Prepare my referral";
  }
});

const STATE_CLASS = {
  NEEDS_INFORMATION: "warn",
  FAILED: "fail",
};

async function render(caseData) {
  $("empty").hidden = true;
  CURRENT.id = caseData.id;
  const meta = $("case-meta");
  meta.hidden = false;
  $("case-id").textContent = "#" + caseData.id;

  const finalState = caseData.state;
  const pill = $("final-state");
  pill.textContent = finalState;
  pill.className =
    "pill " +
    (finalState === "FAILED" ? "fail" :
     finalState === "NEEDS_INFORMATION" ? "warn" : "ok");

  // Build the timeline from the real, persisted action log.
  const tl = $("timeline");
  tl.hidden = false;
  tl.innerHTML = "";
  const result = $("result");
  result.hidden = true;
  result.innerHTML = "";

  const actions = caseData.actions || [];
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  for (let i = 0; i < actions.length; i++) {
    const a = actions[i];
    const li = document.createElement("li");
    const cls =
      a.step === "FAILED" ? "fail" :
      a.step === "NEEDS_INFORMATION" ? "warn" : "done";
    li.className = cls;
    const time = (a.at || "").slice(11, 19);
    li.innerHTML =
      `<span class="node"></span>` +
      `<div class="step">${a.step}<span class="t">${time}</span></div>` +
      `<div class="detail">${escapeHtml(a.detail)}</div>`;
    tl.appendChild(li);
    if (!reduce) await sleep(360);
    li.classList.add("show");
  }

  // Result: packet, or follow-up.
  if (caseData.referral_packet) {
    result.hidden = false;
    let html =
      `<h3>Referral packet</h3><pre class="packet">${highlight(caseData.referral_packet)}</pre>`;
    const ho = caseData.handoff || {};
    if ((ho.notified || []).length || (ho.skipped || []).length) {
      const yes = (ho.notified || []).map((c) =>
        `<li class="ho-yes">${escapeHtml(c.name)}<span>${escapeHtml(c.area)} · notified</span></li>`).join("");
      const no = (ho.skipped || []).map((c) =>
        `<li class="ho-no">${escapeHtml(c.name)}<span>${escapeHtml(c.area)} · not accepting</span></li>`).join("");
      html += `<h3 class="ho-h">Front-office handoff</h3><ul class="handoff">${yes}${no}</ul>`;
    }
    result.innerHTML = html;
  } else if (caseData.follow_up_message) {
    result.hidden = false;
    result.innerHTML =
      `<h3>Automatic follow-up sent</h3>` +
      `<div class="followup">${escapeHtml(caseData.follow_up_message)}</div>` +
      `<div class="reply-box">` +
      `  <h3>Patient reply</h3>` +
      `  <textarea id="reply-text" rows="2" placeholder="e.g. I'm in Bristol and I've had it about three years."></textarea>` +
      `  <label class="reply-photo"><input type="checkbox" id="reply-clear-photo" /> Attach a clear photo (demo)</label>` +
      `  <input id="reply-photo-file" type="file" accept="image/*" />` +
      `  <button class="submit reply-send" id="reply-send" type="button">Send reply</button>` +
      `</div>`;
    $("reply-send").addEventListener("click", replyToCase);
  }
}

async function replyToCase() {
  const btn = $("reply-send");
  btn.disabled = true;
  btn.textContent = "Sending…";
  const fd = new FormData();
  fd.append("text", $("reply-text").value);
  const file = $("reply-photo-file").files[0];
  if (file) {
    fd.append("photo", file);
  } else if ($("reply-clear-photo").checked) {
    fd.append("mock_image_status", "USABLE");
  }
  try {
    const res = await fetch(`/cases/${CURRENT.id}/reply`, {
      method: "POST", body: fd,
    });
    const data = await res.json();
    await render(data);
  } catch (err) {
    alert("Couldn't send the reply. Please try again.");
    console.error(err);
  } finally {
    const b = document.getElementById("reply-send");
    if (b) { b.disabled = false; b.textContent = "Send reply"; }
  }
}

function highlight(text) {
  return escapeHtml(text)
    .replace(/^(REFERRAL PACKET #[^\n]+)/,'<span class="kw">$1</span>')
    .replace(/(Status:|Queue:|Note:)/g, '<span class="kw">$1</span>');
}
function escapeHtml(s) {
  return (s || "").replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

"""FastAPI surface for The Referral Desk: one branded page + a small JSON API."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import config, store
from .models import Case
from .pipeline import run_pipeline, resume_with_reply

BASE = Path(__file__).parent
app = FastAPI(title="Mended Skin — The Referral Desk", version="0.1.0")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

_INDEX = (BASE / "templates" / "index.html").read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    badge = "MOCK MODE" if config.MOCK_MODE else config.GEMINI_MODEL
    return _INDEX.replace("{{MODE_BADGE}}", badge)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/config")
def config_view() -> dict:
    """Non-secret runtime configuration (handy proof for the demo)."""
    return config.summary()


@app.post("/cases")
async def create_case(
    text: str = Form(...),
    location: str = Form(""),
    desired_support: str = Form(""),
    consent: bool = Form(False),
    photo: Optional[UploadFile] = File(None),
    mock_image_status: Optional[str] = Form(None),
) -> JSONResponse:
    image_bytes = None
    mime = "image/jpeg"
    has_photo = False
    if photo is not None and photo.filename:
        image_bytes = await photo.read()
        mime = photo.content_type or "image/jpeg"
        has_photo = len(image_bytes) > 0

    # Demo chips have no real file: a simulated status still exercises the step.
    if not has_photo and mock_image_status:
        has_photo = True

    case = Case(
        raw_text=text,
        location_input=location.strip(),
        desired_support_input=desired_support.strip(),
        has_photo=has_photo,
        consent=consent,
    )
    case = run_pipeline(case, image_bytes=image_bytes, mime_type=mime,
                        mock_image_status=mock_image_status)
    return JSONResponse(case.to_dict())


@app.post("/cases/{case_id}/reply")
async def reply_to_case(
    case_id: str,
    text: str = Form(""),
    location: str = Form(""),
    desired_support: str = Form(""),
    photo: Optional[UploadFile] = File(None),
    mock_image_status: Optional[str] = Form(None),
) -> JSONResponse:
    """Patient supplies missing information; the case resumes and re-processes."""
    doc = store.get(case_id)
    if not doc:
        return JSONResponse({"error": "not found"}, status_code=404)

    image_bytes = None
    mime = "image/jpeg"
    if photo is not None and photo.filename:
        image_bytes = await photo.read()
        mime = photo.content_type or "image/jpeg"
        if not image_bytes:
            image_bytes = None

    case = Case.from_dict(doc)
    case = resume_with_reply(
        case, new_text=text, new_location=location, new_support=desired_support,
        image_bytes=image_bytes, mime_type=mime, mock_image_status=mock_image_status)
    return JSONResponse(case.to_dict())


@app.get("/cases/{case_id}")
def get_case(case_id: str) -> JSONResponse:
    doc = store.get(case_id)
    if not doc:
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(doc)


@app.get("/cases")
def list_cases() -> JSONResponse:
    return JSONResponse({"cases": store.list_recent()})

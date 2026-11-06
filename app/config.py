"""
Central configuration for The Referral Desk.

Every external dependency (Gemini, Firestore) is optional. If credentials are
absent, the app runs in MOCK mode so the full workflow is demonstrable offline.
This is deliberate: the live demo must never fail because of a network hiccup.
"""
import os


def _flag(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


# --- Gemini -----------------------------------------------------------------
# The hackathon mandates "Gemini 3.5 or newer". If "gemini-3.5-flash" ever
# stops resolving, set GEMINI_MODEL=gemini-flash-latest (always newest Flash).
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

# Auth path. Default = Gemini API key (AI Studio): one variable, no IAM setup.
# To use Vertex AI instead, set GOOGLE_GENAI_USE_VERTEXAI=true plus
# GOOGLE_CLOUD_PROJECT / GOOGLE_CLOUD_LOCATION (no GEMINI_API_KEY needed).
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
USE_VERTEX = _flag("GOOGLE_GENAI_USE_VERTEXAI")

# --- Google Cloud -----------------------------------------------------------
GCP_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GCP_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
FIRESTORE_COLLECTION = os.getenv("FIRESTORE_COLLECTION", "referral_cases")

# --- Mode -------------------------------------------------------------------
# MOCK_MODE forces the offline path regardless of credentials. If it is not
# explicitly set, we auto-enable it whenever no Gemini credentials are present.
_explicit_mock = os.getenv("MOCK_MODE")
if _explicit_mock is not None:
    MOCK_MODE = _flag("MOCK_MODE")
else:
    MOCK_MODE = not (GEMINI_API_KEY or USE_VERTEX)

# Use Firestore only when a project is configured and we are not mocking.
USE_FIRESTORE = bool(GCP_PROJECT) and not MOCK_MODE


def summary() -> dict:
    """Non-secret snapshot of the active configuration (safe to log / show)."""
    return {
        "model": GEMINI_MODEL,
        "mock_mode": MOCK_MODE,
        "gemini_backend": "vertex" if USE_VERTEX else "gemini_api",
        "store": "firestore" if USE_FIRESTORE else "in_memory",
        "gcp_project": GCP_PROJECT or None,
    }

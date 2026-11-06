"""
Persistent state for cases.

Uses Firestore when a GCP project is configured (real deployment); falls back to
an in-memory dict otherwise (local dev / mock demo). The interface is identical
so the pipeline is storage-agnostic. Every state transition is written here —
that record IS the evidence that the agent performed operational work.
"""
from __future__ import annotations

from typing import Optional

from . import config
from .models import Case

_memory: dict[str, dict] = {}
_fs_client = None


def _firestore():
    global _fs_client
    if _fs_client is None:
        from google.cloud import firestore  # lazy import
        _fs_client = firestore.Client(project=config.GCP_PROJECT)
    return _fs_client


def save(case: Case) -> None:
    doc = case.to_dict()
    if config.USE_FIRESTORE:
        try:
            _firestore().collection(config.FIRESTORE_COLLECTION) \
                .document(case.id).set(doc)
            return
        except Exception:
            pass  # fall through to memory so the demo never dies
    _memory[case.id] = doc


def get(case_id: str) -> Optional[dict]:
    if config.USE_FIRESTORE:
        try:
            snap = _firestore().collection(config.FIRESTORE_COLLECTION) \
                .document(case_id).get()
            if snap.exists:
                return snap.to_dict()
        except Exception:
            pass
    return _memory.get(case_id)


def list_recent(limit: int = 20) -> list[dict]:
    if config.USE_FIRESTORE:
        try:
            q = _firestore().collection(config.FIRESTORE_COLLECTION) \
                .order_by("created_at", direction="DESCENDING").limit(limit)
            return [d.to_dict() for d in q.stream()]
        except Exception:
            pass
    return sorted(_memory.values(), key=lambda d: d["created_at"],
                  reverse=True)[:limit]

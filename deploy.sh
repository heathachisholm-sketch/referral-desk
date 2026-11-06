#!/usr/bin/env bash
# Deploy The Referral Desk to Cloud Run. Run once for your submission proof;
# you can delete the service afterwards to keep spend near zero.
#
# Prerequisites (one-time):
#   gcloud auth login
#   gcloud config set project YOUR_PROJECT_ID
#   gcloud services enable run.googleapis.com firestore.googleapis.com \
#       aiplatform.googleapis.com cloudbuild.googleapis.com
#   # Create a Firestore database (Native mode) in the console or:
#   gcloud firestore databases create --location=eur3
#
# Usage:
#   export GEMINI_API_KEY=...          # your AI Studio key
#   ./deploy.sh
set -euo pipefail

PROJECT_ID="$(gcloud config get-value project 2>/dev/null)"
REGION="${REGION:-europe-west1}"
SERVICE="${SERVICE:-referral-desk}"
MODEL="${GEMINI_MODEL:-gemini-flash-latest}"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "No project set. Run: gcloud config set project YOUR_PROJECT_ID"; exit 1
fi
if [[ -z "${GEMINI_API_KEY:-}" ]]; then
  echo "Set GEMINI_API_KEY first (export GEMINI_API_KEY=...)"; exit 1
fi

echo "Deploying ${SERVICE} to ${PROJECT_ID} (${REGION})…"
gcloud run deploy "${SERVICE}" \
  --source . \
  --region "${REGION}" \
  --allow-unauthenticated \
  --set-env-vars "GEMINI_API_KEY=${GEMINI_API_KEY},GEMINI_MODEL=${MODEL},GOOGLE_CLOUD_PROJECT=${PROJECT_ID},MOCK_MODE=0"

echo "Done. Service URL above. Firestore writes land in collection 'referral_cases'."

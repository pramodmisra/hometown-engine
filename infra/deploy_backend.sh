#!/usr/bin/env bash
# Deploy the FastAPI backend to Cloud Run.
# Usage: ./infra/deploy_backend.sh
# Requires: gcloud authenticated as the project owner (or with run.admin + cloudbuild perms).
#
# NOTE — Windows quirk: when launched from Git Bash, gcloud sometimes hits a
# transient PermissionError on lib/third_party/oauth2client/client.py. As a
# workaround we route the gcloud call through cmd.exe when one is available.

set -euo pipefail

PROJECT="geminiliveagent-489716"
REGION="us-central1"
SERVICE="hometown-engine-api"
SA="hometown-engine-sa@${PROJECT}.iam.gserviceaccount.com"

ARGS=(
  run deploy "${SERVICE}"
  --project "${PROJECT}"
  --region "${REGION}"
  --source backend/
  --service-account "${SA}"
  --allow-unauthenticated
  --memory 1Gi --cpu 1 --concurrency 40
  --min-instances 0 --max-instances 5
  --timeout 60 --port 8080
  --set-env-vars "GCP_PROJECT=${PROJECT},BQ_DATASET=hometown_engine,BQ_LOCATION=US,VERTEX_LOCATION=us-central1,GEMINI_MODEL_FLASH=gemini-2.5-flash,GEMINI_MODEL_PRO=gemini-2.5-pro,CORS_ORIGINS=*,LOG_LEVEL=INFO"
  --quiet
)

echo "Deploying ${SERVICE} to Cloud Run (${REGION}) in project ${PROJECT}..."

if command -v cmd.exe >/dev/null 2>&1; then
  cmd.exe //c "gcloud ${ARGS[*]}"
else
  gcloud "${ARGS[@]}"
fi

echo
echo "Service URL:"
if command -v cmd.exe >/dev/null 2>&1; then
  cmd.exe //c "gcloud run services describe ${SERVICE} --project ${PROJECT} --region ${REGION} --format=value(status.url)"
else
  gcloud run services describe "${SERVICE}" --project "${PROJECT}" --region "${REGION}" --format='value(status.url)'
fi

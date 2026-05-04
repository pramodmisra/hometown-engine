#!/usr/bin/env bash
# Deploy the React/Vite frontend to Cloud Run via nginx.
# See deploy_backend.sh for the cmd.exe-on-Windows quirk.
set -euo pipefail

PROJECT="geminiliveagent-489716"
REGION="us-central1"
SERVICE="hometown-engine-web"

ARGS=(
  run deploy "${SERVICE}"
  --project "${PROJECT}"
  --region "${REGION}"
  --source frontend/
  --allow-unauthenticated
  --memory 512Mi --cpu 1 --concurrency 80
  --min-instances 0 --max-instances 5
  --timeout 30 --port 8080
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

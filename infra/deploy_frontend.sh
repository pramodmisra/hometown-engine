#!/usr/bin/env bash
# Deploy the React/Vite frontend to Cloud Run via nginx.
set -euo pipefail

PROJECT="geminiliveagent-489716"
REGION="us-central1"
SERVICE="hometown-engine-web"

echo "Deploying ${SERVICE} to Cloud Run (${REGION}) in project ${PROJECT}..."

gcloud run deploy "${SERVICE}" \
  --project "${PROJECT}" \
  --region "${REGION}" \
  --source frontend/ \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --concurrency 80 \
  --min-instances 0 \
  --max-instances 5 \
  --timeout 30 \
  --port 8080

echo
echo "Deployed. Service URL:"
gcloud run services describe "${SERVICE}" --project "${PROJECT}" --region "${REGION}" --format='value(status.url)'

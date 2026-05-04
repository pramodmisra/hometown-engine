#!/usr/bin/env bash
# Deploy the FastAPI backend to Cloud Run.
# Usage: ./infra/deploy_backend.sh
# Requires: gcloud authenticated as the project owner (or with run.admin + cloudbuild perms).

set -euo pipefail

PROJECT="geminiliveagent-489716"
REGION="us-central1"
SERVICE="hometown-engine-api"
SA="hometown-engine-sa@${PROJECT}.iam.gserviceaccount.com"

echo "Deploying ${SERVICE} to Cloud Run (${REGION}) in project ${PROJECT}..."

# --source uses Cloud Build behind the scenes; no local Docker required.
gcloud run deploy "${SERVICE}" \
  --project "${PROJECT}" \
  --region "${REGION}" \
  --source backend/ \
  --service-account "${SA}" \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --concurrency 40 \
  --min-instances 0 \
  --max-instances 5 \
  --timeout 60 \
  --port 8080 \
  --set-env-vars "GCP_PROJECT=${PROJECT}" \
  --set-env-vars "BQ_DATASET=hometown_engine" \
  --set-env-vars "BQ_LOCATION=US" \
  --set-env-vars "VERTEX_LOCATION=us-central1" \
  --set-env-vars "GEMINI_MODEL_FLASH=gemini-2.5-flash" \
  --set-env-vars "GEMINI_MODEL_PRO=gemini-2.5-pro" \
  --set-env-vars "CORS_ORIGINS=*" \
  --set-env-vars "LOG_LEVEL=INFO"

echo
echo "Deployed. Service URL:"
gcloud run services describe "${SERVICE}" --project "${PROJECT}" --region "${REGION}" --format='value(status.url)'

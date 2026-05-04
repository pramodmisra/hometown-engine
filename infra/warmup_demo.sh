#!/usr/bin/env bash
# Run this 2-3 minutes BEFORE recording the demo video.
# It warms the in-memory narrative cache on the live Cloud Run instance,
# so all on-camera narratives render instantly during recording.
#
# Cloud Run idle timeout is ~15 min; if you take a break of 15+ min between
# warmup and recording, run this again.

set -euo pipefail

API="${API:-https://hometown-engine-api-865200026782.us-central1.run.app}"

# States that appear in the demo script storyboard.
STATES=("GA" "IL" "WI" "OR" "MN" "CA" "VT" "MI" "TX" "NY" "PA")

echo "Warming up ${#STATES[@]} narratives at ${API} ..."
for state in "${STATES[@]}"; do
  printf "  %s " "$state"
  status=$(curl -sS -m 60 "$API/api/regions/$state/narrative" -w '\n%{http_code}\n' 2>&1)
  http=$(echo "$status" | tail -1)
  body=$(echo "$status" | head -n -1)
  if [ "$http" = "200" ]; then
    echo "OK"
  else
    echo "HTTP $http"
  fi
done

echo
echo "Warming up Discovery Mode ..."
curl -sS -m 30 "$API/api/hubs/discover" >/dev/null && echo "  OK"

echo
echo "Warming up agent (one warm call) ..."
curl -sS -m 60 -X POST "$API/api/agent/ask" \
  -H "Content-Type: application/json" \
  -d '{"message":"What sports does the Pacific Northwest excel at?"}' >/dev/null && echo "  OK"

echo
echo "Done. Cache should hold for ~15 minutes of idle time."

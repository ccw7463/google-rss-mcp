#!/usr/bin/env bash
# Deploy the server to Google Cloud Run as a public Streamable HTTP endpoint.
#
#   GCP_PROJECT=my-project ./deploy/cloudrun.sh
#
# Cloud Run builds the Dockerfile, injects $PORT, and terminates TLS. The
# resulting https://<service>-<hash>-<region>.a.run.app/mcp is what you register
# with Smithery.
set -euo pipefail

PROJECT="${GCP_PROJECT:?set GCP_PROJECT to your Google Cloud project id}"
REGION="${GCP_REGION:-asia-northeast3}"
SERVICE="${SERVICE_NAME:-google-rss-mcp}"

# --allow-unauthenticated: a public registry listing means anonymous callers.
# --max-instances: a hard ceiling, so a traffic spike cannot run up a bill.
# --min-instances 0: scale to zero, which is what keeps this inside the free tier.
# MCP_STATELESS: sessions live in one instance's memory; statelessness is what
#   makes it safe for Cloud Run to route a follow-up request to a new instance.
# GOOGLE_RSS_LANGUAGE is deliberately unset — see README, "Language and region".
gcloud run deploy "$SERVICE" \
    --source . \
    --project "$PROJECT" \
    --region "$REGION" \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 3 \
    --concurrency 40 \
    --timeout 300 \
    --set-env-vars MCP_TRANSPORT=http,MCP_STATELESS=true

URL="$(gcloud run services describe "$SERVICE" \
    --project "$PROJECT" --region "$REGION" --format 'value(status.url)')"

echo
echo "MCP endpoint:  ${URL}/mcp"
echo "Health check:  ${URL}/health"
echo
echo "Verify before registering with Smithery:"
echo "  curl -s ${URL}/health"

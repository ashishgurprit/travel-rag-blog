#!/usr/bin/env bash
# deploy/setup.sh
# One-time GCP setup for Travel RAG Search Engine.
# Run this once before the first Cloud Build deploy.
#
# Usage:
#   export GCP_PROJECT=your-project-id
#   export GCP_REGION=us-central1   # or your preferred region
#   bash deploy/setup.sh

set -euo pipefail

: "${GCP_PROJECT:?Set GCP_PROJECT environment variable}"
: "${GCP_REGION:=us-central1}"

REPO_NAME=travel-rag
SERVICE_NAME=travel-rag-backend
CONNECTOR_NAME=travel-rag-connector
REDIS_NAME=travel-rag-redis

echo "=== GCP Project: $GCP_PROJECT | Region: $GCP_REGION ==="

# ── 1. Enable APIs ─────────────────────────────────────────────────────────
echo ""
echo "1. Enabling required GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  redis.googleapis.com \
  vpcaccess.googleapis.com \
  --project="$GCP_PROJECT"

# ── 2. Artifact Registry ───────────────────────────────────────────────────
echo ""
echo "2. Creating Artifact Registry repository..."
gcloud artifacts repositories create "$REPO_NAME" \
  --repository-format=docker \
  --location="$GCP_REGION" \
  --description="Travel RAG Docker images" \
  --project="$GCP_PROJECT" 2>/dev/null || echo "   (already exists, skipping)"

# ── 3. Secret Manager — create secrets ────────────────────────────────────
echo ""
echo "3. Creating Secret Manager secrets..."
echo "   (You will be prompted to enter values for required secrets.)"

create_secret() {
  local name="$1" prompt="$2"
  if gcloud secrets describe "$name" --project="$GCP_PROJECT" &>/dev/null; then
    echo "   ✓ $name already exists"
  else
    echo -n "   Enter $prompt (leave blank for now): "
    read -rs value
    echo ""
    echo -n "${value}" | gcloud secrets create "$name" \
      --data-file=- \
      --replication-policy=automatic \
      --project="$GCP_PROJECT"
    echo "   ✓ Created $name"
  fi
}

create_secret PINECONE_API_KEY      "Pinecone API key"
create_secret ANTHROPIC_API_KEY     "Anthropic API key"
create_secret REDIS_URL             "Redis URL (fill after Memorystore is created)"
create_secret PINECONE_INDEX_NAME   "Pinecone index name [travel-rag]"
create_secret CORS_ORIGIN           "Frontend URL (fill after Vercel deploy)"
create_secret BOOKING_AFFILIATE_ID  "Booking.com affiliate ID (can be empty)"
create_secret KLOOK_AFFILIATE_ID    "Klook affiliate ID (can be empty)"
create_secret WISE_AFFILIATE_ID     "Wise affiliate ID (can be empty)"

# ── 4. Grant Cloud Build service account Secret Manager access ─────────────
echo ""
echo "4. Granting Secret Manager access to Cloud Build service account..."
PROJECT_NUMBER=$(gcloud projects describe "$GCP_PROJECT" --format="value(projectNumber)")
CB_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
  --member="serviceAccount:${CB_SA}" \
  --role="roles/secretmanager.secretAccessor" \
  --condition=None \
  --quiet

# Also grant Cloud Run SA (Compute default) secret access
CR_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
  --member="serviceAccount:${CR_SA}" \
  --role="roles/secretmanager.secretAccessor" \
  --condition=None \
  --quiet
echo "   ✓ IAM bindings set"

# ── 5. VPC Access Connector (for Memorystore) ─────────────────────────────
echo ""
echo "5. Creating VPC Access Connector..."
gcloud compute networks vpc-access connectors create "$CONNECTOR_NAME" \
  --region="$GCP_REGION" \
  --range=10.8.0.0/28 \
  --project="$GCP_PROJECT" 2>/dev/null || echo "   (already exists, skipping)"

# ── 6. Memorystore Redis ───────────────────────────────────────────────────
echo ""
echo "6. Creating Memorystore Redis instance (takes ~5 min)..."
gcloud redis instances create "$REDIS_NAME" \
  --size=1 \
  --region="$GCP_REGION" \
  --redis-version=redis_7_0 \
  --tier=BASIC \
  --project="$GCP_PROJECT" 2>/dev/null || echo "   (already exists, skipping)"

echo ""
echo "   Waiting for Redis to be ready..."
gcloud redis instances describe "$REDIS_NAME" \
  --region="$GCP_REGION" \
  --project="$GCP_PROJECT" \
  --format="value(state)"

REDIS_IP=$(gcloud redis instances describe "$REDIS_NAME" \
  --region="$GCP_REGION" \
  --project="$GCP_PROJECT" \
  --format="value(host)")

echo "   Redis IP: $REDIS_IP"
echo -n "redis://${REDIS_IP}:6379" | gcloud secrets versions add REDIS_URL \
  --data-file=- \
  --project="$GCP_PROJECT"
echo "   ✓ REDIS_URL secret updated"

# ── 7. Connect Cloud Build to GitHub ──────────────────────────────────────
echo ""
echo "7. Next manual step:"
echo "   GCP Console → Cloud Build → Triggers → Connect Repository → GitHub"
echo "   Create trigger: push to 'master' branch → run cloudbuild.yaml"
echo "   Substitutions: _REGION=$GCP_REGION, _REPO=$REPO_NAME"

echo ""
echo "=== Setup complete ==="
echo ""
echo "After connecting Cloud Build to GitHub, push to master to trigger a deploy."
echo "Then run: ./scripts/verify_deployment.sh <cloud-run-url>"

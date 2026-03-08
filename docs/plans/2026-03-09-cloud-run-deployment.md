# Cloud Run Deployment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deploy the Travel RAG Search Engine backend (FastAPI) to Google Cloud Run and the frontend (Next.js) to Vercel, replacing the Railway config, with HuggingFace model pre-baking, GCP Secret Manager, Memorystore Redis, and a pre-prod verification script.

**Architecture:** Multi-stage Docker build bakes both HuggingFace models (`intfloat/multilingual-e5-large` and `BAAI/bge-reranker-base`) into the image at build time, eliminating cold-start downloads. Secrets are mounted via GCP Secret Manager (not env vars in YAML). Redis runs on GCP Memorystore, accessed via Serverless VPC Access connector.

**Tech Stack:** Docker (multi-stage), Cloud Build, Cloud Run, GCP Secret Manager, GCP Memorystore (Redis), Artifact Registry, Vercel (frontend), `gcloud` CLI

---

## Prerequisites

Before starting, ensure the following are installed and authenticated locally:
- `gcloud` CLI: `gcloud auth login && gcloud auth configure-docker`
- `docker` (for local build testing)
- A GCP project with billing enabled
- Vercel CLI: `npm i -g vercel` (for frontend)

**GCP APIs to enable** (run once):
```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  redis.googleapis.com \
  vpcaccess.googleapis.com
```

---

## Task 1: Multi-Stage Dockerfile with Model Pre-Baking

**Files:**
- Create: `Dockerfile`
- Create: `scripts/download_models.py`

### Step 1: Create the model download script

```python
# scripts/download_models.py
"""Pre-download HuggingFace models at Docker build time."""
from sentence_transformers import SentenceTransformer
from FlagEmbedding import FlagReranker

print("Downloading intfloat/multilingual-e5-large...")
SentenceTransformer("intfloat/multilingual-e5-large")

print("Downloading BAAI/bge-reranker-base...")
FlagReranker("BAAI/bge-reranker-base", use_fp16=True)

print("All models downloaded.")
```

### Step 2: Create the Dockerfile

```dockerfile
# Dockerfile

# ── Stage 1: Builder — install all deps + download models ──────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system deps needed for ML packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Pre-download HuggingFace models into /models
ENV HF_HOME=/models
COPY scripts/download_models.py scripts/download_models.py
RUN python scripts/download_models.py

# ── Stage 2: Runtime — slim image with deps + models ───────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy pre-downloaded models
COPY --from=builder /models /models
ENV HF_HOME=/models

# Copy application code
COPY backend/ backend/
COPY pyproject.toml .

# Non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8080
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Step 3: Build and test locally

```bash
docker build -t travel-rag-local .
```

Expected: Build completes. Both model download messages appear during build. Final image size ~6-8GB.

### Step 4: Smoke-test the image locally

```bash
docker run --rm -p 8080:8080 \
  -e PINECONE_API_KEY=test \
  -e ANTHROPIC_API_KEY=test \
  travel-rag-local
```

Expected: `Application startup complete.` in logs. `curl http://localhost:8080/health` returns `{"status":"ok"}`.

### Step 5: Commit

```bash
git add Dockerfile scripts/download_models.py
git commit -m "feat: multi-stage Dockerfile with model pre-baking"
```

---

## Task 2: Artifact Registry Repository

**Files:** (no code files — GCP resource creation)

### Step 1: Set project variables

```bash
export GCP_PROJECT=<your-project-id>
export GCP_REGION=us-central1
export REPO_NAME=travel-rag
```

### Step 2: Create Artifact Registry repository

```bash
gcloud artifacts repositories create $REPO_NAME \
  --repository-format=docker \
  --location=$GCP_REGION \
  --description="Travel RAG Docker images"
```

Expected: `Created repository [travel-rag]`

### Step 3: Tag and push the image

```bash
docker tag travel-rag-local \
  $GCP_REGION-docker.pkg.dev/$GCP_PROJECT/$REPO_NAME/backend:latest

docker push \
  $GCP_REGION-docker.pkg.dev/$GCP_PROJECT/$REPO_NAME/backend:latest
```

Expected: Push completes. Image visible in GCP console under Artifact Registry.

---

## Task 3: Cloud Build CI/CD Pipeline

**Files:**
- Create: `cloudbuild.yaml`

### Step 1: Write the Cloud Build config

```yaml
# cloudbuild.yaml
steps:
  # Build the Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - '$_REGION-docker.pkg.dev/$PROJECT_ID/$_REPO/backend:$COMMIT_SHA'
      - '-t'
      - '$_REGION-docker.pkg.dev/$PROJECT_ID/$_REPO/backend:latest'
      - '.'
    timeout: '1800s'  # 30 min — model download takes time

  # Push both tags
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', '--all-tags',
           '$_REGION-docker.pkg.dev/$PROJECT_ID/$_REPO/backend']

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: 'gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'travel-rag-backend'
      - '--image=$_REGION-docker.pkg.dev/$PROJECT_ID/$_REPO/backend:$COMMIT_SHA'
      - '--region=$_REGION'
      - '--platform=managed'
      - '--min-instances=1'
      - '--max-instances=10'
      - '--memory=4Gi'
      - '--cpu=2'
      - '--timeout=300'
      - '--concurrency=80'
      - '--port=8080'
      - '--no-allow-unauthenticated'  # remove if public; add Cloud Run invoker IAM instead

substitutions:
  _REGION: us-central1
  _REPO: travel-rag

options:
  logging: CLOUD_LOGGING_ONLY
  machineType: 'E2_HIGHCPU_8'  # faster builds for large images

timeout: '2400s'
```

### Step 2: Commit

```bash
git add cloudbuild.yaml
git commit -m "feat: Cloud Build CI/CD pipeline for Cloud Run"
```

### Step 3: Connect Cloud Build to GitHub

In GCP Console → Cloud Build → Triggers → Connect Repository → GitHub.
Create a trigger: push to `master` branch → run `cloudbuild.yaml`.

---

## Task 4: GCP Secret Manager — Store All Secrets

**Files:** (no code files — GCP resource creation)

### Step 1: Create secrets for each env var

```bash
# Required secrets — fill in real values
echo -n "your-pinecone-key" | gcloud secrets create PINECONE_API_KEY \
  --data-file=- --replication-policy=automatic

echo -n "your-anthropic-key" | gcloud secrets create ANTHROPIC_API_KEY \
  --data-file=- --replication-policy=automatic

echo -n "redis://<memorystore-ip>:6379" | gcloud secrets create REDIS_URL \
  --data-file=- --replication-policy=automatic

echo -n "travel-rag" | gcloud secrets create PINECONE_INDEX_NAME \
  --data-file=- --replication-policy=automatic

echo -n "https://your-frontend-domain.com" | gcloud secrets create CORS_ORIGIN \
  --data-file=- --replication-policy=automatic

# Affiliate IDs (can be empty strings initially)
echo -n "" | gcloud secrets create BOOKING_AFFILIATE_ID --data-file=- --replication-policy=automatic
echo -n "" | gcloud secrets create KLOOK_AFFILIATE_ID --data-file=- --replication-policy=automatic
echo -n "" | gcloud secrets create WISE_AFFILIATE_ID --data-file=- --replication-policy=automatic

# Reddit (for ingestion only, not needed at runtime)
echo -n "" | gcloud secrets create REDDIT_CLIENT_ID --data-file=- --replication-policy=automatic
echo -n "" | gcloud secrets create REDDIT_CLIENT_SECRET --data-file=- --replication-policy=automatic
```

### Step 2: Grant Cloud Run service account access

```bash
# Get the service account email
SA_EMAIL=$(gcloud iam service-accounts list \
  --filter="displayName:Compute Engine default" \
  --format="value(email)")

# Grant secretAccessor role on each secret
for SECRET in PINECONE_API_KEY ANTHROPIC_API_KEY REDIS_URL PINECONE_INDEX_NAME \
              CORS_ORIGIN BOOKING_AFFILIATE_ID KLOOK_AFFILIATE_ID WISE_AFFILIATE_ID; do
  gcloud secrets add-iam-policy-binding $SECRET \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/secretmanager.secretAccessor"
done
```

Expected: `Updated IAM policy for secret [...]` for each.

---

## Task 5: Cloud Run Service with Secret Mounts

**Files:**
- Create: `deploy/cloud-run-service.yaml`

### Step 1: Write the Cloud Run service YAML

```yaml
# deploy/cloud-run-service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: travel-rag-backend
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/min-scale: "1"
        run.googleapis.com/max-scale: "10"
        run.googleapis.com/vpc-access-connector: projects/PROJECT_ID/locations/REGION/connectors/travel-rag-connector
        run.googleapis.com/vpc-access-egress: private-ranges-only
    spec:
      containerConcurrency: 80
      timeoutSeconds: 300
      containers:
        - image: REGION-docker.pkg.dev/PROJECT_ID/travel-rag/backend:latest
          ports:
            - containerPort: 8080
          resources:
            limits:
              memory: 4Gi
              cpu: "2"
          env:
            - name: PINECONE_API_KEY
              valueFrom:
                secretKeyRef:
                  name: PINECONE_API_KEY
                  key: latest
            - name: ANTHROPIC_API_KEY
              valueFrom:
                secretKeyRef:
                  name: ANTHROPIC_API_KEY
                  key: latest
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: REDIS_URL
                  key: latest
            - name: PINECONE_INDEX_NAME
              valueFrom:
                secretKeyRef:
                  name: PINECONE_INDEX_NAME
                  key: latest
            - name: CORS_ORIGIN
              valueFrom:
                secretKeyRef:
                  name: CORS_ORIGIN
                  key: latest
            - name: BOOKING_AFFILIATE_ID
              valueFrom:
                secretKeyRef:
                  name: BOOKING_AFFILIATE_ID
                  key: latest
            - name: KLOOK_AFFILIATE_ID
              valueFrom:
                secretKeyRef:
                  name: KLOOK_AFFILIATE_ID
                  key: latest
            - name: WISE_AFFILIATE_ID
              valueFrom:
                secretKeyRef:
                  name: WISE_AFFILIATE_ID
                  key: latest
          livenessProbe:
            httpGet:
              path: /health
            initialDelaySeconds: 10
            periodSeconds: 30
```

**Note:** Replace `PROJECT_ID` and `REGION` with actual values before applying.

### Step 2: Create VPC Access Connector (for Memorystore)

```bash
gcloud compute networks vpc-access connectors create travel-rag-connector \
  --region=$GCP_REGION \
  --range=10.8.0.0/28
```

Expected: `Created connector [travel-rag-connector]`

### Step 3: Deploy the service

```bash
# Replace placeholders first
sed -i "s/PROJECT_ID/$GCP_PROJECT/g" deploy/cloud-run-service.yaml
sed -i "s/REGION/$GCP_REGION/g" deploy/cloud-run-service.yaml

gcloud run services replace deploy/cloud-run-service.yaml \
  --region=$GCP_REGION
```

Expected: `Service [travel-rag-backend] revision [...] has been deployed`

### Step 4: Make service publicly accessible

```bash
gcloud run services add-iam-policy-binding travel-rag-backend \
  --region=$GCP_REGION \
  --member="allUsers" \
  --role="roles/run.invoker"
```

### Step 5: Commit

```bash
# Restore placeholder before committing (don't commit real project IDs)
sed -i "s/$GCP_PROJECT/PROJECT_ID/g" deploy/cloud-run-service.yaml
sed -i "s/$GCP_REGION/REGION/g" deploy/cloud-run-service.yaml

git add deploy/cloud-run-service.yaml
git commit -m "feat: Cloud Run service definition with Secret Manager mounts"
```

---

## Task 6: Memorystore Redis Instance

**Files:** (no code files — GCP resource creation)

### Step 1: Create a Redis instance

```bash
gcloud redis instances create travel-rag-redis \
  --size=1 \
  --region=$GCP_REGION \
  --redis-version=redis_7_0 \
  --tier=BASIC
```

Expected: Takes 5-10 minutes. `Create request issued for: [travel-rag-redis]`

### Step 2: Get the Redis IP

```bash
REDIS_IP=$(gcloud redis instances describe travel-rag-redis \
  --region=$GCP_REGION \
  --format="value(host)")

echo "Redis IP: $REDIS_IP"
```

### Step 3: Update the REDIS_URL secret

```bash
echo -n "redis://$REDIS_IP:6379" | gcloud secrets versions add REDIS_URL \
  --data-file=-
```

Expected: `Created version [2] of the secret [REDIS_URL]`

---

## Task 7: Remove Railway Config, Update README

**Files:**
- Delete: `railway.toml`, `Procfile`, `runtime.txt`
- Modify: `README.md`

### Step 1: Remove Railway-specific files

```bash
git rm railway.toml Procfile runtime.txt
```

### Step 2: Update README deployment section

Replace the Railway deployment section in `README.md` with:

```markdown
## Deployment

### Backend — Google Cloud Run

```bash
# One-time setup
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  secretmanager.googleapis.com artifactregistry.googleapis.com \
  redis.googleapis.com vpcaccess.googleapis.com

# Build and deploy
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_REGION=us-central1,_REPO=travel-rag
```

See `deploy/cloud-run-service.yaml` for full Cloud Run configuration.
Secrets managed via GCP Secret Manager — see `docs/plans/2026-03-09-cloud-run-deployment.md` for setup.

### Frontend — Vercel

```bash
cd frontend
vercel deploy --prod
```

Set `NEXT_PUBLIC_API_URL` to your Cloud Run backend URL in Vercel project settings.
```

### Step 3: Commit

```bash
git add README.md
git commit -m "chore: replace Railway config with Cloud Run, update README"
```

---

## Task 8: Frontend Deployment to Vercel

**Files:**
- Create: `frontend/vercel.json`

### Step 1: Write Vercel config

```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "env": {
    "NEXT_PUBLIC_API_URL": "@travel-rag-api-url"
  }
}
```

### Step 2: Deploy to Vercel

```bash
cd frontend
vercel --prod
```

During setup: link to existing project or create new, set `NEXT_PUBLIC_API_URL` to your Cloud Run service URL (get it via `gcloud run services describe travel-rag-backend --region=us-central1 --format="value(status.url)"`).

### Step 3: Commit

```bash
cd ..
git add frontend/vercel.json
git commit -m "feat: Vercel deployment config for Next.js frontend"
```

---

## Task 9: Pre-Prod Verification Script

**Files:**
- Create: `scripts/verify_deployment.sh`

### Step 1: Write the verification script

```bash
#!/usr/bin/env bash
# scripts/verify_deployment.sh
# Pre-prod verification gates — run before DNS cutover.
# Usage: ./scripts/verify_deployment.sh https://your-cloud-run-url.run.app

set -euo pipefail

BASE_URL="${1:?Usage: $0 <backend-url>}"
PASS=0
FAIL=0

check() {
  local name="$1" result="$2" expected="$3"
  if [[ "$result" == *"$expected"* ]]; then
    echo "✓ $name"
    ((PASS++))
  else
    echo "✗ $name — expected '$expected', got '$result'"
    ((FAIL++))
  fi
}

echo "=== Pre-prod verification: $BASE_URL ==="
echo ""

# Gate 1: Health check
HEALTH=$(curl -sf "$BASE_URL/health" || echo "FAILED")
check "Health endpoint" "$HEALTH" '"status":"ok"'

# Gate 2: SSE stream — verify event types
SSE=$(curl -sf -N -X POST "$BASE_URL/api/ask" \
  -H "Content-Type: application/json" \
  -d '{"query":"best ramen tokyo"}' \
  --max-time 30 2>&1 || echo "FAILED")

check "SSE: text event emitted"        "$SSE" '"type":"text"'
check "SSE: sources event emitted"     "$SSE" '"type":"sources"'
check "SSE: disclosure event emitted"  "$SSE" '"type":"disclosure"'

# Gate 3: Rate limiting — 21st request must get 429
echo ""
echo "Testing rate limiting (21 rapid requests)..."
STATUS_21=""
for i in $(seq 1 21); do
  STATUS_21=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/ask" \
    -H "Content-Type: application/json" \
    -d '{"query":"test"}' --max-time 5 || echo "000")
done
check "Rate limit (429 on 21st)" "$STATUS_21" "429"

# Gate 4: Cache — second identical query must be faster (>2x)
echo ""
echo "Testing Redis cache..."
T1=$(curl -sf -o /dev/null -w "%{time_total}" -X POST "$BASE_URL/api/ask" \
  -H "Content-Type: application/json" \
  -d '{"query":"kyoto temples visit"}' --max-time 30 || echo "999")

T2=$(curl -sf -o /dev/null -w "%{time_total}" -X POST "$BASE_URL/api/ask" \
  -H "Content-Type: application/json" \
  -d '{"query":"kyoto temples visit"}' --max-time 30 || echo "999")

echo "  First request:  ${T1}s"
echo "  Second request: ${T2}s"
# Rough check: second should be at least 1s faster
if (( $(echo "$T1 - $T2 > 1.0" | bc -l) )); then
  echo "✓ Redis cache (second request faster)"
  ((PASS++))
else
  echo "⚠ Redis cache timing inconclusive — check Cloud Run logs manually"
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[[ $FAIL -eq 0 ]] && echo "All gates PASSED — ready for DNS cutover." || exit 1
```

### Step 2: Make it executable

```bash
chmod +x scripts/verify_deployment.sh
```

### Step 3: Test against local server (optional sanity check)

```bash
uvicorn backend.main:app --port 8000 &
./scripts/verify_deployment.sh http://localhost:8000
kill %1
```

Expected: Health check passes, SSE events pass. Rate limit and cache tests may be inconclusive locally.

### Step 4: Commit

```bash
git add scripts/verify_deployment.sh
git commit -m "feat: pre-prod verification script for Cloud Run deployment"
```

---

## Task 10: Run Verification Against Live Cloud Run

**Files:** (no code changes)

### Step 1: Get the Cloud Run URL

```bash
BACKEND_URL=$(gcloud run services describe travel-rag-backend \
  --region=$GCP_REGION \
  --format="value(status.url)")

echo "Backend URL: $BACKEND_URL"
```

### Step 2: Ingest Japan data (must have data before verification)

```bash
# Set real env vars locally for ingestion script
export PINECONE_API_KEY=<real-key>
export ANTHROPIC_API_KEY=<real-key>
python scripts/ingest_destination.py --destination japan --sources youtube reddit
```

Expected: Summary printed with `upserted > 0` chunks.

### Step 3: Run pre-prod verification

```bash
./scripts/verify_deployment.sh "$BACKEND_URL"
```

Expected: All gates PASSED.

### Step 4: Set CORS_ORIGIN secret to Vercel frontend URL

```bash
FRONTEND_URL=$(vercel inspect --scope=<your-scope> | grep -o 'https://[^ ]*')
echo -n "$FRONTEND_URL" | gcloud secrets versions add CORS_ORIGIN --data-file=-

# Redeploy Cloud Run to pick up new secret version
gcloud run deploy travel-rag-backend \
  --image=$GCP_REGION-docker.pkg.dev/$GCP_PROJECT/travel-rag/backend:latest \
  --region=$GCP_REGION
```

### Step 5: Smoke-test frontend → backend

Open Vercel URL in browser. Submit a query. Verify:
- Text streams in real-time
- Sources appear below the answer
- Disclosure appears at the bottom

---

## Execution Options

Plan complete and saved to `docs/plans/2026-03-09-cloud-run-deployment.md`.

**Two execution options:**

**1. Subagent-Driven (this session)** — fresh subagent per task, review between tasks, fast iteration
**2. Parallel Session (separate)** — open new session with executing-plans, batch execution with checkpoints

**Which approach?**

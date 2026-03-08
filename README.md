# Travel RAG Search Engine

"Perplexity for Travel" — AI-powered travel Q&A with streaming answers, source citations, and affiliate monetization.

## Architecture

- **Backend**: FastAPI + Pinecone + Claude Sonnet 4.6 streaming
- **Embeddings**: intfloat/multilingual-e5-large (1024 dims)
- **Reranker**: BAAI/bge-reranker-base
- **Cache**: Redis (24h TTL)
- **Frontend**: Next.js 14 (App Router) + Tailwind CSS

## Destinations (MVP)
Japan · Thailand · Italy · Turkey · South Korea

## Setup

### Backend
```bash
pip install -r requirements.txt
cp .env.example .env  # fill in your API keys
uvicorn backend.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

### Ingest Data
```bash
python scripts/ingest_destination.py --destination japan --sources youtube reddit
```

## Running Tests
```bash
python -m pytest -q
```

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

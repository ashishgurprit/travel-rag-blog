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
Deploy backend to Railway using `railway.toml`. Set all env vars from `.env.example` in Railway dashboard.

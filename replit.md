# CogniCare

An intelligent multi-agent Retrieval-Augmented Generation (RAG) system for evidence-based cognitive health education. Ask questions and get grounded, citation-backed answers about Alzheimer's disease, MCI, depression, anxiety, and brain health.

## Run & Operate

- `pnpm --filter @workspace/api-server run dev` — run the Node.js API server (port 8080, path `/api`)
- `bash /home/runner/workspace/services/rag-api/start.sh` — run the Python FastAPI RAG backend (port 5001, path `/rag`)
- `pnpm --filter @workspace/cognicare run dev` — run the React frontend (port 26187, path `/`)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks from OpenAPI spec

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- **Frontend**: React + Vite (artifacts/cognicare), wouter routing, TanStack Query, shadcn/ui, Tailwind CSS
- **RAG Backend**: Python 3.11, FastAPI, uvicorn (services/rag-api)
- **Node.js API**: Express 5 (artifacts/api-server)
- **DB**: PostgreSQL + Drizzle ORM (available, not yet used)
- **AI**: OpenAI gpt-4o-mini for LLM synthesis; TF-IDF (sklearn) for document retrieval

## Where things live

- `artifacts/cognicare/` — React frontend, all pages and components
- `artifacts/cognicare/src/lib/api.ts` — Direct fetch utilities for `/rag/` endpoints
- `artifacts/cognicare/src/hooks/use-rag.ts` — TanStack Query hooks wrapping the RAG API
- `artifacts/cognicare/src/pages/` — Home, Chat, Topics, About pages
- `services/rag-api/` — Python FastAPI RAG backend
- `services/rag-api/main.py` — FastAPI app, routes, CORS
- `services/rag-api/agents/pipeline.py` — 4-agent RAG orchestrator
- `services/rag-api/knowledge/documents.py` — 16 knowledge documents + topic categories
- `lib/api-spec/openapi.yaml` — OpenAPI spec (Node.js `/api` routes only)

## Architecture decisions

- Python FastAPI serves the RAG pipeline at `/rag/`; the proxy routes `/rag/*` to port 5001
- TF-IDF (sklearn cosine similarity) used for retrieval to avoid heavy ML dependencies (no FAISS/sentence-transformers needed)
- 4-agent pipeline: Retrieval → Reasoning (OpenAI) → Validation (confidence scoring) → Synthesis (citation packaging)
- In-memory session/message storage — sessions are ephemeral per server restart (suitable for demo)
- Frontend calls `/rag/` directly via custom fetch (not generated hooks) since the Python API is on a different base path

## Product

- **Home** (`/`) — System overview, live stats from RAG API, topic category cards
- **Chat** (`/chat`) — Conversational interface with session management, citations, agent trace accordion, confidence badges, patient/clinician audience toggle
- **Topics** (`/topics`) — Browse 7 cognitive health topic categories (Alzheimer's, MCI, Depression, Anxiety, Interventions, Caregiving, Brain Health)
- **About** (`/about`) — System architecture, knowledge sources, methodology, disclaimer

## Gotchas

- `OPENAI_API_KEY` must be set as a secret for the chat feature to generate responses
- Python deps are installed at startup by `start.sh` (`pip install -r requirements.txt`)
- Sessions are in-memory only — cleared on rag-api restart
- The proxy routes `/rag` (without trailing slash) to the Python service; FastAPI's `root_path="/rag"` handles this

## User preferences

_Populate as you build — explicit user instructions worth remembering across sessions._

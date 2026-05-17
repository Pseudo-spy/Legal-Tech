# STEPS_BACKEND.md — LegalTech AI Contract Scanner
**Backend-Only Build Order & Execution Guide**
**Read PRD.md, TECH_STACK.md, and FOLDER_STRUCTURE.md before starting any step.**

---

## How to Use This Document

This file covers the complete backend build — every service, pipeline, endpoint, worker task, and data layer needed to power all features defined in the PRD. The frontend (`apps/web/`) is entirely out of scope here. Once the backend is complete, every feature can be verified via curl or a REST client.

Each step is self-contained. Complete it fully, run the verification checklist, and only move to the next step when every item passes. Never skip a step. If a verification fails, fix it before proceeding.

The backend is composed of four layers, built in this order:
1. Infrastructure and environment
2. Database and authentication
3. File handling and document parsing
4. AI pipelines and all feature endpoints

---

## PHASE 0 — Repository & Environment Setup

---

### STEP 0.1 — Initialize the Monorepo Root

Create the root directory `legaltech-ai/` and initialize a git repository. Create the top-level folder structure exactly as defined in FOLDER_STRUCTURE.md, but only the backend-relevant directories need to be wired up now: `services/api/`, `services/ai/`, `apps/worker/`, `packages/`, `infra/`, `scripts/`, `tests/`, and `.github/workflows/`. Create an empty `docker-compose.yml`, `docker-compose.test.yml`, `.gitignore`, and `README.md` at the root. The `.gitignore` must cover Python virtual environments, `__pycache__/`, `.env` files, compiled files, OS artifacts, and the Node-specific folders even if frontend is not yet built.

**Verification:**
- Root directory structure matches FOLDER_STRUCTURE.md at the top level for backend-relevant paths
- Git is initialized and first commit is made
- `.gitignore` blocks `__pycache__/`, `*.pyc`, `.env`, `.DS_Store`, `venv/`, `node_modules/`

---

### STEP 0.2 — Create the Root Environment Variable Template

Create `.env.example` at the monorepo root with every environment variable key listed in FOLDER_STRUCTURE.md's environment variables section. All values must be empty placeholders — no real secrets. Group them by section: Frontend (keep the keys, leave values blank), Backend API, AI Service, Shared. Create a copy as `.env` at the root (this is gitignored). Add an inline comment next to every key explaining what it is and where to get it.

**Verification:**
- `.env.example` exists at root with all variable keys present and grouped correctly
- `.env` exists at root and is confirmed to be gitignored
- Every variable from FOLDER_STRUCTURE.md's env section is present with a comment

---

### STEP 0.3 — Initialize the FastAPI Backend Service

Inside `services/api/`, create a Python virtual environment and install all backend packages from `requirements.txt` as listed in TECH_STACK.md. Create the FastAPI `app/main.py` with: app initialization, CORS middleware configured to allow all origins during development (tighten later), and a single `GET /health` endpoint returning `{"status": "ok", "service": "api"}`. Create `app/core/config.py` using Pydantic BaseSettings to load all backend environment variables from `.env`. Create a `run.py` file that starts uvicorn on port 8000. Create the `Dockerfile` for the API service. Create the folder structure inside `services/api/app/` exactly as defined in FOLDER_STRUCTURE.md: `api/`, `core/`, `models/`, `schemas/`, `services/`, `repositories/`, `db/`, `workers/`, `utils/`, and `templates/`. Add empty `__init__.py` files in each.

**Verification:**
- `uvicorn app.main:app --reload` starts without errors on port 8000
- `curl http://localhost:8000/health` returns `{"status": "ok", "service": "api"}`
- `curl -H "Origin: http://localhost:3000" http://localhost:8000/health` shows CORS headers in the response
- All environment variables load without errors via Pydantic Settings

---

### STEP 0.4 — Initialize the AI Service

Inside `services/ai/`, create a Python virtual environment and install all AI-specific packages: spaCy with `en_core_web_sm`, sentence-transformers (`all-MiniLM-L6-v2`), langdetect, langchain, langchain-openai, PyMuPDF, python-docx, unstructured (pdf and docx extras only), httpx, python-dotenv, and deepl. Create a minimal `main.py` that starts a lightweight FastAPI or plain HTTP service on port 8001 with a `GET /health` endpoint returning `{"status": "ok", "service": "ai"}`. Create all subdirectories defined in FOLDER_STRUCTURE.md under `services/ai/`: `pipelines/`, `prompts/`, `models/`, `rag/`, `rules/`, `parser/`, `translation/`, `cache/`, `data/`, `utils/`. Add `__init__.py` files in each. Create the `Dockerfile` for the AI service.

**Verification:**
- All imports succeed: `import fitz`, `import spacy`, `from sentence_transformers import SentenceTransformer`, `import langdetect`, `from langchain import ...`, `import docx`, `import httpx`
- `python -m spacy download en_core_web_sm` completes and `spacy.load("en_core_web_sm")` works
- `SentenceTransformer("all-MiniLM-L6-v2")` downloads and loads without error
- `curl http://localhost:8001/health` returns `{"status": "ok", "service": "ai"}`

---

### STEP 0.5 — Initialize the Celery Worker

Inside `apps/worker/`, create a Python virtual environment. Install Celery, the Redis client, and any shared dependencies needed for task processing (httpx, sqlalchemy, pydantic). Create `celery_app.py` with Celery initialization configured to use the Redis URL from environment variables as both the broker and result backend. Create the `tasks/` directory with placeholder files for each task defined in FOLDER_STRUCTURE.md: `process_contract.py`, `generate_summary.py`, `generate_counter_offer.py`, `generate_report.py`, `embed_contract.py`, `translate_results.py`, `cleanup_expired_reports.py`. Each placeholder file must define an empty Celery task function decorated with `@app.task` so Celery can discover it. Create the `Dockerfile` for the worker.

**Verification:**
- `celery -A celery_app worker --loglevel=info` starts without errors
- Celery connects to Redis and reports worker ready in the logs
- All task modules are auto-discovered by Celery (they appear in the worker log output)

---

### STEP 0.6 — Set Up Docker Compose for Local Development

Write the `docker-compose.yml` at the root to orchestrate all backend services: `api` (FastAPI on port 8000), `ai` (AI service on port 8001), `worker` (Celery, no exposed port), `redis` (Redis on port 6379), `db` (PostgreSQL 16 on port 5432). Configure environment variable injection from the root `.env` file into each service. Configure volume mounts for hot-reload during development on the API and AI services. Write `docker-compose.test.yml` for isolated test environments with a separate Postgres and Redis instance (different ports to avoid collision). Write `infra/nginx/nginx.conf` as a reverse proxy routing `/api` to FastAPI.

**Verification:**
- `docker-compose up` brings all backend services up without errors
- `curl http://localhost:8000/health` returns `{"status": "ok", "service": "api"}`
- `curl http://localhost:8001/health` returns `{"status": "ok", "service": "ai"}`
- Redis is reachable from the worker container (check worker logs for successful connection)
- PostgreSQL is reachable from the API container (check API logs)

---

## PHASE 1 — Database Foundation

---

### STEP 1.1 — Configure Database Connection

In `services/api/app/db/session.py`, set up the SQLAlchemy async engine using `asyncpg` as the driver, connected to the Neon PostgreSQL URL from environment variables. Configure the async session factory with a reasonable connection pool size. Create `app/db/base.py` that imports the declarative base and will serve as the discovery point for all models during Alembic migrations. Initialize Alembic in the `migrations/` directory. Configure `alembic.ini` and `migrations/env.py` to use the async engine and to auto-discover models from `app/db/base.py`.

**Verification:**
- The async engine connects to the database without raising a connection error on startup
- `alembic current` runs without errors (output shows "head" or no current revision yet — no crash)

---

### STEP 1.2 — Create All Database Models

In `services/api/app/models/`, create every ORM model defined in PRD.md Section 4.3. Create models for: `User`, `Contract`, `Clause`, `ScanJob`, `AnalysisResult`, `CounterOffer`, `PrecedentMatch`, `Report`, and `Embedding`. Each model must have: a UUID primary key, appropriate foreign key relationships, `created_at` and `updated_at` timestamps with auto-population, and all columns from the PRD schema. The `Embedding` model must use the `pgvector` `Vector` column type for the embedding field — import from the `pgvector.sqlalchemy` extension. Import all models in `app/db/base.py` so Alembic can detect them.

**Verification:**
- All model files import without errors: `python -c "from app.models import user, contract, clause, scan_job, analysis_result, counter_offer, precedent_match, report, embedding"`
- No circular import errors when all models are imported together
- The `Embedding` model's embedding column is of type `Vector`

---

### STEP 1.3 — Create and Run the Initial Migration

Generate the first Alembic migration using autogenerate. Before running autogenerate, ensure the migration also enables the `pgvector` extension by adding a manual `op.execute("CREATE EXTENSION IF NOT EXISTS vector")` at the top of the `upgrade()` function. Review the generated migration file to confirm all 9 tables are present with the correct columns, foreign keys, and indexes. Run the migration against the development database. Create a second targeted migration that adds any missing indexes important for performance: an index on `clauses.contract_id`, `scan_jobs.contract_id`, `scan_jobs.status`, `embeddings.contract_id`, and `embeddings.embedding_type`.

**Verification:**
- `alembic upgrade head` runs without errors
- All 9 tables exist in the database: `users`, `contracts`, `clauses`, `scan_jobs`, `analysis_results`, `counter_offers`, `precedent_matches`, `reports`, `embeddings`
- The `pgvector` extension is active: run `SELECT * FROM pg_extension WHERE extname = 'vector'` against the database — it should return one row
- `alembic current` confirms the migration is applied

---

### STEP 1.4 — Create the Repository Layer

In `services/api/app/repositories/`, create a repository file for each entity: `user_repo.py`, `contract_repo.py`, `clause_repo.py`, `scan_job_repo.py`, `precedent_repo.py`, and `report_repo.py`. Each repository contains only async database query functions — no business logic. Standard functions for each: `create`, `get_by_id`, `get_all_by_user_id`, `update`, `delete`. Additional functions: `scan_job_repo` needs `update_status(job_id, status)` and `update_progress(job_id, pct)`. `report_repo` needs `get_by_share_uuid(uuid)` and `delete_expired()`. `clause_repo` needs `get_all_by_contract_id(contract_id)` and `bulk_create(clauses)`. All functions must use the async SQLAlchemy session and return `None` gracefully when a record is not found.

**Verification:**
- All repository files import without errors
- Each repository function can be called with a mock async session without errors (write a quick standalone test script if needed)
- No business logic appears in any repository — only query construction and execution

---

## PHASE 2 — Authentication

---

### STEP 2.1 — Configure Clerk JWT Verification in the Backend

In `services/api/app/core/security.py`, implement Clerk JWT verification. The function must: extract the Bearer token from the `Authorization` header, fetch Clerk's JWKS endpoint to get the public key (cache this — do not refetch on every request), verify the token signature and expiry, extract the `sub` claim as the user ID, and return it. Create a FastAPI dependency function wrapping this so any endpoint can inject it with a single parameter. Any verification failure must raise `HTTPException(status_code=401)`.

In `services/api/app/api/v1/endpoints/auth.py`, create the Clerk webhook endpoint `POST /webhooks/clerk`. This endpoint receives `user.created` and `user.updated` events from Clerk and upserts the user record in the `users` table. Verify the webhook signature using the `CLERK_WEBHOOK_SECRET` from environment variables. Register this endpoint on the router in `app/api/v1/router.py` — create `router.py` now if it does not exist.

**Verification:**
- `curl -H "Authorization: Bearer invalidtoken" http://localhost:8000/api/v1/contracts` returns `401`
- `curl -H "Authorization: Bearer <valid_clerk_jwt>" http://localhost:8000/api/v1/contracts` returns `200` (or `404` if no contracts) — not `401`
- Sending a simulated `user.created` webhook payload to `POST /webhooks/clerk` creates a user row in the `users` table

---

### STEP 2.2 — Mount the API Router and Protect All Routes

Create `services/api/app/api/v1/router.py` that aggregates all v1 endpoint routers (auth, upload, analysis, streaming, counter_offer, summary, power, precedent, report, chat, translate, health). Mount this under the `/api/v1` prefix in `app/main.py`. Create placeholder router files for all endpoints listed in FOLDER_STRUCTURE.md under `app/api/v1/endpoints/` — each must define the router with `APIRouter()` and at minimum a stub endpoint returning `{"status": "not_implemented"}` so the router mounts without errors. Apply the Clerk JWT dependency to all routers except `health` and `webhooks/clerk`.

**Verification:**
- `curl http://localhost:8000/api/v1/health` returns `{"status": "ok"}` without authentication
- `curl http://localhost:8000/api/v1/upload` returns `401` (no token)
- `curl http://localhost:8000/api/v1/scan/test-job-id` returns `401` (no token)
- All expected route paths exist: verify with `curl http://localhost:8000/openapi.json` and inspect the `paths` object

---

## PHASE 3 — File Upload Pipeline

---

### STEP 3.1 — Implement the Upload Endpoint

In `services/api/app/api/v1/endpoints/upload.py`, implement the `POST /api/v1/upload` endpoint. It must: require a valid Clerk JWT, accept a JSON request body containing: `file_url` (Uploadthing URL of the encrypted uploaded file), `original_filename`, `file_type` (pdf or docx), and `file_size_bytes`. Create a `Contract` record in the database with the authenticated user's ID, file reference, and detected language as "unknown" (to be updated after detection). Create a `ScanJob` record with status "queued" and progress 0. Queue the main Celery scan task by calling it with the `contract_id` and `file_url`. Return a JSON response containing `job_id`, `contract_id`, and `status: "queued"`.

In `services/api/app/services/contract_service.py`, implement the business logic called by the upload endpoint: `create_contract()` and `create_scan_job()`.

**Verification:**
- `curl -X POST http://localhost:8000/api/v1/upload -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"file_url":"https://example.com/test.pdf","original_filename":"test.pdf","file_type":"pdf","file_size_bytes":50000}'` returns a JSON object with `job_id`, `contract_id`, and `status: "queued"`
- A `Contract` row is created in the database with the correct `user_id`
- A `ScanJob` row is created with `status = "queued"`
- The Celery task appears in the worker logs as received

---

### STEP 3.2 — Implement File Retrieval and Decryption Utility

In `services/api/app/utils/file_handler.py`, implement the file retrieval and temporary storage utility. It must: accept an Uploadthing file URL, download the file bytes using httpx, save the bytes to a secure temporary file path in `/tmp/` with a UUID filename, and return the temp file path. Also implement a cleanup function that deletes the temp file after processing. Note on encryption: the frontend sends the encryption key in the session via the `Authorization` header alongside the Clerk JWT. The file handler must be designed to accept an optional decryption key and decrypt the file bytes using AES-256-GCM before writing to disk. If no key is provided (for testing), write the raw bytes. Document clearly that in production the key comes from the session header.

**Verification:**
- Calling the download function with a publicly accessible PDF URL downloads the file and returns a valid file path
- The temp file exists on disk after the call
- The cleanup function removes the temp file
- Calling with a non-existent URL raises a clear error — not a silent failure

---

## PHASE 4 — Document Parsing Pipeline

---

### STEP 4.1 — Implement the PDF Parser

In `services/ai/parser/pdf_parser.py`, implement PDF text extraction using PyMuPDF (fitz). The parser must: open the file from a file path, extract text page by page, preserve paragraph structure, strip repeated headers and footers (detect text appearing on 3+ consecutive pages and exclude it), and return a single cleaned text string. Handle password-protected PDFs by returning a dict with `error: "password_protected"`. Handle scanned PDFs (no extractable text) by returning the text as an empty string along with a `requires_ocr: True` flag.

**Verification:**
- Run the parser against a real multi-page PDF contract and confirm readable text is returned
- Run against a scanned PDF — confirm an empty text string is returned with `requires_ocr: True`, no crash
- Run against a password-protected PDF — confirm a graceful error dict is returned, no crash

---

### STEP 4.2 — Implement the DOCX Parser

In `services/ai/parser/docx_parser.py`, implement DOCX text extraction using python-docx. The parser must: open the DOCX from a file path, extract text from all paragraphs in document order, preserve section headings as delimiter markers in the output text, extract text from all tables in the document, and return a single cleaned text string. Handle empty or malformed DOCX files without crashing.

**Verification:**
- Run the parser against a real DOCX contract and confirm readable text including headings is returned
- Run against an empty DOCX — confirm an empty string is returned without crash
- Tables in the DOCX appear as text in the output

---

### STEP 4.3 — Implement the Fallback Parser and Dispatcher

In `services/ai/parser/fallback_parser.py`, implement the unstructured.io fallback parser using only the `pdf` and `docx` extras. Accept a file path and file type, run unstructured on it, and return the extracted text as a string.

In `services/ai/parser/__init__.py` (or a `dispatcher.py`), implement the `parse_document(file_path, file_type)` function: call the appropriate primary parser based on file type, check if the output text is meaningful (more than 100 characters), and call the fallback if the primary returns insufficient content. Return a `ParseResult` object containing `text`, `file_type`, `page_count`, and `requires_ocr` flag.

**Verification:**
- `parse_document("path/to/contract.pdf", "pdf")` returns a `ParseResult` with `text` longer than 100 characters for a normal PDF
- `parse_document("path/to/scanned.pdf", "pdf")` triggers the fallback parser and still returns text if unstructured can extract it
- `parse_document("path/to/contract.docx", "docx")` returns correct text

---

### STEP 4.4 — Implement Clause Segmentation

In `services/ai/pipelines/clause_extraction.py`, implement clause segmentation using spaCy's `en_core_web_sm` model. The segmenter must: load the spaCy model once (use a module-level singleton to avoid reloading), split the contract text into sentence units, group adjacent sentences into logical clauses using heuristics (numbered sections like "1.1", lettered sub-clauses, continuation sentences that don't start with a capital letter or clause number), assign each clause a sequential `position_index`, merge any clause under 10 words into the adjacent clause, split any clause over 500 words at sentence boundaries, and return a list of clause objects each containing: `clause_id` (UUID), `position_index`, `text`, and `word_count`.

**Verification:**
- A 10-page contract text produces between 20 and 100 clause objects
- No clause in the output is under 10 words
- No clause in the output is over 500 words
- `position_index` values are sequential integers starting at 0 with no gaps
- Each `clause_id` is a unique UUID

---

## PHASE 5 — LLM Integration Foundation

---

### STEP 5.1 — Implement the OpenRouter Client

In `services/ai/models/openrouter_client.py`, implement the async OpenRouter API client using httpx. It must: read the API key, primary model name, and fast model name from environment variables, support both standard (non-streaming) and streaming request modes via a parameter, enforce `response_format: {"type": "json_object"}` for all structured output calls, implement retry logic with up to 3 retries and exponential backoff on 429 and 5xx responses, log all requests and responses at DEBUG level, and return the response content as a string.

In `services/ai/models/model_config.py`, define model name constants: `PRIMARY_MODEL` (Llama 3.3 70B) and `FAST_MODEL` (Gemini Flash), along with default temperature settings for each use case (risk analysis, creative counter-offer generation, etc.).

In `services/ai/models/streaming.py`, implement the streaming handler that consumes a streaming httpx response from OpenRouter and yields complete JSON strings one at a time as they arrive (accumulate tokens until a valid JSON object is complete, then yield it).

**Verification:**
- `python -c "from services.ai.models.openrouter_client import call_llm; import asyncio; print(asyncio.run(call_llm('Return JSON: {\"test\": true}', 'fast')))"` returns a JSON string without error
- A simulated 429 response (mock the httpx call) triggers a retry — verify via log output
- The streaming handler yields tokens progressively when `stream=True`

---

### STEP 5.2 — Create All Prompt Template Files

In `services/ai/prompts/`, create all 7 prompt template files as plain text: `risk_analysis.txt`, `type_detection.txt`, `consequence.txt`, `summary.txt`, `power_asymmetry.txt`, `counter_offer.txt`, `precedent.txt`. Each file must contain a clearly structured system prompt and user prompt template, using `{{placeholder}}` syntax for all dynamic values. Refer to PRD.md Section 3 for what each prompt must accomplish and what output fields it must return. Every prompt must instruct the model to return only valid JSON with no preamble, no markdown formatting, and no explanation outside the JSON object.

In `services/ai/utils/` create a `prompt_loader.py` utility that: reads a prompt file by name from the `prompts/` directory, substitutes all `{{placeholder}}` tokens with values from a provided dictionary, raises a clear `ValueError` if a required placeholder is missing or if the prompt file does not exist, and returns the final prompt string.

**Verification:**
- Each of the 7 prompt files exists and contains valid text with at least one `{{placeholder}}`
- `prompt_loader.py` correctly substitutes all placeholders given a matching dictionary
- `prompt_loader.py` raises `ValueError` if a required placeholder is missing
- `prompt_loader.py` raises `ValueError` if the requested prompt file does not exist

---

### STEP 5.3 — Implement All Pydantic Response Schemas

In `services/api/app/schemas/`, create all Pydantic v2 schema files:

`response.py` — define all shared enums: `RiskLevel` (HIGH, MEDIUM, LOW, SAFE), `ContractType` (Employment, NDA, Freelance/SOW, SaaS Subscription, Lease/Rental, Partnership, IP License, Loan, M&A, Other), `ScanStatus` (queued, processing, complete, failed), `SignVerdict` (Yes as-is, Yes with changes, No), `PowerLabel`, `EnforcementLikelihood`.

`clause.py` — `ClauseResult` containing all fields from PRD.md Feature 1: clause_id, position_index, text, risk_level, risk_category, plain_english, worst_case_scenario, negotiable (bool), confidence (float), financial_exposure (optional), headline (optional), scenario (optional), probability (optional).

`scan_job.py` — `ScanJobStatus` (job_id, contract_id, status, progress_pct, error_message optional), `ScanResponse`.

`contract.py` — `ContractCreate`, `ContractRead` (includes contract_type, detected_language, party_roles, created_at, overall_risk_score if available).

`power.py` — `PowerAnalysisResult` (power_score int, power_label, key_imbalances array, leverage_points array).

`precedent.py` — `CaseReference` (name, year, jurisdiction, outcome), `PrecedentMatch` (precedent_summary, enforcement_likelihood, confidence_score, cited_cases array).

`counter_offer.py` — `CounterOfferVersion` (clause_text, explanation), `CounterOfferResult` (aggressive, balanced, conservative, negotiation_email).

`summary.py` — `SummaryCard` (one_liner, should_you_sign, top_3_concerns, top_2_positives, overall_risk_score, negotiating_power), `ProsConsItem` (dimension, point), `ProsConsResult` (pros, cons, verdict).

`chat.py` — `ChatRequest` (question, conversation_history optional array), `ChatResponse` (answer, clause_citation optional, sources array).

`report.py` — `ReportCreate`, `ReportRead` (report_id, share_uuid, share_url, expires_at, language, pdf_path).

`translation.py` — `TranslationRequest` (target_language), `TranslationResponse` (contract_id, target_language, status).

In `services/ai/`, create a matching set of Pydantic models for validating raw LLM JSON responses (these may differ slightly — they represent what the LLM actually returns before being mapped to the API schemas). Create a `validate_llm_response(raw_json_string, pydantic_model)` utility in `services/ai/utils/` that: parses the JSON, validates against the Pydantic model, catches `ValidationError` and logs the raw string on failure, and returns `None` on failure so callers can retry.

**Verification:**
- All schema files import without errors
- `ClauseResult(clause_id="...", position_index=0, text="...", risk_level="HIGH", risk_category="indemnity", plain_english="...", worst_case_scenario="...", negotiable=True, confidence=0.85)` parses without error
- `ClauseResult(risk_level="INVALID")` raises a `ValidationError`
- `validate_llm_response('{"bad": "json"', ClauseResult)` returns `None` without raising

---











# FINE-TUNING PIPELINE — ENGINEERING EXECUTION ROADMAP
### LegalTech AI Platform — Legal Domain Model Fine-Tuning Guide

---

## PHASE 1 — Environment Setup & GPU Infrastructure

---

### STEP 1.1 — GPU Platform Selection and Environment Bootstrap

For free GPU access during development and initial training runs, use the following platforms in priority order: (1) **Google Colab Pro** (A100 40GB, ~$10/month, best $/GPU-hour ratio for < 24hr runs); (2) **Kaggle Notebooks** (free 30hr/week on P100 16GB or T4 16GB, no cost); (3) **Vast.ai** (spot RTX 3090 24GB at ~$0.15/hr, cheapest paid option); (4) **RunPod.io** (A100 80GB at ~$1.99/hr for large runs); (5) **Lambda Labs** (A100 40GB at $1.10/hr, most stable). For production self-hosted inference, use a single `NVIDIA A10G 24GB` or `RTX 4090 24GB` which is sufficient for serving a 7B model at INT4 via vLLM. Create a project directory structure as follows:

```
legaltech-finetune/
├── data/
│   ├── raw/                  # scraped and collected raw data
│   ├── processed/            # cleaned JSONL datasets
│   ├── train/                # train split
│   ├── eval/                 # evaluation split
│   └── test/                 # held-out test split
├── configs/
│   ├── qlora_config.yaml
│   ├── training_args.yaml
│   └── model_config.yaml
├── scripts/
│   ├── prepare_dataset.py
│   ├── train.py
│   ├── evaluate.py
│   ├── merge_adapters.py
│   └── push_to_hub.py
├── adapters/                 # saved LoRA adapter checkpoints
├── merged/                   # merged full model weights
├── eval_results/
└── docker/
    ├── Dockerfile.train
    └── Dockerfile.inference
```

Create `docker/Dockerfile.train`:

```dockerfile
FROM nvidia/cuda:12.1.0-devel-ubuntu22.04
RUN apt-get update && apt-get install -y python3.11 python3-pip git wget
RUN pip install torch==2.2.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
RUN pip install unsloth[cu121-torch220] @ git+https://github.com/unslothai/unsloth.git
RUN pip install transformers==4.40.0 peft==0.10.0 trl==0.8.6 datasets==2.19.0 \
    accelerate==0.29.3 bitsandbytes==0.43.1 sentence-transformers==2.7.0 \
    evaluate rouge_score nltk wandb huggingface_hub scipy scikit-learn
WORKDIR /workspace
```

**Verification:**
- Run `nvidia-smi` inside the container and confirm GPU is detected with correct VRAM reported
- Run `python -c "import unsloth; import trl; import peft; print('OK')"` and confirm no import errors
- Run `python -c "import torch; print(torch.cuda.is_available(), torch.version.cuda)"` and confirm `True` and `12.1`

---

### STEP 1.2 — Base Model Selection for Legal Domain Fine-Tuning

Select the base model based on VRAM constraints and task requirements. The recommended models in priority order are:

**Primary Recommendation — `mistralai/Mistral-7B-Instruct-v0.3`**: Best balance of legal reasoning capability, instruction-following, and VRAM efficiency. Fits in 10GB VRAM at INT4 via QLoRA. Strong multilingual performance for Indian language legal contexts. Apache 2.0 licensed — fully commercial-use compatible.

**Secondary — `meta-llama/Meta-Llama-3-8B-Instruct`**: Superior reasoning and longer context (8192 tokens vs 4096). Requires Llama 3 community license (free for commercial use under 700M users). Use this when clause explanation depth and multi-step legal reasoning are the priority.

**Tertiary — `google/gemma-2-9b-it`**: Best multilingual legal performance for Indian jurisdiction tasks (Bengali, Hindi, Tamil). Gemma Terms of Use apply (free for commercial use).

**For resource-constrained environments — `Qwen/Qwen2-7B-Instruct`**: Strongest Hindi/Bengali instruction-following, Apache 2.0, fits on T4 16GB.

Store the model choice in `configs/model_config.yaml`:

```yaml
base_model: "mistralai/Mistral-7B-Instruct-v0.3"
model_max_length: 4096
dtype: "bfloat16"
load_in_4bit: true
attn_implementation: "flash_attention_2"
trust_remote_code: false
```

**Verification:**
- Run `huggingface-cli login` with a valid token and confirm authentication succeeds
- Run a dry-load: `from unsloth import FastLanguageModel; model, tokenizer = FastLanguageModel.from_pretrained("mistralai/Mistral-7B-Instruct-v0.3", load_in_4bit=True)` and confirm model loads without OOM
- Run `print(model.num_parameters())` and confirm parameter count is approximately 7.24 billion

---

## PHASE 2 — Dataset Preparation & JSONL Formatting

---

### STEP 2.1 — Legal Dataset Collection from Free Sources

Create `scripts/collect_datasets.py`. Collect training data from the following free sources:

**Source 1 — ContractNLI** (Stanford, free): Download `https://stanfordnlp.github.io/contract-nli/` — 607 annotated contracts with hypothesis entailment labels. Use for clause understanding tasks.

**Source 2 — CUAD (Contract Understanding Atticus Dataset)** (free, CC BY 4.0): Download from `https://huggingface.co/datasets/theatticusproject/cuad` via `datasets.load_dataset("theatticusproject/cuad")`. Contains 510 contracts with 13,000+ expert annotations across 41 clause categories. This is the primary source.

**Source 3 — MultiLegalPile** (free): Load via `datasets.load_dataset("joelito/Multi_Legal_Pile", "en_contracts", split="train", streaming=True)`. Filter for Indian jurisdiction contracts using `filter(lambda x: "india" in x["jurisdiction"].lower())`.

**Source 4 — Indian Kanoon API** (free, no auth required): Query `https://api.indiankanoon.org/search/?formInput=contract+clause&pagenum=0` to retrieve Indian court judgments. Extract reasoning paragraphs as legal explanation training examples. Rate limit to 1 request/second. Store raw JSON in `data/raw/indian_kanoon/`.

**Source 5 — Platform-specific synthetic data**: Export all anonymized contract analysis results from your PostgreSQL database using: `SELECT c.extracted_clauses, ca.risk_scores, ca.explanations, ca.suggestions FROM contracts c JOIN contract_analyses ca ON c.id = ca.contract_id WHERE ca.quality_score >= 0.8`. This is your highest-value data. Anonymize by replacing all entity names with `[PARTY_A]`, `[PARTY_B]`, `[COMPANY]` using a regex pass.

**Source 6 — Pile of Law** (free): `datasets.load_dataset("pile-of-law/pile-of-law", "cc_casebooks", streaming=True)` for legal textbook content covering contract law principles.

Save all raw data to `data/raw/` with a `manifest.jsonl` recording source, license, record count, and download timestamp.

**Verification:**
- Run `wc -l data/raw/**/*.jsonl` and confirm total raw record count exceeds 50,000 lines
- Run `python -c "from datasets import load_dataset; d = load_dataset('theatticusproject/cuad'); print(len(d['train']))"` and confirm 22,450 training examples load
- Confirm `data/raw/platform_export.jsonl` contains at least 500 rows from the PostgreSQL export

---

### STEP 2.2 — Dataset Cleaning and Deduplication Pipeline

Create `scripts/clean_dataset.py`. Implement the following cleaning pipeline as a sequential function chain applied to each raw record:

**Step 1 — Length filtering**: Discard records where `len(tokenizer.encode(text)) < 64` (too short for meaningful legal learning) or `> 3500` (exceeds safe context with prompt overhead). Log discarded count.

**Step 2 — Language detection**: Use `langdetect` library to detect language. Keep `en`, `hi`, `bn` (Bengali). Discard records with detection confidence below 0.9. Log language distribution.

**Step 3 — Legal content scoring**: Score each text chunk using a `LegalContentScorer` that checks for presence of at least 3 terms from a curated list of 200 legal terms (`["indemnification", "liability", "jurisdiction", "arbitration", "breach", "consideration", "warranty", ...]`). Discard records scoring below 2 legal term hits per 500 tokens.

**Step 4 — Deduplication**: Use `datasketch` MinHash LSH deduplication with `num_perm=128` and `threshold=0.85`. Build the LSH index incrementally to handle large datasets without loading all data into memory. Log duplicate count.

**Step 5 — PII scrubbing**: Apply `presidio-analyzer` + `presidio-anonymizer` to replace person names, email addresses, phone numbers, Aadhaar numbers (regex: `\d{4}\s\d{4}\s\d{4}`), and PAN numbers (regex: `[A-Z]{5}[0-9]{4}[A-Z]{1}`) with placeholder tokens.

**Step 6 — Quality scoring**: Use a `QualityScorer` that scores each sample on: sentence completeness (ends with `.` or clause terminator), legal structure (contains subject + predicate), and coherence (no garbled OCR artifacts detected by checking ratio of `[a-zA-Z]` to total chars above 0.85). Retain only samples scoring 3/3.

Save cleaned output to `data/processed/cleaned.jsonl` with each record including a `quality_score`, `source`, `language`, and `word_count` field.

**Verification:**
- Run `python scripts/clean_dataset.py --dry-run --sample 1000` and confirm retention rate is between 40% and 70%
- Spot-check 20 random records from `data/processed/cleaned.jsonl` and confirm no real person names, phone numbers, or Aadhaar numbers are present
- Run `python -c "import json; lines = open('data/processed/cleaned.jsonl').readlines(); print(len(lines))"` and confirm at least 30,000 clean records remain

---

### STEP 2.3 — Task-Specific JSONL Dataset Construction

Create `scripts/prepare_dataset.py`. Construct 5 task-specific datasets in **ChatML format** (required by Mistral/Llama instruction models) as JSONL files where each line is a JSON object with `{"messages": [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}]}`.

**Task 1 — Clause Explanation** (`data/processed/clause_explanation.jsonl`):
```json
{
  "messages": [
    {"role": "system", "content": "You are a legal AI assistant specializing in contract analysis for Indian and international commercial law. Explain contract clauses clearly, citing applicable law where relevant."},
    {"role": "user", "content": "Explain this clause and its implications:\n\n[CLAUSE_TEXT]"},
    {"role": "assistant", "content": "[EXPLANATION with risk level, legal basis, and plain English summary]"}
  ]
}
```
Source: CUAD annotations mapped to explanation templates. Generate 8,000 examples.

**Task 2 — Legal Risk Analysis** (`data/processed/risk_analysis.jsonl`):
```json
{
  "messages": [
    {"role": "system", "content": "You are a legal risk analyst. Analyze contract clauses for risk, output structured JSON with risk_level (LOW/MEDIUM/HIGH/CRITICAL), risk_factors (list), applicable_laws (list), and recommendations (list)."},
    {"role": "user", "content": "Analyze the risk in this clause under Indian law:\n\n[CLAUSE_TEXT]\n\nJurisdiction: [JURISDICTION]"},
    {"role": "assistant", "content": "{\"risk_level\": \"HIGH\", \"risk_factors\": [...], \"applicable_laws\": [...], \"recommendations\": [...]}"}
  ]
}
```
Source: Platform PostgreSQL export + CUAD risk labels. Generate 6,000 examples. Ensure 30% of examples have `jurisdiction: India` and sub-state jurisdictions.

**Task 3 — Negotiation Suggestions** (`data/processed/negotiation.jsonl`):
```json
{
  "messages": [
    {"role": "system", "content": "You are a contract negotiation specialist. Given a clause and the party perspective, suggest specific counter-proposal language with legal rationale."},
    {"role": "user", "content": "Party perspective: [PARTY_ROLE]\nOriginal clause:\n[CLAUSE_TEXT]\n\nSuggest a counter-proposal."},
    {"role": "assistant", "content": "Counter-proposal:\n[NEW_CLAUSE_TEXT]\n\nRationale: [LEGAL_REASONING]"}
  ]
}
```
Source: ContractNLI paired with rewritten clauses. Generate 4,000 examples.

**Task 4 — AI Legal Coach Q&A** (`data/processed/legal_coach.jsonl`):
```json
{
  "messages": [
    {"role": "system", "content": "You are an AI legal coach helping a non-lawyer understand their contract. Use plain language, avoid jargon, and always recommend consulting a licensed attorney for final decisions."},
    {"role": "user", "content": "[USER_QUESTION_ABOUT_CONTRACT]"},
    {"role": "assistant", "content": "[PLAIN_LANGUAGE_ANSWER]"}
  ]
}
```
Source: Multi-turn Q&A generated from CUAD annotations using a template expander script. Generate 5,000 examples.

**Task 5 — Jurisdiction-Aware Reasoning** (`data/processed/jurisdiction.jsonl`):
```json
{
  "messages": [
    {"role": "system", "content": "You are a jurisdiction-aware legal analyst. When analyzing contracts, consider applicable local laws, precedents, and regulatory requirements specific to the identified jurisdiction."},
    {"role": "user", "content": "Contract jurisdiction: [JURISDICTION]\nClause: [CLAUSE_TEXT]\n\nWhat local laws apply and how do they affect this clause?"},
    {"role": "assistant", "content": "[JURISDICTION_SPECIFIC_ANALYSIS with cited statutes]"}
  ]
}
```
Source: IndiaCode + EUR-Lex data mapped to clause templates. Generate 3,000 examples.

After generating all 5 files, merge and shuffle into `data/train/train.jsonl` (90%), `data/eval/eval.jsonl` (5%), and `data/test/test.jsonl` (5%) using a stratified split that maintains task type ratios. Write the split script to use `random.seed(42)` for reproducibility.

**Verification:**
- Run `python -c "import json; d=[json.loads(l) for l in open('data/train/train.jsonl')]; print(len(d))"` and confirm at least 23,400 training examples (90% of ~26,000 total)
- Validate every JSONL record has the exact schema: `messages` key, 3 message objects with `role` and `content` keys, by running `python scripts/validate_jsonl.py data/train/train.jsonl`
- Confirm task distribution: run `python -c "import json; from collections import Counter; ..."` and verify no task type exceeds 35% of total records

---

### STEP 2.4 — Dataset Tokenization Dry-Run and Context Length Analysis

Create `scripts/analyze_dataset.py`. Load the tokenizer for the chosen base model and run a tokenization dry-run on the full training set without model loading (tokenizer-only, CPU-safe). For each record, tokenize the full formatted ChatML string and record the token count. Compute: `p50`, `p90`, `p95`, `p99` token length percentiles. Plot a histogram using `matplotlib` saved to `eval_results/token_length_distribution.png`. Any record exceeding `model_max_length - 64` tokens (leaving 64 tokens of padding headroom) must be truncated from the assistant turn only, never from the user/system turns. Implement `truncate_assistant_turn(sample, max_tokens, tokenizer)` that trims the assistant response to fit within the budget while preserving complete sentences (truncate at the last `.` before the limit). Write the truncated dataset to `data/train/train_truncated.jsonl` and log the percentage of records that required truncation. If truncation rate exceeds 15%, flag the dataset for review — this indicates the `model_max_length` may be too small for the dataset's complexity.

**Verification:**
- Confirm `p95` token length is below `model_max_length` (4096 for Mistral-7B) by inspecting `eval_results/token_length_stats.json`
- Confirm truncation rate is below 15% by checking the log output of `scripts/analyze_dataset.py`
- Spot-check 5 truncated records and confirm the assistant response ends with a complete sentence (`.` terminator)

---

## PHASE 3 — QLoRA Configuration & Training Setup

---

### STEP 3.1 — Unsloth Model Loading with 4-bit Quantization

Create `scripts/train.py`. At the top of the script, import and initialize Unsloth before any other Hugging Face imports, as Unsloth monkey-patches the transformers library at import time. Load the model as follows:

```python
from unsloth import FastLanguageModel
import torch

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="mistralai/Mistral-7B-Instruct-v0.3",
    max_seq_length=4096,
    dtype=torch.bfloat16,          # bfloat16 on A100/H100; float16 on T4/V100
    load_in_4bit=True,             # QLoRA 4-bit base
    token=os.environ["HF_TOKEN"],
    # Optional: cache locally to avoid re-downloading
    cache_dir="/workspace/model_cache",
)
```

Configure the tokenizer for ChatML format:

```python
from unsloth.chat_templates import get_chat_template
tokenizer = get_chat_template(
    tokenizer,
    chat_template="chatml",        # matches Mistral-7B-Instruct-v0.3 template
    mapping={"role": "role", "content": "content", "user": "user", "assistant": "assistant"},
)
tokenizer.padding_side = "right"   # critical: prevents gradient issues with left-pad
```

After loading, verify memory usage: `torch.cuda.memory_allocated() / 1e9` should be below 6GB for the 4-bit loaded 7B model, leaving headroom for activations during training.

**Verification:**
- Confirm model loads without `OutOfMemoryError` on a 16GB VRAM GPU (T4/P100)
- Run `print(model.get_memory_footprint())` and confirm it reports approximately 4.5–5.5 GB for the 4-bit model
- Run a single forward pass: `inputs = tokenizer("Test legal clause:", return_tensors="pt").to("cuda"); outputs = model(**inputs)` and confirm no errors

---

### STEP 3.2 — PEFT QLoRA Adapter Configuration

Apply LoRA adapters to the model using Unsloth's `get_peft_model` wrapper, which automatically selects optimal target modules for the detected architecture:

```python
model = FastLanguageModel.get_peft_model(
    model,
    r=64,                          # LoRA rank — 64 for domain-specific fine-tuning
    target_modules=[               # Mistral attention + MLP layers
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ],
    lora_alpha=128,                # alpha = 2 * r for stable training
    lora_dropout=0.05,             # small dropout for regularization
    bias="none",                   # no bias training (saves memory)
    use_gradient_checkpointing="unsloth",  # Unsloth's optimized checkpointing
    random_state=42,
    use_rslora=True,               # Rank-Stabilized LoRA — better convergence
    loftq_config=None,
)
```

Save the LoRA configuration to `configs/qlora_config.yaml`:

```yaml
r: 64
lora_alpha: 128
lora_dropout: 0.05
target_modules:
  - q_proj
  - k_proj
  - v_proj
  - o_proj
  - gate_proj
  - up_proj
  - down_proj
bias: none
use_rslora: true
task_type: CAUSAL_LM
```

Print trainable parameter count: `model.print_trainable_parameters()`. For a 7B model with `r=64` and 7 target modules, expect approximately 83M trainable parameters (~1.1% of total), which is the optimal range for legal domain adaptation without catastrophic forgetting.

**Verification:**
- Run `model.print_trainable_parameters()` and confirm trainable params are between 60M–120M (0.8%–1.6% of total)
- Run `print([n for n, p in model.named_parameters() if p.requires_grad][:5])` and confirm only LoRA parameters are trainable (names contain `lora_A` or `lora_B`)
- Confirm no `ValueError` about incompatible target modules by checking all listed modules exist in `model.named_modules()`

---

### STEP 3.3 — Training Arguments and Hyperparameter Configuration

Create `configs/training_args.yaml` and load it in `train.py` using a `TrainingArguments` object:

```python
from transformers import TrainingArguments

training_args = TrainingArguments(
    output_dir="./adapters/legal-mistral-7b-v1",
    num_train_epochs=3,
    per_device_train_batch_size=2,     # safe for 16GB VRAM with seq_len=4096
    per_device_eval_batch_size=2,
    gradient_accumulation_steps=8,    # effective batch size = 2 * 8 = 16
    warmup_ratio=0.05,                # 5% warmup steps
    learning_rate=2e-4,               # standard QLoRA LR for 7B models
    lr_scheduler_type="cosine",       # cosine decay, better than linear for fine-tuning
    fp16=False,                       # use bf16 instead
    bf16=True,                        # bfloat16 for A100; set fp16=True for T4
    logging_steps=10,
    eval_strategy="steps",
    eval_steps=200,
    save_strategy="steps",
    save_steps=200,
    save_total_limit=3,               # keep only 3 best checkpoints
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    greater_is_better=False,
    optim="adamw_8bit",               # 8-bit Adam — critical for VRAM savings
    weight_decay=0.01,
    max_grad_norm=1.0,                # gradient clipping
    dataloader_num_workers=4,
    group_by_length=True,             # batch similar-length sequences together
    report_to="wandb",                # free W&B logging
    run_name="legal-mistral-7b-qlora-v1",
    seed=42,
)
```

For Kaggle/Colab free-tier (T4 16GB), change: `per_device_train_batch_size=1`, `gradient_accumulation_steps=16`, `bf16=False`, `fp16=True`.

Set up Weights & Biases (free tier, unlimited runs): `import wandb; wandb.init(project="legaltech-finetune", name="mistral-7b-qlora-v1")`. W&B free tier supports unlimited experiment tracking — no paid plan needed.

**Verification:**
- Compute effective batch size: `per_device_train_batch_size * gradient_accumulation_steps * num_gpus` = 16 (single GPU) and confirm this matches the intended training configuration
- Confirm `wandb.init()` connects successfully by checking for `wandb: Currently logged in as:` in stdout
- Confirm `output_dir` path is writable by creating a test file there before training begins

---

### STEP 3.4 — SFTTrainer Dataset Formatting and Training Launch

Implement the dataset formatting function and `SFTTrainer` setup in `train.py`:

```python
from trl import SFTTrainer
from datasets import load_dataset

def formatting_prompts_func(examples):
    convos = examples["messages"]
    texts = [
        tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False)
        for convo in convos
    ]
    return {"text": texts}

train_dataset = load_dataset("json", data_files="data/train/train_truncated.jsonl", split="train")
eval_dataset  = load_dataset("json", data_files="data/eval/eval.jsonl", split="train")

train_dataset = train_dataset.map(formatting_prompts_func, batched=True, remove_columns=train_dataset.column_names)
eval_dataset  = eval_dataset.map(formatting_prompts_func, batched=True, remove_columns=eval_dataset.column_names)

from trl import DataCollatorForCompletionOnlyLM
response_template = "<|im_start|>assistant\n"  # ChatML assistant turn start token
collator = DataCollatorForCompletionOnlyLM(
    response_template=response_template,
    tokenizer=tokenizer,
    mlm=False,
)
# Using DataCollatorForCompletionOnlyLM ensures loss is computed ONLY on
# assistant tokens, not on system/user prompts. This is critical for
# instruction fine-tuning — training on prompt tokens degrades performance.

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    dataset_text_field="text",
    max_seq_length=4096,
    data_collator=collator,
    dataset_num_proc=4,
    packing=False,                 # disable packing when using completion-only collator
    args=training_args,
)

trainer_stats = trainer.train()
print(f"Training completed in {trainer_stats.metrics['train_runtime']:.1f}s")
print(f"Peak VRAM used: {torch.cuda.max_memory_reserved() / 1e9:.2f} GB")
```

Before full training, run a smoke test with 20 steps: add `max_steps=20` to `TrainingArguments` temporarily, confirm training starts, loss decreases in the first 10 steps, and no OOM errors occur. Then remove `max_steps` for the full run.

**Verification:**
- Confirm training loss at step 10 is lower than at step 1 (sanity check that gradients are flowing)
- Monitor W&B dashboard and confirm `train/loss` curve decreases smoothly without spikes above 2× the initial loss value
- Confirm `torch.cuda.max_memory_reserved()` stays below available VRAM (e.g., below 15GB on a 16GB GPU)

---

### STEP 3.5 — Training Monitoring and Early Stopping

Add a `EarlyStoppingCallback` to the trainer to prevent overfitting on the legal domain:

```python
from transformers import EarlyStoppingCallback

trainer.add_callback(EarlyStoppingCallback(
    early_stopping_patience=5,      # stop if eval_loss doesn't improve for 5 evals
    early_stopping_threshold=0.001, # minimum improvement threshold
))
```

Create a custom `LegalMetricsCallback` class that inherits from `TrainerCallback` and overrides `on_evaluate`. In `on_evaluate`, run 10 held-out legal prompt completions from `data/test/test.jsonl` using `model.generate()` with `max_new_tokens=256, temperature=0.1, do_sample=True`. Log the completions to W&B as a `wandb.Table` with columns `step`, `prompt`, `generated_response`, `reference_response`. This gives qualitative visibility into model behavior during training beyond loss curves. Monitor for: repetitive output (sign of overfitting), refusal to answer (sign of over-regularization), and factual errors in legal citations (sign of hallucination).

Set up a training resume checkpoint strategy: before launching training, check if `adapters/legal-mistral-7b-v1/checkpoint-*` exists and pass `resume_from_checkpoint=True` to `trainer.train()` to resume interrupted runs automatically.

**Verification:**
- Confirm `EarlyStoppingCallback` triggers if a synthetic eval with constant loss is fed (unit test the callback with mock trainer state)
- Open W&B and confirm the qualitative completions table updates every 200 steps with readable legal text
- Simulate a training interruption (Ctrl+C at step 400) and confirm `trainer.train(resume_from_checkpoint=True)` resumes from the correct checkpoint without re-running earlier steps

---

## PHASE 4 — Evaluation & Quality Assurance

---

### STEP 4.1 — Automated Evaluation with Legal-Specific Metrics

Create `scripts/evaluate.py`. Load the fine-tuned adapter on top of the base model and run structured evaluation against the held-out `data/test/test.jsonl` split. Implement the following evaluation metrics:

**ROUGE Scores** (for clause explanation and legal coach tasks): Compute `rouge1`, `rouge2`, `rougeL` using `evaluate.load("rouge")`. For legal text, `rougeL` above 0.35 is the target threshold.

**BERTScore** (semantic similarity): Use `evaluate.load("bertscore")` with `model_type="nlpaueb/legal-bert-base-uncased"` — a legal domain BERT model — for more legally-relevant semantic scoring than general BERTScore. Target F1 above 0.75.

**JSON Validity Rate** (for risk analysis task): For all test samples from the risk analysis task, parse the generated output as JSON using `json.loads()` and compute the percentage of valid JSON outputs. Target above 95%.

**Risk Level Accuracy** (for risk analysis task): Extract the `risk_level` field from generated JSON and compare against ground truth. Compute accuracy. Target above 80%.

**Legal Citation Presence Rate** (for jurisdiction task): Check if the generated output contains at least one statute citation using a regex `r"(Section \d+|Article \d+|Act \d{4}|IPC|CPC|CrPC|GDPR|IT Act)"`. Compute presence rate. Target above 70%.

**Perplexity on Legal Test Set**: Load a separate `legal_perplexity_test.txt` (500 sentences from Indian contract law textbooks) and compute perplexity using `model.eval()` mode. Compare against base model perplexity. Fine-tuned model should show 15–30% perplexity reduction on legal text.

Save all metrics to `eval_results/evaluation_report.json` and push to W&B as summary metrics.

**Verification:**
- Confirm `eval_results/evaluation_report.json` contains all 6 metric categories with numerical scores
- Confirm JSON validity rate is above 95% — if below, retrain with more risk analysis examples or add a JSON formatting prompt prefix
- Confirm fine-tuned model perplexity on `legal_perplexity_test.txt` is at least 10% lower than the base model

---

### STEP 4.2 — Human Evaluation Protocol for Legal Quality

Create `scripts/generate_eval_samples.py` that generates 100 diverse test completions covering all 5 task types. Format them into a CSV file `eval_results/human_eval_sheet.csv` with columns: `task_type`, `prompt`, `base_model_response`, `finetuned_response`, `ground_truth`. This CSV is for parallel human evaluation comparing base model vs fine-tuned model responses. Score each on: legal accuracy (1–5), clarity (1–5), completeness (1–5), and hallucination presence (0/1). Implement a lightweight Next.js evaluation UI at `eval_ui/` — a simple side-by-side comparison page that loads the CSV, displays prompt + two anonymous responses (randomized order), and accepts ratings via a form POSTing to a `/api/eval/submit` endpoint that appends results to `eval_results/human_ratings.jsonl`. Compute inter-rater agreement using Cohen's Kappa (`sklearn.metrics.cohen_kappa_score`) if multiple raters are used. The fine-tuned model should achieve a statistically significant improvement (paired t-test p < 0.05) over the base model on at least 3 of the 4 criteria.

**Verification:**
- Confirm the CSV contains 100 rows with 20 samples per task type
- Load the Next.js eval UI at `localhost:3001` and confirm both responses display without revealing which is base vs fine-tuned
- After collecting 50 ratings, run `python scripts/compute_kappa.py` and confirm Cohen's Kappa > 0.6 (substantial agreement) between raters

---

## PHASE 5 — Adapter Saving, Merging & Export

---

### STEP 5.1 — Saving LoRA Adapters and Tokenizer

After training completes, save the LoRA adapters and tokenizer using Unsloth's optimized save methods:

```python
# Save LoRA adapters only (lightweight, ~150MB for r=64 on 7B model)
model.save_pretrained("adapters/legal-mistral-7b-v1-final")
tokenizer.save_pretrained("adapters/legal-mistral-7b-v1-final")

# Save in float16 for smaller size (saves ~2× vs bfloat16 on disk)
model.save_pretrained_merged(
    "merged/legal-mistral-7b-v1-merged",
    tokenizer,
    save_method="merged_16bit",     # merge LoRA into base weights, save as fp16
)

# Save quantized for production deployment (GGUF format for Ollama/llama.cpp)
model.save_pretrained_gguf(
    "merged/legal-mistral-7b-v1-q4km",
    tokenizer,
    quantization_method="q4_k_m",  # Q4_K_M: best quality/size ratio for production
)
```

The directory structure after saving:
- `adapters/legal-mistral-7b-v1-final/` — LoRA weights only (~150–300MB), use for incremental fine-tuning
- `merged/legal-mistral-7b-v1-merged/` — full merged fp16 model (~14GB), use for vLLM deployment
- `merged/legal-mistral-7b-v1-q4km/` — GGUF Q4_K_M (~4.2GB), use for Ollama deployment

Create an `adapter_manifest.json`:
```json
{
  "base_model": "mistralai/Mistral-7B-Instruct-v0.3",
  "adapter_version": "1.0.0",
  "training_date": "2024-XX-XX",
  "task_types": ["clause_explanation", "risk_analysis", "negotiation", "legal_coach", "jurisdiction"],
  "qlora_r": 64,
  "training_samples": 23400,
  "eval_rouge_l": 0.XX,
  "eval_bertscore_f1": 0.XX,
  "model_hash": "sha256:..."
}
```

**Verification:**
- Confirm `adapters/legal-mistral-7b-v1-final/adapter_config.json` exists and contains the correct `r`, `lora_alpha`, and `target_modules` values
- Confirm `merged/legal-mistral-7b-v1-q4km/` contains a `.gguf` file and run `ls -lh` to confirm size is between 3.5GB and 5GB for Q4_K_M
- Load the merged model: `from transformers import AutoModelForCausalLM; m = AutoModelForCausalLM.from_pretrained("merged/legal-mistral-7b-v1-merged")` and confirm it loads without errors

---

### STEP 5.2 — Pushing to Hugging Face Hub (Private Repository)

Create `scripts/push_to_hub.py`. Use `huggingface_hub` to push adapters and merged model to a private HF Hub repository for versioned storage and easy deployment:

```python
from huggingface_hub import HfApi, create_repo

api = HfApi(token=os.environ["HF_TOKEN"])

# Create private repo
create_repo(
    repo_id="your-org/legal-mistral-7b-v1",
    repo_type="model",
    private=True,
    exist_ok=True,
)

# Push LoRA adapters (small, push first for fast recovery)
api.upload_folder(
    folder_path="adapters/legal-mistral-7b-v1-final",
    repo_id="your-org/legal-mistral-7b-v1",
    repo_type="model",
    path_in_repo="lora_adapters/",
    commit_message="Add LoRA adapters v1.0.0",
)

# Push GGUF (for Ollama deployment)
api.upload_file(
    path_or_fileobj="merged/legal-mistral-7b-v1-q4km/legal-mistral-7b-v1.Q4_K_M.gguf",
    path_in_repo="gguf/legal-mistral-7b-v1.Q4_K_M.gguf",
    repo_id="your-org/legal-mistral-7b-v1",
    repo_type="model",
    commit_message="Add Q4_K_M GGUF for Ollama deployment",
)
```

Tag the release using `api.create_tag(repo_id="your-org/legal-mistral-7b-v1", tag="v1.0.0")`. Store the HF Hub URL in `adapter_manifest.json`.

**Verification:**
- Navigate to `https://huggingface.co/your-org/legal-mistral-7b-v1` and confirm the repo exists as private with `lora_adapters/` and `gguf/` folders visible
- Run `api.model_info("your-org/legal-mistral-7b-v1")` and confirm the model card metadata is correct
- Confirm the GGUF file size on HF Hub matches the local file size using `os.path.getsize()`

---

## PHASE 6 — Local Inference Deployment

---

### STEP 6.1 — Ollama Deployment with Custom GGUF Model

Add an `ollama` Docker service to `docker-compose.yml`:

```yaml
ollama:
  image: ollama/ollama:latest
  ports:
    - "11434:11434"
  volumes:
    - ollama_data:/root/.ollama
    - ./merged/legal-mistral-7b-v1-q4km:/models/legal-mistral
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
  environment:
    - OLLAMA_NUM_PARALLEL=4
    - OLLAMA_MAX_LOADED_MODELS=1
    - OLLAMA_KEEP_ALIVE=30m
```

Create `docker/Modelfile.legal`:
```
FROM /models/legal-mistral/legal-mistral-7b-v1.Q4_K_M.gguf

TEMPLATE """<|im_start|>system
{{ .System }}<|im_end|>
<|im_start|>user
{{ .Prompt }}<|im_end|>
<|im_start|>assistant
"""

SYSTEM """You are a legal AI assistant specializing in contract analysis, clause explanation, risk assessment, and jurisdiction-aware legal reasoning. You assist legal professionals and non-lawyers with contract understanding."""

PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096
PARAMETER num_predict 1024
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|im_start|>"
```

Register the model with Ollama:
```bash
docker exec ollama ollama create legal-mistral-7b -f /models/legal-mistral/Modelfile.legal
docker exec ollama ollama list  # confirm model appears
```

Create a `LegalOllamaClient` in `app/services/llm/ollama_client.py` using the `ollama` Python library (`pip install ollama`):

```python
import ollama

class LegalOllamaClient:
    def __init__(self, model="legal-mistral-7b", host="http://ollama:11434"):
        self.client = ollama.Client(host=host)
        self.model = model

    async def generate_stream(self, system: str, user: str):
        stream = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            stream=True,
            options={"temperature": 0.1, "num_predict": 1024},
        )
        for chunk in stream:
            yield chunk["message"]["content"]
```

**Verification:**
- Run `curl http://localhost:11434/api/tags` and confirm `legal-mistral-7b` appears in the model list
- Run `curl -X POST http://localhost:11434/api/generate -d '{"model":"legal-mistral-7b","prompt":"Explain an indemnification clause."}'` and confirm a legal explanation is returned within 10 seconds
- Run `docker stats ollama` during inference and confirm VRAM usage stays below 6GB for the Q4_K_M model

---

### STEP 6.2 — vLLM Deployment for Production Inference (High-Throughput)

For production serving with concurrent users, use **vLLM** which provides PagedAttention for 10–20× higher throughput than naive inference. Add a `vllm` Docker service:

```yaml
vllm:
  image: vllm/vllm-openai:latest
  ports:
    - "8080:8000"
  volumes:
    - ./merged/legal-mistral-7b-v1-merged:/models/legal-mistral-merged
  command: >
    --model /models/legal-mistral-merged
    --served-model-name legal-mistral-7b
    --max-model-len 4096
    --gpu-memory-utilization 0.90
    --tensor-parallel-size 1
    --dtype bfloat16
    --enable-prefix-caching
    --max-num-seqs 64
    --api-key ${VLLM_API_KEY}
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

vLLM exposes an **OpenAI-compatible API** at `http://vllm:8080/v1`. Update the FastAPI backend's LLM service to route to vLLM for production using the `openai` Python client:

```python
from openai import AsyncOpenAI

vllm_client = AsyncOpenAI(
    base_url="http://vllm:8080/v1",
    api_key=os.environ["VLLM_API_KEY"],
)

async def legal_completion(system: str, user: str, stream: bool = True):
    response = await vllm_client.chat.completions.create(
        model="legal-mistral-7b",
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        max_tokens=1024,
        temperature=0.1,
        stream=stream,
    )
    return response
```

Add a `LLMRouter` class that selects between `OllamaClient` (dev/low-load), `VLLMClient` (prod/high-load), and `OpenRouterClient` (existing fallback) based on the `LLM_BACKEND` environment variable.

**Verification:**
- Run `curl http://localhost:8080/v1/models` and confirm `legal-mistral-7b` is listed
- Run a load test using `locust` with 10 concurrent users sending clause explanation prompts and confirm p95 latency is below 8 seconds for 512-token responses
- Confirm prefix caching is working by sending identical system prompts back-to-back and observing reduced time-to-first-token on the second request

---

## PHASE 7 — FastAPI Integration & RAG Pipeline Upgrade

---

### STEP 7.1 — Replacing OpenRouter Calls with Fine-Tuned Model in Existing Services

Create `app/services/llm/llm_factory.py` implementing the `LLMFactory` pattern:

```python
from enum import Enum

class LLMBackend(Enum):
    VLLM = "vllm"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"

class LLMFactory:
    @staticmethod
    def get_client(task_type: str) -> BaseLLMClient:
        backend = os.environ.get("LLM_BACKEND", "vllm")
        # Route different tasks to different backends if needed
        task_routing = {
            "clause_explanation":    LLMBackend.VLLM,
            "risk_analysis":         LLMBackend.VLLM,
            "negotiation":           LLMBackend.VLLM,
            "legal_coach":           LLMBackend.OLLAMA,   # lower latency for voice
            "jurisdiction":          LLMBackend.VLLM,
            "general":               LLMBackend.OPENROUTER, # fallback for novel tasks
        }
        target = task_routing.get(task_type, LLMBackend(backend))
        if target == LLMBackend.VLLM:
            return VLLMClient()
        elif target == LLMBackend.OLLAMA:
            return LegalOllamaClient()
        else:
            return OpenRouterClient()
```

Update each existing service: `ClauseAnalysisService`, `RiskAnalysisService`, `CounterOfferService`, `VoiceCoachAgent`, `JurisdictionRiskAdjuster` — replace hardcoded OpenRouter client instantiation with `LLMFactory.get_client(task_type=self.TASK_TYPE)`. This single change routes all legal tasks through the fine-tuned model.

Add a `FINE_TUNED_MODEL_ENABLED` feature flag in Redis (`SET feature:fine_tuned_model 1`). In `LLMFactory`, check this flag before routing to vLLM/Ollama — if `0`, fall back to OpenRouter. This enables instant rollback without a deployment.

**Verification:**
- Set `LLM_BACKEND=vllm` and `FINE_TUNED_MODEL_ENABLED=1`, then call `POST /api/v1/contracts/{id}/analyze` and confirm the response is generated by the fine-tuned model (check `X-LLM-Backend: vllm` response header added by `LLMFactory`)
- Set `SET feature:fine_tuned_model 0` in Redis and re-call the same endpoint; confirm it falls back to OpenRouter within the same request without restart
- Confirm all 5 task types route to the correct backend by inspecting the `X-LLM-Backend` header for each task type

---

### STEP 7.2 — RAG Pipeline Integration with Fine-Tuned Model

Update `app/services/rag/legal_rag.py` to use the fine-tuned model as the generation backbone while keeping Qdrant for retrieval. The existing RAG pipeline must be updated in three places:

**Update 1 — Embedding model alignment**: The fine-tuned model was trained on legal text. Update the embedding model used for Qdrant ingestion and retrieval to `nlpaueb/legal-bert-base-uncased` (a legal domain sentence transformer) instead of the general `all-MiniLM-L6-v2`, to improve retrieval relevance for legal clauses. Re-embed the Qdrant `contracts` collection with the new model using a one-time migration script `scripts/reembed_qdrant.py`. This script must: load the new embedding model, stream all points from Qdrant in batches of 100, re-embed each payload's `clause_text` field, and upsert updated vectors while preserving all metadata.

**Update 2 — Prompt format for fine-tuned model**: The existing RAG chain uses a generic LangChain `ChatPromptTemplate`. Replace it with a `FinetuneAwareLegalPrompt` class that formats the system prompt and user prompt using ChatML format matching the fine-tuning training template. Pass retrieved context as a `RETRIEVED_CLAUSES` section inside the user message:

```
RETRIEVED LEGAL CONTEXT:
{context}

CONTRACT CLAUSE:
{clause_text}

JURISDICTION: {jurisdiction}

Analyze the risk in this clause.
```

**Update 3 — Re-ranking with cross-encoder**: Add a re-ranking step between Qdrant retrieval and LLM generation using `cross-encoder/ms-marco-MiniLM-L-6-v2` (free, self-hosted). Retrieve top-20 candidates from Qdrant, re-rank using the cross-encoder, pass only the top-5 to the LLM. This improves retrieval precision by 15–25% with minimal latency overhead (cross-encoder inference on CPU < 100ms for 20 candidates).

**Verification:**
- Run `python scripts/reembed_qdrant.py --dry-run` and confirm it logs the correct batch size and expected total points without modifying Qdrant
- Query the RAG endpoint and inspect the `X-Retrieved-Docs` debug header (add this in non-prod mode) to confirm retrieved documents are legal text, not generic content
- Run an A/B test: send 50 identical clause analysis requests to both the old pipeline (OpenRouter + MiniLM) and the new pipeline (fine-tuned + legal-bert + re-ranking) and confirm the new pipeline has a higher average BERTScore against ground truth labels

---

### STEP 7.3 — Fine-Tuned Model Health Check and Fallback Endpoint

Create `app/routers/model_health.py`. Implement `GET /api/v1/model/health` that:
1. Sends a fixed probe prompt `"Define consideration in contract law in one sentence."` to the active LLM backend
2. Validates the response contains at least one of the keywords `["consideration", "exchange", "value", "promise", "contract"]`
3. Measures response latency
4. Returns `{ "backend": str, "status": "healthy"|"degraded"|"offline", "latency_ms": int, "model_version": str }`

Run this health check as a Celery Beat task every 60 seconds. Publish the result to a Redis key `model:health:status` with a 90-second TTL. In `LLMFactory`, check this Redis key before routing — if `status != "healthy"`, automatically fall back to OpenRouter and trigger a PagerDuty/Discord webhook alert via a Celery task. Add the health check result to the existing `/api/v1/health` system health endpoint.

**Verification:**
- Stop the vLLM service and call `GET /api/v1/model/health`; confirm `status: "offline"` is returned within 5 seconds (accounting for timeout)
- Confirm a fallback to OpenRouter occurs automatically for the next request after a failed health check by checking `X-LLM-Backend: openrouter` in the response header
- Confirm the Redis key `model:health:status` expires and is removed after 90 seconds of no updates (health check service stopped)

---

## PHASE 8 — Continuous Fine-Tuning & Production MLOps

---

### STEP 8.1 — Feedback Collection Pipeline for Continuous Improvement

Create a `FeedbackCollector` service in `app/services/feedback_collector.py`. Add a `POST /api/v1/feedback` endpoint accepting `{ contract_id: str, task_type: str, prompt: str, model_response: str, feedback_type: "thumbs_up"|"thumbs_down"|"edit", corrected_response: Optional[str], rating: Optional[int] }`. Store feedback in a new PostgreSQL table `model_feedback`:

```sql
CREATE TABLE model_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id UUID REFERENCES contracts(id),
    task_type VARCHAR(50) NOT NULL,
    prompt TEXT NOT NULL,
    model_response TEXT NOT NULL,
    feedback_type VARCHAR(20) NOT NULL,
    corrected_response TEXT,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    user_id UUID REFERENCES users(id),
    model_version VARCHAR(50) NOT NULL,
    llm_backend VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_feedback_task ON model_feedback(task_type, feedback_type, created_at);
```

Add a thumbs-up/thumbs-down + edit button to every AI response in the Next.js frontend. The edit button opens an inline textarea pre-populated with the model response, allowing the user to correct it. On save, the corrected response is submitted to the feedback endpoint. Set a target of collecting 500 corrected examples before triggering a fine-tuning re-run. Create a Celery Beat task `check_feedback_threshold` that runs daily, counts `SELECT COUNT(*) FROM model_feedback WHERE feedback_type='edit' AND created_at > NOW() - INTERVAL '30 days'`, and triggers a `schedule_finetune_run` task when the threshold is met.

**Verification:**
- Submit a feedback record via `POST /api/v1/feedback` and confirm it appears in `model_feedback` with all fields populated
- Set `corrected_response` to a non-null value and confirm `feedback_type` is automatically set to `edit` by a PostgreSQL trigger or application-level validation
- Run `check_feedback_threshold` manually and confirm it logs the current count and triggers a notification (not a full training run) when below threshold

---

### STEP 8.2 — Automated Re-Training Pipeline with New Feedback Data

Create `scripts/retrain_pipeline.py`. This script orchestrates a full re-training cycle incorporating new feedback data. Steps: (1) Export all `feedback_type='edit'` records from `model_feedback` since the last training run, format them as ChatML JSONL using the corrected responses as ground truth assistant turns; (2) Mix new feedback data with 20% of the original training data (reservoir sampling to prevent catastrophic forgetting); (3) Update the dataset version in `adapter_manifest.json`; (4) Launch `train.py` with `--resume-from-adapter adapters/legal-mistral-7b-v1-final` — this initializes LoRA weights from the previous adapter rather than from scratch, enabling continual learning with 3–5× fewer training steps than the initial run; (5) Run `evaluate.py` on the held-out test set and compare new metrics against the stored baseline in `eval_results/baseline_metrics.json`; (6) If all metrics improve (or degrade by less than 2%), automatically push the new adapter to HF Hub with an incremented version tag and update the `model:latest_version` Redis key; (7) If any metric regresses by more than 2%, send an alert and abort the automatic deployment, requiring manual review. Trigger this script as a Celery task `run_finetune_pipeline` from the `check_feedback_threshold` task.

**Verification:**
- Run the pipeline with `--dry-run` flag and confirm it logs the expected steps without making any writes to disk, HF Hub, or Redis
- Inject 10 synthetic feedback records and run the pipeline; confirm the mixed dataset contains both new feedback and 20% of original data
- Confirm the automatic deployment gate works: artificially lower `rougeL` in the evaluation by modifying `evaluate.py` temporarily, run the pipeline, and confirm it aborts deployment and logs a regression alert

---

### STEP 8.3 — Model Versioning and A/B Testing Infrastructure

Create a `ModelVersionManager` in `app/services/model_version_manager.py`. Store version metadata in Redis hashes: `HSET model:versions:v1.0.0 path adapters/v1 status active traffic_pct 90 metrics_rouge_l 0.38`. Implement shadow mode A/B testing: for 10% of production requests (controlled by `traffic_pct`), route to the candidate model (the newly trained adapter loaded into a second Ollama/vLLM instance on a different port) while returning the primary model's response to the user. Log both responses to `model_ab_results` PostgreSQL table with `{ request_id, primary_response, shadow_response, task_type, timestamp }`. Create a `GET /api/v1/admin/model/ab-results` endpoint that returns aggregate metrics comparing primary vs shadow model across task types. Graduate the shadow model to primary only when: shadow model wins on BERTScore in at least 4 of 5 task types, JSON validity rate is above 95%, and latency p95 is within 20% of the primary model. Automate this graduation using a Celery task `evaluate_ab_test_winner` that runs every 24 hours.

**Verification:**
- Set `traffic_pct=10` for the shadow model and send 100 requests; confirm approximately 10 requests (±3) are logged in `model_ab_results` with non-null `shadow_response`
- Confirm the primary model's response is always returned to the user regardless of routing, by verifying `X-AB-Group` response header matches the routing decision but the response body is always from the primary model
- Run `evaluate_ab_test_winner` with mocked metrics where the shadow model wins all 5 task types; confirm it updates `model:versions:latest` to point to the shadow adapter

---

### STEP 8.4 — Production Deployment Checklist and Monitoring

Create `docker/docker-compose.prod.yml` that extends the base compose file with production overrides. Add resource limits for the vLLM service: `mem_limit: 24g`, `cpus: "8"`. Set `restart: always` on both `vllm` and `ollama` services. Add Prometheus scraping: vLLM exposes metrics at `http://vllm:8080/metrics` — add this as a scrape target in `prometheus.yml`. Add the following Grafana dashboard panels (import via `grafana/dashboards/llm_metrics.json`):

- `vllm:e2e_request_latency_seconds` — request latency histogram by task_type
- `vllm:num_requests_running` — concurrent inflight requests
- `vllm:gpu_cache_usage_perc` — KV cache utilization (alert if > 90%)
- Custom: `legal_task_success_rate` — computed from `model_feedback.rating >= 4` rate per task type, exposed as a custom Prometheus gauge updated by a Celery task every 5 minutes

Set up alerting rules in `prometheus/alerts.yml`:
```yaml
- alert: LLMHighLatency
  expr: histogram_quantile(0.95, vllm:e2e_request_latency_seconds) > 10
  for: 5m
  labels:
    severity: warning

- alert: LLMKVCacheExhausted
  expr: vllm:gpu_cache_usage_perc > 90
  for: 2m
  labels:
    severity: critical
```

**Verification:**
- Open Grafana at `http://localhost:3000` and confirm the LLM metrics dashboard loads with real-time data from at least one completed request
- Trigger the `LLMHighLatency` alert by setting the threshold to `0.001s` temporarily and confirm the alert fires in Prometheus Alertmanager within 5 minutes
- Run `docker-compose -f docker-compose.yml -f docker/docker-compose.prod.yml up -d` and confirm all services start with resource limits applied by running `docker inspect vllm | grep -i memory`

---

*End of STEPS.md — Phase 1 through Phase 8 — Fine-Tuning Pipeline Complete*
## PHASE 6 — Core Scan Pipeline

---

### STEP 6.1 — Implement Contract Type Detection Pipeline

In `services/ai/pipelines/type_detection.py`, implement the contract type auto-detection pipeline. It takes the first 1000 tokens of the contract text, calls the FAST_MODEL using the `type_detection.txt` prompt, parses the response with Pydantic validation, and returns a `TypeDetectionResult` object containing: `contract_type` (one of the 10 defined types), `confidence` (float 0–1), `party_roles` (array of strings), and `requires_manual_selection` (True if confidence < 0.8).

**Verification:**
- Run the function against a real employment contract text — it should return `contract_type = "Employment"` with `confidence > 0.8`
- Run against an NDA — it should return `contract_type = "NDA"`
- Run against ambiguous text — it should return `requires_manual_selection = True` if confidence is low
- The function returns a valid Pydantic model, not a raw dict

---

### STEP 6.2 — Implement the Rule Engine

In `services/ai/rules/regex_rules.py`, define the rule set as a list of rule objects. Each rule object has: `name`, `pattern` (compiled regex), `risk_category`, and `risk_level` (HIGH or MEDIUM). Implement at minimum 40 patterns covering all risk categories from PRD.md Feature 1: indemnity, IP assignment, non-compete, non-solicitation, auto-renewal, limitation of liability, termination for convenience, unilateral modification rights, liquidated damages, arbitration-only, payment clawback, and governing law. Include multiple patterns per category to catch varied phrasing.

In `services/ai/rules/risk_mapper.py`, implement the `triage_clause(clause_text)` function: run all patterns against the text, collect matches, and return the triage result — `GREEN` if zero matches, `YELLOW` if 1–2 matches (none HIGH-level), `RED` if 3+ matches or any single HIGH-level pattern matches. Also return the list of matched rule names for downstream use.

**Verification:**
- `triage_clause("shall indemnify, defend, and hold harmless")` returns `RED` or `YELLOW` with category `indemnity`
- `triage_clause("all intellectual property, inventions, and work product created")` returns `RED` with category `ip_assignment`
- `triage_clause("This agreement will automatically renew")` returns `YELLOW` or `RED` with category `auto_renewal`
- `triage_clause("The parties agree to the following payment terms.")` returns `GREEN`
- A clause with a HIGH-level pattern (e.g., a non-compete) returns `RED` regardless of total match count

---

### STEP 6.3 — Implement the Risk Classification Pipeline

In `services/ai/pipelines/risk_classification.py`, implement the full two-pass risk classification pipeline from PRD.md Feature 1.

Pass 1: run `triage_clause` from the rule engine on every clause. Separate results into GREEN, YELLOW, and RED buckets. GREEN clauses receive a default `ClauseResult` with `risk_level = SAFE` and `confidence = 1.0` — no LLM call needed.

Pass 2: take all YELLOW and RED clauses and batch them into groups of maximum 20. For each batch, call the PRIMARY_MODEL with the `risk_analysis.txt` prompt, injecting the contract type, user role, and the batch of clause texts. Parse and validate each clause result in the response array with Pydantic. If validation fails for any clause in a batch, retry that batch once with a correction prompt before defaulting to a safe fallback result.

Implement a streaming variant of this function that yields each validated `ClauseResult` object one at a time as responses arrive, rather than accumulating all results and returning at the end.

**Verification:**
- Run the pipeline on a 30-clause contract where 10 clauses are GREEN, 15 YELLOW, 5 RED
- Confirm exactly 0 LLM calls are made for GREEN clauses (check call count)
- Confirm YELLOW and RED clauses are batched: 15+5 = 20 in one batch = 1 LLM call
- Confirm all 30 clauses are present in the output with valid `ClauseResult` objects
- The streaming variant yields results progressively — not all at once

---

### STEP 6.4 — Implement the SSE Streaming Endpoint

In `services/api/app/api/v1/endpoints/streaming.py`, implement `GET /api/v1/scan/{jobId}/stream`. This is the most critical endpoint. It must: verify the Clerk JWT, confirm the scan job belongs to the requesting user, subscribe to the Redis pub/sub channel named `scan:{jobId}`, yield each message received from the channel as an SSE event with format `data: {json}\n\n`, send a heartbeat event every 15 seconds to keep the connection alive (format: `event: heartbeat\ndata: {}\n\n`), send a final `event: complete\ndata: {}\n\n` event when the scan job status becomes "complete", and close the StreamingResponse cleanly.

In `services/api/app/services/streaming_service.py`, implement the `publish_clause_result(job_id, clause_result_json)` function that publishes a message to the `scan:{jobId}` Redis pub/sub channel. The Celery worker will call this after each clause is processed.

**Verification:**
- `curl -N -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/scan/<jobId>/stream` keeps the connection open and shows `event: heartbeat` every 15 seconds
- `curl -N -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/scan/<invalid-jobId>/stream` returns `404`
- Manually publishing a message to the Redis channel (using `redis-cli PUBLISH scan:<jobId> '{"test":true}'`) causes it to appear in the curl output
- Calling with another user's job ID returns `403`

---

### STEP 6.5 — Implement the Main Celery Scan Task

In `apps/worker/tasks/process_contract.py`, implement the main scan pipeline Celery task. This task orchestrates all pipeline steps in the exact order from PRD.md Section 4.1. The task receives `contract_id` and `file_url` as arguments and must:

1. Update `ScanJob` status to "processing", progress to 0
2. Download and (if applicable) decrypt the contract file via `file_handler.py`
3. Parse the document with the dispatcher — update progress to 10%
4. Detect language with `langdetect` — if non-English, translate to English via DeepL — update progress to 15%
5. Segment into clauses — update progress to 20%
6. Run the rule engine triage on all clauses — update progress to 25%
7. Detect contract type — update progress to 30%
8. Run risk classification (LLM calls on flagged clauses) — publish each completed clause result to Redis as it arrives — update progress to 60%
9. Run consequence generation on HIGH and MEDIUM clauses — update progress to 70%
10. Run power asymmetry analysis — update progress to 75%
11. Run legal precedent retrieval for each HIGH-risk clause — update progress to 80%
12. Run summary card generation — update progress to 85%
13. Run pros/cons generation — update progress to 88%
14. Store all results in the database (clauses, analysis_result, precedent_matches) — update progress to 95%
15. Run embedding pipeline for Q&A RAG — update progress to 98%
16. If original contract was non-English, translate all result text fields back to the user's preferred language — update progress to 99%
17. Update `ScanJob` status to "complete", progress to 100%
18. Publish a "complete" signal to the Redis pub/sub channel

On any unhandled exception: set `ScanJob` status to "failed" and store the error message. Configure the task to retry up to 3 times on transient failures with exponential backoff.

**Verification:**
- Queue the task manually via `celery -A celery_app call process_contract --args='["<contract_id>", "<file_url>"]'`
- Watch the `scan_jobs` table — `progress_pct` should increase through the steps
- Watch the Redis pub/sub channel for clause results being published
- After completion, `ScanJob` status = "complete" in the database
- After completion, all clause rows exist in the `clauses` table
- `analysis_results` row exists with `overall_risk_score` populated
- If the task is given a bad file URL, status becomes "failed" with an error message

---

### STEP 6.6 — Wire Upload to Scan — End-to-End Integration Check

No new code is written in this step. Test the full loop from upload endpoint to scan completion.

**Verification:**
- `POST /api/v1/upload` with a real PDF URL returns `job_id` and `contract_id`
- Open the SSE stream: `curl -N -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/scan/<jobId>/stream`
- Clause results arrive in the stream as the worker processes them
- The stream receives `event: complete` when the scan finishes
- All clause rows exist in the `clauses` table after completion
- `GET /api/v1/scan/<jobId>` (implement a basic status endpoint if not yet done) returns `status: complete`

---

## PHASE 7 — Remaining AI Feature Pipelines

---

### STEP 7.1 — Implement the Consequence Generation Pipeline

In `services/ai/pipelines/consequence_generation.py`, implement the real-world consequence translator from PRD.md Feature 3. The function accepts an array of HIGH and MEDIUM risk clause results (with their risk categories already assigned), iterates over them, and for each clause calls the PRIMARY_MODEL with the `consequence.txt` prompt injecting: `clause_type`, `user_role`, `contract_type`, and `clause_text`. Parse each response into a Pydantic model containing: `headline`, `scenario`, `financial_exposure`, `probability`, and `similar_case` (optional). Return the input clause results enriched with the consequence fields. Only process HIGH and MEDIUM clauses — skip LOW and SAFE. Batch where possible to reduce LLM calls.

Update the main Celery task to call this pipeline after risk classification and to publish updated clause results (with consequence fields added) back to the Redis channel.

**Verification:**
- Run the pipeline directly on a list of mock HIGH-risk clause objects
- An indemnity clause returns a `financial_exposure` field that is a dollar amount or the string "unlimited" — not empty
- An IP assignment clause returns a `headline` that references IP, portfolio, or ownership
- `probability` is always one of "Low", "Medium", or "High"
- LOW and SAFE clauses are passed through unchanged — no LLM calls for them

---

### STEP 7.2 — Implement the Power Asymmetry Pipeline and Endpoint

In `services/ai/pipelines/power_analysis.py`, implement the power asymmetry scorer from PRD.md Feature 5. The function accepts the full array of clause results (with risk assessments) and the user role. It calls the PRIMARY_MODEL with the `power_asymmetry.txt` prompt, parses the response into a `PowerAnalysisResult` Pydantic model containing: `power_score` (integer -100 to +100), `power_label`, `key_imbalances` (array of objects with `clause`, `why`, `score`), and `leverage_points` (array of strings).

In `services/api/app/api/v1/endpoints/power.py`, implement `GET /api/v1/power/{contractId}`. Verify JWT and ownership, fetch the power analysis result from `analysis_results` table, and return the `PowerAnalysisResult`. If the scan is not yet complete, return `202 Accepted` with a retry message.

**Verification:**
- Run the pipeline on a mock contract with all HIGH-risk clauses — confirm `power_score` is below -30
- `power_score` is always an integer between -100 and +100 — never a float, never out of range
- `key_imbalances` contains at least 1 item when HIGH-risk clauses are present
- `curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/power/<contractId>` returns the power analysis JSON for a completed scan

---

### STEP 7.3 — Implement the Summary Card Pipeline and Endpoint

In `services/ai/pipelines/summary.py`, implement the plain-language summary card generator from PRD.md Feature 4. The function accepts: contract type, all HIGH-risk clause summaries, all MEDIUM-risk clause summaries, and risk distribution statistics (counts per level). It calls the FAST_MODEL with `summary.txt`, parses the response into a `SummaryCard` Pydantic model. In the same pipeline file or as a second function, implement the pros/cons generator: accepts the full clause analysis, calls FAST_MODEL with a pros/cons prompt, returns a `ProsConsResult`.

In `services/api/app/api/v1/endpoints/summary.py`, implement `GET /api/v1/summary/{contractId}`. Verify JWT and ownership, fetch summary and pros/cons from `analysis_results`, and return both as a combined response object.

**Verification:**
- `should_you_sign` is always one of "Yes as-is", "Yes with changes", "No" — never any other value
- `overall_risk_score` is always an integer between 0 and 100
- `top_3_concerns` always has exactly 3 items
- `top_2_positives` always has exactly 2 items
- `curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/summary/<contractId>` returns the full summary JSON

---

### STEP 7.4 — Seed the Legal Precedent Corpus

Before implementing the precedent retrieval pipeline, the corpus must exist. In `services/ai/data/precedents/`, create subdirectories for `employment/`, `ip/`, `nda/`, and `vendor/`. Populate each directory with at minimum 15 real or well-researched fictional court case summary files (at least 60 total across all domains). Each file should contain: case name, year, jurisdiction, outcome, a 2–3 sentence summary of the clause at issue and the court's ruling, and the clause type tag. These do not need to be exact legal documents — they are summaries used for embedding similarity.

In `scripts/seed_precedents.py`, implement the seeding script: read all case summary files from the `data/precedents/` subdirectories, embed each using sentence-transformers `all-MiniLM-L6-v2`, store each embedding in the `embeddings` table with `embedding_type = "precedent"` and metadata (jurisdiction, year, outcome, clause_type) in a JSONB column, and print the total number of records indexed.

Run the script to populate the database.

**Verification:**
- `python scripts/seed_precedents.py` runs without errors and reports at least 60 records indexed
- Query the `embeddings` table: `SELECT COUNT(*) FROM embeddings WHERE embedding_type = 'precedent'` returns at least 60
- A manual pgvector similarity search for a non-compete clause text against the `precedent` embeddings returns at least 3 results with similarity score > 0.4

---

### STEP 7.5 — Implement the Legal Precedent Retrieval Pipeline and Endpoint

In `services/ai/rag/retriever.py`, implement the pgvector similarity search function. It accepts: a query embedding (vector), `embedding_type` filter, optional `clause_type` filter, and `top_k` integer. It runs a pgvector cosine similarity query against the `embeddings` table and returns the top-k results with their metadata and similarity scores.

In `services/ai/rag/vector_store.py`, implement `store_embeddings(contract_id, chunks, embedding_type)` for bulk insert of embedding records.

In `services/ai/pipelines/precedent_retrieval.py`, implement the legal precedent retrieval pipeline from PRD.md Feature 9. For each HIGH-risk clause: embed the clause text, run a similarity search filtered to `embedding_type = "precedent"` and the clause's risk category, retrieve the top 3 matches, call the PRIMARY_MODEL with `precedent.txt` injecting the clause text and the 3 retrieved case summaries, parse the response into a `PrecedentMatch` Pydantic model, calculate the confidence score as the product of average retrieval similarity and the LLM's self-rated confidence (implement this in `services/ai/utils/confidence_scorer.py`), store the result in `precedent_matches`.

In `services/api/app/api/v1/endpoints/precedent.py`, implement `GET /api/v1/precedent/{clauseId}`. Verify JWT, confirm the clause belongs to a contract owned by the user, fetch the `PrecedentMatch` record, and return it.

**Verification:**
- Run the pipeline for a non-compete clause — confirm 3 case cards are returned with `enforcement_likelihood` set
- `confidence_score` is between 0 and 100 — never outside this range
- `cited_cases` has between 1 and 3 items
- `curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/precedent/<clauseId>` returns the precedent JSON for a HIGH-risk clause
- The same call for a LOW-risk clause returns `404` or an empty precedent result (precedent is only generated for HIGH-risk)

---

### STEP 7.6 — Seed the Favorable Clause Corpus and Implement Counter-Offer Pipeline

In `services/ai/data/favorable_clauses/`, create subdirectories for each clause type: `indemnity/`, `ip_assignment/`, `non_compete/`, `auto_renewal/`, `limitation_of_liability/`. Populate each with at minimum 5 example favorable clause variants (25+ total). These are rewritten versions of risky clauses that favor the signing party — they serve as RAG references for counter-offer generation.

In `scripts/index_favorable_clauses.py`, implement the seeding script: read all favorable clause files, embed each, store in the `embeddings` table with `embedding_type = "favorable_clause"` and the clause type as metadata, and print the total indexed.

In `services/ai/pipelines/counter_offer.py`, implement the counter-offer generator from PRD.md Feature 6. The function accepts a HIGH-risk clause with its risk category, embeds it, retrieves the top similar favorable clause variant from pgvector filtered by `embedding_type = "favorable_clause"` and clause type, calls PRIMARY_MODEL with `counter_offer.txt` injecting the original clause, retrieved reference, contract type, and user role, parses the response into a `CounterOfferResult` Pydantic model containing aggressive, balanced, conservative versions plus the negotiation email, and stores in `counter_offers`.

In `apps/worker/tasks/generate_counter_offer.py`, implement the Celery task that calls this pipeline. This task is triggered on-demand (not part of the main scan task).

In `services/api/app/api/v1/endpoints/counter_offer.py`, implement `POST /api/v1/counter-offer/{clauseId}`. Verify JWT and ownership, check if a counter-offer already exists (return it immediately if so), otherwise queue the `generate_counter_offer` task, and return `202 Accepted` with the task status. Implement `GET /api/v1/counter-offer/{clauseId}` to poll for the result.

**Verification:**
- `python scripts/index_favorable_clauses.py` indexes at least 25 records
- Run the counter-offer pipeline directly for an IP assignment clause — confirm three versions are generated and are all different from each other
- The `negotiation_email` is 2 sentences in a professional tone
- `curl -X POST -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/counter-offer/<clauseId>` triggers the task and returns `202`
- Polling `GET /api/v1/counter-offer/<clauseId>` eventually returns the three counter-offer versions

---

## PHASE 8 — RAG Chat Pipeline

---

### STEP 8.1 — Implement the Contract Embedding Pipeline

In `services/ai/utils/chunk_splitter.py`, implement the overlapping chunk splitter: accept a text string, split into chunks of approximately 500 tokens (estimate ~4 chars per token), with a 50-token overlap between adjacent chunks, and return an array of chunk strings.

In `services/ai/rag/embedder.py`, implement the contract embedding function: accept a text string, split into chunks using `chunk_splitter`, embed each chunk using sentence-transformers `all-MiniLM-L6-v2` (load the model once as a singleton), and return an array of `{chunk_text, chunk_index, embedding_vector}` objects.

In `apps/worker/tasks/embed_contract.py`, implement the Celery task that: accepts `contract_id` and `contract_text`, runs the embedding pipeline, and stores all chunk embeddings in the `embeddings` table with `embedding_type = "contract_qa"` and the `contract_id`. This task is called at the end of the main scan task.

**Verification:**
- A 5-page contract text (approximately 2000 words) is split into between 8 and 40 chunks
- Adjacent chunks share content at the boundary (the last 50 tokens of chunk N appear at the start of chunk N+1)
- All embeddings are stored in the `embeddings` table with the correct `contract_id` and `embedding_type = "contract_qa"`
- A similarity search for "non-compete" against a contract's embeddings returns chunks containing non-compete language
- Similarity search results are scoped to a single contract — chunks from other contracts are not returned

---

### STEP 8.2 — Implement the Q&A Chat Pipeline and Endpoint

In `services/ai/rag/chat_chain.py`, implement the LangChain Q&A retrieval chain. Configure it with: the pgvector retriever scoped to a specific `contract_id` fetching the top 5 most similar chunks for the query, a system prompt instructing the model to always cite the clause or section it references and to say explicitly if the answer is not in the contract, and streaming enabled. The function accepts `question`, `contract_id`, and optional `conversation_history` (array of prior Q&A pairs), and returns a streaming generator that yields answer tokens.

In `services/api/app/api/v1/endpoints/chat.py`, implement `POST /api/v1/chat/{contractId}`. Verify JWT and ownership. Confirm the contract's embedding task is complete (check that `embeddings` rows exist for this contract). Accept a `ChatRequest` body. Call the chat chain and return a `StreamingResponse` with `text/event-stream` content type. Include the clause citation as a final event after streaming completes.

In `services/api/app/services/chat_service.py`, implement the orchestration logic that formats the conversation history and calls the chat chain.

**Verification:**
- `curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"question":"What are the notice periods?"}' http://localhost:8000/api/v1/chat/<contractId>` streams an answer for a contract that contains notice period language
- The answer contains a clause reference (e.g., "Section 4.2 states...")
- Asking about something not in the contract returns a response explicitly stating it is not addressed — not a hallucinated answer
- Sending a follow-up question with conversation history in the request body uses the prior context in the answer
- Calling the endpoint on a contract that hasn't been embedded yet returns `400` with a clear message

---

## PHASE 9 — Multilingual Support

---

### STEP 9.1 — Implement Language Detection and the DeepL Translation Wrapper

In `services/ai/translation/detector.py`, implement language detection using `langdetect`. Accept a text string (use only the first 500 characters for speed), return the detected language code as a string (e.g., "es", "fr", "de", "en"), and default to "en" on detection failure. Never raise an unhandled exception from this function.

In `services/ai/translation/translator.py`, implement the DeepL API wrapper. Functions needed: `translate_text(text, source_lang, target_lang)` for a single string, and `translate_batch(texts_array, source_lang, target_lang)` for a list of strings in one API call. Use the DeepL API key from environment variables. Handle rate limits and API errors gracefully by returning the original text if translation fails (with a warning log). Implement a bilingual legal glossary loaded from a JSON file at startup that maps jurisdiction-specific legal terms to their correct equivalents in each target language — apply glossary replacements after DeepL translation.

Create the glossary JSON file at `services/ai/translation/legal_glossary.json` with at minimum 20 legal terms mapped across all 6 supported languages (English, Spanish, French, German, Portuguese, Hindi).

**Verification:**
- `detector.detect_language("Este contrato establece los términos")` returns "es"
- `detector.detect_language("This agreement establishes the terms")` returns "en"
- `translator.translate_text("This agreement establishes the terms", "en", "es")` returns a Spanish translation
- `translator.translate_batch(["clause 1 text", "clause 2 text"], "en", "es")` makes exactly 1 DeepL API call (not 2)
- A key legal term like "indemnity" is correctly translated using the glossary, not just raw DeepL output

---

### STEP 9.2 — Integrate the Multilingual Pipeline and Post-Scan Translation

In `services/ai/pipelines/multilingual_pipeline.py`, implement the full multilingual orchestration pipeline from PRD.md Feature 11. Implement two functions:

`preprocess_contract(text)`: detect language, if non-English translate the full text to English, return `{english_text, original_language, was_translated}`.

`postprocess_results(clause_results, analysis_result, target_language)`: after all analysis is complete, translate all human-readable text fields back to `target_language` using batch translation. Fields to translate: `plain_english`, `worst_case_scenario`, `headline`, `scenario`, `one_liner`, all items in `top_3_concerns`, `top_2_positives`, `leverage_points`, and `negotiation_email`. Store both English and translated versions in the database.

The main Celery task already calls preprocess at step 4 and postprocess at step 16 — ensure both are fully wired.

In `apps/worker/tasks/translate_results.py`, implement the on-demand Celery task for post-scan language switching. It accepts `contract_id` and `target_language`, fetches all stored English results from the database, calls the postprocess function, and updates the stored records with the translated versions.

In `services/api/app/api/v1/endpoints/translate.py`, implement `POST /api/v1/translate/{contractId}`. Verify JWT and ownership. Accept a `TranslationRequest` body with `target_language`. Queue the `translate_results` Celery task. Return `202 Accepted` with the task ID.

**Verification:**
- Upload a Spanish-language PDF contract — after the scan, all `plain_english` fields in the `clauses` table should contain Spanish text (translated back)
- `curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"target_language":"fr"}' http://localhost:8000/api/v1/translate/<contractId>` queues the translation task and returns `202`
- After the task completes, re-fetching clause data shows `plain_english` in French
- An English contract is not translated (no DeepL call is made — verify via logs)
- Legal terms in translated results match the glossary mappings, not raw DeepL output

---

## PHASE 10 — Scan Status and History Endpoints

---

### STEP 10.1 — Implement Scan Status and Contract History Endpoints

In `services/api/app/api/v1/endpoints/analysis.py`, implement all contract and scan status endpoints:

`POST /api/v1/scan/{contractId}` — manually trigger or retrigger a scan for a contract the user owns. Verify JWT and ownership. If a scan is already complete, return the existing results. If failed, reset and requeue.

`GET /api/v1/scan/{jobId}` — return the current `ScanJobStatus` (status, progress_pct, error_message if any). No auth bypass — verify JWT and ownership.

`GET /api/v1/contracts` — return a list of all contracts for the authenticated user, with each contract's: `contract_id`, `original_filename`, `contract_type`, `detected_language`, `created_at`, and `overall_risk_score` (from `analysis_results` if complete, null otherwise).

`GET /api/v1/contracts/{contractId}` — return the full contract detail including all clause results, analysis result, and scan job status.

`DELETE /api/v1/contracts/{contractId}` — soft-delete or hard-delete the contract and all associated data for the authenticated user.

**Verification:**
- `curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/scan/<jobId>` returns `{"status": "complete", "progress_pct": 100}` for a finished scan
- `curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/contracts` returns an array of the user's contracts
- `curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/contracts/<contractId>` returns full contract detail including all clause objects
- Accessing another user's contract returns `403`
- Deleting a contract removes its data and subsequent `GET` returns `404`

---

## PHASE 11 — Report Generation

---

### STEP 11.1 — Build the Jinja2 PDF Report Templates

In `services/api/templates/`, create the Jinja2 HTML templates for the PDF report from PRD.md Feature 12. Create `base.html` with: overall layout, Jinja2 block definitions for each section, color variables for risk levels (HIGH=red, MEDIUM=amber, LOW=green, SAFE=grey), embedded professional-looking CSS for print layout, and a logo placeholder. Create section templates: `cover.html`, `summary.html`, `clauses.html`, `power.html`, `precedent.html`, `counter_offers.html`. The CSS in `static/report.css` must include proper page-break rules to prevent clauses or case citations from being cut mid-page.

Create all 6 i18n language string files in `templates/i18n/`: `en.json`, `es.json`, `fr.json`, `de.json`, `pt.json`, `hi.json`. Each file must contain translated labels for all static report text: section headings, risk level labels, verdict labels, footer disclaimer, etc.

**Verification:**
- Render `base.html` with dummy Jinja2 context data — confirm it produces valid HTML with no template errors
- `weasyprint` can convert the rendered HTML to a PDF without raising errors: `python -c "from weasyprint import HTML; HTML(string='<h1>Test</h1>').write_pdf('/tmp/test.pdf')"`
- The generated test PDF is a valid PDF file (non-zero bytes, opens correctly)
- All 6 i18n JSON files exist and contain at minimum 10 label keys each

---

### STEP 11.2 — Implement the PDF Generation Service and Report Endpoints

In `services/api/app/utils/pdf_generator.py`, implement the PDF generation function. It must: accept a `contract_id` and `language`, fetch all associated data from the database (contract metadata, all clauses sorted by position, analysis result, counter-offers, precedent matches), select the correct i18n JSON file based on language, render each template section with the data using Jinja2, concatenate sections into a complete HTML document, convert to PDF using WeasyPrint, save to a path under a `reports/` directory, and return the file path.

In `services/api/app/services/report_service.py`, implement: `create_report_record(contract_id, language)` — generates a UUID for the share link, calculates the 48-hour expiry timestamp, creates a `Report` record in the database. `get_report(report_id, user_id)` — fetches and returns the report if owned by the user. `get_report_by_share_uuid(share_uuid)` — fetches the report without authentication check, but verifies it has not expired.

In `apps/worker/tasks/generate_report.py`, implement the Celery task that calls `pdf_generator.py` and updates the report record with the PDF path.

In `services/api/app/api/v1/endpoints/report.py`, implement:
`POST /api/v1/report/generate/{contractId}` — verify JWT and ownership, create the report record, queue the `generate_report` Celery task, return `202 Accepted` with the report ID.
`GET /api/v1/report/{reportId}` — verify JWT and ownership, return the PDF as a file download response or a JSON record with the PDF path and share URL.
`GET /api/v1/report/share/{shareUuid}` — public endpoint (no JWT required), fetch report by share UUID, verify it has not expired, return the PDF as a file download or the report data as JSON. Return `410 Gone` if expired.

**Verification:**
- `curl -X POST -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/report/generate/<contractId>` triggers report generation and returns a report ID
- After the Celery task runs, `curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/report/<reportId>` returns the report data including a `share_url`
- `curl http://localhost:8000/api/v1/report/share/<shareUuid>` works without authentication and returns the report data
- Manually set a report's `expires_at` to a time in the past — the same share UUID call should return `410 Gone`
- The generated PDF file is non-zero bytes and opens correctly as a PDF

---

### STEP 11.3 — Implement the Report Cleanup Celery Beat Task

In `apps/worker/tasks/cleanup_expired_reports.py`, implement the Celery Beat periodic task. It must: query the database for all `Report` records where `expires_at < NOW()`, for each expired report attempt to delete the PDF file from the filesystem (log a warning if the file is missing but do not crash), delete the report record from the database, and log the total number of reports cleaned up in this run.

In `apps/worker/celery_app.py`, configure Celery Beat to schedule `cleanup_expired_reports` on an hourly interval.

**Verification:**
- Manually create a report record with `expires_at` set 1 hour in the past and the PDF file on disk
- Call the task directly: `celery -A celery_app call cleanup_expired_reports`
- Confirm the report record no longer exists in the database
- Confirm the PDF file has been deleted from disk
- A report with `expires_at` in the future is NOT deleted
- Confirm the task appears in the Celery Beat schedule: `celery -A celery_app beat --loglevel=debug`

---

## PHASE 12 — Caching Layer

---

### STEP 12.1 — Implement the Redis Result Cache

In `services/ai/cache/result_cache.py`, implement the result caching utility. Functions needed:

`get_cache_key(contract_text)`: generate a SHA-256 hash of the contract text content (stripped of whitespace) — this is the cache key. Never use the filename as part of the key.

`get_cached_results(contract_text)`: check Redis for a cached scan result using the content hash as the key. If found, return the deserialized results. If not found, return `None`.

`store_results(contract_text, results, ttl_days=7)`: serialize the full results dict and store in Redis with a TTL of 7 days.

`invalidate_cache(contract_text)`: delete the cached result for the given content hash.

In `services/ai/cache/cache_config.py`, define constants: default TTL, key prefix convention (e.g., `scan_result:`), and any Redis connection settings.

Integrate the cache check as the very first step in the main Celery scan task (`process_contract.py`): if a cache hit is found, publish the cached clause results to the SSE channel directly and mark the scan job as complete without any LLM or parsing calls. Store results in the cache at the end of every new scan.

**Verification:**
- Run a full scan on a contract — confirm a cache key is stored in Redis after completion (`redis-cli KEYS "scan_result:*"`)
- Upload the exact same contract a second time — confirm the second scan completes in under 2 seconds and no LLM calls appear in the AI service logs
- Rename the file and upload again — confirm the cache is still hit (content hash, not filename)
- Call `invalidate_cache` manually — confirm the key is removed from Redis and the next scan does a full LLM run

---

### STEP 12.2 — Pre-Compute Demo Contract Results

In `services/ai/data/synthetic_contracts/`, create 3 demo contract files: a freelance agreement (containing at least one IP assignment clause and one non-compete clause), an employment contract (containing at least one non-compete and one automatic renewal clause), and an NDA (containing indemnity and governing law clauses). These should be realistic plain-text contracts of at least 5 pages each.

In `scripts/seed_demo_contracts.py`, implement the pre-computation script: for each of the 3 demo contracts, run the full scan pipeline, and store the results in Redis with no TTL (TTL = 0 means permanent). Log the cache key for each contract so it can be referenced in documentation.

**Verification:**
- `python scripts/seed_demo_contracts.py` runs without errors and logs 3 cache keys
- Uploading the demo freelance agreement contract triggers a cache hit and completes in under 3 seconds
- The cached freelance agreement result contains at least one HIGH-risk IP assignment clause
- The cached NDA result contains at least one HIGH-risk indemnity clause

---

## PHASE 13 — Rate Limiting

---

### STEP 13.1 — Implement API Rate Limiting

Configure rate limiting using Upstash Redis (the same Redis instance used for Celery). Implement a rate limiter middleware or per-endpoint dependency in `services/api/app/core/` using a sliding window algorithm backed by Redis atomic operations. Apply rate limits exactly as defined in PRD.md Section 7.4:

- Upload endpoint: 10 uploads per user per hour
- Scan endpoint: 10 scans per user per hour
- Chat endpoint: 100 messages per user per day
- Counter-offer endpoint: 50 requests per user per day

All rate limit keys must be scoped to the authenticated user ID so limits are per-user, not global. On limit exceeded, return `429 Too Many Requests` with a `Retry-After` header indicating when the limit resets.

**Verification:**
- Make 11 rapid upload requests with the same user token — the 11th returns `429`
- The `429` response includes a `Retry-After` header with a valid timestamp
- Rate limits are per-user: two different users can each make 10 uploads without blocking each other
- After the window resets (simulate by moving the Redis key TTL to 0), requests succeed again

---
# ADVANCED FEATURES — ENGINEERING EXECUTION ROADMAP
### LegalTech AI Platform — Phase Implementation Guide

---

## PHASE 1 — AI Legal Coach (Voice-Powered Contract Guidance Assistant)

---

### STEP 1.1 — Speech-to-Text Pipeline with OpenAI Whisper (Self-Hosted)

Install and containerize Whisper using the `faster-whisper` library, which provides a CTranslate2-optimized runtime that is 4× faster than the original Whisper with lower memory usage. Add a new Docker service `whisper-service` to your `docker-compose.yml` using `python:3.11-slim` as the base image. Install `faster-whisper==1.1.0` and `ffmpeg` inside the container. Expose port `8001` internally. On startup, preload the `large-v3` model into memory using `CTranslate2` with `compute_type="int8"` for CPU or `float16` for GPU. Create a FastAPI sub-application at `/api/v1/voice/transcribe` that accepts multipart file uploads (`.webm`, `.wav`, `.ogg`, `.mp3`). Convert incoming audio to 16kHz mono WAV using `ffmpeg` subprocess call before passing to Whisper. Return a JSON response with `{ "transcript": str, "language": str, "confidence": float, "segments": [...] }`. Mount a shared Docker volume `/app/audio_tmp` for temporary file handling. Set `WHISPER_MODEL_SIZE` as an environment variable so the model tier can be changed without rebuilding the image.

**Verification:**
- POST a 30-second `.webm` audio clip to `/api/v1/voice/transcribe` and confirm transcript accuracy above 90% WER on legal vocabulary
- Confirm `language` field auto-detects Hindi, Bengali, and English correctly from test clips
- Measure p95 transcription latency under 4 seconds for a 30-second clip on 4-core CPU

---

### STEP 1.2 — Voice Session Orchestration and LangChain Legal Coach Agent

Create a new FastAPI router `voice_coach.py` under `app/routers/`. Define a `POST /api/v1/voice/coach/session` endpoint that accepts `{ contract_id: str, user_id: str, audio_file: UploadFile }`. The endpoint must: (1) forward audio to the Whisper service via internal HTTP call using `httpx.AsyncClient`, (2) retrieve the parsed contract clauses from PostgreSQL using `contract_id`, (3) inject the transcript and relevant contract context into a LangChain `ConversationalRetrievalChain` backed by your existing Qdrant vector store, and (4) stream the LLM response back to the frontend via SSE. Define a `VoiceCoachAgent` class that wraps a LangChain `AgentExecutor` with three tools: `ClauseLookupTool` (queries Qdrant for relevant clauses by semantic similarity), `RiskExplainerTool` (fetches pre-computed risk scores from Redis by clause hash), and `SimplificationTool` (rewrites legalese into plain language via a dedicated LLM prompt). Store the conversation history per session in Redis using the key pattern `voice_coach:{user_id}:{session_id}` with a 1-hour TTL. Use `ConversationBufferWindowMemory` with `k=10` to keep context manageable. Route all LLM calls through your existing OpenRouter integration using `claude-3-haiku` as the default model for low-latency responses.

**Verification:**
- Assert that a question like "What does the indemnification clause mean?" returns a simplified explanation referencing the exact contract clause text
- Confirm Redis stores conversation turns with correct TTL by inspecting `TTL voice_coach:{id}:{id}` in `redis-cli`
- Confirm SSE stream opens within 800ms of the request and first token arrives within 1.5 seconds

---

### STEP 1.3 — Text-to-Speech Response with Coqui TTS (Self-Hosted)

Add a `coqui-tts` Docker service to `docker-compose.yml` using the `ghcr.io/coqui-ai/tts` base image. Preload the `tts_models/en/ljspeech/tacotron2-DDC` model at container startup for English, and `tts_models/multilingual/multi-dataset/xtts_v2` for multilingual support (supports Hindi, Bengali, and 15+ other languages). Create a FastAPI endpoint `POST /api/v1/voice/synthesize` that accepts `{ text: str, language: str, speed: float }` and streams back an `audio/wav` response using `StreamingResponse`. Implement a Redis-backed audio cache with key `tts_cache:{sha256(text + language)}` and a 24-hour TTL to avoid re-synthesizing identical phrases. For production, add a Celery task `synthesize_legal_response` that pre-generates audio for common legal explanations (boilerplate clause explanations, risk summaries) during off-peak hours and stores them in the cache. In the voice coach endpoint from Step 1.2, after receiving the streamed LLM text response, fire the synthesis task asynchronously and return both the text SSE stream and a `synthesis_task_id` that the frontend can poll or use via a second SSE channel.

**Verification:**
- POST `{ "text": "This clause transfers all liability to you.", "language": "en", "speed": 1.0 }` and receive a valid WAV file with correct audio
- Confirm cache hit returns audio within 50ms by making two identical requests and comparing response times
- Test XTTS v2 with a Bengali text string and verify the output is intelligible

---

### STEP 1.4 — Frontend Voice Interface Component (Next.js 15)

Create a `VoiceCoach` React component at `components/voice/VoiceCoach.tsx`. Use the browser's `MediaRecorder` API with `mimeType: 'audio/webm;codecs=opus'` to capture microphone input. Implement a `useVoiceRecorder` custom hook that manages states: `idle`, `recording`, `processing`, `speaking`. Render a push-to-talk button with a waveform visualizer built using the Web Audio API's `AnalyserNode` and a `<canvas>` element drawing `getByteTimeDomainData()` at 60fps. On recording stop, `MediaRecorder.stop()` assembles a `Blob`, which is converted to `FormData` and POSTed to `/api/v1/voice/coach/session` along with `contract_id`. Open an `EventSource` on the response SSE endpoint to receive streamed text tokens and render them progressively in a chat bubble. When the `synthesis_task_id` is received in the SSE stream, poll `GET /api/v1/voice/synthesize/status/{task_id}` every 500ms until complete, then fetch the audio URL and play it using the `HTMLAudioElement` API. Add a playback speed control (0.75×, 1×, 1.25×) that updates TTS speed on re-synthesis. Store conversation history in component state and display as a chat timeline with user voice inputs shown as transcript bubbles and AI responses shown with an audio play button. Gate the microphone permission request behind an explicit user action using `navigator.mediaDevices.getUserMedia`.

**Verification:**
- Open browser DevTools → Network tab and confirm the FormData POST includes a valid audio blob with non-zero size
- Confirm the SSE stream delivers tokens progressively and the chat bubble updates character by character
- Confirm the audio playback control plays the synthesized voice response without CORS errors

---

### STEP 1.5 — Voice Session Storage and Analytics

Create a PostgreSQL table `voice_coach_sessions` with columns: `id UUID PRIMARY KEY`, `user_id UUID REFERENCES users(id)`, `contract_id UUID REFERENCES contracts(id)`, `session_start TIMESTAMPTZ`, `session_end TIMESTAMPTZ`, `transcript JSONB` (array of `{ role, text, timestamp }` objects), `topics_discussed TEXT[]`, `clauses_referenced UUID[]`, `language VARCHAR(10)`, `created_at TIMESTAMPTZ DEFAULT NOW()`. Write a Celery task `save_voice_session` that is triggered at session end and writes the full session data to this table. Additionally, extract clause IDs referenced during the session using a regex + LLM pass over the transcript and populate `clauses_referenced`. Create a `GET /api/v1/voice/sessions/{user_id}` endpoint that returns paginated session history. On the frontend, add a "Session History" drawer in the `VoiceCoach` component that lists past sessions with clickable transcripts and an option to resume a session (which re-loads the conversation history into `ConversationBufferWindowMemory`).

**Verification:**
- Trigger a complete session and query `SELECT * FROM voice_coach_sessions WHERE user_id = ?` to confirm all fields are populated
- Confirm `clauses_referenced` correctly identifies at least 80% of clauses that were explicitly discussed in test sessions
- Confirm session resume correctly re-loads context by asking a follow-up question that requires prior session knowledge

---

## PHASE 2 — Regional Law Intelligence & Jurisdiction-Aware Analysis

---

### STEP 2.1 — Jurisdiction Data Model and Legal Database Schema

Create the following PostgreSQL tables. `jurisdictions` table: `id UUID PRIMARY KEY`, `country_code CHAR(2)`, `state_province VARCHAR(100)`, `display_name VARCHAR(200)`, `legal_system VARCHAR(50)` (common_law / civil_law / sharia / mixed), `currency VARCHAR(10)`, `official_languages TEXT[]`, `timezone VARCHAR(50)`, `created_at TIMESTAMPTZ`. `legal_rules` table: `id UUID PRIMARY KEY`, `jurisdiction_id UUID REFERENCES jurisdictions(id)`, `category VARCHAR(100)` (e.g., employment, IP, data_privacy, commercial), `rule_name VARCHAR(200)`, `rule_text TEXT`, `effective_date DATE`, `expiry_date DATE`, `citation VARCHAR(500)`, `source_url TEXT`, `embedding VECTOR(768)` (pgvector extension), `created_at TIMESTAMPTZ`. `contract_jurisdiction_analysis` table: `id UUID PRIMARY KEY`, `contract_id UUID REFERENCES contracts(id)`, `detected_jurisdiction_id UUID REFERENCES jurisdictions(id)`, `specified_jurisdiction_id UUID REFERENCES jurisdictions(id)`, `conflicts JSONB`, `compliance_gaps JSONB`, `risk_adjustments JSONB`, `analyzed_at TIMESTAMPTZ`. Enable `pgvector` on your PostgreSQL instance: `CREATE EXTENSION IF NOT EXISTS vector;`. Add an HNSW index: `CREATE INDEX ON legal_rules USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64);`.

**Verification:**
- Run `\d jurisdictions` and `\d legal_rules` in psql and confirm all columns and foreign keys are present
- Run `SELECT * FROM pg_extension WHERE extname = 'vector';` and confirm pgvector is active
- Insert 5 sample `legal_rules` rows and confirm `SELECT id FROM legal_rules ORDER BY embedding <=> $1 LIMIT 3` returns results

---

### STEP 2.2 — Legal Data Ingestion Pipeline for Indian and Global Jurisdictions

Create a Celery task group `ingest_legal_data` under `tasks/jurisdiction_ingestion.py`. Implement scrapers for the following free sources: (1) **IndiaCode** (`https://www.indiacode.nic.in`) — scrape acts and sections using `httpx` + `BeautifulSoup4`, targeting the IT Act 2000, Contract Act 1872, NDA enforceability sections, and PDPB 2023 provisions; (2) **eGazette India** (`https://egazette.nic.in`) — download and parse gazette notifications as PDFs using `pdfminer.six`, extract structured text, and chunk by section; (3) **EUR-Lex** (`https://eur-lex.europa.eu/rest/annotation`) — query the public REST API for GDPR, ePrivacy Directive, and Digital Services Act texts; (4) **CanLII** (`https://www.canlii.org`) — scrape Canadian provincial contract law variations; (5) **CommonLII** (`http://www.commonlii.org`) — scrape common law jurisdictions including Singapore, Malaysia, and Australia. For each scraped legal text, chunk it into 512-token segments with 128-token overlap using LangChain's `RecursiveCharacterTextSplitter`, generate embeddings using `sentence-transformers/legal-bert-base-uncased` (a domain-specific model), and insert into both `legal_rules` (PostgreSQL) and a `jurisdiction_laws` collection in Qdrant. Store the raw source documents in a local MinIO bucket `legal-source-docs` (self-hosted, add to `docker-compose.yml`). Schedule the ingestion task to re-run every Sunday at 2 AM via Celery Beat with `crontab(hour=2, minute=0, day_of_week=0)`.

**Verification:**
- Run `SELECT COUNT(*) FROM legal_rules WHERE jurisdiction_id = (SELECT id FROM jurisdictions WHERE country_code = 'IN')` and confirm at least 500 rules exist after ingestion
- Query Qdrant collection `jurisdiction_laws` and confirm point count matches PostgreSQL `legal_rules` count
- Confirm MinIO bucket `legal-source-docs` contains the original PDF/HTML source files with correct metadata

---

### STEP 2.3 — Jurisdiction Auto-Detection from Contract Text

Create a `JurisdictionDetector` class in `app/services/jurisdiction_detector.py`. This class must implement a multi-signal detection pipeline: (1) **Explicit clause detection** — use a regex pattern library (`legal_regex_patterns.py`) to find governing law clauses, e.g., `r"governed by.*laws of.*?(?P<jurisdiction>[A-Z][a-z]+ ?[A-Z]?[a-z]*)"`, covering 50+ variations of governing law and jurisdiction clauses; (2) **NER-based detection** — use `spaCy` with the `en_core_web_trf` model and a custom NER component trained to recognize `JURISDICTION` entities, court names, and regulatory body names; (3) **LLM fallback** — if regex and NER yield a confidence below 0.7, send the first 3000 characters of the contract to OpenRouter with a structured prompt requesting a JSON response `{ "country": str, "state": str, "confidence": float, "evidence": [str] }`; (4) **Conflict detection** — if multiple jurisdictions are detected (e.g., choice of law clause says UK but parties are Indian entities), flag this as a `JurisdictionConflict` with severity `HIGH`. Return a `JurisdictionDetectionResult` dataclass containing `primary_jurisdiction`, `secondary_jurisdictions`, `conflicts`, `confidence`, and `detection_method`. Cache results in Redis with key `jurisdiction:{contract_id}` and a 7-day TTL.

**Verification:**
- Test with a contract containing `"This agreement shall be governed by the laws of the State of Maharashtra, India"` and confirm `country_code='IN'` and `state_province='Maharashtra'` are detected with confidence above 0.9
- Test with a contract containing conflicting jurisdiction signals and confirm a `JurisdictionConflict` is returned
- Confirm Redis caches the detection result and second call completes in under 5ms

---

### STEP 2.4 — Jurisdiction-Aware Clause Risk Re-Scoring Engine

Extend the existing clause risk analysis pipeline by creating a `JurisdictionRiskAdjuster` class in `app/services/risk_adjuster.py`. This class accepts the original clause risk scores (from your existing AI risk analyzer), the detected jurisdiction, and a list of matching legal rules from the `legal_rules` table, and outputs jurisdiction-adjusted risk scores. Implementation: (1) For each analyzed clause, query Qdrant's `jurisdiction_laws` collection with the clause embedding, filtered by `jurisdiction_id` metadata, to retrieve the top 5 most relevant legal rules; (2) Construct a LangChain `LLMChain` prompt that provides: the clause text, the original risk assessment, and the 5 relevant legal rules, and asks the LLM to output JSON `{ "adjusted_risk_level": str, "jurisdiction_delta": float, "jurisdiction_warnings": [str], "compliance_requirements": [str], "recommended_modifications": [str] }`; (3) Compute a `jurisdiction_delta` float between -1.0 and +1.0 representing whether the jurisdiction increases or decreases the clause risk relative to a neutral baseline; (4) For Indian contracts specifically, add hardcoded rule checks: Arbitration Act 1996 compliance for dispute resolution clauses, Stamp Duty requirements by state, and PDPB 2023 data handling obligations; (5) Store the adjusted analysis in the `contract_jurisdiction_analysis` table and push an update event to the frontend via an SSE channel `contract:{contract_id}:jurisdiction_update`.

**Verification:**
- Analyze a non-compete clause under Indian law and confirm a `jurisdiction_warning` about the unenforceability of non-competes post-employment under Indian Contract Act Section 27
- Confirm the `jurisdiction_delta` for a California-governed contract's non-compete clause is strongly negative (California also bans them), producing a LOW adjusted risk
- Confirm SSE event is received within 2 seconds of the analysis completing

---

### STEP 2.5 — Jurisdiction Intelligence Frontend Panel

Create a `JurisdictionPanel` React component at `components/jurisdiction/JurisdictionPanel.tsx`. On contract load, call `GET /api/v1/contracts/{id}/jurisdiction` and display: a flag icon + jurisdiction name badge (use `country-flag-emoji` npm package), a confidence meter, and any detected conflicts highlighted in amber. Render a "Legal Rules Applied" accordion section listing each relevant legal rule with its citation, source link, and how it affected the risk score. Show a jurisdiction-adjusted risk score diff — e.g., "Original: HIGH → Adjusted for Maharashtra Law: MEDIUM" — with an explanation popover. Add a "Change Jurisdiction" override control that opens a modal with a searchable dropdown of all jurisdictions in the `jurisdictions` table (fetched from `GET /api/v1/jurisdictions`), allowing the user to manually specify a jurisdiction and trigger re-analysis. Implement an animated `JurisdictionConflictBanner` component that appears at the top of the contract view when conflicts are detected, showing the conflicting signals and a recommended resolution. On the contract PDF export, pass jurisdiction data to the existing PDF report generator and include a "Jurisdiction Summary" section with all applied rules and risk adjustments.

**Verification:**
- Load a contract with a Maharashtra governing law clause and confirm the flag, jurisdiction name, and confidence score display correctly
- Trigger a manual jurisdiction override to `Singapore` and confirm the risk scores update within 3 seconds with new SSE data
- Confirm the `JurisdictionConflictBanner` renders when a contract has both `"governed by English law"` and Indian party addresses

---

### STEP 2.6 — Jurisdiction Knowledge Base Management API

Create a CRUD API for jurisdiction data management at `app/routers/jurisdiction_admin.py` behind an `admin` role guard. Endpoints: `GET /api/v1/admin/jurisdictions` (paginated list), `POST /api/v1/admin/jurisdictions` (create new jurisdiction), `PUT /api/v1/admin/jurisdictions/{id}` (update), `POST /api/v1/admin/legal-rules` (add a new legal rule with auto-embedding), `PUT /api/v1/admin/legal-rules/{id}` (update rule text and re-embed), `DELETE /api/v1/admin/legal-rules/{id}` (soft-delete by setting `expiry_date = NOW()`), `POST /api/v1/admin/jurisdictions/bulk-ingest` (trigger the Celery ingestion task for a specific jurisdiction). The `POST /api/v1/admin/legal-rules` endpoint must automatically: generate an embedding for the `rule_text` using `sentence-transformers/legal-bert-base-uncased`, upsert the point in Qdrant with `jurisdiction_id` and `category` metadata, and insert the row in PostgreSQL within a single database transaction that rolls back if either operation fails. Add a Prometheus metric `legal_rules_total` labelled by `jurisdiction_code` and `category` that is incremented on each insert and decremented on each soft-delete.

**Verification:**
- POST a new legal rule via the admin API and confirm it appears in both PostgreSQL and Qdrant with matching IDs
- Trigger a failed Qdrant upsert (by temporarily stopping Qdrant) and confirm the PostgreSQL row is NOT inserted (transaction rollback)
- Query `GET /metrics` and confirm `legal_rules_total{jurisdiction_code="IN", category="employment"}` reflects the correct count

---

## PHASE 3 — Blockchain Contract Verification & Immutable Audit Trail

---

### STEP 3.1 — Polygon PoS Node Setup and Smart Contract Architecture

Use the **Polygon PoS** network (free, EVM-compatible, sub-cent gas fees) for all on-chain operations. For local development and testing, spin up a `hardhat` node inside a new Docker service `blockchain-node` using `node:20-alpine` and installing `hardhat` and `@nomicfoundation/hardhat-toolbox`. For staging and production, configure connections to Polygon Mumbai testnet (free faucet at `faucet.polygon.technology`) and Polygon Mainnet respectively, managed via environment variables `BLOCKCHAIN_NETWORK=mainnet|testnet|local`. Write two Solidity smart contracts in `blockchain/contracts/`. The first, `ContractRegistry.sol`, stores: `contractHash` (keccak256 of the PDF bytes), `metadataHash` (keccak256 of the JSON metadata), `uploaderAddress`, `timestamp`, `ipfsCid`, and emits a `ContractRegistered(bytes32 indexed contractHash, address indexed uploader, uint256 timestamp)` event. The second, `AuditTrail.sol`, stores an append-only log of audit events with: `contractHash`, `eventType` (enum: UPLOADED, ANALYZED, SIGNED, COUNTER_OFFERED, EXPORTED), `actorAddress`, `dataHash` (hash of the event payload), `previousEventHash` (linked list for tamper detection), `timestamp`. Deploy both contracts using `hardhat ignition` with deterministic deployment addresses stored in `blockchain/deployments/{network}.json`. Store ABIs in `blockchain/abis/` for use by the Python backend service.

**Verification:**
- Run `npx hardhat test` inside `blockchain/` and confirm all unit tests for `ContractRegistry.sol` and `AuditTrail.sol` pass
- Deploy to local Hardhat network and confirm `ContractRegistered` event is emitted with correct `contractHash` by inspecting transaction receipt logs
- Run `npx hardhat verify --network mumbai {address}` on testnet and confirm source code is verified on PolygonScan

---

### STEP 3.2 — IPFS Integration for Immutable Document Storage

Add a `go-ipfs` (now `kubo`) Docker service to `docker-compose.yml` using the `ipfs/kubo:latest` image. Mount a persistent volume `/ipfs_data` for the IPFS repository. Expose the API port `5001` internally and the gateway port `8080` internally. In production, configure pinning to **web3.storage** (free tier: 5GB) as a fallback by storing `WEB3_STORAGE_TOKEN` in environment secrets. Create an `IPFSService` class in `app/services/ipfs_service.py` using the `ipfshttpclient` Python library. Implement `upload_contract(file_bytes: bytes, metadata: dict) -> IPFSUploadResult` which: (1) pins the raw PDF bytes to IPFS and records the CID; (2) creates a JSON metadata envelope `{ "contract_id": str, "sha256": str, "upload_timestamp": str, "platform": "legaltech-ai", "version": "1.0" }`, serializes it, and pins it as a second IPFS object; (3) returns `IPFSUploadResult(pdf_cid, metadata_cid, sha256_hash)`. Implement `retrieve_contract(cid: str) -> bytes` that fetches from the local IPFS node first, falling back to the public gateway `https://ipfs.io/ipfs/{cid}` with a 10-second timeout. Add an IPFS gateway health check endpoint `GET /api/v1/blockchain/ipfs/health` that tests connectivity to the local node.

**Verification:**
- Upload a test PDF via `IPFSService.upload_contract()` and confirm a CID string is returned in the format `Qm...` or `bafybe...`
- Retrieve the uploaded document using the returned CID and confirm the bytes match the original file using SHA-256 comparison
- Stop the local IPFS node and confirm retrieval falls back to the public gateway and still returns correct bytes

---

### STEP 3.3 — Python Blockchain Interaction Service

Add `web3==6.15.0`, `eth-account==0.11.0`, and `py-solc-x` to `requirements.txt`. Create `app/services/blockchain_service.py` with a `BlockchainService` class. Initialize `Web3(Web3.HTTPProvider(os.environ['POLYGON_RPC_URL']))` where `POLYGON_RPC_URL` is set to `https://rpc-mumbai.maticvigil.com` for testnet (free, no API key required) or `https://polygon-rpc.com` for mainnet. Load the deployer private key from `BLOCKCHAIN_PRIVATE_KEY` environment variable and create an `Account` object. Load contract ABIs from `blockchain/abis/ContractRegistry.json` and `blockchain/abis/AuditTrail.json` and instantiate both contract objects using `web3.eth.contract(address=..., abi=...)`. Implement `register_contract(contract_id: str, pdf_bytes: bytes, metadata: dict) -> BlockchainRegistrationResult` which: computes `keccak256` of the PDF bytes and metadata JSON using `web3.keccak()`, calls `ContractRegistry.functions.register()` with both hashes and the IPFS CID, signs the transaction with the deployer account using `account.sign_transaction()`, sends it via `web3.eth.send_raw_transaction()`, and polls for receipt with `web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)`. Implement `log_audit_event(contract_id: str, event_type: str, actor_address: str, payload: dict) -> str` which computes the hash of the payload, looks up the previous event hash for this contract from the last `AuditTrail` event log, and calls `AuditTrail.functions.logEvent()` with all fields. All blockchain calls must be wrapped in a Celery task `register_contract_on_chain` to avoid blocking the FastAPI request thread. Store the returned `tx_hash` and `block_number` in the `contract_blockchain_records` PostgreSQL table.

**Verification:**
- Call `register_contract()` with a test PDF and confirm `tx_hash` is a 66-character hex string starting with `0x`
- Query PolygonScan Mumbai for the transaction hash and confirm the `ContractRegistered` event is visible in the transaction logs
- Call `log_audit_event()` twice for the same contract and confirm the second event's `previousEventHash` matches the first event's computed hash

---

### STEP 3.4 — Contract Blockchain Records Database Schema

Create a PostgreSQL migration adding two new tables. `contract_blockchain_records` table: `id UUID PRIMARY KEY`, `contract_id UUID REFERENCES contracts(id) UNIQUE`, `ipfs_pdf_cid VARCHAR(100) NOT NULL`, `ipfs_metadata_cid VARCHAR(100) NOT NULL`, `pdf_sha256 CHAR(64) NOT NULL`, `metadata_sha256 CHAR(64) NOT NULL`, `polygon_tx_hash CHAR(66)`, `polygon_block_number BIGINT`, `polygon_network VARCHAR(20)`, `contract_address CHAR(42)`, `registration_status VARCHAR(20) DEFAULT 'pending'` (pending / confirmed / failed), `confirmed_at TIMESTAMPTZ`, `created_at TIMESTAMPTZ DEFAULT NOW()`. `audit_trail_events` table: `id UUID PRIMARY KEY`, `contract_id UUID REFERENCES contracts(id)`, `event_type VARCHAR(50) NOT NULL`, `actor_user_id UUID REFERENCES users(id)`, `actor_wallet_address CHAR(42)`, `payload JSONB NOT NULL`, `payload_hash CHAR(66) NOT NULL`, `previous_event_hash CHAR(66)`, `polygon_tx_hash CHAR(66)`, `polygon_block_number BIGINT`, `on_chain_status VARCHAR(20) DEFAULT 'pending'`, `occurred_at TIMESTAMPTZ DEFAULT NOW()`, `confirmed_at TIMESTAMPTZ`. Add a partial index: `CREATE INDEX idx_audit_trail_contract ON audit_trail_events(contract_id) WHERE on_chain_status = 'confirmed'`. Create a Celery task `confirm_blockchain_records` that runs every 5 minutes, fetches all `pending` records, queries the Polygon node for transaction receipts, and updates `registration_status` and `confirmed_at` upon confirmation.

**Verification:**
- Insert a pending record and run `confirm_blockchain_records` manually; confirm `registration_status` updates to `confirmed` and `confirmed_at` is set
- Query `SELECT * FROM audit_trail_events WHERE contract_id = ? ORDER BY occurred_at` and confirm the `previous_event_hash` chain is unbroken (each row's hash matches the next row's `previous_event_hash`)
- Confirm the partial index is used by running `EXPLAIN SELECT * FROM audit_trail_events WHERE contract_id = ? AND on_chain_status = 'confirmed'` and checking for `Index Scan`

---

### STEP 3.5 — Contract Integrity Verification Endpoint

Create a `ContractVerifier` class in `app/services/contract_verifier.py`. Implement `verify_contract_integrity(contract_id: str, pdf_bytes: bytes) -> VerificationResult`. This method must: (1) Compute the SHA-256 hash of the provided `pdf_bytes`; (2) Look up the stored `pdf_sha256` in `contract_blockchain_records` for this `contract_id`; (3) Compare the two hashes — if they differ, set `tampered=True`; (4) Query the Polygon node using `ContractRegistry.functions.getContract(contract_id_hash).call()` to retrieve the on-chain hash; (5) Compare the on-chain hash against the local stored hash — this guards against database tampering; (6) Fetch the IPFS metadata by CID and verify its `sha256` field matches; (7) Return a `VerificationResult` dataclass: `{ "contract_id": str, "verified": bool, "tampered": bool, "on_chain_match": bool, "ipfs_match": bool, "blockchain_timestamp": datetime, "tx_hash": str, "polygon_scan_url": str, "verification_certificate": dict }`. Expose this as `POST /api/v1/blockchain/verify` accepting a file upload + `contract_id`. Additionally, create `GET /api/v1/blockchain/audit-trail/{contract_id}` that returns the full ordered audit trail from PostgreSQL, cross-referenced with on-chain events fetched via `AuditTrail.functions.getEvents(contract_id_hash)`.

**Verification:**
- Upload the original contract PDF to `/api/v1/blockchain/verify` and confirm `verified=true`, `tampered=false`, `on_chain_match=true`
- Modify one byte of the PDF locally and upload to `/api/v1/blockchain/verify`; confirm `tampered=true` and `verified=false`
- Confirm the audit trail endpoint returns events in chronological order with correct `polygon_scan_url` links pointing to valid PolygonScan transactions

---

### STEP 3.6 — Digital Signature Workflow with MetaMask / WalletConnect

Install `wagmi@2`, `viem`, and `@web3modal/wagmi` in the Next.js frontend. Configure `WagmiConfig` in `app/providers.tsx` with Polygon mainnet and Mumbai testnet chains. Create a `BlockchainSignature` React component at `components/blockchain/BlockchainSignature.tsx` that: (1) Renders a "Connect Wallet" button using Web3Modal's `w3m-button` component; (2) On wallet connection, displays the wallet address and current network (warns if not on Polygon); (3) Renders a "Sign & Register Contract" button that calls `useSignMessage` from `wagmi` with a structured `personal_sign` message: `"I, {wallet_address}, hereby sign contract {contract_id} with document hash {sha256} on {timestamp}. LegalTech AI Platform."`; (4) POSTs the `{ contract_id, signature, wallet_address, message }` to `POST /api/v1/blockchain/sign` on the backend; (5) The backend endpoint verifies the signature using `web3.eth.account.recover_message(message, signature)` to confirm wallet ownership, stores the signature in `audit_trail_events` as an `SIGNED` event, and triggers the `register_contract_on_chain` Celery task; (6) Returns a transaction hash and PolygonScan URL for the user to verify independently. Render a `VerificationBadge` component on the contract card that shows "Blockchain Verified ✓" when `registration_status = 'confirmed'`, linking to the PolygonScan transaction.

**Verification:**
- Connect MetaMask to Mumbai testnet, click "Sign & Register", sign the message, and confirm a PolygonScan Mumbai URL is returned with a confirmed transaction
- Call `web3.eth.account.recover_message()` on the backend with the signature and confirm it returns the correct wallet address
- Confirm the `VerificationBadge` appears on the contract card within 30 seconds of the Celery task completing (via SSE or polling)

---

### STEP 3.7 — Blockchain Audit Trail Frontend Dashboard

Create an `AuditTrailDashboard` React component at `components/blockchain/AuditTrailDashboard.tsx`. Fetch audit events from `GET /api/v1/blockchain/audit-trail/{contract_id}` and render them as a vertical timeline using a custom CSS timeline component (no external timeline library needed — use `position: relative` with a left border pseudo-element). Each event node must display: event type icon (upload, analyze, sign, export), actor wallet address (truncated to `0x1234...abcd`), human-readable timestamp, event payload summary, on-chain status badge (Pending / Confirmed), and a "View on PolygonScan" link. At the top of the dashboard, render a `ContractVerificationCard` showing the IPFS CID with a link to `https://ipfs.io/ipfs/{cid}`, the SHA-256 hash, the Polygon transaction hash, block number, block timestamp, and a large "VERIFIED" or "TAMPERED" status banner with appropriate color. Add a "Download Verification Certificate" button that calls `GET /api/v1/blockchain/certificate/{contract_id}` and downloads a JSON file containing all verification proofs, suitable for legal submission. Add a "Verify Now" button that opens a file input, accepts a PDF upload, and calls `POST /api/v1/blockchain/verify` to re-run integrity verification, displaying the full `VerificationResult` in a modal.

**Verification:**
- Load the dashboard for a verified contract and confirm all audit events display with correct timestamps and PolygonScan links
- Click "Verify Now", upload the original contract PDF, and confirm the "VERIFIED" banner displays within 5 seconds
- Click "Download Verification Certificate" and confirm the downloaded JSON contains `tx_hash`, `ipfs_cid`, `sha256`, `blockchain_timestamp`, and `on_chain_match: true`

---

### STEP 3.8 — Blockchain Service Resilience and Gas Management

In `blockchain_service.py`, implement a `GasEstimator` utility that calls `web3.eth.gas_price` and applies a 20% buffer: `gas_price = int(web3.eth.gas_price * 1.2)`. For mainnet, integrate with the **Polygon Gas Station** free API at `https://gasstation.polygon.technology/v2` to fetch `safeLow`, `standard`, and `fast` gas prices, selecting `standard` by default and `fast` when the `priority=high` flag is set by the caller. Implement a retry decorator `@blockchain_retry(max_attempts=3, backoff_factor=2)` that retries on `TransactionNotFound`, `TimeExhausted`, and connection errors. Add a circuit breaker using the `pybreaker` library (`pip install pybreaker`) that opens after 5 consecutive failures and resets after 60 seconds, falling back to a `pending` local-only record. Create a `BlockchainHealthMonitor` Celery Beat task that runs every 10 minutes: checks Polygon node connectivity, confirms the `ContractRegistry` contract is reachable via `functions.owner().call()`, logs block latency, and pushes a `blockchain_health` metric to Prometheus. Store the current Polygon block number in Redis key `blockchain:latest_block` updated on each health check.

**Verification:**
- Simulate a Polygon RPC failure by setting an invalid `POLYGON_RPC_URL` and confirm the circuit breaker opens after 5 failures and the contract record is saved with `registration_status='pending'`
- Confirm Prometheus metric `blockchain_health_status{network="mumbai"}` equals `1` when healthy and `0` when the circuit is open
- Verify that a retry on `TimeExhausted` does not double-submit the transaction by confirming only one `ContractRegistered` event exists on-chain for the contract

---

*End of STEPS.md — Phase 1, Phase 2, Phase 3*

## PHASE 14 — Testing

---

### STEP 14.1 — Backend Unit Tests

In `services/api/tests/unit/`, write unit tests for all service layer functions using pytest and pytest-asyncio. Mock all external dependencies (LLM calls, Redis, database) — no real network calls. Cover: `contract_service`, `analysis_service`, `report_service`, `chat_service`, `translation_service`, `streaming_service`. In `services/ai/tests/test_pipelines.py`, write unit tests for all pipeline functions with mocked LLM responses — confirm Pydantic validation is applied correctly and that mock responses in the right shape parse without error. In `services/ai/tests/test_rules.py`, write unit tests for the rule engine — test every regex pattern with at least one matching clause and one non-matching clause.

**Verification:**
- `pytest services/api/tests/unit/ -v` passes with all tests green
- `pytest services/ai/tests/ -v` passes with all tests green
- No test makes a real LLM call or database call (verified by checking that tests complete even with invalid API keys)
- Rule engine tests achieve coverage of all 40+ regex patterns
- Service layer test coverage is above 80%: `pytest --cov=app/services services/api/tests/unit/`

---

### STEP 14.2 — Backend Integration Tests

In `tests/` (root) and `services/api/tests/integration/`, write integration tests using the `docker-compose.test.yml` environment. Use `httpx.AsyncClient` with the FastAPI app in test mode. Use a real test database (not mocked). Seed the test database with known contract and user data before each test class.

Write tests for: the full upload-to-scan pipeline end-to-end (upload endpoint → Celery task → database results), SSE streaming delivering at least one clause event for a known contract, the chat endpoint returning a non-hallucinated answer for a seeded contract, the translation endpoint switching a contract's language and updating stored results, report generation producing a non-empty PDF, the share link endpoint working without authentication, and the cleanup task correctly deleting an expired report.

**Verification:**
- `pytest tests/ -v` passes with all tests green (requires `docker-compose.test.yml` running)
- The full scan pipeline integration test completes in under 60 seconds
- The SSE test receives at least one `data:` event line
- The chat test asserts the response does NOT contain fabricated contract terms

---

### STEP 14.3 — API Pipeline Smoke Test Script

Create `scripts/test_full_pipeline.py` — a standalone script (not a pytest test) that exercises the full backend API flow end to end using a hardcoded demo contract file. The script should: call the upload endpoint, open the SSE stream and read until complete, call the summary endpoint, call the power endpoint, call the counter-offer endpoint for the first HIGH-risk clause, call the chat endpoint with a question, generate a report and verify the share link works. Print a pass/fail result for each step. This script is useful for manual verification after deployments.

**Verification:**
- `python scripts/test_full_pipeline.py` runs against the local backend and prints "PASS" for every step
- Any network error or unexpected status code prints "FAIL" for that step and continues to the next
- The script completes within 120 seconds for a normal scan

---

## PHASE 15 — CI/CD and Deployment

---

### STEP 15.1 — Set Up GitHub Actions CI for the Backend

In `.github/workflows/ci.yml`, create the CI pipeline that runs on every pull request and push to main. It must run: backend linting with ruff or flake8 across all Python services, backend type checking (if using mypy), unit tests for the API service, unit tests for the AI service, and integration tests using `docker-compose.test.yml`. The pipeline must fail fast. Use GitHub Actions service containers for Postgres and Redis instead of full docker-compose where possible for speed.

**Verification:**
- Opening a pull request triggers the CI pipeline automatically
- A failing unit test causes the pipeline to fail and the PR shows a red status
- All existing tests pass on the `main` branch (green status)

---

### STEP 15.2 — Deploy the Backend to Railway

Deploy the FastAPI API service, the AI service, and the Celery worker to Railway as three separate services. Configure: the `services/api/Dockerfile` for the API service on Railway, the `services/ai/Dockerfile` for the AI service, the `apps/worker/Dockerfile` for the Celery worker, all backend environment variables in Railway's dashboard using the `.env.example` as the reference, the Neon database URL as `DATABASE_URL`, and the Upstash Redis URL as `REDIS_URL`. Configure Railway to run database migrations automatically as a deploy step: add `alembic upgrade head` to the API service's start command or as a pre-deploy hook. Run the seeding scripts (`seed_precedents.py`, `index_favorable_clauses.py`, `seed_demo_contracts.py`) once against the production database after first deployment.

**Verification:**
- All three services are running on Railway with a green status
- `curl https://<railway-api-url>/health` returns `{"status": "ok", "service": "api"}`
- `curl https://<railway-api-url>/api/v1/scan/fake-id` returns `401` (auth is working in production)
- `alembic current` on the production database shows migrations are applied
- The Celery worker shows as connected in its Railway logs
- `python scripts/test_full_pipeline.py` pointed at the production URL passes all steps

---

### STEP 15.3 — Final Backend Production Verification

This is the final verification step for the complete backend. Test every feature via curl or a REST client against the production deployment.

**Verification:**
- Upload a real PDF contract — scan job is created and scan completes successfully
- SSE stream delivers clause-by-clause results
- At least one HIGH-risk clause is detected and stored
- Summary endpoint returns `should_you_sign` and `overall_risk_score`
- Power endpoint returns a `power_score` with `key_imbalances`
- Precedent endpoint for a HIGH-risk clause returns at least one case citation
- Counter-offer endpoint returns three versions for a HIGH-risk clause
- Chat endpoint answers a question about the contract with a clause citation and does not fabricate terms
- Report generation produces a downloadable PDF
- The share link for the report works without authentication
- Uploading a Spanish contract — after scan, clause `plain_english` fields contain Spanish text
- Switching language to French via the translate endpoint re-translates all fields to French
- Uploading the same contract twice — second scan returns from cache in under 3 seconds
- Uploading demo contract files — results return in under 3 seconds from pre-computed cache
- The rate limiter blocks the 11th upload attempt in under an hour

---

## Build Order Summary

```
PHASE 0  — Repository & Environment Setup     (Steps 0.1–0.6)
PHASE 1  — Database Foundation                (Steps 1.1–1.4)
PHASE 2  — Authentication                     (Steps 2.1–2.2)
PHASE 3  — File Upload Pipeline               (Steps 3.1–3.2)
PHASE 4  — Document Parsing Pipeline          (Steps 4.1–4.4)
PHASE 5  — LLM Integration Foundation        (Steps 5.1–5.3)
PHASE 6  — Core Scan Pipeline                 (Steps 6.1–6.6)
PHASE 7  — Remaining AI Feature Pipelines    (Steps 7.1–7.6)
PHASE 8  — RAG Chat Pipeline                  (Steps 8.1–8.2)
PHASE 9  — Multilingual Support               (Steps 9.1–9.2)
PHASE 10 — Scan Status and History Endpoints  (Step 10.1)
PHASE 11 — Report Generation                  (Steps 11.1–11.3)
PHASE 12 — Caching Layer                      (Steps 12.1–12.2)
PHASE 13 — Rate Limiting                      (Step 13.1)
PHASE 14 — Testing                            (Steps 14.1–14.3)
PHASE 15 — CI/CD and Deployment               (Steps 15.1–15.3)
```

**Total: 39 steps across 15 phases. Complete every verification before proceeding to the next step.**

---

## Appendix — API Endpoint Reference

All endpoints below are prefixed with `/api/v1`. All except `/health` and `/webhooks/clerk` and `/report/share/{shareUuid}` require a valid Clerk JWT in the `Authorization: Bearer` header.

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check — no auth |
| POST | /webhooks/clerk | Clerk user sync webhook — no auth, but webhook signature required |
| POST | /upload | Upload a contract file URL and start a scan job |
| GET | /scan/{jobId} | Get the status and progress of a scan job |
| GET | /scan/{jobId}/stream | SSE stream — delivers clause results in real time |
| GET | /contracts | List all contracts for the authenticated user |
| GET | /contracts/{contractId} | Get full contract detail including all clauses |
| DELETE | /contracts/{contractId} | Delete a contract and all associated data |
| GET | /summary/{contractId} | Get the summary card and pros/cons for a completed scan |
| GET | /power/{contractId} | Get the power asymmetry analysis |
| GET | /precedent/{clauseId} | Get the legal precedent match for a HIGH-risk clause |
| POST | /counter-offer/{clauseId} | Queue counter-offer generation for a HIGH-risk clause |
| GET | /counter-offer/{clauseId} | Get the generated counter-offer (poll after POST) |
| POST | /chat/{contractId} | Ask a question about the contract — streams the answer |
| POST | /translate/{contractId} | Queue a post-scan translation to a different language |
| POST | /report/generate/{contractId} | Queue PDF report generation |
| GET | /report/{reportId} | Get the report (authenticated) |
| GET | /report/share/{shareUuid} | Get the report via share link — no auth, checks expiry |

---

*This document covers the complete backend build. No frontend code is referenced. Every feature in PRD.md has a corresponding backend implementation step here. Use the frontend document separately when building the UI layer on top of these endpoints.*

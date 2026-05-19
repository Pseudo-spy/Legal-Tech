# 🏛️ LegalTech Contract Scanner

> **"A legal guardian angel for freelancers and small business owners."**  
> Scan any contract, understand every risk, negotiate with confidence — no lawyer required.

---

## 🚀 Features

### Core Scanning
- **Multi-format support** — Upload PDF, DOCX, TXT files; handles password-protected and scanned PDFs
- **Clause extraction** — Intelligent segmentation using NLP with position tracking
- **9 risk categories** — IP ownership, liability, confidentiality, payment, termination, jurisdiction, indemnification, non-compete, arbitration
- **Color-coded risk levels** — 🟢 Green (safe), 🟡 Yellow (caution), 🔴 Red (danger)
- **Consequence explanation** — Plain-English explanations of what each risky clause means for you

### AI-Powered Analysis
- **Contract type detection** — Automatically identifies SOW, NDA, MSA, employment, lease, SaaS agreements
- **Power asymmetry scoring** — Quantifies contract imbalance with leverage points and negotiation insights
- **Legal precedent retrieval** — Matches clauses to 500+ court cases and favorable precedents
- **Counter-offer generation** — Suggests fair alternative language for red-flagged clauses

### Smart Chat & Search
- **RAG-powered Q&A** — Ask questions about your contract in plain English; get answers sourced from the document
- **Vector embeddings** — Semantic search across your contract history with pgvector
- **Streaming responses** — Real-time SSE streaming for all analysis results

### Multilingual & Accessibility
- **6 languages** — Works with English, Spanish, French, German, Portuguese, Hindi contracts
- **Auto-detection** — Detects source language and translates results back
- **Legal glossary** — Domain-specific terminology preserved across translations
- **PDF report export** — Beautiful shareable reports in multiple languages

### Developer Experience
- **REST API** — FastAPI backend with JWT authentication (Clerk)
- **Async workers** — Celery + Redis for background processing
- **Docker-ready** — One-command deployment with docker-compose
- **Streaming endpoints** — Server-Sent Events for real-time progress

---

## 📈 Target Users

- **Freelancers** — Sign client SOWs and project contracts with confidence
- **Small business owners** — Review vendor, lease, or SaaS agreements
- **Startups** — Navigate employment and partnership contracts
- **Legal professionals** — Use as a first-pass review tool

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                   │
└────────────┬──────────────────────────────────┬────────────┘
             │ JWT Auth (Clerk)                  │ File Upload (Uploadthing)
             ▼                                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (port 8000)              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ Contracts│ │  Chat    │ │ Reports  │ │   Webhooks   │  │
│  └─────┬────┘ └─────┬────┘ └────┬────┘ └──────┬───────┘  │
└────────┼─────────────┼───────────┼─────────────┼──────────┘
         │             │           │             │
    PostgreSQL      Redis       Celery         AI Service
    + pgvector     (Queue)    Workers         (port 8001)
                                              ┌───────────┐
                                              │  Pipeline │ ──► OpenRouter
                                              │  (LLM)    │     (Free Models)
                                              └───────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **API** | FastAPI, SQLAlchemy (async), Pydantic v2 |
| **AI** | spaCy, LangChain, pgvector, sentence-transformers |
| **LLM** | OpenRouter (LLaMA 3.3, Gemini 2.0 Flash) |
| **Workers** | Celery 5, Redis |
| **Database** | PostgreSQL 16, pgvector |
| **Auth** | Clerk (JWT verification via JWKS) |
| **Translation** | DeepL API |
| **Reports** | WeasyPrint (HTML→PDF) |
| **Container** | Docker, Docker Compose |

---

## 📁 Project Structure

```
LegalTech/
├── services/
│   ├── api/               # FastAPI backend (port 8000)
│   │   ├── app/
│   │   │   ├── api/v1/    # REST endpoints
│   │   │   ├── core/      # Security, config, rate limiting
│   │   │   ├── db/        # Session, base, models
│   │   │   ├── models/    # ORM models (9 tables)
│   │   │   ├── schemas/   # Pydantic schemas
│   │   │   ├── services/  # Business logic
│   │   │   └── utils/     # File handling, PDF generation
│   │   ├── migrations/    # Alembic DB migrations
│   │   └── templates/     # Report HTML templates
│   │
│   └── ai/                # AI service (port 8001)
│       ├── app/
│       │   ├── parser/    # PDF, DOCX, fallback parsers
│       │   ├── pipelines/ # Type detection, risk, power, chat
│       │   ├── prompts/  # LLM prompt templates
│       │   ├── rules/     # Regex risk rules
│       │   ├── rag/       # Embedding, vector store
│       │   ├── multilingual/ # Translation, language detection
│       │   ├── data/      # Precedents, favorable clauses
│       │   └── scripts/   # Seeding scripts
│       └── models/        # OpenRouter client
│
├── apps/
│   └── worker/            # Celery worker
│       ├── tasks/         # Async tasks (scan, embed, translate, report)
│       └── pipeline/      # Step-by-step contract processing
│
├── agents/                # Agent prompts & context
├── docs/                  # PRD, tech stack, setup steps
├── scripts/               # Utility scripts
└── tests/                 # Test suite
```

---

## 🔌 API Endpoints

### Public
| Method | Endpoint | Description |
|--------|-----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/webhooks/clerk` | Clerk webhook handler |

### Protected (JWT Required)
| Method | Endpoint | Description |
|--------|-----------|-------------|
| POST | `/api/v1/upload` | Upload contract & start scan |
| GET | `/api/v1/scan/{jobId}` | Get scan status |
| GET | `/api/v1/scan/{jobId}/stream` | SSE progress stream |
| GET | `/api/v1/contracts` | List user's contracts |
| GET | `/api/v1/contracts/{id}` | Get contract details |
| DELETE | `/api/v1/contracts/{id}` | Delete contract |
| GET | `/api/v1/summary/{contractId}` | Get summary card |
| GET | `/api/v1/power/{contractId}` | Get power analysis |
| GET | `/api/v1/precedent/{clauseId}` | Get legal precedent |
| POST | `/api/v1/counter-offer/{clauseId}` | Generate counter-offer |
| POST | `/api/v1/chat/{contractId}` | RAG Q&A chat (streaming) |
| POST | `/api/v1/translate/{contractId}` | Translate results |
| POST | `/api/v1/report/generate/{contractId}` | Generate PDF report |
| GET | `/api/v1/report/{reportId}` | Get report |
| GET | `/api/v1/report/share/{shareUuid}` | Public share link |

---

## 💡 Vision

> Track power asymmetry across every contract you've ever signed.  
> *"Your last 5 contracts averaged -42. You're consistently undervalued."*  
> That's not a hackathon project — that's a product.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 16 + pgvector
- Redis 7
- Docker (optional)

### Setup

```bash
# 1. Clone & enter directory
cd LegalTech

# 2. Copy environment template
cp .env.example .env
# Edit .env with your API keys

# 3. Start database & redis (Docker)
docker-compose up -d db redis

# 4. Run migrations
cd services/api
alembic upgrade head

# 5. Start services (3 terminals)
# Terminal 1: API
cd services/api && uvicorn app.main:app --reload --port 8000

# Terminal 2: AI Service
cd services/ai && uvicorn app.main:app --reload --port 8001

# Terminal 3: Celery Worker
cd apps/worker && celery -A celery_app worker --loglevel=info
```

Or use Docker Compose for everything:
```bash
docker-compose up --build
```

---

## ⚙️ Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname

# Redis
REDIS_URL=rediss://default:pass@host:6379

# Auth (Clerk)
CLERK_JWKS_URL=https://your-org.clerk.com/.well-known/jwks.json

# AI Models (OpenRouter)
OPENROUTER_API_KEY=sk-or-v1-...
PRIMARY_MODEL=meta-llama/llama-3.3-70b-instruct:free
FAST_MODEL=google/gemini-2.0-flash-exp:free

# Translation (DeepL)
DEEPL_API_KEY=your_key_here

# Shared
AI_SERVICE_URL=http://localhost:8001
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_risk_classification.py -v

# Verify end-to-end
./test-analyze.ps1
```

---

## 📊 Database Schema (9 Tables)

| Table | Purpose |
|-------|---------|
| `users` | Clerk-authenticated users |
| `contracts` | Uploaded contracts with metadata |
| `clauses` | Extracted clauses with risk scores |
| `scan_jobs` | Async processing jobs |
| `analysis_results` | Risk classification results |
| `counter_offers` | AI-generated counter proposals |
| `precedent_matches` | Court case references |
| `reports` | Generated PDF reports |
| `embeddings` | Vector embeddings for RAG |

---

## 🔒 Security Features

- **JWT verification** via Clerk JWKS
- **Ownership checks** on all contract endpoints
- **Rate limiting** on upload endpoints
- **Webhook signature verification** (Clerk)
- **AES-256-GCM** decryption for sensitive files

---

## 🌍 Multilingual Support

| Language | Code | Status |
|----------|------|--------|
| English | `en` | ✅ Primary |
| Spanish | `es` | ✅ |
| French | `fr` | ✅ |
| German | `de` | ✅ |
| Portuguese | `pt` | ✅ |
| Hindi | `hi` | ✅ |

---

## 📝 License

MIT License - see [LICENCE](LICENCE)

---

*Last updated: May 2026*
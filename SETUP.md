# LegalTech AI Contract Scanner - Setup Guide

A complete guide to set up the LegalTech AI Contract Scanner from scratch.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Structure](#project-structure)
3. [Environment Setup](#environment-setup)
4. [Database Setup](#database-setup)
5. [Service Setup](#service-setup)
   - [API Service](#api-service)
   - [AI Service](#ai-service)
   - [Celery Worker](#celery-worker)
6. [Verification](#verification)
7. [Running the Application](#running-the-application)
8. [API Endpoints](#api-endpoints)
9. [Common Issues](#common-issues)

---

## Prerequisites

| Tool | Version | Required |
|------|---------|----------|
| Python | 3.11+ | Yes |
| Node.js | 18+ | For frontend (future) |
| Docker | Latest | Optional (recommended) |
| Docker Compose | Latest | Optional (recommended) |
| PostgreSQL | 16 | For local dev |
| Redis | 7 | For local dev |

---

## Project Structure

```
LegalTech/
├── .env                    # Environment variables (gitignored)
├── .env.example            # Template for env variables
├── docker-compose.yml      # Docker services definition
├── README.md              # Project overview
├── SETUP.md               # This file
│
├── services/
│   ├── api/               # FastAPI backend (port 8000)
│   │   ├── app/           # Application code
│   │   ├── migrations/    # Alembic migrations
│   │   ├── requirements.txt
│   │   └── venv/          # Virtual environment
│   │
│   └── ai/                # AI service (port 8001)
│       ├── app/           # Application code
│       ├── requirements.txt
│       └── venv/          # Virtual environment
│
├── apps/
│   └── worker/            # Celery worker
│       ├── tasks/         # Celery tasks
│       ├── requirements.txt
│       └── venv/          # Virtual environment
│
├── agents/                # Agent prompts & context
├── docs/                  # PRD, Tech Stack, Steps
├── scripts/               # Utility scripts
└── tests/                # Test files
```

---

## Environment Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd LegalTech
```

### 2. Copy Environment Template

```bash
# Copy the example file
cp .env.example .env
```

### 3. Configure .env File

Edit `.env` with your actual values:

```bash
# ── Frontend (leave empty for now) ────────────────────────────
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=
UPLOADTHING_SECRET=
UPLOADTHING_APP_ID=

# ── Backend API ───────────────────────────────────────────────
# PostgreSQL connection string (asyncpg driver)
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname
# Redis URL (rediss:// for SSL)
REDIS_URL=rediss://default:password@host:6379
# Clerk webhook secret (from Clerk dashboard)
CLERK_WEBHOOK_SECRET=
# IMPORTANT: Add your Clerk JWKS URL
CLERK_JWKS_URL=https://your-org.clerk.com/.well-known/jwks.json

# ── AI Service ─────────────────────────────────────────────────
# OpenRouter API key (from openrouter.ai)
OPENROUTER_API_KEY=
PRIMARY_MODEL=meta-llama/llama-3.3-70b-instruct:free
FAST_MODEL=google/gemini-2.0-flash-exp:free
DEEPL_API_KEY=
EMBEDDING_MODEL=all-MiniLM-L6-v2

# ── Shared ─────────────────────────────────────────────────────
AI_SERVICE_URL=http://localhost:8001
ENVIRONMENT=development
```

**Important:** Replace `CLERK_JWKS_URL` with your actual Clerk instance URL. For local development, you can get this from your Clerk dashboard.

---

## Database Setup

### Option A: Using Docker (Recommended)

```bash
# Start only PostgreSQL and Redis containers
docker-compose up db redis

# Or start all services
docker-compose up -d
```

### Option B: Local Installation

#### Install PostgreSQL

**Windows:**
- Download from https://www.postgresql.org/download/windows/
- During installation, set password for `postgres` user

**macOS:**
```bash
brew install postgresql@16
brew services start postgresql@16
```

**Linux (Ubuntu):**
```bash
sudo apt update
sudo apt install postgresql-16
sudo systemctl start postgresql
```

#### Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE legaltech;

# Exit
\q
```

#### Update DATABASE_URL in .env

```bash
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/legaltech
```

---

## Service Setup

### API Service

```bash
cd services/api

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### AI Service

```bash
cd services/ai

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### Celery Worker

```bash
cd apps/worker

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Database Migration Setup

```bash
cd services/api

# Activate virtual environment
# Windows:
..\venv\Scripts\activate
# macOS/Linux:
source ../venv/bin/activate

# Generate initial migration (if not exists)
alembic revision --autogenerate -m "Initial migration"

# Apply all migrations
alembic upgrade head

# Verify migration status
alembic current

# Check database tables
psql -U postgres -d legaltech -c "\dt"
```

---

## Verification

### 1. Verify API Service

```bash
cd services/api
# Activate venv, then:
uvicorn app.main:app --reload --port 8000

# In another terminal, test health endpoint:
curl http://localhost:8000/health
# Expected: {"status":"ok","service":"api"}

curl http://localhost:8000/api/v1/health
# Expected: {"status":"ok"}
```

### 2. Verify AI Service

```bash
cd services/ai
# Activate venv, then:
uvicorn app.main:app --reload --port 8001

# In another terminal:
curl http://localhost:8001/health
# Expected: {"status":"ok","service":"ai"}
```

### 3. Verify Celery Worker

```bash
cd apps/worker
# Activate venv, then:
celery -A celery_app worker --loglevel=info

# Expected: Worker is ready
```

### 4. Verify Database Connection

```bash
cd services/api
# Activate venv, then:
python -c "from app.db.session import engine; import asyncio; asyncio.run(engine.connect())"
# Expected: No errors
```

---

## Running the Application

### Option A: Docker Compose (All Services)

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Option B: Manual Startup

**Terminal 1 - API:**
```bash
cd services/api
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - AI Service:**
```bash
cd services/ai
venv\Scripts\activate
uvicorn app.main:app --reload --port 8001
```

**Terminal 3 - Celery Worker:**
```bash
cd apps/worker
venv\Scripts\activate
celery -A celery_app worker --loglevel=info
```

---

## API Endpoints

### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/health` | API health check |
| POST | `/api/v1/webhooks/clerk` | Clerk webhook |

### Protected Endpoints (Require JWT)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/upload` | Upload contract & start scan |
| GET | `/api/v1/scan/{jobId}` | Get scan status |
| GET | `/api/v1/scan/{jobId}/stream` | SSE stream |
| GET | `/api/v1/contracts` | List contracts |
| GET | `/api/v1/contracts/{id}` | Get contract |
| DELETE | `/api/v1/contracts/{id}` | Delete contract |
| GET | `/api/v1/summary/{contractId}` | Get summary card |
| GET | `/api/v1/power/{contractId}` | Get power analysis |
| GET | `/api/v1/precedent/{clauseId}` | Get legal precedent |
| POST | `/api/v1/counter-offer/{clauseId}` | Generate counter-offer |
| GET | `/api/v1/counter-offer/{clauseId}` | Get counter-offer |
| POST | `/api/v1/chat/{contractId}` | Q&A chat |
| POST | `/api/v1/translate/{contractId}` | Translate results |
| POST | `/api/v1/report/generate/{contractId}` | Generate PDF |
| GET | `/api/v1/report/{reportId}` | Get report |
| GET | `/api/v1/report/share/{shareUuid}` | Public share link |

---

## Testing the Upload Flow

### 1. Get a Clerk JWT Token

For testing, you can use Clerk's frontend to get a test token, or create a simple test:

```bash
# Test with invalid token - should return 401
curl -X GET http://localhost:8000/api/v1/contracts \
  -H "Authorization: Bearer invalid_token"
# Expected: 401 Unauthorized
```

### 2. Test Upload Endpoint

```bash
# Replace <valid_jwt> with actual Clerk JWT
curl -X POST http://localhost:8000/api/v1/upload \
  -H "Authorization: Bearer <valid_jwt>" \
  -H "Content-Type: application/json" \
  -d '{
    "file_url": "https://example.com/test.pdf",
    "original_filename": "test.pdf",
    "file_type": "pdf",
    "file_size_bytes": 50000
  }'

# Expected response:
# {
#   "job_id": "<uuid>",
#   "contract_id": "<uuid>",
#   "status": "queued",
#   "progress_pct": 0.0
# }
```

---

## Common Issues

### 1. `ModuleNotFoundError: No module named 'app'`

**Solution:** Make sure you're in the correct directory and venv is activated.

```bash
cd services/api
venv\Scripts\activate
```

### 2. `connection refused` to PostgreSQL

**Solution:** Ensure PostgreSQL is running and DATABASE_URL is correct.

```bash
# Check if PostgreSQL is running
pg_isready -U postgres

# Or check Docker
docker ps
```

### 3. `ModuleNotFoundError: No module named 'pgvector'`

**Solution:** Install pgvector.

```bash
pip install pgvector
```

### 4. JWT Verification Fails

**Solution:** Check CLERK_JWKS_URL in .env

```bash
# Should be something like:
CLERK_JWKS_URL=https://your-org.clerk.com/.well-known/jwks.json
```

### 5. spaCy Model Not Found

**Solution:** Download the model.

```bash
cd services/ai
python -m spacy download en_core_web_sm
```

### 6. Alembic Migration Errors

**Solution:** Check database connection and ensure DATABASE_URL is correct.

```bash
cd services/api
alembic current
alembic upgrade head
```

---

## Next Steps

After successful setup:

1. **Configure Clerk** - Add your Clerk publishable/secret keys
2. **Configure Uploadthing** - Add your uploadthing keys for file uploads
3. **Add OpenRouter API Key** - For LLM functionality
4. **Add DeepL API Key** - For translation (optional)
5. **Build Frontend** - Set up Next.js app in `apps/web/`

---

## Help

- **Docs:** See `docs/PRD.md` for product details
- **Backend Steps:** See `docs/STEPS_BACKEND.md`
- **Tech Stack:** See `docs/TECH_STACK.md`

---

*Last updated: May 2026*
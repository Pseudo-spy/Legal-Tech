from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.routes.chat import router as chat_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="LegalTech AI Service",
    description="AI and NLP pipelines for contract analysis",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(chat_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ai"}


@app.get("/")
async def root():
    return {"message": "LegalTech AI Service", "version": "1.0.0"}

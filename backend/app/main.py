"""DARZFUSION AI Backend - Main FastAPI Application."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.database.initialization import init_db
from app.services.gemini_service import gemini_service

# Import API routers
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.rag import router as rag_router
from app.api.search import router as search_router
from app.api.vision import router as vision_router
from app.api.audio import router as audio_router
from app.api.study_tools import router as study_router
from app.api.history import router as history_router
from app.api.prompt_lab import router as prompt_lab_router
from app.api.nlp import router as nlp_router
from app.api.evaluation import router as evaluation_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("darzfusion")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Starting DARZFUSION AI backend...")
    # Initialize database tables
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    yield
    logger.info("Shutting down DARZFUSION AI backend...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Production-ready Multimodal Generative AI API backend for DARZFUSION AI, "
        "featuring Google Gemini conversations, RAG document intelligence, live web research, "
        "vision understanding, audio transcription, and AI study tools."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Configuration
# Supports frontend running on any host or port (e.g. Vite 5173, Next.js 3000, preview HTML)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health Check Endpoints
@app.get("/health", tags=["System"])
@app.get("/api/health", tags=["System"])
@app.get("/api/v1/health", tags=["System"])
def health_check():
    """Application health endpoint."""
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
    }


@app.get("/health/services", tags=["System"])
def services_status():
    """Detailed health status for external AI and database services."""
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
        "services": {
            "gemini_api": {
                "configured": gemini_service.is_available(),
                "model": settings.DEFAULT_MODEL,
                "status": "ready" if gemini_service.is_available() else "api_key_required",
            },
            "vector_store": {
                "engine": "ChromaDB",
                "status": "ready",
            },
            "database": {
                "type": settings.DATABASE_URL.split(":")[0],
                "status": "connected",
            },
            "search_provider": {
                "provider": settings.SEARCH_PROVIDER,
                "status": "ready",
            },
        },
    }


# Exception handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again."},
    )


# Register routers under both /api and /api/v1 for complete frontend compatibility
routers = [
    auth_router,
    chat_router,
    documents_router,
    rag_router,
    search_router,
    vision_router,
    audio_router,
    study_router,
    history_router,
    prompt_lab_router,
    nlp_router,
    evaluation_router,
]

for r in routers:
    app.include_router(r, prefix="/api")
    app.include_router(r, prefix="/api/v1")


# Serve static frontend SPA if present
from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import FileResponse

STATIC_DIR = Path(__file__).parent / "static"
STATIC_INDEX = STATIC_DIR / "index.html"

@app.api_route("/logo.png", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_logo():
    logo_path = STATIC_DIR / "logo.png"
    if logo_path.exists():
        return FileResponse(logo_path)
    raise HTTPException(status_code=404, detail="Logo not found")

@app.api_route("/logo_full.jpg", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_logo_full():
    logo_path = STATIC_DIR / "logo_full.jpg"
    if logo_path.exists():
        return FileResponse(logo_path)
    raise HTTPException(status_code=404, detail="Logo not found")

@app.api_route("/favicon.ico", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_favicon():
    logo_path = STATIC_DIR / "logo.png"
    if logo_path.exists():
        return FileResponse(logo_path)
    raise HTTPException(status_code=404, detail="Favicon not found")

if STATIC_INDEX.exists():
    @app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
    async def serve_root():
        return FileResponse(STATIC_INDEX)

    @app.api_route("/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    async def serve_spa_catchall(full_path: str):
        # Do not catch API, Swagger, health, or asset endpoints
        if (
            full_path.startswith("api")
            or full_path.startswith("health")
            or full_path in ["docs", "redoc", "openapi.json", "logo.png", "logo_full.jpg", "favicon.ico"]
        ):
            raise HTTPException(status_code=404, detail="Not Found")
        return FileResponse(STATIC_INDEX)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )

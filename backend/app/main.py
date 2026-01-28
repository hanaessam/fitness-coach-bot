from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from backend.app.core.config import settings
from backend.app.api.routes import router
from backend.app.services.rag_service import rag_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("Starting Fitness Coach Bot API...")
    try:
        rag_service.load_vectorstore()
        print("✓ RAG service initialized")
    except Exception as e:
        print(f"⚠ Warning: Could not load vectorstore: {e}")
        print("  Run build_database.py first to create the vectorstore")
    
    yield
    
    # Shutdown
    print("Shutting down API...")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix=settings.API_V1_STR, tags=["fitness"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Fitness Coach Bot API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True
    )
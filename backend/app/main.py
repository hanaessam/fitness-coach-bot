"""
FastAPI application with RAG system
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from datetime import datetime

from app.config import settings
from app.routes import router
from app.response_models import ErrorResponse
from app.services.rag_service import rag_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("\n" + "=" * 60)
    print("Starting Fitness Coach Bot API")
    print("=" * 60)

    # Try to load RAG system
    try:
        rag_service.load_vectorstore()
        print("✓ RAG system initialized")
    except Exception as e:
        print(f"⚠ Warning: Could not load RAG system: {e}")
        print("  Exercise search will not work until database is built")
        print("  Run: python build_database.py")

    print("=" * 60 + "\n")

    yield

    print("\nShutting down API...")


# Create FastAPI app
app = FastAPI(
    title="Fitness Coach Bot API",
    description="AI-powered fitness coaching with RAG",
    version="1.0.0",
    lifespan=lifespan,
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "details": exc.errors(),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "details": {"error": str(exc)},
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# Include router
app.include_router(router)


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "success": True,
        "message": "Fitness Coach Bot API",
        "data": {
            "version": "1.0.0",
            "docs": "/docs",
            "endpoints": {
                "health": "/api/v1/health",
                "calculate": "/api/v1/calculate-calories",
                "chat": "/api/v1/chat",
                "search": "/api/v1/exercises/search",
                "workout": "/api/v1/generate-workout-plan",
                "meal": "/api/v1/generate-meal-plan",
                "llm_test": "/api/v1/llm/test",
            },
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    # Auto-reload in development mode
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True,  # Enable auto-reload!
    )

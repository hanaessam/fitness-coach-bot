"""
FastAPI application with standardized responses
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.routes import router
from app.response_models import ErrorResponse
from datetime import datetime

# Create FastAPI app
app = FastAPI(
    title="Fitness Coach Bot API",
    description="AI-powered fitness coaching with standardized responses",
    version="1.0.0"
)

# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with standard format"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "details": exc.errors(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions with standard format"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "details": {"error": str(exc)},
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Include router
app.include_router(router)

@app.get("/")
def root():
    """Root endpoint with standard response"""
    return {
        "success": True,
        "message": "Fitness Coach Bot API",
        "data": {
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/api/v1/health",
            "endpoints": [
                "/api/v1/health",
                "/api/v1/calculate-calories"
            ]
        },
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.BACKEND_HOST, port=settings.BACKEND_PORT)

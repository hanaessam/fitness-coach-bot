"""
API routes - Clean HTTP handling only
Business logic is delegated to services
"""
from fastapi import APIRouter, HTTPException, status
from typing import Optional
from app.models import MealPlanRequest, UserProfile, WorkoutPlanRequest
from app.response_models import (
    APIResponse,
    HealthCheckData,
    CalorieCalculationData,
    ChatData,
    ChatRequest,
)
from app.services.calculator import calculator
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.utils.workout_parser import WorkoutParser
from app.utils.meal_parser import MealParser
from app.services.gym_analytics import get_gym_analytics
import time

# Track server start time
START_TIME = time.time()

# Create router
router = APIRouter(prefix="/api/v1", tags=["fitness"])


# =============================================================================
# HEALTH & SYSTEM ENDPOINTS
# =============================================================================

@router.get("/health", response_model=APIResponse)
def health_check():
    """Health check endpoint with system status"""
    uptime = time.time() - START_TIME
    
    health_data = HealthCheckData(
        status="healthy",
        version="1.0.0",
        uptime_seconds=round(uptime, 2),
        checks={
            "api": True,
            "calculator": True,
            "llm": True,
            "rag": rag_service.is_initialized,
            "analytics": get_gym_analytics() is not None,
        },
    )
    
    return APIResponse(
        success=True,
        message="API is healthy and running",
        data=health_data.dict()
    )

# ... keep all other endpoints the same until analytics section ...

# =============================================================================
# ANALYTICS ENDPOINTS
# =============================================================================

@router.get("/analytics/benchmark", response_model=APIResponse)
def get_performance_benchmark(
    age: int,
    gender: str,
    experience_level: int,
    workout_type: Optional[str] = None
):
    """Get performance benchmarks for similar users"""
    analytics = get_gym_analytics()
    
    if analytics is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "message": "Analytics service not available",
                "error_code": "ANALYTICS_NOT_LOADED",
            },
        )
    
    try:
        benchmark = analytics.get_benchmark(
            age=age,
            gender=gender,
            experience_level=experience_level,
            workout_type=workout_type,
        )
        
        return APIResponse(
            success=benchmark.get("found", True),
            message="Benchmark data retrieved" if benchmark.get("found") else "No similar users found",
            data=benchmark,
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Error retrieving benchmark",
                "error_code": "BENCHMARK_ERROR",
                "details": {"error": str(e)},
            },
        )


@router.get("/analytics/recommend-workout", response_model=APIResponse)
def recommend_workout_type(
    age: int,
    gender: str,
    goal: str,
    experience_level: int
):
    """Get workout type recommendations based on goals"""
    analytics = get_gym_analytics()
    
    if analytics is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "message": "Analytics service not available",
                "error_code": "ANALYTICS_NOT_LOADED",
            },
        )
    
    try:
        recommendations = analytics.recommend_workout_type(
            age=age,
            gender=gender,
            goal=goal,
            experience_level=experience_level
        )
        
        return APIResponse(
            success=True,
            message="Workout recommendations generated",
            data=recommendations,
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Error generating recommendations",
                "error_code": "RECOMMENDATION_ERROR",
                "details": {"error": str(e)},
            },
        )


@router.post("/analytics/predict-calories", response_model=APIResponse)
def predict_calories_burned(
    weight: float,
    session_duration: float,
    workout_type: str,
    experience_level: int
):
    """Predict calories burned for a workout session"""
    analytics = get_gym_analytics()
    
    if analytics is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "message": "Analytics service not available",
                "error_code": "ANALYTICS_NOT_LOADED",
            },
        )
    
    try:
        prediction = analytics.predict_calories(
            weight=weight,
            session_duration=session_duration,
            workout_type=workout_type,
            experience_level=experience_level,
        )
        
        return APIResponse(
            success=True,
            message="Calorie prediction generated",
            data=prediction
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Error predicting calories",
                "error_code": "PREDICTION_ERROR",
                "details": {"error": str(e)},
            },
        )

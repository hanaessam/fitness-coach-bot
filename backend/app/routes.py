"""
API routes - Clean HTTP handling only
Business logic is delegated to services
"""
from fastapi import APIRouter, HTTPException, status
from app.models import UserProfile
from app.response_models import (
    APIResponse,
    HealthCheckData,
    CalorieCalculationData
)
from app.services.calculator import calculator
import time

# Track server start time
START_TIME = time.time()

# Create router
router = APIRouter(prefix="/api/v1", tags=["fitness"])

@router.get("/health", response_model=APIResponse)
def health_check():
    """
    Health check endpoint
    
    Returns server status and uptime
    """
    uptime = time.time() - START_TIME
    
    health_data = HealthCheckData(
        status="healthy",
        version="1.0.0",
        uptime_seconds=round(uptime, 2),
        checks={
            "api": True,
            "calculator": True,
            "config": True
        }
    )
    
    return APIResponse(
        success=True,
        message="API is healthy and running",
        data=health_data.dict()
    )

@router.post("/calculate-calories", response_model=APIResponse)
def calculate_calories(profile: UserProfile):
    """
    Calculate complete nutritional breakdown
    
    This endpoint:
    1. Validates user profile (automatic via Pydantic)
    2. Delegates calculation to calculator service
    3. Returns standardized response
    
    The route is clean - all business logic is in the service!
    """
    try:
        # Delegate to service - this is the key pattern!
        breakdown = calculator.calculate_full_breakdown(
            weight_kg=profile.weight,
            height_cm=profile.height,
            age=profile.age,
            sex=profile.sex,
            activity_level=profile.activity_level,
            goal=profile.goal
        )
        
        # Wrap in response model
        calc_data = CalorieCalculationData(**breakdown)
        
        return APIResponse(
            success=True,
            message="Nutritional breakdown calculated successfully",
            data=calc_data.dict()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Error calculating calories",
                "error_code": "CALCULATION_ERROR",
                "details": {"error": str(e)}
            }
        )

# Add this import at the top with other imports
from app.services.llm_service import llm_service
from app.response_models import LLMTestData, ChatData, ChatRequest

# Add these endpoints at the end of the file

@router.get("/llm/test", response_model=APIResponse)
def test_llm_connection():
    """
    Test OpenAI API connection
    
    This endpoint verifies that:
    1. API key is configured
    2. API is reachable
    3. Model is responding
    
    Use this to debug LLM issues
    """
    try:
        test_result = llm_service.test_connection()
        
        if test_result["status"] == "connected":
            return APIResponse(
                success=True,
                message="OpenAI API connection successful",
                data=test_result
            )
        else:
            return APIResponse(
                success=False,
                message="OpenAI API connection failed",
                data=test_result
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Error testing LLM connection",
                "error_code": "LLM_TEST_ERROR",
                "details": {"error": str(e)}
            }
        )

@router.post("/chat", response_model=APIResponse)
def fitness_chat(request: ChatRequest):
    """
    Chat with FitCoach AI assistant
    
    This is a simple chat endpoint for testing LLM functionality.
    It uses a fitness expert persona to answer questions.
    
    Example questions:
    - "What's a good beginner workout?"
    - "How much protein should I eat?"
    - "What are compound exercises?"
    """
    try:
        chat_result = llm_service.fitness_chat(request.message)
        chat_data = ChatData(**chat_result)
        
        return APIResponse(
            success=True,
            message="Response generated successfully",
            data=chat_data.dict()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Error generating response",
                "error_code": "CHAT_ERROR",
                "details": {"error": str(e)}
            }
        )

# Add this import at the top with other imports
from app.services.llm_service import llm_service
from app.response_models import LLMTestData, ChatData, ChatRequest

# Add these endpoints at the end of the file

@router.get("/llm/test", response_model=APIResponse)
def test_llm_connection():
    """
    Test OpenAI API connection
    
    This endpoint verifies that:
    1. API key is configured
    2. API is reachable
    3. Model is responding
    
    Use this to debug LLM issues
    """
    try:
        test_result = llm_service.test_connection()
        
        if test_result["status"] == "connected":
            return APIResponse(
                success=True,
                message="OpenAI API connection successful",
                data=test_result
            )
        else:
            return APIResponse(
                success=False,
                message="OpenAI API connection failed",
                data=test_result
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Error testing LLM connection",
                "error_code": "LLM_TEST_ERROR",
                "details": {"error": str(e)}
            }
        )

@router.post("/chat", response_model=APIResponse)
def fitness_chat(request: ChatRequest):
    """
    Chat with FitCoach AI assistant
    
    This is a simple chat endpoint for testing LLM functionality.
    It uses a fitness expert persona to answer questions.
    
    Example questions:
    - "What's a good beginner workout?"
    - "How much protein should I eat?"
    - "What are compound exercises?"
    """
    try:
        chat_result = llm_service.fitness_chat(request.message)
        chat_data = ChatData(**chat_result)
        
        return APIResponse(
            success=True,
            message="Response generated successfully",
            data=chat_data.dict()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Error generating response",
                "error_code": "CHAT_ERROR",
                "details": {"error": str(e)}
            }
        )

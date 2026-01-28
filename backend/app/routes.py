"""
API routes - Clean HTTP handling only
Business logic is delegated to services
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Optional
from app.models import UserProfile
from app.response_models import (
    APIResponse,
    HealthCheckData,
    CalorieCalculationData,
    LLMTestData,
    ChatData,
    ChatRequest
)
from app.services.calculator import calculator
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
import time

# Track server start time
START_TIME = time.time()

# Create router
router = APIRouter(prefix="/api/v1", tags=["fitness"])

@router.get("/health", response_model=APIResponse)
def health_check():
    """Health check endpoint"""
    uptime = time.time() - START_TIME
    
    health_data = HealthCheckData(
        status="healthy",
        version="1.0.0",
        uptime_seconds=round(uptime, 2),
        checks={
            "api": True,
            "calculator": True,
            "llm": True,
            "rag": rag_service.is_initialized
        }
    )
    
    return APIResponse(
        success=True,
        message="API is healthy and running",
        data=health_data.dict()
    )

@router.post("/calculate-calories", response_model=APIResponse)
def calculate_calories(profile: UserProfile):
    """Calculate complete nutritional breakdown"""
    try:
        breakdown = calculator.calculate_full_breakdown(
            weight_kg=profile.weight,
            height_cm=profile.height,
            age=profile.age,
            sex=profile.sex,
            activity_level=profile.activity_level,
            goal=profile.goal
        )
        
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

@router.get("/llm/test", response_model=APIResponse)
def test_llm_connection():
    """Test OpenAI API connection"""
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
    """Chat with FitCoach AI assistant"""
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

@router.get("/exercises/search", response_model=APIResponse)
def search_exercises(
    query: str,
    limit: int = 5,
    level: Optional[str] = None,
    body_part: Optional[str] = None,
    equipment: Optional[str] = None
):
    """
    Search exercises using semantic search
    
    Args:
        query: Search query (e.g., "chest exercises")
        limit: Number of results (1-20)
        level: Filter by level (beginner/intermediate/advanced)
        body_part: Filter by body part (chest/back/legs/etc)
        equipment: Filter by equipment type
    
    Returns:
        List of relevant exercises
    
    Examples:
        - /api/v1/exercises/search?query=chest%20exercises&limit=5
        - /api/v1/exercises/search?query=beginner%20workout&level=beginner
        - /api/v1/exercises/search?query=legs&body_part=Legs&limit=10
    """
    if not rag_service.is_initialized:
        try:
            rag_service.load_vectorstore()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "success": False,
                    "message": "Exercise database not available",
                    "error_code": "RAG_NOT_INITIALIZED",
                    "details": {"error": str(e)}
                }
            )
    
    try:
        # Build ChromaDB-compatible filter
        # ChromaDB requires $and operator for multiple conditions
        filter_conditions = []
        
        if level:
            filter_conditions.append({"level": level.capitalize()})
        if body_part:
            filter_conditions.append({"body_part": body_part.capitalize()})
        if equipment:
            filter_conditions.append({"equipment": equipment.capitalize()})
        
        # Construct proper filter format
        chroma_filter = None
        if filter_conditions:
            if len(filter_conditions) == 1:
                # Single condition - use directly
                chroma_filter = filter_conditions[0]
            else:
                # Multiple conditions - use $and operator
                chroma_filter = {"$and": filter_conditions}
        
        # Search exercises
        results = rag_service.search_exercises(
            query=query,
            k=min(limit, 20),
            filters=chroma_filter
        )
        
        # Format results
        exercises = [
            {
                "title": doc.metadata['title'],
                "description": doc.metadata['description'],
                "type": doc.metadata['type'],
                "body_part": doc.metadata['body_part'],
                "equipment": doc.metadata['equipment'],
                "level": doc.metadata['level']
            }
            for doc in results
        ]
        
        return APIResponse(
            success=True,
            message=f"Found {len(exercises)} exercises",
            data={
                "query": query,
                "filters": {
                    "level": level,
                    "body_part": body_part,
                    "equipment": equipment
                },
                "count": len(exercises),
                "exercises": exercises
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Error searching exercises",
                "error_code": "SEARCH_ERROR",
                "details": {"error": str(e)}
            }
        )

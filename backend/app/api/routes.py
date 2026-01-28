from fastapi import APIRouter, HTTPException, Depends, status
from typing import List

from backend.app.models.schemas import (
    CalorieCalculationRequest,
    CalorieBreakdown,
    WorkoutPlanRequest,
    WorkoutPlanResponse,
    MealPlanRequest,
    MealPlanResponse,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    Exercise
)
from backend.app.services.calculator import CalorieCalculator
from backend.app.services.rag_service import rag_service
from backend.app.services.llm_service import llm_service

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "vectorstore_loaded": rag_service.is_initialized
    }

@router.post("/calculate-calories", response_model=CalorieBreakdown)
async def calculate_calories(request: CalorieCalculationRequest):
    """Calculate caloric needs and macro breakdown"""
    try:
        profile = request.profile
        
        breakdown = CalorieCalculator.calculate_full_breakdown(
            weight_kg=profile.weight,
            height_cm=profile.height,
            age=profile.age,
            sex=profile.sex,
            activity_level=profile.activity_level,
            goal=profile.goal
        )
        
        return CalorieBreakdown(**breakdown)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating calories: {str(e)}"
        )

@router.post("/generate-workout", response_model=WorkoutPlanResponse)
async def generate_workout(request: WorkoutPlanRequest):
    """Generate personalized workout plan"""
    try:
        if not rag_service.is_initialized:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG service not initialized"
            )
        
        profile = request.profile
        
        # Build search query
        query_parts = [
            profile.goal.value,
            profile.level.value,
            f"{profile.days_available} days",
        ]
        if request.focus_areas:
            query_parts.extend(request.focus_areas)
        
        search_query = " ".join(query_parts) + " exercises"
        
        # Search for relevant exercises
        relevant_docs = rag_service.search_exercises(search_query, k=15)
        
        # Extract exercise information
        exercises_info = []
        exercises_list = []
        for doc in relevant_docs:
            exercise_str = f"{doc.metadata['title']} ({doc.metadata['body_part']}, {doc.metadata['level']})"
            exercises_info.append(exercise_str)
            exercises_list.append(Exercise(**doc.metadata, description=""))
        
        # Generate workout plan
        workout_plan = llm_service.generate_workout_plan(
            user_profile=profile.dict(),
            relevant_exercises=exercises_info
        )
        
        return WorkoutPlanResponse(
            plan=workout_plan,
            exercises_used=exercises_list[:10]  # Return top 10
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating workout: {str(e)}"
        )

@router.post("/generate-meal-plan", response_model=MealPlanResponse)
async def generate_meal_plan(request: MealPlanRequest):
    """Generate personalized meal plan"""
    try:
        meal_plan = llm_service.generate_meal_plan(
            target_calories=request.target_calories,
            protein_g=request.protein_g,
            carbs_g=request.carbs_g,
            fat_g=request.fat_g,
            dietary_restrictions=request.dietary_restrictions
        )
        
        return MealPlanResponse(
            plan=meal_plan,
            total_calories=request.target_calories,
            total_protein=request.protein_g,
            total_carbs=request.carbs_g,
            total_fat=request.fat_g
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating meal plan: {str(e)}"
        )

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with fitness assistant"""
    try:
        response = llm_service.chat(
            user_message=request.message,
            conversation_history=request.conversation_history,
            user_context=request.user_context
        )
        
        # Check if we need RAG context for exercise-related queries
        context_used = any(keyword in request.message.lower() 
                          for keyword in ['exercise', 'workout', 'movement', 'lift'])
        
        return ChatResponse(
            response=response,
            context_used=context_used
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat: {str(e)}"
        )

@router.get("/exercises/search")
async def search_exercises(
    query: str,
    limit: int = 10,
    body_part: str = None,
    level: str = None
):
    """Search exercises in database"""
    try:
        if not rag_service.is_initialized:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG service not initialized"
            )
        
        # Build filters
        filters = {}
        if body_part:
            filters['body_part'] = body_part
        if level:
            filters['level'] = level
        
        results = rag_service.search_exercises(query, k=limit, filters=filters if filters else None)
        
        exercises = [
            {
                "title": doc.metadata['title'],
                "body_part": doc.metadata['body_part'],
                "equipment": doc.metadata['equipment'],
                "level": doc.metadata['level'],
                "type": doc.metadata['type']
            }
            for doc in results
        ]
        
        return {"exercises": exercises, "count": len(exercises)}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching exercises: {str(e)}"
        )
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
            "rag": rag_service.is_initialized,
        },
    )

    return APIResponse(
        success=True, message="API is healthy and running", data=health_data.dict()
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
            goal=profile.goal,
        )

        calc_data = CalorieCalculationData(**breakdown)

        return APIResponse(
            success=True,
            message="Nutritional breakdown calculated successfully",
            data=calc_data.dict(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Error calculating calories",
                "error_code": "CALCULATION_ERROR",
                "details": {"error": str(e)},
            },
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
                data=test_result,
            )
        else:
            return APIResponse(
                success=False, message="OpenAI API connection failed", data=test_result
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Error testing LLM connection",
                "error_code": "LLM_TEST_ERROR",
                "details": {"error": str(e)},
            },
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
            data=chat_data.dict(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Error generating response",
                "error_code": "CHAT_ERROR",
                "details": {"error": str(e)},
            },
        )


@router.get("/exercises/search", response_model=APIResponse)
def search_exercises(
    query: str,
    limit: int = 5,
    level: Optional[str] = None,
    body_part: Optional[str] = None,
    equipment: Optional[str] = None,
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
                    "details": {"error": str(e)},
                },
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
            query=query, k=min(limit, 20), filters=chroma_filter
        )

        # Format results
        exercises = [
            {
                "title": doc.metadata["title"],
                "description": doc.metadata["description"],
                "type": doc.metadata["type"],
                "body_part": doc.metadata["body_part"],
                "equipment": doc.metadata["equipment"],
                "level": doc.metadata["level"],
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
                    "equipment": equipment,
                },
                "count": len(exercises),
                "exercises": exercises,
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Error searching exercises",
                "error_code": "SEARCH_ERROR",
                "details": {"error": str(e)},
            },
        )


@router.post("/generate-workout-plan", response_model=APIResponse)
def generate_workout_plan(request: WorkoutPlanRequest):
    """
    Generate personalized workout plan using RAG + LLM

    This endpoint:
    1. Searches for relevant exercises using RAG
    2. Generates structured plan using LLM
    3. Returns complete workout program

    The plan includes:
    - Day-by-day breakdown
    - Specific exercises with sets/reps
    - Rest periods and duration
    - Safety notes
    """
    try:
        # Ensure RAG is initialized
        if not rag_service.is_initialized:
            rag_service.load_vectorstore()

        profile = request.profile

        # Build search query based on user profile
        search_terms = []

        # Add goal-specific terms
        if profile.goal.value == "lose":
            search_terms.extend(["cardio", "fat burning", "circuit"])
        elif profile.goal.value == "gain":
            search_terms.extend(["strength", "muscle building", "compound"])
        else:
            search_terms.extend(["fitness", "conditioning"])

        # Add focus areas if specified
        if request.focus_areas:
            search_terms.extend(request.focus_areas)

        # Add level
        search_terms.append(
            profile.level.value if hasattr(profile, "level") else "beginner"
        )

        # Create search query
        search_query = " ".join(search_terms) + " exercises"

        # Search for relevant exercises (get more than needed)
        exercise_docs = rag_service.search_exercises(
            query=search_query, k=30  # Get plenty of exercises for variety
        )

        # Extract exercise information
        exercise_list = []
        exercises_used = []

        for doc in exercise_docs:
            exercise_info = (
                f"{doc.metadata['title']} "
                f"({doc.metadata['body_part']}, "
                f"{doc.metadata['equipment']}, "
                f"{doc.metadata['level']})"
            )
            exercise_list.append(exercise_info)

            exercises_used.append(
                {
                    "title": doc.metadata["title"],
                    "body_part": doc.metadata["body_part"],
                    "equipment": doc.metadata["equipment"],
                    "level": doc.metadata["level"],
                }
            )

        # Generate workout plan using LLM
        workout_plan_text = llm_service.generate_workout_plan(
            user_profile={
                "age": profile.age,
                "sex": profile.sex.value,
                "goal": profile.goal.value,
                "level": (
                    profile.level.value if hasattr(profile, "level") else "beginner"
                ),
                "activity_level": profile.activity_level.value,
            },
            relevant_exercises=exercise_list,
            days_per_week=request.days_per_week,
        )

        # Return structured response
        try:
            parsed_plan = WorkoutParser.parse_workout_plan(workout_plan_text)
        except:
            parsed_plan = None  # Fallback if parsing fails

        return APIResponse(
            success=True,
            message="Workout plan generated successfully",
            data={
                "structured_plan": parsed_plan,
                "raw_plan": workout_plan_text,
                "exercises_used": exercises_used[:15],  # First 15
                "total_exercises": len(exercises_used),
                "days_per_week": request.days_per_week,
                "profile_summary": {
                    "goal": profile.goal.value,
                    "level": (
                        profile.level.value if hasattr(profile, "level") else "beginner"
                    ),
                    "age": profile.age,
                },
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Error generating workout plan",
                "error_code": "WORKOUT_GENERATION_ERROR",
                "details": {"error": str(e)},
            },
        )


@router.post("/generate-meal-plan", response_model=APIResponse)
def generate_meal_plan(request: MealPlanRequest):
    """
    Generate personalized meal plan (1-7 days)

    Supports:
    - Single day meal plan (days=1)
    - Weekly meal plan (days=7)
    """
    try:
        profile = request.profile

        # Calculate nutritional needs
        breakdown = calculator.calculate_full_breakdown(
            weight_kg=profile.weight,
            height_cm=profile.height,
            age=profile.age,
            sex=profile.sex,
            activity_level=profile.activity_level,
            goal=profile.goal,
        )

        # Generate appropriate meal plan
        if request.days == 1:
            meal_plan_text = llm_service.generate_meal_plan(
                target_calories=breakdown["target_calories"],
                protein_g=breakdown["protein_g"],
                carbs_g=breakdown["carbs_g"],
                fat_g=breakdown["fat_g"],
                dietary_restrictions=profile.restrictions,
            )
        else:
            meal_plan_text = llm_service.generate_weekly_meal_plan(
                target_calories=breakdown["target_calories"],
                protein_g=breakdown["protein_g"],
                carbs_g=breakdown["carbs_g"],
                fat_g=breakdown["fat_g"],
                dietary_restrictions=profile.restrictions,
            )

        # Parse meal plan
        try:
            parsed_meal_plan = MealParser.parse_meal_plan(meal_plan_text)
        except Exception as parse_error:
            print(f"Warning: Could not parse meal plan: {parse_error}")
            parsed_meal_plan = {
                "type": "single_day" if request.days == 1 else "weekly",
                "meals": [],
                "error": str(parse_error),
            }

        return APIResponse(
            success=True,
            message=f"{request.days}-day meal plan generated successfully",
            data={
                "structured_plan": parsed_meal_plan,
                "raw_plan": meal_plan_text,
                "nutritional_targets": {
                    "calories": breakdown["target_calories"],
                    "protein_g": breakdown["protein_g"],
                    "carbs_g": breakdown["carbs_g"],
                    "fat_g": breakdown["fat_g"],
                },
                "metadata": {
                    "days": request.days,
                    "goal": profile.goal.value,
                    "dietary_restrictions": profile.restrictions,
                },
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Error generating meal plan",
                "error_code": "MEAL_GENERATION_ERROR",
                "details": {"error": str(e)},
            },
        )


@router.post("/generate-workout-plan", response_model=APIResponse)
def generate_workout_plan(request: WorkoutPlanRequest):
    """
    Generate personalized workout plan using RAG + LLM

    This endpoint:
    1. Searches for relevant exercises using RAG
    2. Generates structured plan using LLM
    3. Returns complete workout program

    The plan includes:
    - Day-by-day breakdown
    - Specific exercises with sets/reps
    - Rest periods and duration
    - Safety notes
    """
    try:
        # Ensure RAG is initialized
        if not rag_service.is_initialized:
            rag_service.load_vectorstore()

        profile = request.profile

        # Build search query based on user profile
        search_terms = []

        # Add goal-specific terms
        if profile.goal.value == "lose":
            search_terms.extend(["cardio", "fat burning", "circuit"])
        elif profile.goal.value == "gain":
            search_terms.extend(["strength", "muscle building", "compound"])
        else:
            search_terms.extend(["fitness", "conditioning"])

        # Add focus areas if specified
        if request.focus_areas:
            search_terms.extend(request.focus_areas)

        # Add level
        search_terms.append(
            profile.level.value if hasattr(profile, "level") else "beginner"
        )

        # Create search query
        search_query = " ".join(search_terms) + " exercises"

        # Search for relevant exercises (get more than needed)
        exercise_docs = rag_service.search_exercises(
            query=search_query, k=30  # Get plenty of exercises for variety
        )

        # Extract exercise information
        exercise_list = []
        exercises_used = []

        for doc in exercise_docs:
            exercise_info = (
                f"{doc.metadata['title']} "
                f"({doc.metadata['body_part']}, "
                f"{doc.metadata['equipment']}, "
                f"{doc.metadata['level']})"
            )
            exercise_list.append(exercise_info)

            exercises_used.append(
                {
                    "title": doc.metadata["title"],
                    "body_part": doc.metadata["body_part"],
                    "equipment": doc.metadata["equipment"],
                    "level": doc.metadata["level"],
                }
            )

        # Generate workout plan using LLM
        workout_plan_text = llm_service.generate_workout_plan(
            user_profile={
                "age": profile.age,
                "sex": profile.sex.value,
                "goal": profile.goal.value,
                "level": (
                    profile.level.value if hasattr(profile, "level") else "beginner"
                ),
                "activity_level": profile.activity_level.value,
            },
            relevant_exercises=exercise_list,
            days_per_week=request.days_per_week,
        )

        # Return structured response
        return APIResponse(
            success=True,
            message="Workout plan generated successfully",
            data={
                "plan": workout_plan_text,
                "exercises_used": exercises_used[:15],  # First 15
                "total_exercises": len(exercises_used),
                "days_per_week": request.days_per_week,
                "profile_summary": {
                    "goal": profile.goal.value,
                    "level": (
                        profile.level.value if hasattr(profile, "level") else "beginner"
                    ),
                    "age": profile.age,
                },
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Error generating workout plan",
                "error_code": "WORKOUT_GENERATION_ERROR",
                "details": {"error": str(e)},
            },
        )


@router.post("/generate-meal-plan", response_model=APIResponse)
def generate_meal_plan(profile: UserProfile):
    """
    Generate personalized meal plan

    This endpoint:
    1. Calculates caloric needs
    2. Generates structured meal plan using LLM
    3. Returns daily meal breakdown
    """
    try:
        # Calculate nutritional needs
        breakdown = calculator.calculate_full_breakdown(
            weight_kg=profile.weight,
            height_cm=profile.height,
            age=profile.age,
            sex=profile.sex,
            activity_level=profile.activity_level,
            goal=profile.goal,
        )

        # Generate meal plan using LLM
        meal_plan_text = llm_service.generate_meal_plan(
            target_calories=breakdown["target_calories"],
            protein_g=breakdown["protein_g"],
            carbs_g=breakdown["carbs_g"],
            fat_g=breakdown["fat_g"],
            dietary_restrictions=getattr(profile, "restrictions", []),
        )

        return APIResponse(
            success=True,
            message="Meal plan generated successfully",
            data={
                "meal_plan": meal_plan_text,
                "nutritional_targets": {
                    "calories": breakdown["target_calories"],
                    "protein_g": breakdown["protein_g"],
                    "carbs_g": breakdown["carbs_g"],
                    "fat_g": breakdown["fat_g"],
                },
                "goal": profile.goal.value,
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Error generating meal plan",
                "error_code": "MEAL_GENERATION_ERROR",
                "details": {"error": str(e)},
            },
        )

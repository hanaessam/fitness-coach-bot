"""
API Routes - Fitness Coach Bot
Clean HTTP handling with business logic delegated to services
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional

# Models
from app.models import MealPlanRequest, UserProfile, WorkoutPlanRequest

# Response models
from app.response_models import (
    APIResponse,
    HealthCheckData,
    CalorieCalculationData,
    ChatData,
    ChatRequest,
)

# Services
from app.services.calculator import calculator
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.services.gym_analytics import get_gym_analytics

# Parsers
from app.utils.workout_parser import WorkoutParser
from app.utils.meal_parser import MealParser

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
    """
    Health check endpoint

    Returns system status and uptime
    """
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
        success=True, message="API is healthy and running", data=health_data.dict()
    )


@router.get("/llm/test", response_model=APIResponse)
def test_llm_connection():
    """
    Test OpenAI API connection

    Use this endpoint to verify LLM is working
    """
    try:
        test_result = llm_service.test_connection()

        return APIResponse(
            success=test_result["status"] == "connected",
            message=f"OpenAI API connection {test_result['status']}",
            data=test_result,
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


# =============================================================================
# CALCULATOR ENDPOINTS
# =============================================================================


@router.post("/calculate-calories", response_model=APIResponse)
def calculate_calories(profile: UserProfile):
    """
    Calculate personalized calorie and macro targets

    Uses Mifflin-St Jeor equation for BMR calculation
    Applies activity multipliers and goal adjustments
    """
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


# =============================================================================
# CHAT ENDPOINTS
# =============================================================================


@router.post("/chat", response_model=APIResponse)
def fitness_chat(request: ChatRequest):
    """
    Chat with FitCoach AI assistant

    General fitness questions and advice
    """
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


# =============================================================================
# EXERCISE SEARCH (RAG)
# =============================================================================


@router.get("/exercises/search", response_model=APIResponse)
def search_exercises(
    query: str,
    limit: int = 5,
    level: Optional[str] = None,
    body_part: Optional[str] = None,
    equipment: Optional[str] = None,
):
    """
    Semantic exercise search using RAG

    Args:
        query: Search term (e.g., "chest exercises")
        limit: Number of results (1-20)
        level: Filter by difficulty (beginner/intermediate/advanced)
        body_part: Filter by target area (chest/back/legs/etc)
        equipment: Filter by equipment type

    Examples:
        - /api/v1/exercises/search?query=chest&limit=5
        - /api/v1/exercises/search?query=legs&level=beginner&equipment=Body%20Only
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
        # Build ChromaDB filter
        filter_conditions = []

        if level:
            filter_conditions.append({"level": level.capitalize()})
        if body_part:
            filter_conditions.append({"body_part": body_part.capitalize()})
        if equipment:
            filter_conditions.append({"equipment": equipment.capitalize()})

        # ChromaDB requires $and for multiple conditions
        chroma_filter = None
        if filter_conditions:
            if len(filter_conditions) == 1:
                chroma_filter = filter_conditions[0]
            else:
                chroma_filter = {"$and": filter_conditions}

        # Search
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


# =============================================================================
# WORKOUT PLAN GENERATION (RAG + LLM + Analytics)
# =============================================================================


@router.post("/generate-workout-plan", response_model=APIResponse)
def generate_workout_plan(request: WorkoutPlanRequest):
    """
    Generate personalized workout plan

    Uses:
    - RAG to find relevant exercises from database
    - Gym analytics to provide benchmarks (if available)
    - LLM to create structured workout plan

    Returns:
    - Structured plan (parsed JSON)
    - Raw markdown plan
    - Exercise database
    - Benchmark data (similar users' stats)
    """
    try:
        # Ensure RAG is initialized
        if not rag_service.is_initialized:
            rag_service.load_vectorstore()

        profile = request.profile

        # Build search query based on goal
        search_terms = []

        if profile.goal.value == "lose":
            search_terms.extend(["cardio", "fat burning", "circuit"])
        elif profile.goal.value == "gain":
            search_terms.extend(["strength", "muscle building", "compound"])
        else:
            search_terms.extend(["fitness", "conditioning"])

        if request.focus_areas:
            search_terms.extend(request.focus_areas)

        search_terms.append(profile.level.value)
        search_query = " ".join(search_terms) + " exercises"

        # Search for relevant exercises
        exercise_docs = rag_service.search_exercises(query=search_query, k=30)

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
                    "description": doc.metadata.get("description", ""),
                }
            )

        # Get benchmark data if available
        benchmark_info = None
        analytics = get_gym_analytics()

        if analytics:
            try:
                exp_level_map = {"beginner": 1, "intermediate": 2, "advanced": 3}

                benchmark = analytics.get_benchmark(
                    age=profile.age,
                    gender=profile.sex.value,
                    experience_level=exp_level_map.get(profile.level.value, 1),
                )

                workout_recs = analytics.recommend_workout_type(
                    age=profile.age,
                    gender=profile.sex.value,
                    goal=profile.goal.value,
                    experience_level=exp_level_map.get(profile.level.value, 1),
                )

                benchmark_info = {
                    "benchmark": benchmark,
                    "recommendations": workout_recs,
                }
            except Exception as e:
                print(f"Warning: Could not get benchmark data: {e}")

        # Generate workout plan using LLM
        workout_plan_text = llm_service.generate_workout_plan(
            user_profile={
                "age": profile.age,
                "sex": profile.sex.value,
                "goal": profile.goal.value,
                "level": profile.level.value,
                "activity_level": profile.activity_level.value,
            },
            relevant_exercises=exercise_list,
            days_per_week=request.days_per_week,
        )

        # Parse into structured format
        try:
            parsed_plan = WorkoutParser.parse_workout_plan(workout_plan_text)
        except Exception as parse_error:
            print(f"Warning: Could not parse workout plan: {parse_error}")
            parsed_plan = None

        return APIResponse(
            success=True,
            message="Workout plan generated successfully",
            data={
                "structured_plan": parsed_plan,
                "raw_plan": workout_plan_text,
                "exercises_database": exercises_used[:15],
                "benchmark_data": benchmark_info,
                "metadata": {
                    "days_per_week": request.days_per_week,
                    "total_exercises_available": len(exercises_used),
                    "profile": {
                        "goal": profile.goal.value,
                        "level": profile.level.value,
                        "age": profile.age,
                        "sex": profile.sex.value,
                    },
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


# =============================================================================
# MEAL PLAN GENERATION (LLM-Only)
# =============================================================================


@router.post("/generate-meal-plan", response_model=APIResponse)
def generate_meal_plan(request: MealPlanRequest):
    """
    Generate personalized meal plan (1-7 days)

    Uses LLM to create nutritionally balanced meal plans
    Supports dietary restrictions (vegetarian, vegan, gluten-free, etc.)

    Args:
        request: Contains user profile and number of days

    Returns:
        - Structured meal plan (parsed JSON)
        - Raw markdown plan
        - Nutritional targets
        - Metadata
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
                "parsing_error": str(parse_error),
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


# =============================================================================
# ANALYTICS ENDPOINTS (Gym Member Data)
# =============================================================================


@router.get("/analytics/benchmark", response_model=APIResponse)
def get_performance_benchmark(
    age: int, gender: str, experience_level: int, workout_type: Optional[str] = None
):
    """
    Get performance benchmarks from similar users

    Args:
        age: User age
        gender: male or female
        experience_level: 1=beginner, 2=intermediate, 3=advanced
        workout_type: Optional (Cardio, Strength, HIIT, Yoga)

    Returns:
        Average stats from gym members dataset

    Example:
        /api/v1/analytics/benchmark?age=25&gender=female&experience_level=1
    """
    analytics = get_gym_analytics()

    if analytics is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "message": "Analytics service not available",
                "error_code": "ANALYTICS_NOT_LOADED",
                "hint": "Gym members dataset not found",
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
            message=(
                "Benchmark data retrieved"
                if benchmark.get("found")
                else "No similar users found"
            ),
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
def recommend_workout_type(age: int, gender: str, goal: str, experience_level: int):
    """
    Get workout type recommendations based on goals

    Uses gym member data to recommend optimal workout types

    Args:
        age: User age
        gender: male or female
        goal: lose, gain, or maintain
        experience_level: 1=beginner, 2=intermediate, 3=advanced

    Returns:
        Recommended workout types with expected results
    """
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
            age=age, gender=gender, goal=goal, experience_level=experience_level
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
    weight: float, session_duration: float, workout_type: str, experience_level: int
):
    """
    Predict calories burned for a workout session

    Uses gym member data to estimate calorie burn

    Args:
        weight: User weight in kg
        session_duration: Duration in hours
        workout_type: Cardio, Strength, HIIT, or Yoga
        experience_level: 1=beginner, 2=intermediate, 3=advanced

    Returns:
        Predicted calorie burn with confidence level
    """
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
            success=True, message="Calorie prediction generated", data=prediction
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

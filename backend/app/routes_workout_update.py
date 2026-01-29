# Add this to your imports at the top of routes.py
from http.client import HTTPException
from app.utils.workout_parser import WorkoutParser
from backend.app.response_models import APIResponse
from backend.app.services import llm_service, rag_service


@router.post("/generate-workout-plan", response_model=APIResponse)
def generate_workout_plan(request: WorkoutPlanRequest):
    """
    Generate personalized workout plan using RAG + LLM

    Returns a beautifully structured workout plan with:
    - Overview and goals
    - Day-by-day breakdown
    - Exercise details (sets, reps, rest)
    - Duration estimates
    - Safety notes
    """
    try:
        # Ensure RAG is initialized
        if not rag_service.is_initialized:
            rag_service.load_vectorstore()

        profile = request.profile

        # Build search query
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

        # Search for exercises
        exercise_docs = rag_service.search_exercises(query=search_query, k=30)

        # Prepare exercise list
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

        # Generate workout plan
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

        # Parse the plan into structured format
        parsed_plan = WorkoutParser.parse_workout_plan(workout_plan_text)

        # Combine with exercise database
        return APIResponse(
            success=True,
            message="Workout plan generated successfully",
            data={
                "structured_plan": parsed_plan,
                "raw_plan": workout_plan_text,
                "exercises_database": exercises_used[:15],
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

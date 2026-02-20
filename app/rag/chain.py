from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.rag.retriever import query_exercises, query_nutrients
from app.prompts.system_prompt import SYSTEM_PROMPT

load_dotenv()


def build_retrieval_query(profile):
    # Build a targeted search query from the user's profile and goal
    goal_keywords = {
        "lose": "fat loss cardio calorie burn",
        "aggressive_lose": "fat loss high intensity calorie burn",
        "maintain": "general fitness maintenance",
        "recomp": "strength training muscle building maintenance",
        "lean_bulk": "muscle building hypertrophy strength",
        "bulk": "mass building heavy compound strength",
    }

    goal = profile.get("goal", "maintain")
    base_query = goal_keywords.get(goal, "general fitness")
    activity = profile.get("activity_level", "")
    return f"{base_query} {activity}".strip()


def build_nutrition_query(profile):
    # Build a search query for nutrition based on goal and dietary restrictions
    goal_nutrition = {
        "lose": "low calorie high protein",
        "aggressive_lose": "low calorie high protein low fat",
        "maintain": "balanced nutrition moderate calories",
        "recomp": "high protein moderate carbs",
        "lean_bulk": "high protein high calorie",
        "bulk": "high calorie high protein high carbs",
    }

    goal = profile.get("goal", "maintain")
    base_query = goal_nutrition.get(goal, "balanced nutrition")
    restrictions = profile.get("dietary_restrictions", "")
    if restrictions:
        base_query = f"{base_query} {restrictions}"
    return base_query


def format_context(exercises, nutrients):
    # Format retrieved documents into a readable context block
    ex_block = "\n".join(f"- {e}" for e in exercises)
    nu_block = "\n".join(f"- {n}" for n in nutrients)
    return (
        f"RELEVANT EXERCISES:\n{ex_block}\n\n"
        f"RELEVANT FOODS:\n{nu_block}"
    )


def generate_plan(profile):
    # Retrieve relevant exercises and nutrients
    exercise_query = build_retrieval_query(profile)
    nutrition_query = build_nutrition_query(profile)
    exercises = query_exercises(exercise_query, k=5)
    nutrients = query_nutrients(nutrition_query, k=5)
    context = format_context(exercises, nutrients)

    # Build the human message with profile and context
    human_message = (
        f"User Profile:\n"
        f"- Weight: {profile['weight_kg']} kg\n"
        f"- Height: {profile['height_cm']} cm\n"
        f"- Age: {profile['age']}\n"
        f"- Sex: {profile['sex']}\n"
        f"- Activity Level: {profile['activity_level']}\n"
        f"- Goal: {profile['goal']}\n"
        f"- Dietary Restrictions: {profile.get('dietary_restrictions', 'None')}\n"
        f"- Plan Duration: {profile.get('plan_duration', 'weekly')}\n"
        f"- Daily Calorie Target: {profile['target_calories']} kcal\n\n"
        f"Retrieved Context:\n{context}\n\n"
        f"Based on the user's profile and the retrieved exercise and food data, "
        f"generate a personalized fitness and nutrition plan. Follow the output "
        f"format specified in your instructions with CALORIE SUMMARY, WORKOUT "
        f"PLAN, and MEAL PLAN sections."
    )

    # LCEL chain: prompt | llm
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
    ])

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        max_tokens=1500,
    )

    chain = prompt | llm

    response = chain.invoke({"input": human_message})
    return response.content


if __name__ == "__main__":
    test_profile = {
        "weight_kg": 70,
        "height_cm": 170,
        "age": 25,
        "sex": "female",
        "goal": "lose",
        "activity_level": "moderate",
        "dietary_restrictions": "vegetarian",
        "plan_duration": "weekly",
        "target_calories": 1650,
    }

    print("Generating plan for test profile...")
    print("=" * 60)
    result = generate_plan(test_profile)
    print(result)
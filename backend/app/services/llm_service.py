"""
LLM Service for AI-powered features
Handles all interactions with OpenAI API
"""

from openai import OpenAI
from typing import List, Dict, Optional
from app.config import settings


class LLMService:
    """
    Service for LLM interactions

    This handles all communication with OpenAI's API,
    including system prompts, conversation management,
    and error handling.
    """

    def __init__(self):
        """Initialize OpenAI client"""
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.MODEL_NAME
        self.temperature = settings.TEMPERATURE
        self.max_tokens = settings.MAX_TOKENS

    def simple_chat(
        self, user_message: str, system_prompt: Optional[str] = None
    ) -> str:
        """
        Simple chat completion - for testing and basic queries

        Args:
            user_message: The user's message/question
            system_prompt: Optional system instructions

        Returns:
            AI response as string

        Example:
            >>> llm = LLMService()
            >>> response = llm.simple_chat("What's a good beginner workout?")
            >>> print(response)
        """
        messages = []

        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add user message
        messages.append({"role": "user", "content": user_message})

        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            return response.choices[0].message.content

        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    def fitness_chat(self, user_message: str) -> Dict[str, any]:
        """
        Chat with fitness expert persona

        This is a specialized version with a fitness-focused system prompt

        Args:
            user_message: User's fitness question

        Returns:
            Dictionary with response and metadata
        """
        system_prompt = """You are FitCoach, a knowledgeable and supportive fitness assistant.

Your expertise includes:
- Exercise technique and form
- Workout programming
- Nutrition basics
- Injury prevention
- Motivation and habit formation

Your style:
- Encouraging but realistic
- Evidence-based recommendations
- Clear, concise explanations
- Safety-first approach

Remember:
- Never diagnose medical conditions
- Always recommend consulting professionals for injuries
- Emphasize proper form over heavy weight
- Promote sustainable habits over quick fixes"""

        try:
            response_text = self.simple_chat(user_message, system_prompt)

            return {
                "response": response_text,
                "model_used": self.model,
                "persona": "FitCoach",
            }

        except Exception as e:
            raise Exception(f"Fitness chat error: {str(e)}")

    def test_connection(self) -> Dict[str, any]:
        """
        Test OpenAI API connection

        Returns:
            Status information about the connection
        """
        try:
            # Simple test prompt
            response = self.simple_chat(
                "Say 'Connection successful!' if you can read this."
            )

            return {
                "status": "connected",
                "model": self.model,
                "test_response": response[:100],  # First 100 chars
                "api_configured": True,
            }

        except Exception as e:
            return {
                "status": "error",
                "model": self.model,
                "error": str(e),
                "api_configured": False,
            }

    def generate_workout_plan(
        self, user_profile: Dict, relevant_exercises: List[str], days_per_week: int
    ) -> str:
        """
        Generate structured workout plan

        Args:
            user_profile: User's fitness profile
            relevant_exercises: List of exercise names from RAG
            days_per_week: Number of training days

        Returns:
            Structured workout plan text
        """
        system_prompt = """You are an expert fitness trainer creating personalized workout plans.

Your plans should:
- Match the user's experience level
- Align with their fitness goals
- Use the provided exercises from the database
- Include proper progression
- Specify sets, reps, and rest periods
- Be realistic and sustainable

Format your response as a structured plan with:
1. Plan Overview
2. Day-by-day breakdown
3. Each exercise with sets x reps and rest periods
4. Estimated duration per session
5. Important safety notes

CRITICAL: Only use exercises from the provided list. Do not invent exercises."""

        # Build detailed prompt
        goal_text = {
            "lose": "weight loss and fat reduction",
            "gain": "muscle building and strength",
            "maintain": "maintaining fitness and general health",
        }.get(user_profile["goal"], "fitness")

        user_prompt = f"""Create a {days_per_week}-day workout plan for:

USER PROFILE:
- Age: {user_profile['age']} years
- Sex: {user_profile['sex']}
- Experience Level: {user_profile.get('level', 'beginner')}
- Goal: {goal_text}
- Activity Level: {user_profile.get('activity_level', 'moderate')}

AVAILABLE EXERCISES (use these):
{chr(10).join(f"- {ex}" for ex in relevant_exercises[:20])}

REQUIREMENTS:
- Create a {days_per_week}-day split
- Each day should have 4-6 exercises
- Specify sets x reps for each exercise
- Include rest periods (e.g., "90 seconds")
- Total workout time: 45-60 minutes per session
- Only use exercises from the list above

Format each day as:
**Day X: [Focus Area]**
1. [Exercise Name] - [Sets]x[Reps], Rest: [Time]
2. [Exercise Name] - [Sets]x[Reps], Rest: [Time]
...
Estimated Duration: [Time]

Include warm-up and cool-down reminders."""

        try:
            response = self.simple_chat(user_prompt, system_prompt)
            return response

        except Exception as e:
            raise Exception(f"Error generating workout plan: {str(e)}")

    def generate_meal_plan(
        self,
        target_calories: float,
        protein_g: float,
        carbs_g: float,
        fat_g: float,
        dietary_restrictions: List[str] = None,
    ) -> str:
        """
        Generate daily meal plan

        Args:
            target_calories: Target daily calories
            protein_g: Protein target in grams
            carbs_g: Carbs target in grams
            fat_g: Fat target in grams
            dietary_restrictions: List of dietary restrictions

        Returns:
            Structured meal plan text
        """
        system_prompt = """You are a certified nutritionist creating meal plans.

    Your meal plans should:
    - Meet the exact calorie and macro targets
    - Respect dietary restrictions
    - Include whole, nutritious foods
    - Provide variety
    - Be realistic and practical
    - Include approximate portions

    Format each meal with:
    - Meal name and time
    - Main ingredients
    - Portion sizes
    - Macro breakdown (calories, protein, carbs, fat)"""

        restrictions_text = (
            ", ".join(dietary_restrictions) if dietary_restrictions else "None"
        )

        user_prompt = f"""Create a 1-day sample meal plan with these targets:

    NUTRITIONAL TARGETS:
    - Total Calories: {target_calories:.0f} kcal
    - Protein: {protein_g:.0f}g
    - Carbohydrates: {carbs_g:.0f}g
    - Fat: {fat_g:.0f}g

    DIETARY RESTRICTIONS: {restrictions_text}

    Create 3 main meals and 1-2 snacks that hit these targets.

    Format each meal as:
    **[Meal Name] ([Time])**
    - Ingredients with portions
    - Macros: X cal, Xg protein, Xg carbs, Xg fat

    Include a daily total at the end."""

        try:
            response = self.simple_chat(user_prompt, system_prompt)
            return response

        except Exception as e:
            raise Exception(f"Error generating meal plan: {str(e)}")

    def generate_weekly_meal_plan(
        self,
        target_calories: float,
        protein_g: float,
        carbs_g: float,
        fat_g: float,
        dietary_restrictions: List[str] = None,
    ) -> str:
        """
        Generate 7-day meal plan with variety

        Args:
            target_calories: Daily target calories
            protein_g: Daily protein target
            carbs_g: Daily carbs target
            fat_g: Daily fat target
            dietary_restrictions: List of restrictions

        Returns:
            Structured 7-day meal plan text
        """
        system_prompt = """You are a certified nutritionist creating weekly meal plans.

Your meal plans should:
- Provide variety across the week
- Meet daily calorie and macro targets
- Respect dietary restrictions
- Include whole, nutritious foods
- Be realistic and practical
- Minimize food waste by reusing ingredients

CRITICAL: Follow this EXACT format for consistency:

**Day X - [Theme Name]**

**Breakfast (Time)**
- Ingredient 1 - amount
- Ingredient 2 - amount
**Macros:** X kcal, Xg protein, Xg carbs, Xg fat

**Snack 1 (Time)**
- Ingredient 1 - amount
**Macros:** X kcal, Xg protein, Xg carbs, Xg fat

**Lunch (Time)**
- Ingredient 1 - amount
- Ingredient 2 - amount
**Macros:** X kcal, Xg protein, Xg carbs, Xg fat

**Snack 2 (Time)**
- Ingredient 1 - amount
**Macros:** X kcal, Xg protein, Xg carbs, Xg fat

**Dinner (Time)**
- Ingredient 1 - amount
- Ingredient 2 - amount
**Macros:** X kcal, Xg protein, Xg carbs, Xg fat

**Daily Total:**
- **Calories:** X kcal
- **Protein:** Xg
- **Carbohydrates:** Xg
- **Fat:** Xg

---

Repeat for all 7 days. Use the EXACT formatting shown above."""

        restrictions_text = (
            ", ".join(dietary_restrictions) if dietary_restrictions else "None"
        )

        user_prompt = f"""Create a 7-day meal plan with these daily targets:

NUTRITIONAL TARGETS (PER DAY):
- Total Calories: {target_calories:.0f} kcal
- Protein: {protein_g:.0f}g
- Carbohydrates: {carbs_g:.0f}g
- Fat: {fat_g:.0f}g

DIETARY RESTRICTIONS: {restrictions_text}

REQUIREMENTS:
- 7 complete days
- 3 main meals + 1-2 snacks per day
- Vary meals across the week (don't repeat same meal)
- Reuse some ingredients to minimize waste
- Each meal should list ingredients with portions
- Include macro breakdown for each meal
- Include daily totals for each day

Make it practical, delicious, and varied!"""

        try:
            # Use higher token limit for weekly meal plans
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                max_tokens=4000,  # Increased for weekly plans
            )

            return response.choices[0].message.content

        except Exception as e:
            raise Exception(f"Error generating weekly meal plan: {str(e)}")


# Create singleton instance
llm_service = LLMService()

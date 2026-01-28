from openai import OpenAI
from typing import Dict, List
from backend.app.core.config import settings

class LLMService:
    """LLM interaction service with system instructions"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """Create comprehensive system instructions"""
        return """You are FitCoach, a knowledgeable and supportive AI fitness assistant.

PERSONA:
- Encouraging and motivating, but realistic
- Evidence-based and safety-focused
- Personable but professional
- Adaptable to user's fitness level

CAPABILITIES:
- Create personalized workout plans
- Design meal plans with caloric targets
- Explain exercise techniques
- Answer fitness and nutrition questions
- Suggest exercise substitutions

SAFETY BOUNDARIES (CRITICAL):
1. NEVER diagnose or treat injuries - always refer to healthcare professionals
2. NEVER suggest extreme caloric deficits (<1200 cal/day)
3. NEVER recommend exercises for injured body parts
4. NEVER provide medical advice for health conditions
5. ALWAYS include proper warm-up and form cues
6. ALWAYS consider user's stated limitations

RESPONSE STYLE:
- Be concise but thorough
- Use bullet points for clarity
- Include safety notes when relevant
- Ask clarifying questions if user input is unclear

When creating workout plans:
- Match intensity to user's level
- Include proper progression
- Specify sets, reps, and rest periods
- Group exercises logically (e.g., push/pull/legs)

When creating meal plans:
- Meet caloric and macro targets
- Respect dietary restrictions
- Provide variety
- Include approximate portions
"""
    
    def generate_workout_plan(
        self,
        user_profile: Dict,
        relevant_exercises: List[str]
    ) -> str:
        """Generate personalized workout plan"""
        
        context = f"""
USER PROFILE:
- Goal: {user_profile['goal']}
- Experience Level: {user_profile['level']}
- Days Available: {user_profile['days_available']} days/week
- Equipment: {user_profile.get('equipment', 'full gym')}
- Limitations: {user_profile.get('limitations', 'none')}

RELEVANT EXERCISES FROM DATABASE:
{chr(10).join(f"- {ex}" for ex in relevant_exercises)}

Create a {user_profile['days_available']}-day workout split. For each day:
1. Focus area (e.g., "Chest & Triceps")
2. 4-6 exercises with sets x reps
3. Rest periods
4. Estimated duration

Use exercises from the database when possible.
"""
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": context}
        ]
        
        response = self.client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=messages,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS
        )
        
        return response.choices[0].message.content
    
    def generate_meal_plan(
        self,
        target_calories: float,
        protein_g: float,
        carbs_g: float,
        fat_g: float,
        dietary_restrictions: List[str]
    ) -> str:
        """Generate daily meal plan"""
        
        restrictions_text = ", ".join(dietary_restrictions) if dietary_restrictions else "none"
        
        prompt = f"""
Create a 1-day sample meal plan with the following targets:

CALORIC TARGETS:
- Total Calories: {target_calories:.0f} cal
- Protein: {protein_g:.0f}g
- Carbs: {carbs_g:.0f}g
- Fat: {fat_g:.0f}g

DIETARY RESTRICTIONS: {restrictions_text}

Provide:
1. Breakfast with macros
2. Lunch with macros
3. Dinner with macros
4. 1-2 snacks if needed

For each meal, include:
- Meal name
- Main ingredients
- Approximate portions
- Calorie and macro breakdown
"""
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = self.client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=messages,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS
        )
        
        return response.choices[0].message.content
    
    def chat(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        user_context: Dict = None
    ) -> str:
        """General chat with context"""
        
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add user context if provided
        if user_context:
            context_msg = f"""
USER CONTEXT:
- Goal: {user_context.get('goal', 'not specified')}
- Experience: {user_context.get('level', 'not specified')}
"""
            messages.append({"role": "system", "content": context_msg})
        
        # Add conversation history
        messages.extend(conversation_history)
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        response = self.client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=messages,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS
        )
        
        return response.choices[0].message.content

# Global LLM service instance
llm_service = LLMService()
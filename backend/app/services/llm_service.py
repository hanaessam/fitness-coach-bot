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
    
    def simple_chat(self, user_message: str, system_prompt: Optional[str] = None) -> str:
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
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Add user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
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
                "persona": "FitCoach"
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
            response = self.simple_chat("Say 'Connection successful!' if you can read this.")
            
            return {
                "status": "connected",
                "model": self.model,
                "test_response": response[:100],  # First 100 chars
                "api_configured": True
            }
        
        except Exception as e:
            return {
                "status": "error",
                "model": self.model,
                "error": str(e),
                "api_configured": False
            }


# Create singleton instance
llm_service = LLMService()

import requests
from typing import Dict, List, Optional
import streamlit as st

class FitnessAPIClient:
    """Client for interacting with FastAPI backend"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def _handle_response(self, response: requests.Response) -> Dict:
        """Handle API response"""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = response.json().get('detail', str(e))
            st.error(f"API Error: {error_detail}")
            raise
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            raise
    
    def health_check(self) -> Dict:
        """Check API health"""
        response = self.session.get(f"{self.base_url}/health")
        return self._handle_response(response)
    
    def calculate_calories(self, profile: Dict) -> Dict:
        """Calculate caloric needs"""
        payload = {"profile": profile}
        response = self.session.post(
            f"{self.base_url}/calculate-calories",
            json=payload
        )
        return self._handle_response(response)
    
    def generate_workout(self, profile: Dict, focus_areas: List[str] = None) -> Dict:
        """Generate workout plan"""
        payload = {
            "profile": profile,
            "focus_areas": focus_areas
        }
        response = self.session.post(
            f"{self.base_url}/generate-workout",
            json=payload
        )
        return self._handle_response(response)
    
    def generate_meal_plan(
        self,
        target_calories: float,
        protein_g: float,
        carbs_g: float,
        fat_g: float,
        dietary_restrictions: List[str]
    ) -> Dict:
        """Generate meal plan"""
        payload = {
            "target_calories": target_calories,
            "protein_g": protein_g,
            "carbs_g": carbs_g,
            "fat_g": fat_g,
            "dietary_restrictions": dietary_restrictions
        }
        response = self.session.post(
            f"{self.base_url}/generate-meal-plan",
            json=payload
        )
        return self._handle_response(response)
    
    def chat(
        self,
        message: str,
        conversation_history: List[Dict],
        user_context: Optional[Dict] = None
    ) -> Dict:
        """Send chat message"""
        payload = {
            "message": message,
            "conversation_history": conversation_history,
            "user_context": user_context
        }
        response = self.session.post(
            f"{self.base_url}/chat",
            json=payload
        )
        return self._handle_response(response)
    
    def search_exercises(
        self,
        query: str,
        limit: int = 10,
        body_part: str = None,
        level: str = None
    ) -> Dict:
        """Search exercises"""
        params = {"query": query, "limit": limit}
        if body_part:
            params["body_part"] = body_part
        if level:
            params["level"] = level
        
        response = self.session.get(
            f"{self.base_url}/exercises/search",
            params=params
        )
        return self._handle_response(response)
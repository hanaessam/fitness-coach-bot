"""
Standardized API response models
"""
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime

class APIResponse(BaseModel):
    """Standard response wrapper for all API endpoints"""
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Human-readable message")
    data: Optional[Any] = Field(None, description="The actual response data")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Response timestamp"
    )

class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = Field(default=False)
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class HealthCheckData(BaseModel):
    """Health check data"""
    status: str
    version: str
    uptime_seconds: Optional[float] = None
    checks: Optional[Dict[str, bool]] = None

class CalorieCalculationData(BaseModel):
    """Complete calorie calculation breakdown"""
    # Basic metrics
    bmr: float = Field(..., description="Basal Metabolic Rate")
    tdee: float = Field(..., description="Total Daily Energy Expenditure")
    
    # Target calories
    target_calories: float = Field(..., description="Daily calorie target")
    deficit_surplus_calories: float = Field(..., description="Calorie deficit/surplus")
    deficit_surplus_percent: float = Field(..., description="Percentage change")
    
    # Macronutrients
    protein_g: float = Field(..., description="Daily protein target (grams)")
    carbs_g: float = Field(..., description="Daily carbs target (grams)")
    fat_g: float = Field(..., description="Daily fat target (grams)")
    
    # Recommendation
    recommendation: str = Field(..., description="Personalized guidance")
    
    class Config:
        json_schema_extra = {
            "example": {
                "bmr": 1446.25,
                "tdee": 2241.69,
                "target_calories": 1793.35,
                "deficit_surplus_calories": -448.34,
                "deficit_surplus_percent": -0.20,
                "protein_g": 157.2,
                "carbs_g": 179.3,
                "fat_g": 49.8,
                "recommendation": "Aim for 1793 calories/day for safe weight loss..."
            }
        }

class LLMTestData(BaseModel):
    """LLM connection test data"""
    status: str
    model: str
    test_response: Optional[str] = None
    error: Optional[str] = None
    api_configured: bool

class ChatData(BaseModel):
    """Chat response data"""
    response: str = Field(..., description="AI response")
    model_used: str = Field(..., description="Model that generated response")
    persona: Optional[str] = Field(None, description="AI persona used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "For beginners, I recommend starting with...",
                "model_used": "gpt-4o-mini",
                "persona": "FitCoach"
            }
        }

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., min_length=1, max_length=2000, description="User's message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What's a good beginner workout routine?"
            }
        }

class LLMTestData(BaseModel):
    """LLM connection test data"""
    status: str
    model: str
    test_response: Optional[str] = None
    error: Optional[str] = None
    api_configured: bool

class ChatData(BaseModel):
    """Chat response data"""
    response: str = Field(..., description="AI response")
    model_used: str = Field(..., description="Model that generated response")
    persona: Optional[str] = Field(None, description="AI persona used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "For beginners, I recommend starting with...",
                "model_used": "gpt-4o-mini",
                "persona": "FitCoach"
            }
        }

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., min_length=1, max_length=2000, description="User's message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What's a good beginner workout routine?"
            }
        }

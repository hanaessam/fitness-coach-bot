from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from enum import Enum

# Enums
class Sex(str, Enum):
    MALE = "male"
    FEMALE = "female"

class Goal(str, Enum):
    LOSE = "lose"
    GAIN = "gain"
    MAINTAIN = "maintain"

class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    VERY_ACTIVE = "very_active"
    EXTREME = "extreme"

class FitnessLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

# Request Models
class UserProfile(BaseModel):
    """User profile information"""
    name: Optional[str] = Field(None, description="User's name")
    age: int = Field(..., ge=15, le=100, description="Age in years")
    sex: Sex = Field(..., description="Biological sex")
    weight: float = Field(..., ge=30, le=300, description="Weight in kg")
    height: int = Field(..., ge=120, le=250, description="Height in cm")
    goal: Goal = Field(..., description="Fitness goal")
    days_available: int = Field(..., ge=1, le=7, description="Days available for training per week")
    activity_level: ActivityLevel = Field(default=ActivityLevel.MODERATE, description="Daily activity level")
    level: FitnessLevel = Field(default=FitnessLevel.BEGINNER, description="Fitness experience level")
    restrictions: List[str] = Field(default=[], description="Dietary restrictions")
    limitations: Optional[str] = Field(None, description="Injuries or physical limitations")
    equipment: Optional[str] = Field(default="full gym", description="Available equipment")

class CalorieCalculationRequest(BaseModel):
    """Request for calorie calculation"""
    profile: UserProfile

class WorkoutPlanRequest(BaseModel):
    """Request for workout plan generation"""
    profile: UserProfile
    focus_areas: Optional[List[str]] = Field(default=None, description="Specific body parts to focus on")

class MealPlanRequest(BaseModel):
    """Request for meal plan generation"""
    target_calories: float = Field(..., ge=1000, le=5000)
    protein_g: float = Field(..., ge=50, le=400)
    carbs_g: float = Field(..., ge=50, le=600)
    fat_g: float = Field(..., ge=20, le=200)
    dietary_restrictions: List[str] = Field(default=[])

class ChatRequest(BaseModel):
    """Chat message request"""
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_history: List[Dict[str, str]] = Field(default=[])
    user_context: Optional[Dict] = Field(default=None, description="User profile context")

# Response Models
class CalorieBreakdown(BaseModel):
    """Calorie calculation results"""
    bmr: float = Field(..., description="Basal Metabolic Rate")
    tdee: float = Field(..., description="Total Daily Energy Expenditure")
    target_calories: float = Field(..., description="Target daily calories")
    deficit_surplus_calories: float = Field(..., description="Calorie deficit or surplus")
    deficit_surplus_percent: float = Field(..., description="Percentage deficit or surplus")
    protein_g: float = Field(..., description="Daily protein target in grams")
    carbs_g: float = Field(..., description="Daily carbs target in grams")
    fat_g: float = Field(..., description="Daily fat target in grams")

class Exercise(BaseModel):
    """Exercise information"""
    title: str
    description: str
    type: str
    body_part: str
    equipment: str
    level: str

class WorkoutPlanResponse(BaseModel):
    """Workout plan response"""
    plan: str = Field(..., description="Generated workout plan text")
    exercises_used: List[Exercise] = Field(default=[], description="Exercises included in plan")

class MealPlanResponse(BaseModel):
    """Meal plan response"""
    plan: str = Field(..., description="Generated meal plan text")
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float

class ChatResponse(BaseModel):
    """Chat response"""
    response: str = Field(..., description="AI assistant response")
    context_used: bool = Field(default=False, description="Whether RAG context was used")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    vectorstore_loaded: bool

class ErrorResponse(BaseModel):
    """Error response"""
    detail: str
    error_code: Optional[str] = None
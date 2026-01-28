"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

# Enums for type safety
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

# Request model
class UserProfile(BaseModel):
    """User profile for calorie calculation"""
    age: int = Field(..., ge=15, le=100, description="Age in years")
    sex: Sex
    weight: float = Field(..., ge=30, le=300, description="Weight in kg")
    height: int = Field(..., ge=120, le=250, description="Height in cm")
    goal: Goal
    activity_level: ActivityLevel = Field(default=ActivityLevel.MODERATE, description="Daily activity level")
    
    class Config:
        json_schema_extra = {
            "example": {
                "age": 25,
                "sex": "female",
                "weight": 70,
                "height": 170,
                "goal": "lose",
                "activity_level": "moderate"
            }
        }

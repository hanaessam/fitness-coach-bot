"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List
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


class FitnessLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


# Request models
class UserProfile(BaseModel):
    """User profile for calorie calculation"""

    age: int = Field(..., ge=15, le=100, description="Age in years")
    sex: Sex
    weight: float = Field(..., ge=30, le=300, description="Weight in kg")
    height: int = Field(..., ge=120, le=250, description="Height in cm")
    goal: Goal
    activity_level: ActivityLevel = Field(
        default=ActivityLevel.MODERATE, description="Daily activity level"
    )
    level: FitnessLevel = Field(
        default=FitnessLevel.BEGINNER, description="Fitness experience level"
    )
    restrictions: List[str] = Field(default=[], description="Dietary restrictions")

    class Config:
        json_schema_extra = {
            "example": {
                "age": 25,
                "sex": "female",
                "weight": 70,
                "height": 170,
                "goal": "lose",
                "activity_level": "moderate",
                "level": "beginner",
                "restrictions": [],
            }
        }


class WorkoutPlanRequest(BaseModel):
    """Request for generating a workout plan"""

    profile: UserProfile
    days_per_week: int = Field(..., ge=1, le=7, description="Training days per week")
    focus_areas: Optional[List[str]] = Field(
        default=None,
        description="Specific body parts to emphasize (e.g., ['chest', 'legs'])",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "profile": {
                    "age": 25,
                    "sex": "female",
                    "weight": 70,
                    "height": 170,
                    "goal": "lose",
                    "activity_level": "moderate",
                    "level": "beginner",
                    "restrictions": [],
                },
                "days_per_week": 3,
                "focus_areas": ["chest", "legs"],
            }
        }


class MealPlanRequest(BaseModel):
    """Request for meal plan generation"""

    profile: UserProfile
    days: int = Field(default=1, ge=1, le=7, description="Number of days (1-7)")

    class Config:
        json_schema_extra = {
            "example": {
                "profile": {
                    "age": 25,
                    "sex": "female",
                    "weight": 70,
                    "height": 170,
                    "goal": "lose",
                    "activity_level": "moderate",
                    "level": "beginner",
                    "restrictions": [],
                },
                "days": 7,
            }
        }

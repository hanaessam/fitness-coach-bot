from typing import Dict
from backend.app.core.config import settings
from backend.app.models.schemas import Sex, Goal, ActivityLevel

class CalorieCalculator:
    """Calculate caloric needs with Chain-of-Thought reasoning"""
    
    @staticmethod
    def calculate_bmr(weight_kg: float, height_cm: float, age: int, sex: Sex) -> float:
        """
        Calculate Basal Metabolic Rate using Mifflin-St Jeor equation
        
        Chain-of-Thought:
        1. Base formula: 10*weight + 6.25*height - 5*age
        2. Add sex-specific adjustment
        """
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age
        
        if sex == Sex.MALE:
            bmr += 5
        else:
            bmr -= 161
        
        return round(bmr, 2)
    
    @staticmethod
    def calculate_tdee(bmr: float, activity_level: ActivityLevel) -> float:
        """Calculate Total Daily Energy Expenditure"""
        multipliers = {
            ActivityLevel.SEDENTARY: 1.2,
            ActivityLevel.LIGHT: 1.375,
            ActivityLevel.MODERATE: 1.55,
            ActivityLevel.VERY_ACTIVE: 1.725,
            ActivityLevel.EXTREME: 1.9
        }
        
        multiplier = multipliers[activity_level]
        tdee = bmr * multiplier
        
        return round(tdee, 2)
    
    @staticmethod
    def calculate_target_calories(tdee: float, goal: Goal) -> Dict[str, float]:
        """
        Calculate target calories based on goal with safety constraints
        
        Chain-of-Thought:
        1. Apply goal-specific multiplier
        2. Enforce safety limits
        3. Calculate deficit/surplus
        """
        if goal == Goal.LOSE:
            target = tdee * 0.80  # 20% deficit
            deficit_surplus = -0.20
        elif goal == Goal.GAIN:
            target = tdee * 1.15  # 15% surplus
            deficit_surplus = 0.15
        else:  # MAINTAIN
            target = tdee
            deficit_surplus = 0.0
        
        # Apply safety constraints
        target = max(settings.MIN_CALORIES, min(settings.MAX_CALORIES, target))
        
        return {
            'target_calories': round(target, 2),
            'tdee': tdee,
            'deficit_surplus_percent': deficit_surplus,
            'deficit_surplus_calories': round(target - tdee, 2)
        }
    
    @staticmethod
    def calculate_macros(target_calories: float, goal: Goal) -> Dict[str, float]:
        """Calculate macronutrient distribution"""
        if goal == Goal.LOSE:
            protein_percent = 0.35
            fat_percent = 0.25
            carb_percent = 0.40
        elif goal == Goal.GAIN:
            protein_percent = 0.30
            fat_percent = 0.25
            carb_percent = 0.45
        else:  # MAINTAIN
            protein_percent = 0.30
            fat_percent = 0.30
            carb_percent = 0.40
        
        return {
            'protein_g': round((target_calories * protein_percent) / 4, 1),
            'carbs_g': round((target_calories * carb_percent) / 4, 1),
            'fat_g': round((target_calories * fat_percent) / 9, 1)
        }
    
    @classmethod
    def calculate_full_breakdown(
        cls,
        weight_kg: float,
        height_cm: float,
        age: int,
        sex: Sex,
        activity_level: ActivityLevel,
        goal: Goal
    ) -> Dict[str, float]:
        """Calculate complete caloric breakdown"""
        bmr = cls.calculate_bmr(weight_kg, height_cm, age, sex)
        tdee = cls.calculate_tdee(bmr, activity_level)
        target = cls.calculate_target_calories(tdee, goal)
        macros = cls.calculate_macros(target['target_calories'], goal)
        
        return {
            'bmr': bmr,
            **target,
            **macros
        }
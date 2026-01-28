"""
Calorie Calculator Service with Chain-of-Thought Reasoning

This service encapsulates all calorie calculation logic using the
Mifflin-St Jeor equation, which is the most accurate for most people.
"""
from typing import Dict
from app.models import Sex, Goal, ActivityLevel

class CalorieCalculator:
    """
    Calculator for BMR, TDEE, and target calories
    
    Uses evidence-based formulas with clear reasoning steps
    """
    
    # Safety constraints
    MIN_CALORIES = 1200
    MAX_CALORIES = 4000
    MAX_DEFICIT_PERCENT = 0.25  # Maximum 25% calorie deficit
    
    @staticmethod
    def calculate_bmr(weight_kg: float, height_cm: float, age: int, sex: Sex) -> float:
        """
        Calculate Basal Metabolic Rate using Mifflin-St Jeor equation
        
        Chain-of-Thought:
        1. Start with base calculation: 10*weight + 6.25*height - 5*age
        2. Add sex-specific adjustment:
           - Men: +5 calories (higher muscle mass)
           - Women: -161 calories (lower muscle mass)
        
        Args:
            weight_kg: Weight in kilograms
            height_cm: Height in centimeters
            age: Age in years
            sex: Biological sex (male/female)
        
        Returns:
            BMR in calories per day
        
        Example:
            For a 25-year-old female, 70kg, 170cm:
            Base: 10*70 + 6.25*170 - 5*25 = 1537.5
            Female adjustment: -161
            BMR = 1376.5 calories/day
        """
        # Base calculation
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age
        
        # Sex-specific adjustment
        if sex == Sex.MALE:
            bmr += 5
        else:  # Female
            bmr -= 161
        
        return round(bmr, 2)
    
    @staticmethod
    def calculate_tdee(bmr: float, activity_level: ActivityLevel) -> float:
        """
        Calculate Total Daily Energy Expenditure
        
        Chain-of-Thought:
        1. BMR = calories burned at complete rest
        2. TDEE = BMR × activity multiplier
        3. Activity multipliers based on research:
           - Sedentary: BMR × 1.2 (desk job, no exercise)
           - Light: BMR × 1.375 (light exercise 1-3 days/week)
           - Moderate: BMR × 1.55 (moderate exercise 3-5 days/week)
           - Very Active: BMR × 1.725 (hard exercise 6-7 days/week)
           - Extreme: BMR × 1.9 (athlete-level training)
        
        Args:
            bmr: Basal Metabolic Rate
            activity_level: Activity level enum
        
        Returns:
            TDEE in calories per day
        
        Example:
            For BMR of 1376.5 and moderate activity:
            TDEE = 1376.5 × 1.55 = 2133.6 calories/day
        """
        # Research-based activity multipliers
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
        1. Determine goal-specific strategy:
           - Weight Loss: 20% deficit (safe rate: 0.5-1kg/week)
           - Muscle Gain: 15% surplus (optimal for lean mass)
           - Maintain: No change
        2. Apply safety constraints:
           - Minimum: 1200 cal/day (prevent malnutrition)
           - Maximum: 4000 cal/day (prevent excessive gain)
           - Max deficit: 25% (prevent muscle loss)
        3. Calculate deficit/surplus in calories
        
        Args:
            tdee: Total Daily Energy Expenditure
            goal: Weight goal (lose/gain/maintain)
        
        Returns:
            Dictionary with:
            - target_calories: Daily calorie target
            - tdee: Original TDEE
            - deficit_surplus_percent: Percentage change
            - deficit_surplus_calories: Absolute calorie change
        
        Example:
            For TDEE of 2133 and weight loss goal:
            Target = 2133 × 0.80 = 1706 calories
            Deficit = -427 calories/day = -20%
            Expected loss: ~0.5kg/week
        """
        if goal == Goal.LOSE:
            # 20% deficit for safe weight loss
            target = tdee * 0.80
            deficit_surplus_percent = -0.20
        elif goal == Goal.GAIN:
            # 15% surplus for lean muscle gain
            target = tdee * 1.15
            deficit_surplus_percent = 0.15
        else:  # MAINTAIN
            target = tdee
            deficit_surplus_percent = 0.0
        
        # Apply safety constraints
        target = max(CalorieCalculator.MIN_CALORIES, 
                    min(CalorieCalculator.MAX_CALORIES, target))
        
        # Calculate actual deficit/surplus
        deficit_surplus_calories = target - tdee
        actual_percent = deficit_surplus_calories / tdee if tdee > 0 else 0
        
        return {
            'target_calories': round(target, 2),
            'tdee': tdee,
            'deficit_surplus_percent': round(actual_percent, 3),
            'deficit_surplus_calories': round(deficit_surplus_calories, 2)
        }
    
    @staticmethod
    def calculate_macros(target_calories: float, goal: Goal) -> Dict[str, float]:
        """
        Calculate macronutrient distribution
        
        Chain-of-Thought:
        1. Macros affect body composition differently:
           - Protein: 4 cal/g, builds/preserves muscle
           - Carbs: 4 cal/g, provides energy
           - Fat: 9 cal/g, hormone production, satiety
        
        2. Goal-specific distributions:
           - Weight Loss: High protein (preserve muscle), moderate carbs
           - Muscle Gain: High carbs (energy), adequate protein
           - Maintain: Balanced distribution
        
        3. Calculate grams from percentages
        
        Args:
            target_calories: Daily calorie target
            goal: Weight goal
        
        Returns:
            Dictionary with protein_g, carbs_g, fat_g
        
        Example:
            For 1706 calories and weight loss:
            Protein (35%): 1706 × 0.35 / 4 = 149g
            Carbs (40%): 1706 × 0.40 / 4 = 171g
            Fat (25%): 1706 × 0.25 / 9 = 47g
        """
        if goal == Goal.LOSE:
            # Higher protein to preserve muscle during deficit
            protein_percent = 0.35
            carb_percent = 0.40
            fat_percent = 0.25
        elif goal == Goal.GAIN:
            # Higher carbs for energy during surplus
            protein_percent = 0.30
            carb_percent = 0.45
            fat_percent = 0.25
        else:  # MAINTAIN
            # Balanced distribution
            protein_percent = 0.30
            carb_percent = 0.40
            fat_percent = 0.30
        
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
        """
        Calculate complete nutritional breakdown
        
        This is the main method that orchestrates all calculations
        with full Chain-of-Thought reasoning.
        
        Chain-of-Thought Process:
        1. Calculate BMR (resting metabolism)
        2. Calculate TDEE (daily energy needs)
        3. Calculate target calories (based on goal)
        4. Calculate macro distribution (optimal ratios)
        5. Generate personalized recommendation
        
        Args:
            weight_kg: Weight in kilograms
            height_cm: Height in centimeters
            age: Age in years
            sex: Biological sex
            activity_level: Daily activity level
            goal: Weight management goal
        
        Returns:
            Complete nutritional breakdown dictionary
        """
        # Step 1: Calculate BMR
        bmr = cls.calculate_bmr(weight_kg, height_cm, age, sex)
        
        # Step 2: Calculate TDEE
        tdee = cls.calculate_tdee(bmr, activity_level)
        
        # Step 3: Calculate target calories
        target_data = cls.calculate_target_calories(tdee, goal)
        
        # Step 4: Calculate macros
        macros = cls.calculate_macros(target_data['target_calories'], goal)
        
        # Step 5: Generate recommendation
        recommendation = cls._generate_recommendation(
            target_data['target_calories'],
            target_data['deficit_surplus_calories'],
            goal
        )
        
        # Combine all results
        return {
            'bmr': bmr,
            **target_data,
            **macros,
            'recommendation': recommendation
        }
    
    @staticmethod
    def _generate_recommendation(
        target: float,
        deficit_surplus: float,
        goal: Goal
    ) -> str:
        """
        Generate personalized recommendation message
        
        Args:
            target: Target calories
            deficit_surplus: Calorie deficit or surplus
            goal: Weight goal
        
        Returns:
            Human-readable recommendation string
        """
        if goal == Goal.LOSE:
            weekly_loss = abs(deficit_surplus) * 7 / 7700  # 7700 cal ≈ 1kg fat
            return (
                f"Aim for {round(target)} calories/day for safe weight loss. "
                f"Expected loss: ~{round(weekly_loss, 1)}kg/week. "
                f"Focus on high protein to preserve muscle."
            )
        elif goal == Goal.GAIN:
            weekly_gain = deficit_surplus * 7 / 7700
            return (
                f"Aim for {round(target)} calories/day for muscle gain. "
                f"Expected gain: ~{round(weekly_gain, 1)}kg/week. "
                f"Focus on progressive overload in training."
            )
        else:  # MAINTAIN
            return (
                f"Aim for {round(target)} calories/day to maintain current weight. "
                f"Focus on consistent habits and performance."
            )


# Create singleton instance
calculator = CalorieCalculator()

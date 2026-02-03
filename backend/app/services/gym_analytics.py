"""
Gym Analytics Service
Analyzes gym member data to provide personalized benchmarks
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path

class GymAnalytics:
    """Analyzes gym member exercise data"""
    
    _instance = None  # Singleton instance
    
    def __init__(self, csv_path: str):
        """Load gym members dataset"""
        self.csv_path = Path(csv_path)
        
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Dataset not found: {csv_path}")
        
        self.df = pd.read_csv(csv_path)
        self.df.columns = self.df.columns.str.strip()
        
        print(f"✓ Loaded {len(self.df)} gym member records")
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance"""
        return cls._instance
    
    @classmethod
    def set_instance(cls, instance):
        """Set singleton instance"""
        cls._instance = instance
    
    def get_benchmark(
        self,
        age: int,
        gender: str,
        experience_level: int,
        workout_type: Optional[str] = None
    ) -> Dict:
        """Get performance benchmarks for similar users"""
        filtered = self.df.copy()
        
        # Age range (±10 years)
        filtered = filtered[
            (filtered['Age'] >= age - 10) & 
            (filtered['Age'] <= age + 10)
        ]
        
        # Gender
        gender_map = {'male': 'Male', 'female': 'Female'}
        if gender.lower() in gender_map:
            filtered = filtered[filtered['Gender'] == gender_map[gender.lower()]]
        
        # Experience level
        filtered = filtered[filtered['Experience_Level'] == experience_level]
        
        # Workout type (optional)
        if workout_type and 'Workout_Type' in filtered.columns:
            filtered = filtered[filtered['Workout_Type'] == workout_type]
        
        if len(filtered) == 0:
            return {
                "found": False,
                "message": "No similar users found"
            }
        
        # Calculate benchmarks
        return {
            "found": True,
            "sample_size": len(filtered),
            "avg_session_duration": round(filtered['Session_Duration (hours)'].mean(), 2),
            "avg_calories_burned": round(filtered['Calories_Burned'].mean(), 0),
            "avg_workout_frequency": round(filtered['Workout_Frequency (days/week)'].mean(), 1),
            "avg_bmi": round(filtered['BMI'].mean(), 1),
            "percentile_25_calories": round(filtered['Calories_Burned'].quantile(0.25), 0),
            "percentile_50_calories": round(filtered['Calories_Burned'].quantile(0.50), 0),
            "percentile_75_calories": round(filtered['Calories_Burned'].quantile(0.75), 0)
        }
    
    def recommend_workout_type(
        self,
        age: int,
        gender: str,
        goal: str,
        experience_level: int
    ) -> Dict:
        """Recommend workout type based on goals"""
        goal_mapping = {
            'lose': ['Cardio', 'HIIT'],
            'gain': ['Strength', 'HIIT'],
            'maintain': ['Cardio', 'Strength', 'Yoga']
        }
        
        preferred_types = goal_mapping.get(goal, ['Cardio', 'Strength'])
        recommendations = []
        
        for workout_type in preferred_types:
            benchmark = self.get_benchmark(age, gender, experience_level, workout_type)
            
            if benchmark['found']:
                recommendations.append({
                    "workout_type": workout_type,
                    "avg_calories_per_session": benchmark['avg_calories_burned'],
                    "recommended_duration": benchmark['avg_session_duration'],
                    "recommended_frequency": benchmark['avg_workout_frequency'],
                    "confidence": "high" if benchmark['sample_size'] > 5 else "medium"
                })
        
        return {
            "primary_goal": goal,
            "recommendations": sorted(
                recommendations,
                key=lambda x: x['avg_calories_per_session'],
                reverse=(goal == 'lose')
            )
        }
    
    def predict_calories(
        self,
        weight: float,
        session_duration: float,
        workout_type: str,
        experience_level: int
    ) -> Dict:
        """Predict calories burned"""
        filtered = self.df[
            (self.df['Workout_Type'] == workout_type) &
            (self.df['Experience_Level'] == experience_level)
        ]
        
        if len(filtered) == 0:
            # Fallback estimates
            base_calories = {
                'Cardio': 400,
                'Strength': 350,
                'HIIT': 600,
                'Yoga': 250
            }.get(workout_type, 400)
            
            predicted = base_calories * session_duration * (weight / 70)
            
            return {
                "predicted_calories": round(predicted, 0),
                "method": "fallback_estimate",
                "confidence": "low"
            }
        
        # Data-based prediction
        avg_calories_per_hour = filtered['Calories_Burned'].mean() / filtered['Session_Duration (hours)'].mean()
        avg_weight = filtered['Weight (kg)'].mean()
        
        weight_factor = weight / avg_weight
        predicted = avg_calories_per_hour * session_duration * weight_factor
        
        return {
            "predicted_calories": round(predicted, 0),
            "method": "data_based",
            "confidence": "high" if len(filtered) > 10 else "medium",
            "sample_size": len(filtered)
        }


def get_gym_analytics():
    """Get gym analytics instance (lazy loading)"""
    return GymAnalytics.get_instance()


def load_gym_analytics(csv_path: str = None) -> bool:
    """Load gym analytics service"""
    if csv_path is None:
        # Auto-detect dataset
        backend_dir = Path(__file__).parent.parent.parent
        project_root = backend_dir.parent
        
        possible_paths = [
            project_root / "data" / "raw" / "gym_members_exercise_tracking.csv",
            project_root / "data" / "raw" / "sample_gym_members.csv"
        ]
        
        for path in possible_paths:
            if path.exists():
                csv_path = str(path)
                break
    
    if csv_path:
        try:
            analytics = GymAnalytics(csv_path)
            GymAnalytics.set_instance(analytics)
            return True
        except Exception as e:
            print(f"Error loading gym analytics: {e}")
            return False
    else:
        print("No gym analytics dataset found")
        return False

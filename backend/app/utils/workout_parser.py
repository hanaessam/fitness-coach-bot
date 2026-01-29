"""
Workout plan parser
Converts LLM text output into structured JSON
"""

import re
from typing import List, Dict


class WorkoutParser:
    """Parse workout plan text into structured format"""

    @staticmethod
    def parse_workout_plan(plan_text: str) -> Dict:
        """
        Parse workout plan text into structured format

        Args:
            plan_text: Raw workout plan from LLM

        Returns:
            Structured workout plan dictionary
        """
        lines = plan_text.split("\n")

        # Extract overview
        overview = WorkoutParser._extract_overview(lines)

        # Extract days
        days = WorkoutParser._extract_days(plan_text)

        # Extract safety notes
        safety_notes = WorkoutParser._extract_safety_notes(lines)

        return {
            "overview": overview,
            "days": days,
            "safety_notes": safety_notes,
            "total_days": len(days),
        }

    @staticmethod
    def _extract_overview(lines: List[str]) -> str:
        """Extract plan overview"""
        overview_lines = []
        in_overview = False

        for line in lines:
            if "Plan Overview" in line or "Overview" in line:
                in_overview = True
                continue

            if in_overview:
                if line.startswith("**Day") or line.startswith("###"):
                    break
                if line.strip():
                    overview_lines.append(line.strip())

        return " ".join(overview_lines) if overview_lines else "Custom workout plan"

    @staticmethod
    def _extract_days(plan_text: str) -> List[Dict]:
        """Extract individual workout days"""
        days = []

        # Split by day markers
        day_pattern = r"\*\*Day (\d+):\s*([^*]+)\*\*"
        day_matches = list(re.finditer(day_pattern, plan_text))

        for i, match in enumerate(day_matches):
            day_num = int(match.group(1))
            focus = match.group(2).strip()

            # Get text for this day (until next day or end)
            start_pos = match.end()
            end_pos = (
                day_matches[i + 1].start()
                if i + 1 < len(day_matches)
                else len(plan_text)
            )
            day_text = plan_text[start_pos:end_pos]

            # Extract exercises
            exercises = WorkoutParser._extract_exercises(day_text)

            # Extract duration
            duration = WorkoutParser._extract_duration(day_text)

            # Extract notes for this day
            notes = WorkoutParser._extract_day_notes(day_text)

            days.append(
                {
                    "day": day_num,
                    "focus": focus,
                    "exercises": exercises,
                    "duration": duration,
                    "notes": notes,
                }
            )

        return days

    @staticmethod
    def _extract_exercises(day_text: str) -> List[Dict]:
        """Extract exercises from day text"""
        exercises = []

        # Pattern: "1. Exercise Name - 3x10, Rest: 90 seconds"
        exercise_pattern = (
            r"\d+\.\s*\*\*([^*]+)\*\*\s*-\s*(\d+x\d+(?:-\d+)?),\s*Rest:\s*([^*\n]+)"
        )

        matches = re.finditer(exercise_pattern, day_text)

        for match in matches:
            exercises.append(
                {
                    "name": match.group(1).strip(),
                    "sets_reps": match.group(2).strip(),
                    "rest": match.group(3).strip(),
                }
            )

        return exercises

    @staticmethod
    def _extract_duration(day_text: str) -> str:
        """Extract estimated duration"""
        duration_match = re.search(r"Estimated Duration:\s*([^\n]+)", day_text)
        return duration_match.group(1).strip() if duration_match else "45-60 minutes"

    @staticmethod
    def _extract_day_notes(day_text: str) -> str:
        """Extract notes specific to this day"""
        notes = []

        # Look for warm-up, cool-down
        warmup_match = re.search(r"Warm-up:\s*\n\s*-\s*([^\n]+)", day_text)
        if warmup_match:
            notes.append(f"Warm-up: {warmup_match.group(1).strip()}")

        cooldown_match = re.search(r"Cool-down:\s*\n\s*-\s*([^\n]+)", day_text)
        if cooldown_match:
            notes.append(f"Cool-down: {cooldown_match.group(1).strip()}")

        return " | ".join(notes) if notes else ""

    @staticmethod
    def _extract_safety_notes(lines: List[str]) -> List[str]:
        """Extract safety notes"""
        safety_notes = []
        in_safety = False

        for line in lines:
            if "Safety Notes" in line or "Important" in line:
                in_safety = True
                continue

            if in_safety and line.strip().startswith("-"):
                note = line.strip().lstrip("- ").strip()
                if note:
                    safety_notes.append(note)

        return safety_notes

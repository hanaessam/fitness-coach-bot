"""
Meal plan parser - handles various LLM output formats
"""

import re
from typing import List, Dict


class MealParser:
    """Parse meal plan text into structured format"""

    @staticmethod
    def parse_meal_plan(meal_text: str) -> Dict:
        """Parse meal plan text - supports both 1-day and 7-day formats"""

        # Check if it's a 7-day plan
        if re.search(r"Day\s+\d+", meal_text, re.IGNORECASE):
            return MealParser._parse_weekly_plan(meal_text)
        else:
            return MealParser._parse_single_day(meal_text)

    @staticmethod
    def _parse_single_day(meal_text: str) -> Dict:
        """Parse single day meal plan"""
        meals = MealParser._extract_meals_from_text(meal_text)
        daily_totals = MealParser._extract_daily_totals(meal_text)

        return {
            "type": "single_day",
            "meals": meals,
            "daily_totals": daily_totals,
            "total_meals": len(meals),
        }

    @staticmethod
    def _parse_weekly_plan(meal_text: str) -> Dict:
        """Parse 7-day meal plan"""
        days = []

        # Split by day markers - more flexible pattern
        day_pattern = r"(?:###\s*)?\*\*Day\s+(\d+)(?:\s*-\s*(.+?))?\*\*"

        # Find all day markers
        day_matches = list(re.finditer(day_pattern, meal_text, re.IGNORECASE))

        for i, day_match in enumerate(day_matches):
            day_num = int(day_match.group(1))
            day_name = (
                day_match.group(2).strip() if day_match.group(2) else f"Day {day_num}"
            )

            # Get content from this day to the next day (or end of text)
            start_pos = day_match.end()
            if i + 1 < len(day_matches):
                end_pos = day_matches[i + 1].start()
            else:
                end_pos = len(meal_text)

            day_content = meal_text[start_pos:end_pos]

            meals = MealParser._extract_meals_from_text(day_content)
            daily_totals = MealParser._extract_daily_totals(day_content)

            days.append(
                {
                    "day": day_num,
                    "name": day_name,
                    "meals": meals,
                    "daily_totals": daily_totals,
                }
            )

        # If no days were parsed but we have content, try to parse as single sections
        if not days and meal_text.strip():
            # Fall back to simple day detection
            day_sections = re.split(r"---+", meal_text)
            for i, section in enumerate(day_sections, 1):
                if section.strip():
                    meals = MealParser._extract_meals_from_text(section)
                    daily_totals = MealParser._extract_daily_totals(section)
                    if meals or any(daily_totals.values()):
                        days.append(
                            {
                                "day": i,
                                "name": f"Day {i}",
                                "meals": meals,
                                "daily_totals": daily_totals,
                            }
                        )

        # Calculate weekly totals
        weekly_totals = {
            "calories": sum(d["daily_totals"]["calories"] for d in days),
            "protein_g": sum(d["daily_totals"]["protein_g"] for d in days),
            "carbs_g": sum(d["daily_totals"]["carbs_g"] for d in days),
            "fat_g": sum(d["daily_totals"]["fat_g"] for d in days),
        }

        return {
            "type": "weekly",
            "days": days,
            "weekly_totals": weekly_totals,
            "total_days": len(days),
        }

    @staticmethod
    def _extract_meals_from_text(text: str) -> List[Dict]:
        """Extract meals from text section"""
        meals = []

        # Look for meal headers: **Breakfast (8:00 AM)** or **Snack 1 (10:30 AM)**
        meal_pattern = r"\*\*([^*]+?)\s*\(([^)]+)\)\*\*"
        meal_matches = re.finditer(meal_pattern, text)

        # Convert to list to process sequentially
        meal_list = list(meal_matches)

        for i, meal_match in enumerate(meal_list):
            meal_name = meal_match.group(1).strip()
            meal_time = meal_match.group(2).strip()

            # Get text from this meal to the next meal (or end of text)
            start_pos = meal_match.end()
            if i + 1 < len(meal_list):
                end_pos = meal_list[i + 1].start()
            else:
                end_pos = len(text)

            meal_section = text[start_pos:end_pos]

            # Skip if this is a Daily Total section
            if "Daily Total" in meal_name or "Weekly Total" in meal_name:
                continue

            # Extract ingredients (lines starting with -)
            ingredients = []
            ingredient_lines = re.findall(r"-\s*([^\n]+)", meal_section)

            for line in ingredient_lines:
                # Skip macro lines
                if "Macros:" in line or "kcal" in line:
                    continue

                # Try to parse "ingredient - amount" format
                if " - " in line:
                    parts = line.split(" - ", 1)
                    name = parts[0].strip()
                    amount = parts[1].strip()
                else:
                    # Try to extract amount in parentheses
                    amount_match = re.search(r"\(([^)]+)\)", line)
                    if amount_match:
                        name = line[: amount_match.start()].strip()
                        amount = amount_match.group(1).strip()
                    else:
                        name = line.strip()
                        amount = ""

                if name:  # Only add if we have a name
                    ingredients.append({"name": name, "amount": amount})

            # Extract macros
            macros = MealParser._extract_macros_from_section(meal_section)

            # Add meal if we have either ingredients or macros
            if ingredients or macros["calories"] > 0:
                meals.append(
                    {
                        "name": meal_name,
                        "time": meal_time,
                        "ingredients": ingredients,
                        "macros": macros,
                    }
                )

        return meals

    @staticmethod
    def _extract_macros_from_section(section: str) -> Dict:
        """Extract macros from a section"""
        macros = {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}

        # Multiple patterns to handle different formats
        patterns = [
            # **Macros:** 623 kcal, 42g protein, 36g carbs, 39g fat
            r"\*\*Macros:?\*\*\s*(\d+)\s*kcal,\s*(\d+)g\s*protein,\s*(\d+)g\s*carbs?,\s*(\d+)g\s*fat",
            # Macros: 623 kcal, 42g protein, 36g carbs, 39g fat (without bold)
            r"Macros:?\s*(\d+)\s*kcal,\s*(\d+)g\s*protein,\s*(\d+)g\s*carbs?,\s*(\d+)g\s*fat",
            # 623 cal, 42g protein, 36g carbs, 39g fat
            r"(\d+)\s*(?:cal|kcal),\s*(\d+)g\s*protein,\s*(\d+)g\s*carbs?,\s*(\d+)g\s*fat",
        ]

        for pattern in patterns:
            macros_match = re.search(pattern, section, re.IGNORECASE)
            if macros_match:
                macros["calories"] = int(macros_match.group(1))
                macros["protein_g"] = int(macros_match.group(2))
                macros["carbs_g"] = int(macros_match.group(3))
                macros["fat_g"] = int(macros_match.group(4))
                break

        return macros

    @staticmethod
    def _extract_daily_totals(text: str) -> Dict:
        """Extract daily totals"""
        totals = {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}

        # Look for Daily Total section - more flexible patterns
        patterns = [
            r"\*\*Daily Total:?\*\*(.*?)(?:---|$)",
            r"Daily Total:?\*?(.*?)(?:---|$)",
            r"Daily Total:?(.*?)(?:---|$)",
        ]

        daily_section = ""
        for pattern in patterns:
            daily_match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if daily_match:
                daily_section = daily_match.group(1)
                break

        if daily_section:
            # Extract individual values with multiple patterns
            cal_patterns = [
                r"\*\*Calories:?\*\*\s*(\d+)\s*kcal",
                r"Calories:?\s*(\d+)\s*kcal",
                r"(\d+)\s*kcal",
            ]
            for pattern in cal_patterns:
                cal_match = re.search(pattern, daily_section, re.IGNORECASE)
                if cal_match:
                    totals["calories"] = int(cal_match.group(1))
                    break

            protein_patterns = [r"\*\*Protein:?\*\*\s*(\d+)g", r"Protein:?\s*(\d+)g"]
            for pattern in protein_patterns:
                protein_match = re.search(pattern, daily_section, re.IGNORECASE)
                if protein_match:
                    totals["protein_g"] = int(protein_match.group(1))
                    break

            carbs_patterns = [
                r"\*\*Carbohydrate?s?:?\*\*\s*(\d+)g",
                r"Carbohydrate?s?:?\s*(\d+)g",
            ]
            for pattern in carbs_patterns:
                carbs_match = re.search(pattern, daily_section, re.IGNORECASE)
                if carbs_match:
                    totals["carbs_g"] = int(carbs_match.group(1))
                    break

            fat_patterns = [r"\*\*Fat:?\*\*\s*(\d+)g", r"Fat:?\s*(\d+)g"]
            for pattern in fat_patterns:
                fat_match = re.search(pattern, daily_section, re.IGNORECASE)
                if fat_match:
                    totals["fat_g"] = int(fat_match.group(1))
                    break

        return totals

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

# Source: ACSM, Eric Helms' Muscle & Strength Pyramid
GOAL_ADJUSTMENTS = {
    "lose": -500,
    "aggressive_lose": -750,
    "maintain": 0,
    "recomp": 0,
    "lean_bulk": 300,
    "bulk": 500,
}

SAFETY_FLOOR = 1200

# BMI thresholds per WHO classification
BMI_UNDERWEIGHT = 18.5
BMI_NORMAL_UPPER = 24.9


def calculate_bmi(weight_kg, height_cm):
    # BMI = weight(kg) / height(m)^2
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 2)


def calculate_bmr(weight_kg, height_cm, age, sex):
    # Mifflin-St Jeor equation (Academy of Nutrition and Dietetics, 2005)
    # Male:   (10 x weight_kg) + (6.25 x height_cm) - (5 x age) + 5
    # Female: (10 x weight_kg) + (6.25 x height_cm) - (5 x age) - 161
    bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
    if sex == "male":
        bmr += 5
    elif sex == "female":
        bmr -= 161
    else:
        raise ValueError(f"Invalid sex: {sex}. Must be 'male' or 'female'.")
    return round(bmr, 2)


def calculate_tdee(bmr, activity_level):
    # TDEE = BMR x activity multiplier (Harris-Benedict activity factors)
    if activity_level not in ACTIVITY_MULTIPLIERS:
        raise ValueError(
            f"Invalid activity level: {activity_level}. "
            f"Must be one of {list(ACTIVITY_MULTIPLIERS.keys())}."
        )
    return round(bmr * ACTIVITY_MULTIPLIERS[activity_level], 2)


def calculate_calorie_target(weight_kg, height_cm, age, sex, activity_level, goal):
    # Returns dict with: bmr, tdee, bmi, target_calories, goal, warning
    if goal not in GOAL_ADJUSTMENTS:
        raise ValueError(
            f"Invalid goal: {goal}. "
            f"Must be one of {list(GOAL_ADJUSTMENTS.keys())}."
        )

    bmi = calculate_bmi(weight_kg, height_cm)
    bmr = calculate_bmr(weight_kg, height_cm, age, sex)
    tdee = calculate_tdee(bmr, activity_level)
    target = round(tdee + GOAL_ADJUSTMENTS[goal], 2)

    warnings = []

    # Aggressive deficit safety: block if BMI is normal or underweight
    if goal == "aggressive_lose" and bmi <= BMI_NORMAL_UPPER:
        warnings.append(
            f"Your BMI is {bmi}, which is within or below the normal range. "
            f"An aggressive caloric deficit is not recommended and may lead to "
            f"disordered eating patterns or nutrient deficiencies. "
            f"Please consider the standard 'lose' goal instead, and consult "
            f"a healthcare professional if you are struggling with body image."
        )
        # Override to standard deficit for safety
        target = round(tdee + GOAL_ADJUSTMENTS["lose"], 2)
        goal = "lose"

    # Underweight warning for any deficit goal
    if bmi < BMI_UNDERWEIGHT and goal in ("lose", "aggressive_lose"):
        warnings.append(
            f"Your BMI is {bmi}, which is classified as underweight. "
            f"A caloric deficit is not recommended. If you are experiencing "
            f"pressure to lose weight or concerns about your body, please "
            f"reach out to a healthcare professional or contact the National "
            f"Alliance for Eating Disorders helpline at 1-866-662-1235."
        )
        # Override to maintenance for safety
        target = round(tdee, 2)
        goal = "maintain"

    # General safety floor check
    if target < SAFETY_FLOOR:
        warnings.append(
            f"Calculated target of {target} kcal/day is below the safety "
            f"floor of {SAFETY_FLOOR} kcal/day. This may be unsafe and could "
            f"contribute to disordered eating. Please consult a healthcare "
            f"professional before proceeding."
        )

    warning = " | ".join(warnings) if warnings else None

    return {
        "bmr": bmr,
        "tdee": tdee,
        "bmi": bmi,
        "target_calories": target,
        "goal": goal,
        "warning": warning,
    }
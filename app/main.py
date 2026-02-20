import streamlit as st
import requests

API_URL = "http://localhost:8000/generate-plan"

# --- Mapping display labels to API values ---

GOAL_MAP = {
    "Lose Weight": "lose",
    "Gain Weight": "lean_bulk",
    "Maintain": "maintain",
    "Bulk": "bulk",
}

ACTIVITY_MAP = {
    "Sedentary": "sedentary",
    "Lightly Active": "light",
    "Moderately Active": "moderate",
    "Active": "active",
    "Very Active": "very_active",
}

# --- Page config ---

st.set_page_config(page_title="FitBot", page_icon="dumbbell", layout="centered")
st.title("FitBot — Your Personal Fitness Coach")

# --- Sidebar form ---

with st.sidebar:
    st.header("Your Profile")

    weight_kg = st.number_input("Weight (kg)", min_value=30.0, max_value=300.0, value=70.0, step=0.5)
    height_cm = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=170.0, step=0.5)
    age = st.number_input("Age", min_value=13, max_value=120, value=25, step=1)
    sex = st.selectbox("Sex", ["Male", "Female"])
    goal = st.selectbox("Fitness Goal", list(GOAL_MAP.keys()))
    activity_level = st.selectbox("Activity Level", list(ACTIVITY_MAP.keys()))

    dietary_restrictions = st.multiselect(
        "Dietary Restrictions",
        ["Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Halal", "None"],
        default=["None"],
    )

    plan_duration = st.radio("Plan Duration", ["Daily", "Weekly"], index=1)

    generate_button = st.button("Generate My Plan")

# --- Main area ---

if generate_button:
    # Clean up dietary restrictions
    restrictions = [r.lower() for r in dietary_restrictions if r != "None"]

    payload = {
        "weight_kg": weight_kg,
        "height_cm": height_cm,
        "age": age,
        "sex": sex.lower(),
        "goal": GOAL_MAP[goal],
        "activity_level": ACTIVITY_MAP[activity_level],
        "dietary_restrictions": restrictions,
        "plan_duration": plan_duration.lower(),
    }

    with st.spinner("Generating your personalized plan..."):
        try:
            response = requests.post(API_URL, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the API. Make sure the FastAPI server is running.")
            st.stop()
        except requests.exceptions.HTTPError as e:
            st.error(f"API error: {e.response.text}")
            st.stop()
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            st.stop()

    # Calorie summary card
    calories = data.get("calories", {})
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("BMR", f"{calories.get('bmr', 0):.0f} kcal")
    col2.metric("TDEE", f"{calories.get('tdee', 0):.0f} kcal")
    col3.metric("Target", f"{calories.get('target', 0):.0f} kcal")
    col4.metric("BMI", f"{calories.get('bmi', 0):.1f}")

    # Warning display
    warning = data.get("warning")
    if warning:
        st.warning(warning)

    # Plan display
    st.divider()
    st.markdown(data.get("plan", "No plan returned."))
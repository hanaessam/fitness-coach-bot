import streamlit as st
import requests

API_URL = "http://localhost:8000"

GOAL_MAP = {
    "Lose Weight": "lose",
    "Aggressive Fat Loss": "aggressive_lose",
    "Maintain": "maintain",
    "Body Recomposition": "recomp",
    "Lean Bulk": "lean_bulk",
    "Bulk": "bulk",
}

ACTIVITY_MAP = {
    "Sedentary": "sedentary",
    "Lightly Active": "light",
    "Moderately Active": "moderate",
    "Active": "active",
    "Very Active": "very_active",
}

st.set_page_config(page_title="FitBot", page_icon="dumbbell", layout="centered")


# --- Session state initialization ---

def init_session_state():
    if "plan_generated" not in st.session_state:
        st.session_state.plan_generated = False
    if "plan_data" not in st.session_state:
        st.session_state.plan_data = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "onboarding_done" not in st.session_state:
        st.session_state.onboarding_done = False

init_session_state()


# --- Onboarding ---

def show_onboarding():
    st.title("Welcome to FitBot")
    st.markdown(
        "Your personal AI-powered fitness and nutrition coach. "
        "FitBot creates customized workout and meal plans based on your "
        "body metrics, goals, and dietary preferences."
    )

    st.subheader("How It Works")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Step 1**")
        st.markdown("Enter your body metrics and fitness goals in the sidebar.")
    with col2:
        st.markdown("**Step 2**")
        st.markdown("FitBot calculates your calories and searches its exercise and nutrition database.")
    with col3:
        st.markdown("**Step 3**")
        st.markdown("Get a personalized plan and chat with FitBot to refine it.")

    st.subheader("What You Get")
    st.markdown(
        "- A calorie summary based on the Mifflin-St Jeor equation\n"
        "- A workout plan tailored to your fitness level\n"
        "- A meal plan that respects your dietary restrictions\n"
        "- A chat interface to ask follow-up questions about your plan"
    )

    st.subheader("Safety First")
    st.markdown(
        "FitBot is not a doctor. It will never diagnose injuries or medical conditions. "
        "It enforces a minimum calorie floor of 1200 kcal/day and will always recommend "
        "consulting a healthcare professional before starting a new program."
    )

    if st.button("Get Started"):
        st.session_state.onboarding_done = True
        st.rerun()


# --- Sidebar ---

def show_sidebar():
    with st.sidebar:
        st.header("Your Profile")

        weight_kg = st.number_input(
            "Weight (kg)", min_value=30.0, max_value=300.0, value=70.0, step=0.5
        )
        height_cm = st.number_input(
            "Height (cm)", min_value=100.0, max_value=250.0, value=170.0, step=0.5
        )
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

        st.divider()
        if st.button("Show Tutorial"):
            st.session_state.onboarding_done = False
            st.session_state.plan_generated = False
            st.session_state.chat_history = []
            st.rerun()

        return {
            "weight_kg": weight_kg,
            "height_cm": height_cm,
            "age": age,
            "sex": sex,
            "goal": goal,
            "activity_level": activity_level,
            "dietary_restrictions": dietary_restrictions,
            "plan_duration": plan_duration,
            "generate_button": generate_button,
        }


# --- Plan generation ---

def generate_plan(form_data):
    restrictions = [r.lower() for r in form_data["dietary_restrictions"] if r != "None"]

    payload = {
        "weight_kg": form_data["weight_kg"],
        "height_cm": form_data["height_cm"],
        "age": form_data["age"],
        "sex": form_data["sex"].lower(),
        "goal": GOAL_MAP[form_data["goal"]],
        "activity_level": ACTIVITY_MAP[form_data["activity_level"]],
        "dietary_restrictions": restrictions,
        "plan_duration": form_data["plan_duration"].lower(),
    }

    with st.spinner("Generating your personalized plan..."):
        try:
            response = requests.post(f"{API_URL}/generate-plan", json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            st.session_state.plan_data = data
            st.session_state.plan_generated = True
            st.session_state.chat_history = []
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the API. Make sure the FastAPI server is running.")
        except requests.exceptions.HTTPError as e:
            st.error(f"API error: {e.response.text}")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")


# --- Plan display ---

def show_plan():
    data = st.session_state.plan_data
    if not data:
        return

    st.title("FitBot — Your Personal Fitness Coach")

    # Calorie summary
    calories = data.get("calories", {})
    st.subheader("Calorie Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("BMR", f"{calories.get('bmr', 0):.0f} kcal")
    col2.metric("TDEE", f"{calories.get('tdee', 0):.0f} kcal")
    col3.metric("Target", f"{calories.get('target', 0):.0f} kcal")
    col4.metric("BMI", f"{calories.get('bmi', 0):.1f}")

    # Warning
    warning = data.get("warning")
    if warning:
        st.warning(warning)

    # Tabbed plan sections
    st.divider()
    plan_text = data.get("plan", "")

    tab_workout, tab_meal, tab_full = st.tabs(["Workout Plan", "Meal Plan", "Full Plan"])

    with tab_workout:
        # Extract workout section if possible
        if "## WORKOUT PLAN" in plan_text and "## MEAL PLAN" in plan_text:
            workout_section = plan_text.split("## WORKOUT PLAN")[1].split("## MEAL PLAN")[0]
            st.markdown(workout_section)
        else:
            st.markdown("Workout plan section not found. See the Full Plan tab.")

    with tab_meal:
        # Extract meal section if possible
        if "## MEAL PLAN" in plan_text:
            meal_section = plan_text.split("## MEAL PLAN")[1]
            st.markdown(meal_section)
        else:
            st.markdown("Meal plan section not found. See the Full Plan tab.")

    with tab_full:
        st.markdown(plan_text)


# --- Chat interface ---

def show_chat():
    st.divider()
    st.subheader("Chat with FitBot")
    st.caption("Ask follow-up questions about your plan, request substitutions, or get more details.")

    # Display chat history
    for message in st.session_state.chat_history:
        role = message["role"]
        content = message["content"]
        with st.chat_message(role):
            st.markdown(content)

    # Chat input
    user_input = st.chat_input("Ask FitBot about your plan...")
    if user_input:
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Call chat endpoint
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    payload = {
                        "message": user_input,
                        "plan_context": st.session_state.plan_data.get("plan", ""),
                        "chat_history": st.session_state.chat_history[:-1],
                    }
                    response = requests.post(
                        f"{API_URL}/chat", json=payload, timeout=60
                    )
                    response.raise_for_status()
                    reply = response.json().get("reply", "Sorry, I could not generate a response.")
                except Exception as e:
                    reply = f"Error: {str(e)}"

                st.markdown(reply)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})


# --- Main app flow ---

if not st.session_state.onboarding_done:
    show_onboarding()
else:
    form_data = show_sidebar()
    if form_data["generate_button"]:
        generate_plan(form_data)
    if st.session_state.plan_generated:
        show_plan()
        show_chat()
    else:
        st.title("FitBot — Your Personal Fitness Coach")
        st.info("Fill in your profile in the sidebar and click Generate My Plan to get started.")
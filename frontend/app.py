import streamlit as st
import sys
from pathlib import Path

# Add frontend to path
frontend_path = Path(__file__).parent
sys.path.insert(0, str(frontend_path))

from utils.api_client import FitnessAPIClient
from components.dashboard import render_dashboard
from components.workout import render_workout_plan
from components.meal import render_meal_plan
from components.chat import render_chat

# Page config
st.set_page_config(
    page_title="FitCoach - AI Fitness Assistant",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF4B4B;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        background-color: #FF4B4B;
        color: white;
        font-weight: 600;
        border-radius: 0.5rem;
        padding: 0.5rem 2rem;
    }
    .stButton>button:hover {
        background-color: #FF3333;
    }
</style>
""", unsafe_allow_html=True)

# Initialize API client
@st.cache_resource
def get_api_client():
    """Get API client (cached)"""
    return FitnessAPIClient()

def initialize_session_state():
    """Initialize session state variables"""
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = {}
    if 'caloric_data' not in st.session_state:
        st.session_state.caloric_data = None
    if 'workout_plan' not in st.session_state:
        st.session_state.workout_plan = None
    if 'meal_plan' not in st.session_state:
        st.session_state.meal_plan = None
    if 'exercises_used' not in st.session_state:
        st.session_state.exercises_used = []

def render_sidebar(api_client):
    """Render sidebar with user profile form"""
    
    with st.sidebar:
        st.markdown("### 👤 Your Profile")
        
        # Basic info
        name = st.text_input("Name", value=st.session_state.user_profile.get('name', ''))
        age = st.number_input("Age", min_value=15, max_value=100,
                             value=st.session_state.user_profile.get('age', 25))
        sex = st.selectbox("Sex", ["male", "female"],
                          index=0 if st.session_state.user_profile.get('sex', 'male') == 'male' else 1)
        
        col1, col2 = st.columns(2)
        with col1:
            weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0,
                                    value=st.session_state.user_profile.get('weight', 70.0),
                                    step=0.5)
        with col2:
            height = st.number_input("Height (cm)", min_value=120, max_value=220,
                                    value=st.session_state.user_profile.get('height', 170))
        
        # Fitness info
        st.markdown("---")
        goal = st.selectbox("Goal", ["lose", "gain", "maintain"],
                           format_func=lambda x: x.title(),
                           index=["lose", "gain", "maintain"].index(
                               st.session_state.user_profile.get('goal', 'maintain')))
        
        days_available = st.slider("Days Available to Train", 1, 7,
                                   st.session_state.user_profile.get('days_available', 3))
        
        activity_level = st.selectbox(
            "Activity Level",
            ["sedentary", "light", "moderate", "very_active", "extreme"],
            format_func=lambda x: x.replace('_', ' ').title(),
            index=2
        )
        
        level = st.selectbox("Experience Level",
                            ["beginner", "intermediate", "advanced"],
                            format_func=lambda x: x.title(),
                            index=0)
        
        # Dietary restrictions
        st.markdown("---")
        restrictions = st.multiselect(
            "Dietary Restrictions",
            ["Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Nut Allergy", "None"],
            default=st.session_state.user_profile.get('restrictions', ["None"])
        )
        
        # Limitations
        limitations = st.text_area("Injuries or Limitations (optional)",
                                   value=st.session_state.user_profile.get('limitations', ''))
        
        # Save profile button
        if st.button("💾 Save Profile", use_container_width=True):
            profile = {
                'name': name,
                'age': age,
                'sex': sex,
                'weight': weight,
                'height': height,
                'goal': goal,
                'days_available': days_available,
                'activity_level': activity_level,
                'level': level,
                'restrictions': restrictions,
                'limitations': limitations,
                'equipment': 'full gym'
            }
            
            try:
                # Calculate calories via API
                result = api_client.calculate_calories(profile)
                
                st.session_state.user_profile = profile
                st.session_state.caloric_data = result
                
                st.success(f"✅ Profile saved! Target: {result['target_calories']:.0f} cal/day")
                
            except Exception as e:
                st.error(f"Error saving profile: {str(e)}")
        
        # Clear session
        st.markdown("---")
        if st.button("🔄 Start New Session", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            initialize_session_state()
            st.rerun()

def main():
    """Main application"""
    
    # Initialize
    initialize_session_state()
    api_client = get_api_client()
    
    # Check backend health
    try:
        health = api_client.health_check()
        if health['status'] != 'healthy':
            st.error("⚠️ Backend API is not responding correctly")
            return
    except Exception as e:
        st.error(f"""
        ⚠️ Cannot connect to backend API
        
        Please make sure the backend is running:
        ```bash
        cd backend
        python -m app.main
        ```
        
        Error: {str(e)}
        """)
        return
    
    # Render sidebar
    render_sidebar(api_client)
    
    # Main header
    st.markdown('<div class="main-header">💪 FitCoach - Your AI Fitness Assistant</div>',
                unsafe_allow_html=True)
    
    # Check if profile is complete
    if not st.session_state.user_profile:
        st.info("👈 Please fill out your profile in the sidebar to get started!")
        return
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🏋️ Workout Plan", "🍽️ Meal Plan", "💬 Chat"])
    
    with tab1:
        if st.session_state.caloric_data:
            render_dashboard(st.session_state.caloric_data, st.session_state.user_profile)
        else:
            st.info("Save your profile to see your dashboard")
    
    with tab2:
        render_workout_plan(api_client, st.session_state.user_profile)
    
    with tab3:
        render_meal_plan(api_client, st.session_state.caloric_data, st.session_state.user_profile)
    
    with tab4:
        render_chat(api_client, st.session_state.user_profile)

if __name__ == "__main__":
    main()
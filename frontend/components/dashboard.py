import streamlit as st
import pandas as pd

def render_dashboard(caloric_data: dict, profile: dict):
    """Render user dashboard"""
    
    st.markdown("## 📊 Your Fitness Dashboard")
    
    # Metrics row 1
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Goal", profile['goal'].title())
        st.metric("Experience", profile['level'].title())
    
    with col2:
        st.metric(
            "Target Calories",
            f"{caloric_data['target_calories']:.0f} cal/day"
        )
        st.metric("TDEE", f"{caloric_data['tdee']:.0f} cal/day")
    
    with col3:
        st.metric("Training Days", f"{profile['days_available']}/week")
        deficit = caloric_data['deficit_surplus_calories']
        st.metric(
            "Daily Deficit/Surplus",
            f"{deficit:+.0f} cal",
            delta=f"{caloric_data['deficit_surplus_percent']*100:.0f}%"
        )
    
    # Macro breakdown
    st.markdown("---")
    st.markdown("### 🎯 Daily Macro Targets")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Protein", f"{caloric_data['protein_g']:.0f}g", 
                 help="4 calories per gram")
    
    with col2:
        st.metric("Carbs", f"{caloric_data['carbs_g']:.0f}g",
                 help="4 calories per gram")
    
    with col3:
        st.metric("Fat", f"{caloric_data['fat_g']:.0f}g",
                 help="9 calories per gram")
    
    # Visualization
    st.markdown("---")
    st.markdown("### 📈 Caloric Breakdown")
    
    macro_df = pd.DataFrame({
        'Macro': ['Protein', 'Carbs', 'Fat'],
        'Calories': [
            caloric_data['protein_g'] * 4,
            caloric_data['carbs_g'] * 4,
            caloric_data['fat_g'] * 9
        ]
    })
    
    st.bar_chart(macro_df.set_index('Macro'))
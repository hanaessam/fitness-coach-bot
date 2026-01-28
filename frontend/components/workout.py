import streamlit as st

def render_workout_plan(api_client, profile):
    """Render workout plan generator"""
    
    st.markdown("## 🏋️ Your Personalized Workout Plan")
    
    # Options
    with st.expander("⚙️ Workout Options"):
        focus_areas = st.multiselect(
            "Focus Areas (optional)",
            ["Chest", "Back", "Legs", "Shoulders", "Arms", "Core"],
            help="Select specific body parts to emphasize"
        )
    
    # Generate button
    if st.button("🎯 Generate Workout Plan", type="primary", use_container_width=True):
        with st.spinner("Creating your personalized workout plan..."):
            try:
                result = api_client.generate_workout(
                    profile=profile,
                    focus_areas=focus_areas if focus_areas else None
                )
                
                st.session_state.workout_plan = result['plan']
                st.session_state.exercises_used = result.get('exercises_used', [])
                st.success("✅ Workout plan generated!")
                
            except Exception as e:
                st.error(f"Error generating workout plan: {str(e)}")
    
    # Display plan
    if st.session_state.get('workout_plan'):
        st.markdown("---")
        st.markdown(st.session_state.workout_plan)
        
        # Download button
        col1, col2 = st.columns([3, 1])
        with col2:
            st.download_button(
                label="📥 Download",
                data=st.session_state.workout_plan,
                file_name="my_workout_plan.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        # Show exercises used
        if st.session_state.get('exercises_used'):
            with st.expander("📋 Exercises Used in This Plan"):
                for ex in st.session_state.exercises_used:
                    st.write(f"**{ex['title']}** - {ex['body_part']} ({ex['level']})")
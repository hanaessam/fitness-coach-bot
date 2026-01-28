import streamlit as st

def render_meal_plan(api_client, caloric_data, profile):
    """Render meal plan generator"""
    
    st.markdown("## 🍽️ Your Personalized Meal Plan")
    
    if not caloric_data:
        st.warning("⚠️ Please save your profile first to generate a meal plan.")
        return
    
    # Display targets
    st.info(f"""
    **Your Daily Targets:**
    - Calories: {caloric_data['target_calories']:.0f} cal
    - Protein: {caloric_data['protein_g']:.0f}g
    - Carbs: {caloric_data['carbs_g']:.0f}g
    - Fat: {caloric_data['fat_g']:.0f}g
    """)
    
    # Generate button
    if st.button("🍽️ Generate Meal Plan", type="primary", use_container_width=True):
        with st.spinner("Creating your personalized meal plan..."):
            try:
                result = api_client.generate_meal_plan(
                    target_calories=caloric_data['target_calories'],
                    protein_g=caloric_data['protein_g'],
                    carbs_g=caloric_data['carbs_g'],
                    fat_g=caloric_data['fat_g'],
                    dietary_restrictions=profile.get('restrictions', [])
                )
                
                st.session_state.meal_plan = result['plan']
                st.success("✅ Meal plan generated!")
                
            except Exception as e:
                st.error(f"Error generating meal plan: {str(e)}")
    
    # Display plan
    if st.session_state.get('meal_plan'):
        st.markdown("---")
        st.markdown(st.session_state.meal_plan)
        
        # Download button
        col1, col2 = st.columns([3, 1])
        with col2:
            st.download_button(
                label="📥 Download",
                data=st.session_state.meal_plan,
                file_name="my_meal_plan.txt",
                mime="text/plain",
                use_container_width=True
            )
import streamlit as st

def render_chat(api_client, profile):
    """Render chat interface"""
    
    st.markdown("## 💬 Chat with FitCoach")
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat messages
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about fitness, nutrition, or your plan..."):
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Prepare conversation history (last 10 messages)
                    history = st.session_state.chat_history[-10:-1]
                    
                    # Get user context
                    user_context = {
                        'goal': profile.get('goal'),
                        'level': profile.get('level')
                    } if profile else None
                    
                    result = api_client.chat(
                        message=prompt,
                        conversation_history=history,
                        user_context=user_context
                    )
                    
                    response = result['response']
                    st.markdown(response)
                    
                    # Add to history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response
                    })
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": error_msg
                    })
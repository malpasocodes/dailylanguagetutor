import streamlit as st
from utils.ollama_client import OllamaClient

def run_chat_app(model: str, language: str):
    """Run the chat application with the selected model and language."""
    
    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat title
    st.title(f"Chat in {language}")
    st.caption(f"Using model: {model}")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Display assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # Initialize Ollama client
            client = OllamaClient()
            
            # Stream the response
            for chunk in client.chat_stream(
                model=model,
                messages=st.session_state.messages,
                target_language=language
            ):
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
        
        # Add assistant message to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # Clear chat button
    if st.button("Clear Chat", type="secondary"):
        st.session_state.messages = []
        st.rerun()
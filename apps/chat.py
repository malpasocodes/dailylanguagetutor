import streamlit as st
from utils.ollama_client import OllamaClient

def run_chat_app(model: str, language: str):
    """Run the chat application with the selected model and language."""
    
    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Initialize translations in session state
    if "translations" not in st.session_state:
        st.session_state.translations = {}
    
    # Display chat title
    st.title(f"Chat in {language}")
    st.caption(f"Using model: {model}")
    
    # Display chat history
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
        
        # Add translation section for assistant messages
        if message["role"] == "assistant":
            # Create a unique container for each message
            with st.container():
                # Add some spacing
                st.markdown("")
                
                # Create columns for button and translation
                col1, col2 = st.columns([2, 10])
                
                with col1:
                    # Use a simple key based on index
                    if st.button("🔤 Translate", key=f"trans_{i}"):
                        # Translate if not already done
                        if i not in st.session_state.translations:
                            with st.spinner("Translating..."):
                                client = OllamaClient()
                                translation = client.translate_to_english(
                                    model=model,
                                    text=message["content"],
                                    source_language=language
                                )
                                st.session_state.translations[i] = translation
                                st.rerun()
                
                with col2:
                    # Display translation if available
                    if i in st.session_state.translations:
                        st.info(f"**English Translation:** {st.session_state.translations[i]}")
            
            # Add separator
            st.markdown("---")
    
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
        
        # Rerun to show the new message with translate button
        st.rerun()
import streamlit as st
import time
from utils.ollama_client import OllamaClient
from apps.chat import run_chat_app
from apps.flashcard import run_flashcard_app
from apps.news import run_news_app

# Page configuration
st.set_page_config(
    page_title="Daily Language Tutor",
    page_icon="🌍",
    layout="wide"
)

# Initialize Ollama client
@st.cache_resource
def get_ollama_client():
    return OllamaClient()

# Get available models
@st.cache_data(ttl=60)
def get_available_models():
    client = get_ollama_client()
    models = client.list_models()
    return models if models else ["No models found"]

# Language flag mapping
LANGUAGE_FLAGS = {
    "French": "🇫🇷",
    "German": "🇩🇪",
    "Spanish": "🇪🇸",
    "Italian": "🇮🇹"
}

# Sidebar configuration
with st.sidebar:
    st.title("🌍 Daily Language Tutor")
    st.divider()
    
    # Model selection
    available_models = get_available_models()
    selected_model = st.selectbox(
        "Select Model",
        options=available_models,
        help="Choose an Ollama model for language generation"
    )
    
    # Model status indicator
    if selected_model != "No models found":
        model_status_container = st.empty()
        
        # Check model status
        with model_status_container:
            with st.spinner("Checking model..."):
                time.sleep(0.5)  # Brief delay for better UX
                client = get_ollama_client()
                is_loaded = client.check_model_loaded(selected_model)
                
            if is_loaded:
                st.success("🟢 Model loaded", icon="✅")
            else:
                st.error("🔴 Model not loaded", icon="❌")
    
    # Language selection
    languages = ["French", "German", "Spanish", "Italian"]
    selected_language = st.selectbox(
        "Select Language",
        options=languages,
        help="Choose your target language"
    )
    
    # Language confirmation
    flag = LANGUAGE_FLAGS.get(selected_language, "🌐")
    st.info(f"{flag} **{selected_language}** selected")
    
    # App selection
    apps = ["Chat", "Flash Card", "News"]
    selected_app = st.selectbox(
        "Select Application",
        options=apps,
        help="Choose the application to use"
    )
    
    st.divider()
    st.caption("Powered by Ollama & Streamlit")

# Main content area
if selected_model == "No models found":
    st.error("⚠️ No Ollama models found. Please ensure Ollama is running and has models installed.")
    st.info("To install models, run: `ollama pull llama2` or any other model")
else:
    # Route to selected app
    if selected_app == "Chat":
        run_chat_app(selected_model, selected_language)
    elif selected_app == "Flash Card":
        run_flashcard_app(selected_model, selected_language)
    elif selected_app == "News":
        run_news_app(selected_model, selected_language)

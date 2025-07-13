import streamlit as st
import time
import os
from dotenv import load_dotenv
from utils.ollama_client import OllamaClient
from utils.cloud_clients import OpenAIClient, AnthropicClient
from apps.chat import run_chat_app
from apps.flashcard import run_flashcard_app
from apps.dictionary import run_dictionary_app
from apps.roleplay import run_roleplay_app

# Load environment variables from .env file
load_dotenv()

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

# Initialize cloud client
@st.cache_resource
def get_cloud_client(provider, api_key):
    if provider == "OpenAI":
        return OpenAIClient(api_key)
    elif provider == "Anthropic":
        return AnthropicClient(api_key)
    return None

# Cloud model options
CLOUD_MODELS = {
    "OpenAI": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
    "Anthropic": ["claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-opus-20240229"]
}

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
    
    # API Mode selection
    api_mode = st.selectbox(
        "API Mode",
        options=["Ollama (Local)", "Cloud API"],
        help="Choose between local Ollama or cloud-based LLM APIs"
    )
    
    # Initialize client and models based on API mode
    client = None
    selected_model = None
    
    if api_mode == "Ollama (Local)":
        # Model selection for Ollama
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
                    ollama_client = get_ollama_client()
                    is_loaded = ollama_client.check_model_loaded(selected_model)
                    
                if is_loaded:
                    st.success("🟢 Model loaded", icon="✅")
                    client = ollama_client
                else:
                    st.error("🔴 Model not loaded", icon="❌")
    
    else:  # Cloud API
        # Get default provider from environment
        default_provider = os.getenv("DEFAULT_CLOUD_PROVIDER", "OpenAI")
        provider_options = ["OpenAI", "Anthropic"]
        default_index = provider_options.index(default_provider) if default_provider in provider_options else 0
        
        # Cloud provider selection
        cloud_provider = st.selectbox(
            "Cloud Provider",
            options=provider_options,
            index=default_index,
            help="Choose your cloud LLM provider"
        )
        
        # Check for API key in environment variables
        env_key_map = {
            "OpenAI": "OPENAI_API_KEY",
            "Anthropic": "ANTHROPIC_API_KEY"
        }
        
        env_api_key = os.getenv(env_key_map[cloud_provider])
        
        if env_api_key:
            st.success(f"✅ {cloud_provider} API key loaded from environment", icon="🔑")
            api_key = env_api_key
            
            # Option to override with manual input
            with st.expander("🔧 Override API Key"):
                manual_api_key = st.text_input(
                    "Manual API Key",
                    type="password",
                    help=f"Override the environment {cloud_provider} API key",
                    placeholder="sk-..."
                )
                if manual_api_key:
                    api_key = manual_api_key
                    st.warning("Using manual API key override")
        else:
            st.warning(f"⚠️ No {cloud_provider} API key found in environment", icon="🔑")
            st.info(f"💡 Tip: Add `{env_key_map[cloud_provider]}` to your .env file for easier testing")
            
            # Manual API key input
            api_key = st.text_input(
                "API Key",
                type="password",
                help=f"Enter your {cloud_provider} API key",
                placeholder="sk-..."
            )
        
        if api_key:
            # Get default model from environment
            default_model_key = f"DEFAULT_{cloud_provider.upper()}_MODEL"
            default_model = os.getenv(default_model_key)
            
            # Model selection for cloud
            model_options = CLOUD_MODELS[cloud_provider]
            default_model_index = 0
            if default_model and default_model in model_options:
                default_model_index = model_options.index(default_model)
            
            selected_model = st.selectbox(
                "Select Model",
                options=model_options,
                index=default_model_index,
                help=f"Choose a {cloud_provider} model"
            )
            
            # Try to initialize client
            try:
                client = get_cloud_client(cloud_provider, api_key)
                st.success(f"🟢 {cloud_provider} client ready", icon="✅")
            except Exception as e:
                st.error(f"🔴 Error: {str(e)}", icon="❌")
        else:
            st.warning("⚠️ Please enter your API key", icon="🔑")
    
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
    apps = ["Chat", "Flash Card", "Dictionary", "Roleplay"]
    selected_app = st.selectbox(
        "Select Application",
        options=apps,
        help="Choose the application to use"
    )
    
    # Clear Chat button (only show for Chat app)
    if selected_app == "Chat":
        st.markdown("")  # Add some spacing
        if st.button("🗑️ Clear Chat", type="secondary", use_container_width=True):
            st.session_state.messages = []
            st.session_state.translations = {}
            st.rerun()
    
    st.divider()
    st.caption("Powered by Ollama & Streamlit")

# Main content area
# Dictionary app doesn't need LLM client - always available
if selected_app == "Dictionary":
    run_dictionary_app(selected_language)
elif not client or not selected_model:
    # Show appropriate error for apps that need LLM
    st.error(f"⚠️ {selected_app} app requires an LLM connection")
    
    if api_mode == "Ollama (Local)":
        if selected_model == "No models found":
            st.info("📋 **To use Ollama:**")
            st.write("1. Ensure Ollama is running")
            st.write("2. Install a model: `ollama pull llama2`")
        else:
            st.info("📋 **Troubleshooting:**")
            st.write("1. Check that Ollama is running")
            st.write("2. Verify the selected model is available")
    else:
        st.info("📋 **To use Cloud API:**")
        st.write("1. Enter your API key in the sidebar")
        st.write("2. Select a model")
        st.write("3. Verify your API key is valid")
    
    st.markdown("---")
    st.info("💡 **Tip:** The Dictionary app is always available and doesn't require an LLM connection!")
else:
    # Route to apps that need LLM client
    if selected_app == "Chat":
        run_chat_app(client, selected_model, selected_language)
    elif selected_app == "Flash Card":
        run_flashcard_app(client, selected_model, selected_language)
    elif selected_app == "Roleplay":
        run_roleplay_app(client, selected_model, selected_language)

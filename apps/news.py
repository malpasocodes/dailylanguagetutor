import streamlit as st
from utils.ollama_client import OllamaClient
from datetime import datetime

def run_news_app(model: str, language: str):
    """Run the news application with the selected model and language."""
    
    # Store model in session state
    st.session_state.current_model = model
    
    # Initialize session state
    if "news_headlines" not in st.session_state:
        st.session_state.news_headlines = []
    if "news_loaded" not in st.session_state:
        st.session_state.news_loaded = False
    if "selected_category" not in st.session_state:
        st.session_state.selected_category = "All"
    
    # Display title
    st.title(f"📰 News in {language}")
    st.caption(f"Using model: {model}")
    
    # Controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Category filter
        categories = ["All", "politics", "technology", "sports", "health", "entertainment", 
                     "business", "science", "culture", "environment", "international"]
        selected_category = st.selectbox(
            "Filter by category:",
            categories,
            index=categories.index(st.session_state.selected_category)
        )
        st.session_state.selected_category = selected_category
    
    with col2:
        if st.button("🔄 Refresh News", type="primary"):
            load_news(model, language)
    
    with col3:
        if st.button("📊 Show Debug"):
            show_debug_info()
    
    # Load news on first visit
    if not st.session_state.news_loaded:
        load_news(model, language)
    
    # Display news
    if st.session_state.news_headlines:
        display_news(selected_category)
    elif st.session_state.news_loaded:
        st.info("No news available. Try refreshing.")

def load_news(model: str, language: str):
    """Load real news headlines from NewsAPI.org."""
    client = OllamaClient()
    
    with st.spinner(f"Loading latest real news in {language}..."):
        # Try to get real news first
        result = client.get_real_news_headlines(language, 10)
        
        # If real news fails and no API key, try LLM generation as fallback
        if result and result.get("error") and result.get("source") == "no_api_key":
            with st.spinner(f"Generating news headlines in {language}..."):
                result = client.generate_news_headlines(model, language, 8)
    
    if result and result.get("headlines") and not result.get("error"):
        st.session_state.news_headlines = result["headlines"]
        st.session_state.news_source = result.get("source", "unknown")
        st.session_state.news_debug = result.get("debug", "")
        st.session_state.news_loaded = True
        
        # Show success message with source info
        source = result.get("source", "unknown")
        if source == "newsapi":
            st.success(f"✅ Loaded {len(result['headlines'])} real news headlines from NewsAPI.org")
        elif source == "cached":
            st.success(f"✅ Loaded {len(result['headlines'])} cached headlines")
        else:
            st.success(f"✅ Loaded {len(result['headlines'])} news headlines")
        
    else:
        st.session_state.news_loaded = True
        st.error("❌ Failed to load news headlines")
        
        if result:
            with st.expander("🔍 Error Details"):
                st.write("**Debug Info:**", result.get("debug", "Unknown error"))
                
                # Show setup instructions if no API key
                if result.get("setup_instructions"):
                    st.write("**Setup Instructions:**")
                    st.code(result.get("setup_instructions", ""))
                
                if result.get("raw_response"):
                    st.write("**Raw Response:**")
                    st.code(result.get("raw_response", "No response"))
                if result.get("attempted_parse"):
                    st.write("**Attempted Parse:**")
                    st.code(result.get("attempted_parse", "No content"))

def display_news(selected_category: str):
    """Display news headlines with filtering."""
    headlines = st.session_state.news_headlines
    
    # Filter by category
    if selected_category != "All":
        headlines = [h for h in headlines if h.get("category", "").lower() == selected_category.lower()]
    
    if not headlines:
        st.info(f"No news found for category: {selected_category}")
        return
    
    # Display headlines
    st.write(f"**Showing {len(headlines)} headlines**")
    st.write(f"*Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    
    for i, headline in enumerate(headlines):
        with st.container():
            # Header row
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### {headline.get('headline', 'No headline')}")
            
            with col2:
                category = headline.get('category', 'general')
                category_color = get_category_color(category)
                st.markdown(f"<span style='background-color: {category_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em;'>{category.upper()}</span>", 
                           unsafe_allow_html=True)
            
            # Summary
            summary = headline.get('summary', 'No summary available')
            st.write(summary)
            
            # Footer
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                source = headline.get('source', 'Unknown Source')
                st.caption(f"📰 {source}")
            with col2:
                date = headline.get('date', datetime.now().strftime('%Y-%m-%d'))
                st.caption(f"📅 {date}")
            with col3:
                # Add "Read More" link for real news
                if headline.get('url'):
                    st.link_button("🔗 Read Full Article", headline['url'], use_container_width=True)
            
            # Divider
            if i < len(headlines) - 1:
                st.divider()

def get_category_color(category: str) -> str:
    """Get color for category badge."""
    colors = {
        'politics': '#FF6B6B',
        'technology': '#4ECDC4',
        'sports': '#45B7D1',
        'health': '#96CEB4',
        'entertainment': '#FFEAA7',
        'business': '#DDA0DD',
        'science': '#74B9FF',
        'culture': '#FD79A8',
        'environment': '#00B894',
        'international': '#6C5CE7'
    }
    return colors.get(category.lower(), '#95A5A6')

def show_debug_info():
    """Show debug information in a modal."""
    if st.session_state.news_headlines:
        with st.expander("🔍 Debug Information", expanded=True):
            st.write("**Source:**", st.session_state.get("news_source", "unknown"))
            st.write("**Debug:**", st.session_state.get("news_debug", ""))
            st.write("**Headlines loaded:**", len(st.session_state.news_headlines))
            
            # Show sample headlines
            st.write("**Sample headlines:**")
            for i, headline in enumerate(st.session_state.news_headlines[:3]):
                st.write(f"{i+1}. {headline.get('headline', 'No headline')} ({headline.get('category', 'no category')})")
    else:
        st.info("No news data to debug.")
import streamlit as st
from utils.ollama_client import OllamaClient
from database.database import db
import random
from datetime import datetime

def run_flashcard_app(client, model: str, language: str):
    """Run the flashcard application with the selected model and language."""
    
    # Store model and client in session state for access in other functions
    st.session_state.current_model = model
    st.session_state.current_client = client
    
    # Initialize session state
    if "flashcard_words" not in st.session_state:
        st.session_state.flashcard_words = []
    if "current_word_index" not in st.session_state:
        st.session_state.current_word_index = 0
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "game_started" not in st.session_state:
        st.session_state.game_started = False
    if "show_result" not in st.session_state:
        st.session_state.show_result = False
    if "user_answer" not in st.session_state:
        st.session_state.user_answer = ""
    if "word_source" not in st.session_state:
        st.session_state.word_source = "generated"  # "generated" or "database"
    
    # Display title
    st.title(f"Flash Cards - {language}")
    st.caption(f"Using model: {model}")
    
    # Game setup
    if not st.session_state.game_started:
        # Word source selection
        st.write("### Choose word source:")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📚 My Vocabulary", type="primary" if st.session_state.word_source == "database" else "secondary", use_container_width=True):
                st.session_state.word_source = "database"
                st.rerun()
        
        with col2:
            if st.button("🎲 Generated Words", type="primary" if st.session_state.word_source == "generated" else "secondary", use_container_width=True):
                st.session_state.word_source = "generated"
                st.rerun()
        
        # Show vocabulary count if database is selected
        if st.session_state.word_source == "database":
            vocab_count = len(db.get_vocabulary(language))
            if vocab_count == 0:
                st.warning(f"You don't have any {language} words in your vocabulary yet. Add some words in the Dictionary app or use Generated Words.")
            else:
                st.info(f"You have {vocab_count} {language} words in your vocabulary.")
        
        st.write("### Select number of words to practice:")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("5 Words", type="primary", use_container_width=True):
                start_game(5, client, model, language)
        with col2:
            if st.button("10 Words", type="primary", use_container_width=True):
                start_game(10, client, model, language)
        with col3:
            if st.button("25 Words", type="primary", use_container_width=True):
                start_game(25, client, model, language)
    
    # Game in progress
    else:
        # Check if game is complete
        if st.session_state.current_word_index >= len(st.session_state.flashcard_words):
            show_final_score()
        else:
            show_current_word()

def start_game(word_count: int, client, model: str, language: str):
    """Initialize a new game with the specified number of words."""
    
    if st.session_state.word_source == "database":
        # Get words from database
        with st.spinner(f"Loading {word_count} {language} words from your vocabulary..."):
            vocab_words = db.get_vocabulary(language)
            
            if len(vocab_words) < word_count:
                st.error(f"❌ You only have {len(vocab_words)} {language} words in your vocabulary, but requested {word_count}.")
                st.info("Add more words in the Dictionary app or try a smaller number.")
                return
            
            # Prioritize words with lower confidence scores and older review dates
            # Sort by confidence score (ascending) and last_reviewed (oldest first)
            vocab_words.sort(key=lambda w: (w.confidence_score, w.last_reviewed or datetime.min))
            
            # Select the requested number of words
            selected_words = vocab_words[:word_count]
            
            # Convert to flashcard format
            flashcard_words = []
            for vocab in selected_words:
                flashcard_words.append({
                    "word": vocab.word,
                    "translation": vocab.translation,
                    "part_of_speech": vocab.part_of_speech or "unknown",
                    "vocab_id": vocab.id  # Store ID for updating review stats
                })
            
            # Shuffle the words
            random.shuffle(flashcard_words)
            
            st.session_state.flashcard_words = flashcard_words
            st.session_state.debug_info = f"Loaded {word_count} words from your vocabulary"
            st.session_state.categories = []
            st.session_state.current_word_index = 0
            st.session_state.score = 0
            st.session_state.game_started = True
            st.session_state.show_result = False
            st.session_state.user_answer = ""
            st.rerun()
    
    else:
        # Generate words using AI
        with st.spinner(f"Generating {word_count} unique {language} words..."):
            result = client.generate_flashcard_words(model, language, word_count)
        
        if result and result.get("words") and not result.get("error"):
            st.session_state.flashcard_words = result["words"]
            st.session_state.word_source = result.get("source", "unknown")
            st.session_state.debug_info = result.get("debug", "")
            st.session_state.categories = result.get("categories", [])
            st.session_state.current_word_index = 0
            st.session_state.score = 0
            st.session_state.game_started = True
            st.session_state.show_result = False
            st.session_state.user_answer = ""
            st.rerun()
        else:
            # Show detailed error information
            st.error("❌ Failed to generate vocabulary words")
            
            if result:
                with st.expander("🔍 Error Details", expanded=True):
                    st.write("**Debug Info:**", result.get("debug", "Unknown error"))
                    if result.get("raw_response"):
                        st.write("**Raw Response:**")
                        st.code(result.get("raw_response", "No response"))
                    if result.get("attempted_parse"):
                        st.write("**What we tried to parse:**")
                        st.code(result.get("attempted_parse", "No content"))
                        
            st.info("💡 **Troubleshooting Tips:**")
            st.write("1. Ensure your model supports JSON generation")
            st.write("2. Try a different model (some models work better with structured output)")
            st.write("3. Check your API connection and credentials")
            
            if st.button("🔄 Try Again", type="primary"):
                st.rerun()

def show_current_word():
    """Display the current word and handle user input."""
    words = st.session_state.flashcard_words
    current_index = st.session_state.current_word_index
    current_word = words[current_index]
    
    # Progress indicator
    progress = (current_index + 1) / len(words)
    st.progress(progress)
    st.write(f"**Word {current_index + 1} of {len(words)}**")
    
    # Show debug info
    if current_index == 0:  # Only show on first word
        source = st.session_state.get("word_source", "unknown")
        debug_info = st.session_state.get("debug_info", "")
        categories = st.session_state.get("categories", [])
        
        if source == "database":
            st.success(f"📚 Using words from your vocabulary database")
            st.info("Words are prioritized by confidence score and review history")
        elif source == "generated":
            st.success(f"🎲 Words dynamically generated by {st.session_state.current_model}")
            if categories:
                st.info(f"📚 Focus categories: {', '.join(categories)}")
        
        with st.expander("🔍 Word Source Details"):
            st.write("**Source:**", "Your Vocabulary" if source == "database" else "AI Generated")
            st.write("**Info:**", debug_info)
            
            # Show the actual words
            st.write("**Words in this session:**")
            word_list = [f"{i+1}. {w['word']} ({w['part_of_speech']}) = {w['translation']}" 
                        for i, w in enumerate(words[:5])]  # Show first 5 words
            for word_item in word_list:
                st.write(word_item)
            if len(words) > 5:
                st.write(f"... and {len(words) - 5} more words")
    
    # Display the word
    st.markdown("---")
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.markdown(f"### {current_word['word']}")
    with col2:
        st.markdown(f"*({current_word['part_of_speech']})*")
    with col3:
        # Show confidence score for database words
        if st.session_state.word_source == "database" and "vocab_id" in current_word:
            vocab_items = db.get_vocabulary()
            for vocab in vocab_items:
                if vocab.id == current_word["vocab_id"]:
                    confidence_percent = int(vocab.confidence_score * 100)
                    st.caption(f"Confidence: {confidence_percent}%")
                    break
    
    # User input
    if not st.session_state.show_result:
        user_answer = st.text_input(
            "Enter the English translation:",
            key=f"answer_{current_index}",
            value=st.session_state.user_answer
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Submit", type="primary", disabled=not user_answer):
                check_answer(user_answer, current_word['translation'])
    else:
        # Show result
        if st.session_state.last_answer_correct:
            st.success("✅ Correct!")
        else:
            st.error(f"❌ Incorrect. The correct answer is: **{current_word['translation']}**")
        
        if st.button("Next Word", type="primary"):
            st.session_state.current_word_index += 1
            st.session_state.show_result = False
            st.session_state.user_answer = ""
            st.rerun()
    
    # Option to quit
    st.markdown("---")
    if st.button("Quit Game", type="secondary"):
        reset_game()

def check_answer(user_answer: str, correct_answer: str):
    """Check if the user's answer is correct."""
    # Normalize answers for comparison
    user_answer = user_answer.strip().lower()
    correct_answer = correct_answer.strip().lower()
    
    # Check for exact match or common variations
    is_correct = False
    if user_answer == correct_answer:
        is_correct = True
    elif correct_answer.startswith("to ") and user_answer == correct_answer[3:]:
        # Handle infinitive verbs (e.g., "to eat" vs "eat")
        is_correct = True
    elif user_answer.startswith("to ") and user_answer[3:] == correct_answer:
        # Handle infinitive verbs (reverse case)
        is_correct = True
    
    if is_correct:
        st.session_state.score += 1
        st.session_state.last_answer_correct = True
    else:
        st.session_state.last_answer_correct = False
    
    # Update review statistics if word is from database
    if st.session_state.word_source == "database":
        current_word = st.session_state.flashcard_words[st.session_state.current_word_index]
        if "vocab_id" in current_word:
            # Calculate new confidence score
            # Increase by 0.2 for correct, decrease by 0.3 for incorrect
            # Clamp between 0 and 1
            vocab_id = current_word["vocab_id"]
            
            # Get current confidence score from database
            vocab_items = db.get_vocabulary()
            current_confidence = 0.0
            for vocab in vocab_items:
                if vocab.id == vocab_id:
                    current_confidence = vocab.confidence_score
                    break
            
            if is_correct:
                new_confidence = min(1.0, current_confidence + 0.2)
            else:
                new_confidence = max(0.0, current_confidence - 0.3)
            
            # Update in database
            db.update_review(vocab_id, new_confidence)
    
    st.session_state.show_result = True
    st.rerun()

def show_final_score():
    """Display the final score and options to play again."""
    total_words = len(st.session_state.flashcard_words)
    score = st.session_state.score
    percentage = (score / total_words) * 100
    
    st.balloons()
    st.markdown("## 🎉 Game Complete!")
    
    # Score display
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.metric("Final Score", f"{score}/{total_words}", f"{percentage:.0f}%")
    
    # Feedback message
    if percentage >= 80:
        st.success("Excellent work! You're mastering this vocabulary! 🌟")
    elif percentage >= 60:
        st.info("Good job! Keep practicing to improve further. 💪")
    else:
        st.warning("Keep practicing! You'll get better with time. 📚")
    
    # Play again button
    if st.button("Play Again", type="primary"):
        reset_game()

def reset_game():
    """Reset the game state."""
    # Preserve word source selection
    word_source = st.session_state.get("word_source", "generated")
    
    st.session_state.flashcard_words = []
    st.session_state.current_word_index = 0
    st.session_state.score = 0
    st.session_state.game_started = False
    st.session_state.show_result = False
    st.session_state.user_answer = ""
    st.session_state.word_source = word_source  # Restore word source
    st.rerun()
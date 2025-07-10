import streamlit as st
from utils.ollama_client import OllamaClient
from database import db, Vocabulary
from datetime import datetime

def run_chat_app(model: str, language: str):
    """Run the chat application with the selected model and language."""
    
    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Initialize translations in session state
    if "translations" not in st.session_state:
        st.session_state.translations = {}
    
    # Initialize vocabulary forms state
    if "show_vocab_form" not in st.session_state:
        st.session_state.show_vocab_form = {}
    
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
                
                # Create columns for buttons and content
                col1, col2, col3 = st.columns([2, 2, 8])
                
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
                    # Add Vocabulary button
                    if st.button("📚 Add Vocabulary", key=f"vocab_{i}"):
                        # Toggle the form display
                        st.session_state.show_vocab_form[i] = not st.session_state.show_vocab_form.get(i, False)
                        st.rerun()
                
                with col3:
                    # Display translation if available
                    if i in st.session_state.translations:
                        st.info(f"**English Translation:** {st.session_state.translations[i]}")
                
                # Display vocabulary form if toggled
                if st.session_state.show_vocab_form.get(i, False):
                    with st.container():
                        st.markdown("### Add to Vocabulary")
                        with st.form(key=f"vocab_form_{i}"):
                            # Pre-populate with empty values
                            word = st.text_input("Word", placeholder="e.g., dramaturgo", key=f"word_{i}")
                            
                            # Add a button to get AI suggestions
                            if word:
                                if st.form_submit_button("🤖 Get AI Suggestions", type="secondary"):
                                    with st.spinner(f"Looking up '{word}'..."):
                                        client = OllamaClient()
                                        vocab_info = client.enrich_vocabulary(model, word, language)
                                        
                                        if vocab_info:
                                            # Store in session state for this form
                                            st.session_state[f"vocab_info_{i}"] = vocab_info
                                            st.rerun()
                            
                            # Get stored vocab info if available
                            vocab_info = st.session_state.get(f"vocab_info_{i}", {})
                            
                            translation = st.text_input(
                                "Translation", 
                                value=vocab_info.get("translation", ""),
                                placeholder="e.g., playwright"
                            )
                            
                            # Map AI part of speech to our options
                            pos_mapping = {
                                "noun": "Noun",
                                "verb": "Verb",
                                "adjective": "Adjective",
                                "adverb": "Adverb",
                                "preposition": "Preposition",
                                "conjunction": "Conjunction",
                                "pronoun": "Pronoun"
                            }
                            default_pos = pos_mapping.get(vocab_info.get("part_of_speech", "").lower(), "Noun")
                            
                            part_of_speech = st.selectbox(
                                "Part of Speech",
                                ["Noun", "Verb", "Adjective", "Adverb", "Preposition", "Conjunction", "Pronoun", "Other"],
                                index=["Noun", "Verb", "Adjective", "Adverb", "Preposition", "Conjunction", "Pronoun", "Other"].index(default_pos)
                            )
                            
                            example_sentence = st.text_area(
                                "Example Sentence (optional)", 
                                value=vocab_info.get("example_sentence", ""),
                                placeholder="El dramaturgo escribió una obra nueva."
                            )
                            
                            # Combine notes with gender and pronunciation if available
                            ai_notes = []
                            if vocab_info.get("gender"):
                                ai_notes.append(f"Gender: {vocab_info['gender']}")
                            if vocab_info.get("pronunciation_hint"):
                                ai_notes.append(f"Pronunciation: {vocab_info['pronunciation_hint']}")
                            if vocab_info.get("notes"):
                                ai_notes.append(vocab_info["notes"])
                            
                            notes = st.text_area(
                                "Notes (optional)", 
                                value="\n".join(ai_notes),
                                placeholder="Any additional notes..."
                            )
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.form_submit_button("Add", type="primary"):
                                    if word and translation:
                                        # Create vocabulary entry
                                        vocab = Vocabulary(
                                            word=word.strip(),
                                            translation=translation.strip(),
                                            language=language,
                                            part_of_speech=part_of_speech.lower(),
                                            example_sentence=example_sentence.strip() if example_sentence else None,
                                            notes=notes.strip() if notes else None,
                                            date_added=datetime.now()
                                        )
                                        
                                        # Save to database
                                        if db.add_vocabulary(vocab):
                                            st.success(f"Added '{word}' to your {language} vocabulary!")
                                            # Clean up session state
                                            if f"vocab_info_{i}" in st.session_state:
                                                del st.session_state[f"vocab_info_{i}"]
                                            # Hide the form
                                            st.session_state.show_vocab_form[i] = False
                                            st.rerun()
                                        else:
                                            st.error(f"'{word}' already exists in your {language} vocabulary!")
                                    else:
                                        st.error("Please fill in both Word and Translation fields.")
                            
                            with col_cancel:
                                if st.form_submit_button("Cancel"):
                                    # Clean up session state
                                    if f"vocab_info_{i}" in st.session_state:
                                        del st.session_state[f"vocab_info_{i}"]
                                    st.session_state.show_vocab_form[i] = False
                                    st.rerun()
            
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
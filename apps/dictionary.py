import streamlit as st
import pandas as pd
from datetime import datetime
from database import db, Vocabulary
import csv
from io import StringIO

def run_dictionary_app(selected_language: str):
    """Run the dictionary application."""
    
    st.title("📚 Vocabulary Dictionary")
    
    # Language selector with current language as default
    languages = ["All Languages", "French", "German", "Spanish", "Italian"]
    
    # Controls row
    col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
    
    with col1:
        # Find the index of selected_language or default to "All Languages"
        default_index = languages.index(selected_language) if selected_language in languages else 0
        filter_language = st.selectbox(
            "Filter by Language",
            options=languages,
            index=default_index,
            key="dict_language_filter"
        )
    
    with col2:
        search_term = st.text_input(
            "Search words",
            placeholder="Search word or translation...",
            key="dict_search"
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            options=["Date Added (Newest)", "Date Added (Oldest)", "Alphabetical", "Times Reviewed"],
            key="dict_sort"
        )
    
    with col4:
        view_mode = st.radio(
            "View",
            options=["Cards", "Table"],
            horizontal=True,
            key="dict_view"
        )
    
    # Get vocabulary from database
    if filter_language == "All Languages":
        words = db.get_vocabulary()
    else:
        words = db.get_vocabulary(filter_language)
    
    # Apply search filter
    if search_term:
        search_lower = search_term.lower()
        words = [w for w in words if 
                search_lower in w.word.lower() or 
                search_lower in w.translation.lower()]
    
    # Apply sorting
    if sort_by == "Date Added (Newest)":
        words.sort(key=lambda x: x.date_added, reverse=True)
    elif sort_by == "Date Added (Oldest)":
        words.sort(key=lambda x: x.date_added)
    elif sort_by == "Alphabetical":
        words.sort(key=lambda x: x.word.lower())
    elif sort_by == "Times Reviewed":
        words.sort(key=lambda x: x.times_reviewed, reverse=True)
    
    # Display statistics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Words", len(words))
    
    with col2:
        # Count by language
        lang_counts = {}
        for w in db.get_vocabulary():  # Get all words for stats
            lang_counts[w.language] = lang_counts.get(w.language, 0) + 1
        
        if filter_language != "All Languages" and filter_language in lang_counts:
            st.metric(f"{filter_language} Words", lang_counts[filter_language])
        else:
            st.metric("Languages", len(lang_counts))
    
    with col3:
        # Average reviews
        avg_reviews = sum(w.times_reviewed for w in words) / len(words) if words else 0
        st.metric("Avg. Reviews", f"{avg_reviews:.1f}")
    
    with col4:
        # Export button
        if st.button("📥 Export CSV", type="secondary"):
            csv_data = export_to_csv(words)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"vocabulary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    st.markdown("---")
    
    # Display words
    if not words:
        st.info("No vocabulary words found. Start adding words from the Chat app!")
    else:
        if view_mode == "Cards":
            display_as_cards(words)
        else:
            display_as_table(words)


def display_as_cards(words):
    """Display vocabulary words as cards."""
    # Create columns for card layout
    cols_per_row = 2
    
    for i in range(0, len(words), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j, col in enumerate(cols):
            if i + j < len(words):
                word = words[i + j]
                with col:
                    with st.container():
                        # Card styling with border
                        st.markdown(
                            f"""
                            <div style="border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                                <h4 style="margin: 0 0 8px 0;">{word.word}</h4>
                                <p style="color: #666; margin: 4px 0;"><strong>{word.translation}</strong></p>
                                <p style="font-size: 0.9em; color: #888; margin: 4px 0;">
                                    {word.part_of_speech} • {word.language} • Reviews: {word.times_reviewed}
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        # Expandable details
                        with st.expander("Details"):
                            if word.example_sentence:
                                st.markdown(f"**Example:** {word.example_sentence}")
                            if word.notes:
                                st.markdown(f"**Notes:** {word.notes}")
                            st.caption(f"Added: {word.date_added.strftime('%Y-%m-%d %H:%M')}")
                            if word.last_reviewed:
                                st.caption(f"Last reviewed: {word.last_reviewed.strftime('%Y-%m-%d %H:%M')}")
                            
                            # Edit/Delete buttons
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("✏️ Edit", key=f"edit_{word.id}"):
                                    st.session_state[f"editing_{word.id}"] = True
                                    st.rerun()
                            
                            with col2:
                                if st.button("🗑️ Delete", key=f"delete_{word.id}", type="secondary"):
                                    if delete_vocabulary(word.id):
                                        st.success(f"Deleted '{word.word}'")
                                        st.rerun()
                        
                        # Edit form if in edit mode
                        if st.session_state.get(f"editing_{word.id}", False):
                            show_edit_form(word)


def display_as_table(words):
    """Display vocabulary words as a table."""
    # Convert to DataFrame for table display
    data = []
    for w in words:
        data.append({
            "Word": w.word,
            "Translation": w.translation,
            "Language": w.language,
            "Part of Speech": w.part_of_speech,
            "Reviews": w.times_reviewed,
            "Added": w.date_added.strftime('%Y-%m-%d'),
            "ID": w.id
        })
    
    df = pd.DataFrame(data)
    
    # Display the table without the ID column
    display_df = df.drop(columns=['ID'])
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Reviews": st.column_config.NumberColumn(
                "Reviews",
                help="Number of times reviewed",
                format="%d"
            ),
            "Added": st.column_config.DateColumn(
                "Added",
                help="Date added to dictionary"
            )
        }
    )
    
    # Batch operations
    st.markdown("### Manage Entries")
    
    # Select word for operations
    selected_word_idx = st.selectbox(
        "Select a word to edit or delete",
        options=range(len(df)),
        format_func=lambda x: f"{df.iloc[x]['Word']} ({df.iloc[x]['Language']})",
        key="table_word_select"
    )
    
    if selected_word_idx is not None:
        selected_word = words[selected_word_idx]
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✏️ Edit Selected", key="table_edit"):
                st.session_state[f"editing_{selected_word.id}"] = True
                st.rerun()
        
        with col2:
            if st.button("🗑️ Delete Selected", key="table_delete", type="secondary"):
                if delete_vocabulary(selected_word.id):
                    st.success(f"Deleted '{selected_word.word}'")
                    st.rerun()
        
        # Show edit form if editing
        if st.session_state.get(f"editing_{selected_word.id}", False):
            show_edit_form(selected_word)


def show_edit_form(word: Vocabulary):
    """Show edit form for a vocabulary word."""
    st.markdown("### Edit Vocabulary")
    
    with st.form(key=f"edit_form_{word.id}"):
        new_word = st.text_input("Word", value=word.word)
        new_translation = st.text_input("Translation", value=word.translation)
        
        # Map part of speech
        pos_options = ["noun", "verb", "adjective", "adverb", "preposition", "conjunction", "pronoun", "other"]
        current_pos_index = pos_options.index(word.part_of_speech.lower()) if word.part_of_speech.lower() in pos_options else 0
        
        new_pos = st.selectbox(
            "Part of Speech",
            options=[p.capitalize() for p in pos_options],
            index=current_pos_index
        )
        
        new_example = st.text_area("Example Sentence", value=word.example_sentence or "")
        new_notes = st.text_area("Notes", value=word.notes or "")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Save", type="primary"):
                # Update the word
                updated_vocab = Vocabulary(
                    id=word.id,
                    word=new_word,
                    translation=new_translation,
                    language=word.language,
                    part_of_speech=new_pos.lower(),
                    example_sentence=new_example if new_example else None,
                    notes=new_notes if new_notes else None,
                    date_added=word.date_added,
                    times_reviewed=word.times_reviewed,
                    last_reviewed=word.last_reviewed,
                    confidence_score=word.confidence_score
                )
                
                if update_vocabulary(updated_vocab):
                    st.success("Updated successfully!")
                    del st.session_state[f"editing_{word.id}"]
                    st.rerun()
                else:
                    st.error("Failed to update")
        
        with col2:
            if st.form_submit_button("Cancel"):
                del st.session_state[f"editing_{word.id}"]
                st.rerun()


def delete_vocabulary(vocab_id: int) -> bool:
    """Delete a vocabulary word (placeholder - needs DB method)."""
    # This will be implemented when we add the delete method to the database
    return db.delete_vocabulary(vocab_id)


def update_vocabulary(vocab: Vocabulary) -> bool:
    """Update a vocabulary word (placeholder - needs DB method)."""
    # This will be implemented when we add the update method to the database
    return db.update_vocabulary(vocab)


def export_to_csv(words) -> str:
    """Export vocabulary words to CSV format."""
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Word", "Translation", "Language", "Part of Speech", 
        "Example Sentence", "Notes", "Date Added", "Times Reviewed", 
        "Last Reviewed", "Confidence Score"
    ])
    
    # Write data
    for w in words:
        writer.writerow([
            w.word,
            w.translation,
            w.language,
            w.part_of_speech,
            w.example_sentence or "",
            w.notes or "",
            w.date_added.strftime('%Y-%m-%d %H:%M:%S'),
            w.times_reviewed,
            w.last_reviewed.strftime('%Y-%m-%d %H:%M:%S') if w.last_reviewed else "",
            f"{w.confidence_score:.2f}"
        ])
    
    return output.getvalue()
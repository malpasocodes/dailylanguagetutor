## Project Concept: Daily Language Tutor

### Technology Stack
- Using Streamlit for web interface
- Utilizing local LLMs via Ollama
- Package management with UV
- Development in Python virtual environment (venv)
- uv documentation is here and should be referenced during the project as needed: https://docs.astral.sh/uv/
- streamlist documentation is here and should be referenced during the project as needed: https://docs.streamlit.io/
- Ollama API documentation is here and should be referenced during the project as needed: https://github.com/ollama/ollama/blob/main/docs/api.md

### User Interface Design
- The streamlit sidebar at the top will have the following two selectbox. The first selectbox will allow the user to choose among the locally installed Ollama models. The second selectbox below will allow the user to choose a language. The primary languages for now will be French, German, Spanish, and Italian.
- The third selectbox on the sidebar will allow the user to choose the particular app they want to run: Chat, Flash Card, or Dictionary.

### Vocabulary Management System
- SQLite database for persistent storage of vocabulary words
- Each vocabulary entry includes: word, translation, language, part of speech, example sentence, notes, and metadata (date added, times reviewed, confidence score)
- Vocabulary can be added from the Chat app with AI-powered enrichment
- Dictionary app provides full CRUD operations on vocabulary entries
- Export functionality to CSV for external use
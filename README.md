# Daily Language Tutor

An AI-powered language learning application that helps users practice French, German, Spanish, and Italian through interactive chat, vocabulary management, and flashcard exercises.

## Version 0.2

### Features

- **Multi-Language Support**: Practice French 🇫🇷, German 🇩🇪, Spanish 🇪🇸, and Italian 🇮🇹
- **Local LLM Integration**: Uses Ollama for completely offline language learning
- **Interactive Chat**: Chat with AI that responds exclusively in your target language
- **Translation Feature**: Translate AI responses to English with one click
- **Vocabulary Management**: Add new vocabulary words from chat conversations
- **AI-Powered Vocabulary Enrichment**: Get AI suggestions for translations, parts of speech, and examples
- **Dictionary App**: View, search, edit, and manage your vocabulary collection
- **Flashcard Practice**: Learn vocabulary with customizable word counts (5, 10, or 25 words)
- **Real-time Model Status**: Visual confirmation when models are loaded and ready
- **Export Functionality**: Export vocabulary to CSV format
- **Persistent Storage**: SQLite database for vocabulary management

### Prerequisites

- Python 3.9 or higher
- [UV package manager](https://github.com/astral-sh/uv)
- [Ollama](https://ollama.ai/) installed and running locally
- At least one Ollama model installed (e.g., `llama2`, `mistral`)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd DailyLanguageTutor
```

2. Install dependencies using UV:
```bash
uv pip install -r pyproject.toml
```

### Running the Application

1. Ensure Ollama is running:
```bash
ollama serve
```

2. Start the Streamlit application:
```bash
streamlit run main.py
```

3. Open your browser to `http://localhost:8501`

### Usage

#### Chat Application
1. Select your preferred Ollama model from the sidebar
2. Choose your target language
3. Select "Chat" from the application dropdown
4. Start chatting in any language - the AI will always respond in your selected target language
5. Click "🔤 Translate" below any AI response to see the English translation
6. Click "📚 Add Vocabulary" to save new words to your personal dictionary
   - Enter the word and translation manually, or
   - Click "🤖 Get AI Suggestions" to auto-fill information
7. Use "🗑️ Clear Chat" in the sidebar to start a new conversation

#### Dictionary Application
1. Select "Dictionary" from the application dropdown
2. Filter vocabulary by language or view all languages
3. Search for specific words or translations
4. Choose between Card or Table view
5. Edit or delete vocabulary entries
6. Export your vocabulary to CSV format

#### Flashcard Application
1. Select your model and target language
2. Choose "Flash Card" from the application dropdown
3. Select the number of words to practice (5, 10, or 25)
4. Enter the English translation for each word shown
5. Get immediate feedback on your answers
6. View your final score at the end

### Project Structure

```
DailyLanguageTutor/
├── main.py                 # Main Streamlit application
├── apps/
│   ├── chat.py            # Chat application
│   ├── dictionary.py      # Dictionary application
│   └── flashcard.py       # Flashcard application
├── database/
│   ├── __init__.py        # Database package initialization
│   ├── database.py        # SQLite database operations
│   └── models.py          # Data models
├── utils/
│   └── ollama_client.py   # Ollama API wrapper
├── vocabulary.db          # SQLite database (created on first use)
├── pyproject.toml         # Project dependencies
├── README.md              # This file
└── CLAUDE.md              # AI assistant instructions
```

### Dependencies

- **streamlit**: Web interface framework
- **requests**: HTTP library for Ollama API communication
- **pandas**: Data manipulation for dictionary display
- **sqlite3**: Built-in database for vocabulary storage

### Changelog

#### Version 0.2 (Current)
##### Added
- Vocabulary management system with SQLite database
- "Add Vocabulary" button in chat interface
- AI-powered vocabulary enrichment using Ollama
- Dictionary app with search, filter, and sort capabilities
- Edit and delete functionality for vocabulary entries
- Export vocabulary to CSV
- Card and table view modes for dictionary
- Vocabulary statistics display

##### Changed
- Updated UI with better emoji icons
- Improved project structure with database module

#### Version 0.10
##### Added
- Translation feature for chat responses
- English translation button below each AI response
- Model loading status indicator
- Clear Chat button moved to sidebar
- Improved flashcard word generation with better variety

##### Fixed
- Translation button visibility across different models
- Session state management for translations
- Consistent UI behavior when switching models/languages

##### Removed
- News application (API limitations)
- python-dotenv dependency

### Database Schema

The vocabulary database uses SQLite with the following schema:

```sql
CREATE TABLE vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,
    translation TEXT NOT NULL,
    language TEXT NOT NULL,
    part_of_speech TEXT,
    example_sentence TEXT,
    notes TEXT,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    times_reviewed INTEGER DEFAULT 0,
    last_reviewed TIMESTAMP,
    confidence_score REAL DEFAULT 0.0,
    UNIQUE(word, language)
)
```

### Known Issues

- Some models may have difficulty generating properly formatted JSON for flashcards
- Mistral model works best for flashcard generation
- The AI suggestions feature depends on the quality of the selected Ollama model

### Future Enhancements

- Integration with flashcard app to practice saved vocabulary
- Spaced repetition algorithm for vocabulary review
- Import vocabulary from external sources
- Categories and tags for vocabulary organization
- Progress tracking and learning analytics

### Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

### License

[Your license here]

### Acknowledgments

- Powered by [Ollama](https://ollama.ai/) for local LLM inference
- Built with [Streamlit](https://streamlit.io/) for the web interface
- Package management by [UV](https://github.com/astral-sh/uv)
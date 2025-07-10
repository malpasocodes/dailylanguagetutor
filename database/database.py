import sqlite3
from typing import List, Optional
from datetime import datetime
from .models import Vocabulary

class VocabularyDatabase:
    def __init__(self, db_path: str = "vocabulary.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database and create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS vocabulary (
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
            ''')
            conn.commit()
    
    def add_vocabulary(self, vocab: Vocabulary) -> bool:
        """Add a new vocabulary word to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO vocabulary (word, translation, language, part_of_speech, 
                                          example_sentence, notes, date_added, confidence_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (vocab.word, vocab.translation, vocab.language, vocab.part_of_speech,
                      vocab.example_sentence, vocab.notes, vocab.date_added, vocab.confidence_score))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            # Word already exists for this language
            return False
    
    def get_vocabulary(self, language: Optional[str] = None) -> List[Vocabulary]:
        """Get all vocabulary words, optionally filtered by language."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if language:
                cursor = conn.execute(
                    'SELECT * FROM vocabulary WHERE language = ? ORDER BY date_added DESC',
                    (language,)
                )
            else:
                cursor = conn.execute('SELECT * FROM vocabulary ORDER BY date_added DESC')
            
            words = []
            for row in cursor:
                vocab = Vocabulary(
                    id=row['id'],
                    word=row['word'],
                    translation=row['translation'],
                    language=row['language'],
                    part_of_speech=row['part_of_speech'],
                    example_sentence=row['example_sentence'],
                    notes=row['notes'],
                    date_added=datetime.fromisoformat(row['date_added']),
                    times_reviewed=row['times_reviewed'],
                    last_reviewed=datetime.fromisoformat(row['last_reviewed']) if row['last_reviewed'] else None,
                    confidence_score=row['confidence_score']
                )
                words.append(vocab)
            
            return words
    
    def word_exists(self, word: str, language: str) -> bool:
        """Check if a word already exists in the database for a given language."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT COUNT(*) FROM vocabulary WHERE word = ? AND language = ?',
                (word, language)
            )
            return cursor.fetchone()[0] > 0
    
    def update_review(self, vocab_id: int, confidence_score: float):
        """Update review statistics for a vocabulary word."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE vocabulary 
                SET times_reviewed = times_reviewed + 1,
                    last_reviewed = CURRENT_TIMESTAMP,
                    confidence_score = ?
                WHERE id = ?
            ''', (confidence_score, vocab_id))
            conn.commit()
    
    def delete_vocabulary(self, vocab_id: int) -> bool:
        """Delete a vocabulary word by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('DELETE FROM vocabulary WHERE id = ?', (vocab_id,))
                conn.commit()
                return True
        except sqlite3.Error:
            return False
    
    def update_vocabulary(self, vocab: Vocabulary) -> bool:
        """Update an existing vocabulary word."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE vocabulary 
                    SET word = ?,
                        translation = ?,
                        part_of_speech = ?,
                        example_sentence = ?,
                        notes = ?
                    WHERE id = ?
                ''', (vocab.word, vocab.translation, vocab.part_of_speech,
                      vocab.example_sentence, vocab.notes, vocab.id))
                conn.commit()
                return True
        except sqlite3.Error:
            return False

# Global database instance
db = VocabularyDatabase()
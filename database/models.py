from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Vocabulary:
    id: Optional[int] = None
    word: str = ""
    translation: str = ""
    language: str = ""
    part_of_speech: str = ""
    example_sentence: Optional[str] = None
    notes: Optional[str] = None
    date_added: datetime = datetime.now()
    times_reviewed: int = 0
    last_reviewed: Optional[datetime] = None
    confidence_score: float = 0.0
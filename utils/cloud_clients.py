import json
import random
import time
from typing import List, Dict, Generator, Optional
from abc import ABC, abstractmethod

class BaseLLMClient(ABC):
    """Base class for all LLM clients (Ollama and Cloud)"""
    
    @abstractmethod
    def chat_stream(self, model: str, messages: List[Dict[str, str]], target_language: str = None) -> Generator[str, None, None]:
        pass
    
    @abstractmethod
    def generate_flashcard_words(self, model: str, language: str, count: int) -> Optional[Dict[str, any]]:
        pass
    
    @abstractmethod
    def translate_to_english(self, model: str, text: str, source_language: str) -> str:
        pass
    
    @abstractmethod
    def enrich_vocabulary(self, model: str, word: str, language: str) -> Optional[Dict[str, str]]:
        pass

class OpenAIClient(BaseLLMClient):
    """OpenAI API client"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
    
    def chat_stream(self, model: str, messages: List[Dict[str, str]], target_language: str = None) -> Generator[str, None, None]:
        """Stream chat completions from OpenAI"""
        if target_language:
            system_prompt = f"You must respond only in {target_language}. Never use any other language regardless of the input language."
            messages = [{"role": "system", "content": system_prompt}] + messages
        
        try:
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                max_tokens=1000,
                temperature=0.7
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def generate_flashcard_words(self, model: str, language: str, count: int) -> Optional[Dict[str, any]]:
        """Generate flashcard words with translations"""
        categories = ["food", "animals", "colors", "family", "nature", "emotions", "daily activities", "clothing", "weather", "body parts", "transportation", "professions"]
        selected_categories = random.sample(categories, min(3, len(categories)))
        random_seed = random.randint(1000, 9999)
        
        messages = [
            {
                "role": "system",
                "content": "You are a language teacher creating vocabulary flashcards. Always respond with valid JSON only, no markdown, no explanation."
            },
            {
                "role": "user",
                "content": f"""Generate exactly {count} {language} vocabulary words for beginners.

Focus on these categories: {', '.join(selected_categories)}
Seed for variety: {random_seed}
Current time: {int(time.time())}

IMPORTANT: Generate DIFFERENT words each time. Avoid the most basic words like hello, house, water.

Return ONLY a JSON array (no markdown blocks) with this exact format:
[
  {{"word": "{language} word", "part_of_speech": "noun/verb/adjective", "translation": "English translation"}}
]

For verbs: use infinitive form in {language} and "to ..." in English.
Vary your selections - include less common but still useful beginner words."""
            }
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.9,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            
            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            content = content.strip()
            
            # Find JSON array
            start_idx = content.find('[')
            end_idx = content.rfind(']')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_content = content[start_idx:end_idx + 1]
            else:
                json_content = content
            
            words_data = json.loads(json_content)
            
            if isinstance(words_data, list) and len(words_data) > 0:
                valid_words = []
                for w in words_data:
                    if isinstance(w, dict) and all(k in w for k in ["word", "part_of_speech", "translation"]):
                        valid_words.append(w)
                
                if len(valid_words) >= count:
                    sample_words = [w["word"] for w in valid_words[:3]]
                    return {
                        "words": valid_words[:count],
                        "source": "generated",
                        "debug": f"Successfully generated {count} words. Sample: {', '.join(sample_words)}...",
                        "categories": selected_categories
                    }
                    
        except Exception as e:
            return {
                "words": None,
                "source": "error",
                "debug": f"Error: {str(e)}",
                "error": True
            }
        
        return {
            "words": None,
            "source": "failed",
            "debug": "Generation failed - no valid JSON response",
            "error": True
        }
    
    def translate_to_english(self, model: str, text: str, source_language: str) -> str:
        """Translate text to English"""
        messages = [
            {
                "role": "system",
                "content": "You are a professional translator. Translate the given text to English accurately and naturally. Respond only with the English translation, no explanations or additional text."
            },
            {
                "role": "user",
                "content": f"Translate this {source_language} text to English: {text}"
            }
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Translation error: {str(e)}"
    
    def enrich_vocabulary(self, model: str, word: str, language: str) -> Optional[Dict[str, str]]:
        """Get enriched information about a vocabulary word"""
        messages = [
            {
                "role": "system",
                "content": "You are a language teacher providing vocabulary information. Always respond with valid JSON only, no markdown, no explanation."
            },
            {
                "role": "user",
                "content": f"""Provide information about this {language} word: "{word}"

Return ONLY a JSON object (no markdown blocks) with this exact format:
{{
  "translation": "English translation",
  "part_of_speech": "noun/verb/adjective/adverb/etc",
  "example_sentence": "Example sentence in {language}",
  "pronunciation_hint": "Pronunciation guide if helpful",
  "gender": "masculine/feminine/neuter (only for languages with grammatical gender)",
  "notes": "Any useful notes about usage or context"
}}

If the word doesn't exist or is misspelled, still provide your best attempt."""
            }
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=500,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            
            # Handle markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            vocab_info = json.loads(content.strip())
            
            if isinstance(vocab_info, dict) and "translation" in vocab_info and "part_of_speech" in vocab_info:
                return vocab_info
                
        except Exception:
            pass
        
        return None

class AnthropicClient(BaseLLMClient):
    """Anthropic API client"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("Anthropic package not installed. Run: pip install anthropic")
    
    def chat_stream(self, model: str, messages: List[Dict[str, str]], target_language: str = None) -> Generator[str, None, None]:
        """Stream chat completions from Anthropic"""
        # Convert messages to Anthropic format
        system_message = ""
        if target_language:
            system_message = f"You must respond only in {target_language}. Never use any other language regardless of the input language."
        
        # Filter out system messages and combine them
        filtered_messages = []
        for msg in messages:
            if msg["role"] == "system":
                if system_message:
                    system_message += "\n\n" + msg["content"]
                else:
                    system_message = msg["content"]
            else:
                filtered_messages.append(msg)
        
        try:
            with self.client.messages.stream(
                model=model,
                max_tokens=1000,
                system=system_message,
                messages=filtered_messages
            ) as stream:
                for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def generate_flashcard_words(self, model: str, language: str, count: int) -> Optional[Dict[str, any]]:
        """Generate flashcard words with translations"""
        categories = ["food", "animals", "colors", "family", "nature", "emotions", "daily activities", "clothing", "weather", "body parts", "transportation", "professions"]
        selected_categories = random.sample(categories, min(3, len(categories)))
        random_seed = random.randint(1000, 9999)
        
        prompt = f"""Generate exactly {count} {language} vocabulary words for beginners.

Focus on these categories: {', '.join(selected_categories)}
Seed for variety: {random_seed}
Current time: {int(time.time())}

IMPORTANT: Generate DIFFERENT words each time. Avoid the most basic words like hello, house, water.

Return ONLY a JSON array (no markdown blocks) with this exact format:
[
  {{"word": "{language} word", "part_of_speech": "noun/verb/adjective", "translation": "English translation"}}
]

For verbs: use infinitive form in {language} and "to ..." in English.
Vary your selections - include less common but still useful beginner words."""
        
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=1000,
                system="You are a language teacher creating vocabulary flashcards. Always respond with valid JSON only, no markdown, no explanation.",
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            
            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            content = content.strip()
            
            # Find JSON array
            start_idx = content.find('[')
            end_idx = content.rfind(']')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_content = content[start_idx:end_idx + 1]
            else:
                json_content = content
            
            words_data = json.loads(json_content)
            
            if isinstance(words_data, list) and len(words_data) > 0:
                valid_words = []
                for w in words_data:
                    if isinstance(w, dict) and all(k in w for k in ["word", "part_of_speech", "translation"]):
                        valid_words.append(w)
                
                if len(valid_words) >= count:
                    sample_words = [w["word"] for w in valid_words[:3]]
                    return {
                        "words": valid_words[:count],
                        "source": "generated",
                        "debug": f"Successfully generated {count} words. Sample: {', '.join(sample_words)}...",
                        "categories": selected_categories
                    }
                    
        except Exception as e:
            return {
                "words": None,
                "source": "error",
                "debug": f"Error: {str(e)}",
                "error": True
            }
        
        return {
            "words": None,
            "source": "failed",
            "debug": "Generation failed - no valid JSON response",
            "error": True
        }
    
    def translate_to_english(self, model: str, text: str, source_language: str) -> str:
        """Translate text to English"""
        prompt = f"Translate this {source_language} text to English: {text}"
        
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=500,
                system="You are a professional translator. Translate the given text to English accurately and naturally. Respond only with the English translation, no explanations or additional text.",
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            return f"Translation error: {str(e)}"
    
    def enrich_vocabulary(self, model: str, word: str, language: str) -> Optional[Dict[str, str]]:
        """Get enriched information about a vocabulary word"""
        prompt = f"""Provide information about this {language} word: "{word}"

Return ONLY a JSON object (no markdown blocks) with this exact format:
{{
  "translation": "English translation",
  "part_of_speech": "noun/verb/adjective/adverb/etc",
  "example_sentence": "Example sentence in {language}",
  "pronunciation_hint": "Pronunciation guide if helpful",
  "gender": "masculine/feminine/neuter (only for languages with grammatical gender)",
  "notes": "Any useful notes about usage or context"
}}

If the word doesn't exist or is misspelled, still provide your best attempt."""
        
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=500,
                system="You are a language teacher providing vocabulary information. Always respond with valid JSON only, no markdown, no explanation.",
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            
            # Handle markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            vocab_info = json.loads(content.strip())
            
            if isinstance(vocab_info, dict) and "translation" in vocab_info and "part_of_speech" in vocab_info:
                return vocab_info
                
        except Exception:
            pass
        
        return None
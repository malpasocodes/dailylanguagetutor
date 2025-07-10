import requests
import json
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Generator, Optional

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        
    def list_models(self) -> List[str]:
        """Get list of available Ollama models."""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except requests.RequestException as e:
            print(f"Error fetching models: {e}")
            return []
    
    def chat_stream(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        target_language: str = None
    ) -> Generator[str, None, None]:
        """Stream chat completions from Ollama."""
        if target_language:
            system_prompt = f"You must respond only in {target_language}. Never use any other language regardless of the input language."
            messages = [{"role": "system", "content": system_prompt}] + messages
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": True
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=True
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
                    except json.JSONDecodeError:
                        continue
                        
        except requests.RequestException as e:
            yield f"Error: {str(e)}"
    
    def check_model_loaded(self, model: str) -> bool:
        """Check if a model is loaded and ready to use."""
        try:
            payload = {
                "model": model,
                "prompt": "test",
                "stream": False,
                "options": {
                    "num_predict": 1
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=5
            )
            response.raise_for_status()
            return True
        except requests.RequestException:
            return False
    
    def generate_flashcard_words(
        self, 
        model: str, 
        language: str, 
        count: int
    ) -> Optional[Dict[str, any]]:
        """Generate flashcard words with translations."""
        # Add randomization to get different words each time
        categories = ["food", "animals", "colors", "family", "nature", "emotions", "daily activities", "clothing", "weather", "body parts", "transportation", "professions"]
        selected_categories = random.sample(categories, min(3, len(categories)))
        random_seed = random.randint(1000, 9999)
        
        # Use chat endpoint for better reliability
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
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.9,  # Higher temperature for more variety
                "seed": random_seed
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if "message" in result and "content" in result["message"]:
                content = result["message"]["content"]
                
                # Try to extract JSON from the response
                # Handle cases where the model might include markdown code blocks
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                
                # Find JSON array in the content
                content = content.strip()
                
                # Try to find the start and end of JSON array
                start_idx = content.find('[')
                end_idx = content.rfind(']')
                
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_content = content[start_idx:end_idx + 1]
                else:
                    json_content = content
                
                words_data = json.loads(json_content)
                
                # Validate the structure
                if isinstance(words_data, list) and len(words_data) > 0:
                    # Ensure all required fields are present
                    valid_words = []
                    for w in words_data:
                        if isinstance(w, dict) and all(k in w for k in ["word", "part_of_speech", "translation"]):
                            valid_words.append(w)
                    
                    if len(valid_words) >= count:
                        # Show sample of generated words in debug
                        sample_words = [w["word"] for w in valid_words[:3]]
                        return {
                            "words": valid_words[:count],
                            "source": "generated",
                            "debug": f"Successfully generated {count} words. Sample: {', '.join(sample_words)}...",
                            "categories": selected_categories
                        }
                    elif len(valid_words) > 0:
                        # Return None instead of partial words
                        return {
                            "words": None,
                            "source": "failed",
                            "debug": f"Generated only {len(valid_words)} words out of {count} requested. Raw response: {content[:200]}...",
                            "error": True
                        }
                        
        except json.JSONDecodeError as e:
            error_msg = f"JSON Parse Error: {str(e)}"
            raw_response = content[:500] if 'content' in locals() else "No response"
            
            # Try to show what we tried to parse
            attempted_json = json_content[:200] if 'json_content' in locals() else content[:200] if 'content' in locals() else "No content"
            
            return {
                "words": None,
                "source": "json_error",
                "debug": error_msg,
                "raw_response": raw_response,
                "attempted_parse": attempted_json,
                "error": True
            }
        except (requests.RequestException, KeyError) as e:
            error_msg = f"Error: {type(e).__name__}: {str(e)}"
            raw_response = result if 'result' in locals() else "No response"
            return {
                "words": None,
                "source": "error",
                "debug": error_msg,
                "raw_response": str(raw_response)[:500],
                "error": True
            }
        
        # Return error if generation fails
        return {
            "words": None,
            "source": "failed",
            "debug": "Generation failed - no valid JSON response",
            "error": True
        }
    
    def translate_to_english(self, model: str, text: str, source_language: str) -> str:
        """Translate text from source language to English."""
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
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if "message" in result and "content" in result["message"]:
                return result["message"]["content"].strip()
            else:
                return "Translation failed: No response content"
                
        except requests.RequestException as e:
            return f"Translation error: {str(e)}"
    
    def enrich_vocabulary(self, model: str, word: str, language: str) -> Optional[Dict[str, str]]:
        """Get enriched information about a vocabulary word."""
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
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if "message" in result and "content" in result["message"]:
                content = result["message"]["content"]
                
                # Handle markdown code blocks
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                
                # Parse JSON
                vocab_info = json.loads(content.strip())
                
                # Validate required fields
                if isinstance(vocab_info, dict) and "translation" in vocab_info and "part_of_speech" in vocab_info:
                    return vocab_info
                    
        except (json.JSONDecodeError, requests.RequestException, KeyError):
            pass
        
        return None
    


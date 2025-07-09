import requests
import json
import random
import time
import os
from datetime import datetime, timedelta
from typing import List, Dict, Generator, Optional

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.news_api_key = os.getenv("NEWS_API_KEY")
        self.news_cache = {}
        self.cache_duration = 1800  # 30 minutes in seconds
        
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
    
    def get_real_news_headlines(
        self,
        language: str,
        count: int = 10
    ) -> Optional[Dict[str, any]]:
        """Get real news headlines from NewsAPI.org."""
        
        # Language mapping for NewsAPI.org
        language_codes = {
            "French": "fr",
            "German": "de", 
            "Spanish": "es",
            "Italian": "it"
        }
        
        lang_code = language_codes.get(language, "en")
        cache_key = f"{lang_code}_{count}"
        
        # Check cache first
        if cache_key in self.news_cache:
            cached_data, timestamp = self.news_cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                return {
                    "headlines": cached_data["headlines"],
                    "source": "cached",
                    "debug": f"Returned {len(cached_data['headlines'])} cached headlines",
                    "language": language
                }
        
        # If no API key, fall back to LLM generation
        if not self.news_api_key:
            return {
                "headlines": None,
                "source": "no_api_key",
                "debug": "No NEWS_API_KEY found. Please set your NewsAPI.org key in environment variables.",
                "error": True,
                "setup_instructions": "1. Go to https://newsapi.org/register\n2. Get your free API key\n3. Set environment variable: export NEWS_API_KEY=your_key_here"
            }
        
        try:
            # NewsAPI.org top headlines endpoint
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                "apiKey": self.news_api_key,
                "language": lang_code,
                "pageSize": count,
                "sortBy": "publishedAt"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") == "ok" and data.get("articles"):
                headlines = []
                for article in data["articles"]:
                    # Skip articles with "[Removed]" content
                    if article.get("title") == "[Removed]" or article.get("description") == "[Removed]":
                        continue
                        
                    headline = {
                        "headline": article.get("title", "No title"),
                        "category": self._categorize_article(article.get("description", "")),
                        "summary": article.get("description", "No summary available"),
                        "source": article.get("source", {}).get("name", "Unknown Source"),
                        "date": article.get("publishedAt", "")[:10],  # Extract date part
                        "url": article.get("url", "")
                    }
                    headlines.append(headline)
                
                # Cache the results
                self.news_cache[cache_key] = ({"headlines": headlines}, time.time())
                
                return {
                    "headlines": headlines,
                    "source": "newsapi",
                    "debug": f"Successfully fetched {len(headlines)} real headlines from NewsAPI.org",
                    "language": language
                }
            else:
                error_msg = data.get("message", "Unknown error from NewsAPI.org")
                return {
                    "headlines": None,
                    "source": "api_error",
                    "debug": f"NewsAPI.org error: {error_msg}",
                    "error": True
                }
                
        except requests.RequestException as e:
            return {
                "headlines": None,
                "source": "network_error",
                "debug": f"Network error: {str(e)}",
                "error": True
            }
        except Exception as e:
            return {
                "headlines": None,
                "source": "error",
                "debug": f"Unexpected error: {str(e)}",
                "error": True
            }
    
    def _categorize_article(self, description: str) -> str:
        """Simple categorization based on keywords in description."""
        if not description:
            return "general"
            
        desc_lower = description.lower()
        
        # Simple keyword matching
        if any(word in desc_lower for word in ["election", "government", "minister", "president", "parliament", "political"]):
            return "politics"
        elif any(word in desc_lower for word in ["technology", "tech", "digital", "software", "ai", "computer"]):
            return "technology"
        elif any(word in desc_lower for word in ["sport", "football", "soccer", "basketball", "tennis", "game"]):
            return "sports"
        elif any(word in desc_lower for word in ["health", "medical", "doctor", "hospital", "disease", "medicine"]):
            return "health"
        elif any(word in desc_lower for word in ["business", "economy", "economic", "market", "finance", "company"]):
            return "business"
        elif any(word in desc_lower for word in ["entertainment", "movie", "film", "music", "celebrity", "show"]):
            return "entertainment"
        elif any(word in desc_lower for word in ["science", "research", "study", "scientific", "discovery"]):
            return "science"
        elif any(word in desc_lower for word in ["environment", "climate", "environmental", "pollution", "green"]):
            return "environment"
        else:
            return "general"

    def generate_news_headlines(
        self, 
        model: str, 
        language: str, 
        count: int = 8
    ) -> Optional[Dict[str, any]]:
        """Generate news headlines in the target language."""
        categories = [
            "politics", "technology", "sports", "health", "entertainment", 
            "business", "science", "culture", "environment", "international"
        ]
        
        # Generate realistic dates (last 3 days)
        today = datetime.now()
        recent_dates = [
            (today - timedelta(days=i)).strftime("%Y-%m-%d") 
            for i in range(3)
        ]
        
        random_seed = random.randint(1000, 9999)
        
        messages = [
            {
                "role": "system",
                "content": f"You are a news editor creating realistic headlines in {language}. Always respond with valid JSON only, no markdown, no explanation."
            },
            {
                "role": "user",
                "content": f"""Generate {count} realistic news headlines in {language} for today's date.

Create a JSON array with this exact format:
[
  {{
    "headline": "Headline text in {language}",
    "category": "politics/technology/sports/health/entertainment/business/science/culture/environment/international",
    "summary": "Brief 1-2 sentence summary in {language}",
    "source": "Realistic news source name",
    "date": "2025-01-09"
  }}
]

Requirements:
- Headlines should sound like real current news
- Mix different categories: {', '.join(categories[:5])}
- Use realistic source names appropriate for {language}
- Summaries should be 1-2 sentences max
- Make headlines engaging but realistic
- Use recent dates: {', '.join(recent_dates)}
- Seed: {random_seed}
"""
            }
        ]
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.8,
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
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                
                # Find JSON array in the content
                content = content.strip()
                start_idx = content.find('[')
                end_idx = content.rfind(']')
                
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_content = content[start_idx:end_idx + 1]
                else:
                    json_content = content
                
                news_data = json.loads(json_content)
                
                # Validate the structure
                if isinstance(news_data, list) and len(news_data) > 0:
                    valid_headlines = []
                    required_fields = ["headline", "category", "summary", "source", "date"]
                    
                    for item in news_data:
                        if isinstance(item, dict) and all(k in item for k in required_fields):
                            valid_headlines.append(item)
                    
                    if len(valid_headlines) >= count:
                        return {
                            "headlines": valid_headlines[:count],
                            "source": "generated",
                            "debug": f"Successfully generated {len(valid_headlines[:count])} headlines",
                            "language": language
                        }
                    elif len(valid_headlines) > 0:
                        return {
                            "headlines": valid_headlines,
                            "source": "partial",
                            "debug": f"Generated {len(valid_headlines)} headlines out of {count} requested",
                            "language": language
                        }
                        
        except json.JSONDecodeError as e:
            return {
                "headlines": None,
                "source": "json_error",
                "debug": f"JSON Parse Error: {str(e)}",
                "raw_response": content[:500] if 'content' in locals() else "No response",
                "attempted_parse": json_content[:200] if 'json_content' in locals() else "No content",
                "error": True
            }
        except (requests.RequestException, KeyError) as e:
            return {
                "headlines": None,
                "source": "error",
                "debug": f"Error: {type(e).__name__}: {str(e)}",
                "error": True
            }
        
        return {
            "headlines": None,
            "source": "failed",
            "debug": "Generation failed - no valid JSON response",
            "error": True
        }
    

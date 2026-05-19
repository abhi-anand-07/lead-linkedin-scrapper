"""
Gemini LLM Client Wrapper (using google-genai SDK)
Supports gemini-2.0-flash with JSON mode.
"""
import os
import json
import re
from typing import Optional


class GeminiClient:
    """Wrapper for Google Gemini API using the modern google-genai SDK."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
        self._client = None
        
        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except ImportError:
                raise ImportError("google-genai not installed. Run: pip install google-genai")
    
    def is_available(self) -> bool:
        return self._client is not None and self.api_key is not None
    
    def generate_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> dict:
        """Generate structured JSON output from Gemini."""
        if not self.is_available():
            raise RuntimeError("Gemini client not available. Set GEMINI_API_KEY.")
        
        from google import genai
        from google.genai import types
        
        response = self._client.models.generate_content(
            model=self.model_name,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=1024,
                response_mime_type="application/json"
            )
        )
        
        text = response.text.strip()
        
        # Sometimes Gemini wraps JSON in markdown
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        
        return json.loads(text)
    
    def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = 500) -> str:
        """Generate plain text output from Gemini."""
        if not self.is_available():
            raise RuntimeError("Gemini client not available. Set GEMINI_API_KEY.")
        
        from google import genai
        from google.genai import types
        
        response = self._client.models.generate_content(
            model=self.model_name,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens
            )
        )
        
        return response.text.strip()

import google.generativeai as genai
import os
import json
from typing import List, Dict, Any

class CourseParser:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        
        # Try models in order of preference (Flash models are best for long context parsing)
        models_to_try = ['gemini-2.0-flash-lite', 'gemini-flash-latest']
        self.model = None
        
        for model_name in models_to_try:
            try:
                # Test initialization
                test_model = genai.GenerativeModel(model_name)
                self.model = test_model
                print(f"✅ CourseParser initialized with {model_name}")
                break
            except Exception:
                continue
                
        if not self.model:
            print("⚠️ All models failed for Parser. Defaulting to gemini-2.0-flash-lite.")
            self.model = genai.GenerativeModel('gemini-2.0-flash-lite')

    def parse_raw_text(self, raw_text: str) -> List[Dict[str, str]]:
        """
        Parses unstructured text into a list of course dictionaries.
        """
        if not raw_text or len(raw_text.strip()) < 10:
            return []

        prompt = """
        You are a data extraction assistant. The following text is copied from a university course search system. It is messy and unstructured.
        
        Your task is to extract ALL valid courses from the text.
        
        For each course, extract:
        1. "course_id": The course code (e.g., "CS-GY 6083", "CS 101", "MATH-UA 123").
        2. "name": The full course title.
        3. "instructor": The professor's name. If multiple are listed, take the first one. If not found, use "Staff".
        
        Output strictly in JSON format as a list of objects:
        [
            {"course_id": "...", "name": "...", "instructor": "..."},
            ...
        ]
        
        Do not include markdown formatting like ```json. Just the raw JSON string.
        If the text contains no courses, return [].
        
        Input Text:
        """
        
        # Truncate to avoid token limits if necessary, though 1.5 Flash handles 1M tokens.
        # Safe limit for now: 50,000 chars (~12k tokens)
        truncated_text = raw_text[:50000]
        
        try:
            response = self.model.generate_content([prompt, truncated_text])
            text = response.text.strip()
            
            # Clean up markdown if present
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
                
            return json.loads(text.strip())
        except Exception as e:
            print(f"Error parsing text: {e}")
            return []

import google.generativeai as genai
import json
import re
import os

class JudgeAgent:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        # Use a fast model for the Judge
        self.model = genai.GenerativeModel('gemini-2.0-flash-lite', generation_config={"response_mime_type": "application/json"})

    def extract_rmp_data(self, raw_text):
        """
        Extracts structured RMP data from raw search result text.
        Returns a dictionary with rating, difficulty, etc.
        """
        if not raw_text:
            return self._empty_result()

        prompt = f"""
        You are a Data Extractor. Your job is to extract Rate My Professors (RMP) statistics from the provided text.
        
        Rules:
        1. Look for "Rating", "Quality", "Difficulty", "Would Take Again".
        2. If data is missing, use null.
        3. "would_take_again" should be a number (0-100) or null.
        4. "rating" and "difficulty" should be floats (0.0-5.0) or null.
        5. "summary" should be a concise summary of the student reviews found in the text (max 2 sentences).
        
        Text to Analyze:
        {raw_text[:50000]}
        
        Output JSON Schema:
        {{
            "rmp_rating": float | null,
            "difficulty": float | null,
            "would_take_again_percent": float | null,
            "summary": string,
            "has_data": boolean,
            "review_count": int | null
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text)
            
            # Handle case where model returns a list [ { ... } ]
            if isinstance(data, list):
                if len(data) > 0 and isinstance(data[0], dict):
                    return data[0]
                else:
                    return self._empty_result()
            
            # Handle case where model returns a dict { ... }
            if isinstance(data, dict):
                return data
                
            return self._empty_result()
        except Exception as e:
            print(f"Judge Error: {e}")
            return self._empty_result()

    def _empty_result(self):
        return {
            "rmp_rating": None,
            "difficulty": None,
            "would_take_again_percent": None,
            "summary": "No data found.",
            "has_data": False,
            "review_count": 0
        }

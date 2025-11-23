import google.generativeai as genai
from PIL import Image
import os
import json
from typing import List, Dict, Any

class CourseVision:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        
        # Try models in order of preference (Flash models are best for vision)
        models_to_try = ['gemini-1.5-flash', 'gemini-2.0-flash-lite']
        self.model = None
        
        for model_name in models_to_try:
            try:
                # Test initialization
                test_model = genai.GenerativeModel(model_name)
                self.model = test_model
                print(f"✅ CourseVision initialized with {model_name}")
                break
            except Exception:
                continue
                
        if not self.model:
            print("⚠️ All models failed for Vision. Defaulting to gemini-2.0-flash-lite.")
            self.model = genai.GenerativeModel('gemini-2.0-flash-lite')

    def extract_course_info(self, image: Image.Image) -> List[Dict[str, str]]:
        """
        Analyzes a screenshot and extracts course information.
        Returns a list of dictionaries with 'course_id', 'name', 'instructor'.
        """
        prompt = """
        Analyze this screenshot of a course selection system (like NYU Albert).
        Extract all visible courses.
        
        For each course, identify:
        1. Course Code (e.g., CS-GY 6083)
        2. Course Name (e.g., Principles of Database Systems)
        3. Instructor Name (e.g., Ying Lu)
        
        Output strictly in JSON format as a list of objects:
        [
            {"course_id": "...", "name": "...", "instructor": "..."},
            ...
        ]
        If no courses are found, return [].
        Do not include markdown formatting like ```json. Just the raw JSON string.
        """
        
        try:
            response = self.model.generate_content([prompt, image])
            text = response.text.strip()
            
            # Clean up markdown if present
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
                
            return json.loads(text.strip())
        except Exception as e:
            print(f"Error extracting course info: {e}")
            return []

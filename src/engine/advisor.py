import os
import google.generativeai as genai
from src.vector_store.store import CourseVectorStore
from typing import List, Dict, Any

from src.data.rmp import RMPSearcher, RMPAggregator
import json

class CourseAdvisor:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        
        # Try models in order of preference
        models_to_try = ['gemini-1.5-flash', 'gemini-2.0-flash-lite']
        self.model = None
        for model_name in models_to_try:
            try:
                test_model = genai.GenerativeModel(model_name)
                test_model.generate_content("Test")
                self.model = test_model
                break
            except Exception:
                continue
        if not self.model:
            self.model = genai.GenerativeModel('gemini-2.0-flash-lite')

        self.searcher = RMPSearcher()
        self.aggregator = RMPAggregator()
        
    def analyze_course(self, course_info: Dict[str, str], user_profile: Dict[str, Any]) -> str:
        """
        Analyzes a single course based on extracted info and user profile.
        """
        course_id = course_info.get('course_id', 'Unknown Course')
        instructor = course_info.get('instructor', 'Staff')
        
        print(f"🕵️ Analyzing {course_id} with {instructor}...")
        
        # 1. Reality Check (Search)
        rmp_content = ""
        if instructor and instructor != "Staff":
            rmp_content = self.searcher.search_professor(instructor, "NYU")
            
        reddit_content = self.searcher.search_reddit(course_id)
        
        # 2. Generate Advice
        prompt = f"""
        You are a savvy "Senior Student" at NYU Tandon. 
        Give honest, direct advice about this course to a junior student.
        
        Course: {course_id} ({course_info.get('name')})
        Instructor: {instructor}
        
        User Profile:
        - Identity: {user_profile.get('identity')}
        - Goal: {user_profile.get('goal')}
        - Avoid: {', '.join(user_profile.get('avoid', []))}
        
        Real-world Feedback (Search Results):
        [Rate My Professor]: {rmp_content[:1000] if rmp_content else "No RMP found."}
        [Reddit/Online Discussions]: {reddit_content[:1000] if reddit_content else "No Reddit discussions found."}
        
        Instructions:
        1. **Vibe Check**: Is this course a "Gem" (神课) or a "Pitfall" (坑)?
        2. **Workload**: Is it easy A or heavy workload? Match with user's goal.
        3. **Professor**: Is the professor good? (Quote RMP if possible).
        4. **Verdict**: RECOMMENDED or NOT RECOMMENDED based on user's specific goal.
        
        Tone: Informal, helpful, realistic. Use emojis.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating advice: {e}"

if __name__ == "__main__":
    # Simple test
    advisor = CourseAdvisor()
    print(advisor.get_advice("I want a course with a good professor for AI."))

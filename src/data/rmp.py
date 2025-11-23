import os
from typing import Optional
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

class RMPSearcher:
    def __init__(self):
        self.tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    def search_professor(self, professor_name: str, school: str) -> str:
        """
        Searches for Rate My Professor page content for a given professor.
        """
        query = f"{professor_name} {school} Rate My Professors"
        try:
            response = self.tavily.search(query=query, search_depth="advanced", max_results=1)
            if not response.get('results'):
                return ""
            return response['results'][0]['content']
        except Exception as e:
            print(f"Error searching RMP for {professor_name}: {e}")
            return ""

    def search_reddit(self, course_code: str) -> str:
        """
        Searches Reddit for course reviews and workload discussions.
        """
        query = f"{course_code} NYU Tandon reddit workload review"
        try:
            # Search for top 2 results to get a mix of opinions
            response = self.tavily.search(query=query, search_depth="advanced", max_results=2)
            if not response.get('results'):
                return ""
            
            # Combine content from results
            combined_content = "\n\n".join([res['content'] for res in response['results']])
            return combined_content
        except Exception as e:
            print(f"Error searching Reddit for {course_code}: {e}")
            return ""

import google.generativeai as genai

import traceback

class RMPAggregator:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        
        # Try models in order of preference
        models_to_try = ['gemini-1.5-flash', 'gemini-2.0-flash-lite']
        self.model = None
        
        for model_name in models_to_try:
            try:
                # Test the model with a simple generation to see if it works
                test_model = genai.GenerativeModel(model_name)
                test_model.generate_content("Test")
                self.model = test_model
                print(f"✅ RMPAggregator initialized with {model_name}")
                break
            except Exception:
                continue
                
        if not self.model:
            print("⚠️ All models failed. Defaulting to gemini-2.0-flash-lite (unsafe).")
            self.model = genai.GenerativeModel('gemini-2.0-flash-lite')

    def summarize_reviews(self, professor_name: str, search_content: str) -> dict:
        if not search_content:
            return {"rating": 0.0, "summary": "No reviews found."}
            
        prompt = f"""
        You are an assistant summarizing professor reviews for a student.
        
        Based on the following search results from Rate My Professors (or similar sites), 
        provide a concise summary of the professor's teaching style, difficulty, and overall quality.
        Also, extract a numerical rating (0-5) if available, otherwise estimate it based on sentiment.
        
        Search Content:
        {search_content}
        
        Output Format:
        Rating: [0-5]/5
        Summary: [2-3 sentences summary]
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = response.text.strip()
            
            # Simple parsing of the result
            lines = result.split('\n')
            rating = 0.0
            summary = result
            
            for line in lines:
                if line.startswith("Rating:"):
                    try:
                        rating_str = line.split(":")[1].strip().split("/")[0]
                        rating = float(rating_str)
                    except:
                        pass
                elif line.startswith("Summary:"):
                    summary = line.split(":", 1)[1].strip()
            
            return {"rating": rating, "summary": summary}
        except Exception as e:
            print("\n🔴 严重错误：Gemini API 调用失败")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误详情: {str(e)}")
            traceback.print_exc()
            raise e

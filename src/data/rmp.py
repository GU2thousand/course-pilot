import os
import time
import traceback
from typing import Optional
from tavily import TavilyClient
from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core import exceptions

load_dotenv()

class RMPSearcher:
    def __init__(self):
        # 确保这里 api_key 读取正确
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
            response = self.tavily.search(query=query, search_depth="advanced", max_results=2)
            if not response.get('results'):
                return ""
            
            combined_content = "\n\n".join([res['content'] for res in response['results']])
            return combined_content
        except Exception as e:
            print(f"Error searching Reddit for {course_code}: {e}")
            return ""

class RMPAggregator:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        
        # 不要用 gemini-2.0-flash-lite，它对免费用户限制极严
        # 推荐使用 gemini-1.5-flash 或者 gemini-2.0-flash
        self.model_name = 'gemini-2.0-flash-lite' 
        self.model = genai.GenerativeModel(self.model_name)
        print(f"✅ 使用全新 Key 启动，模型锁定为: {self.model_name}")
        
        self.model = None
        self.model_name = ""

        print("🔄 初始化 AI 模型...")
        for name in candidates:
            try:
                # print(f"   尝试连接: {name} ...", end="") 
                # 这里不带 models/ 前缀尝试，如果失败 SDK 通常会自动处理
                test_model = genai.GenerativeModel(name)
                test_model.generate_content("Hi") 
                self.model = test_model
                self.model_name = name
                print(f"✅ 成功连接到主力模型: {name}")
                break
            except Exception:
                # 静默失败，尝试下一个
                continue
        
        if not self.model:
            print("⚠️ 警告：主力模型均连接失败。尝试使用 Lite 版本（可能受限）...")
            self.model_name = 'gemini-2.0-flash-lite'
            self.model = genai.GenerativeModel(self.model_name)

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
        
        # --- 自动重试机制 (针对 429 错误) ---
        max_retries = 3
        base_wait_time = 5 

        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                result = response.text.strip()
                
                # 简单解析逻辑
                lines = result.split('\n')
                rating = 0.0
                summary = result
                
                for line in lines:
                    if line.startswith("Rating:"):
                        try:
                            rating_str = line.split(":")[1].strip().split("/")[0]
                            clean_rating = ''.join(filter(lambda x: x.isdigit() or x == '.', rating_str))
                            rating = float(clean_rating)
                        except:
                            pass
                    elif line.startswith("Summary:"):
                        summary = line.split(":", 1)[1].strip()
                
                return {"rating": rating, "summary": summary}

            except exceptions.ResourceExhausted:
                # 遇到 429 错误：等待并重试
                wait_time = base_wait_time * (2 ** attempt) 
                print(f"\n⏳ 触发 API 速率限制。等待 {wait_time} 秒后重试 (模型: {self.model_name})...")
                time.sleep(wait_time)
            
            except Exception as e:
                print(f"\n⚠️ 未知错误: {e}")
                break 
        
        return {"rating": 0.0, "summary": "Error retrieving summary."}
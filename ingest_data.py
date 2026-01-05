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
        # 确保这里 api_key 读取正确，如果报错可以手动填入测试
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
        
        # --- 修改点 1: 移除复杂的测试回退逻辑，直接锁定最稳定的模型 ---
        self.model_name = 'gemini-1.5-flash'
        self.model = genai.GenerativeModel(self.model_name)
        print(f"✅ RMPAggregator initialized with {self.model_name}")

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
        
        # --- 修改点 2: 增加自动重试机制 (Retry Logic) ---
        max_retries = 3
        base_wait_time = 5  # 基础等待时间 5 秒

        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                result = response.text.strip()
                
                # Simple parsing
                lines = result.split('\n')
                rating = 0.0
                summary = result
                
                for line in lines:
                    if line.startswith("Rating:"):
                        try:
                            rating_str = line.split(":")[1].strip().split("/")[0]
                            # 清理可能出现的非数字字符
                            clean_rating = ''.join(filter(lambda x: x.isdigit() or x == '.', rating_str))
                            rating = float(clean_rating)
                        except:
                            pass
                    elif line.startswith("Summary:"):
                        try:
                            summary = line.split(":", 1)[1].strip()
                        except:
                            pass
                
                return {"rating": rating, "summary": summary}

            except exceptions.ResourceExhausted:
                # 专门捕获 429 配额超限错误
                wait_time = base_wait_time * (2 ** attempt) # 5s, 10s, 20s...
                print(f"\n⏳ 配额超限 (429)。正在等待 {wait_time} 秒后重试 (尝试 {attempt+1}/{max_retries})...")
                time.sleep(wait_time)
            
            except Exception as e:
                print(f"\n⚠️ 生成时发生未知错误: {e}")
                traceback.print_exc()
                break # 其他错误通常重试也没用，直接跳出
        
        # 如果重试多次还是失败，返回默认空值，防止程序崩溃
        print(f"❌ 无法处理教授 {professor_name} 的数据，跳过。")
        return {"rating": 0.0, "summary": "Error retrieving summary."}
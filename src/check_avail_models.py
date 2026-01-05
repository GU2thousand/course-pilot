import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ 没有找到 API Key")
else:
    genai.configure(api_key=api_key)
    print(f"🔑 使用 Key: {api_key[:5]}... 进行查询")
    
    print("\n📋 你的账号可用的模型列表：")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"  ✅ {m.name}")
    except Exception as e:
        print(f"❌ 查询失败: {e}")
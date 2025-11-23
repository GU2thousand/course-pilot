import os
import google.generativeai as genai
from dotenv import load_dotenv

# 1. 加载环境变量
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ 错误：未找到 GOOGLE_API_KEY，请检查你的 .env 文件")
else:
    print(f"✅ 找到 API Key: {api_key[:5]}******")
    
    # 2. 配置 API
    try:
        genai.configure(api_key=api_key)
        
        print("\n📡 正在连接 Google 服务器查询可用模型...")
        models = genai.list_models()
        
        found_any = False
        print("\n--- 你可以使用以下模型 (Text Generation) ---")
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                print(f"✅ {m.name}")
                found_any = True
        
        if not found_any:
            print("⚠️ 连接成功，但没有找到支持生成内容的模型。可能是地区限制或 Key 权限问题。")
            
    except Exception as e:
        print(f"\n❌ 连接失败，详细错误信息：\n{e}")

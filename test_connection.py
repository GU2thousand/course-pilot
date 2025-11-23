import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    print("📡 Testing connection to Gemini 1.5 Flash...")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found.")
        return

    genai.configure(api_key=api_key)
    
    models_to_try = ['gemini-1.5-flash', 'gemini-2.0-flash-lite']
    
    for model_name in models_to_try:
        print(f"🔄 Trying model: {model_name}...")
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Hello, are you online?")
            print(f"✅ Connection Successful with {model_name}! Response: {response.text}")
            return
        except Exception as e:
            print(f"⚠️ Failed with {model_name}: {e}")
            
    print("❌ All models failed.")

if __name__ == "__main__":
    test_connection()

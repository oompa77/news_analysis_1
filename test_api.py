"""
Test Google API Key functionality
"""
import os
from dotenv import load_dotenv
load_dotenv(override=True)

import google.generativeai as genai

api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key loaded: {api_key[:20]}...{api_key[-4:]}")
print()

genai.configure(api_key=api_key)

# Test with gemini-2.5-flash-lite (the model used in your app)
print("Testing gemini-2.5-flash-lite model...")
try:
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    response = model.generate_content("안녕하세요! 간단한 테스트입니다. '구글 API 작동 중'이라고 답변해주세요.")
    print("[SUCCESS] API is working!")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"[ERROR] {e}")

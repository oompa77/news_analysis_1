"""
Final API key test with override
"""
import os
from dotenv import load_dotenv

# CRITICAL: override existing environment variables
load_dotenv(override=True)

import google.generativeai as genai

api_key = os.getenv("GOOGLE_API_KEY")

print("="*60)
print("Final Gemini API Test")
print("="*60)
print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
print(f"Length: {len(api_key)}")
print()

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    print("Sending test request...")
    response = model.generate_content("Say 'API key is working!' in Korean")
    
    print()
    print("="*60)
    print("[SUCCESS] API Key is WORKING!")
    print("="*60)
    print(f"Response: {response.text}")
    
except Exception as e:
    print()
    print("="*60)
    print("[FAIL] API Key test failed")
    print("="*60)
    print(f"Error: {e}")

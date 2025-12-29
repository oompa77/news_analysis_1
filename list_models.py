"""
List available Gemini models
"""
import os
from dotenv import load_dotenv
load_dotenv(override=True)

import google.generativeai as genai

api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

print("="*60)
print("Available Gemini Models")
print("="*60)
print()

try:
    models = genai.list_models()
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            print(f"Model: {model.name}")
            print(f"  Display name: {model.display_name}")
            print(f"  Supported methods: {model.supported_generation_methods}")
            print()
except Exception as e:
    print(f"Error listing models: {e}")

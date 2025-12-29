# -*- coding: utf-8 -*-
"""
Test different models to find one with available quota
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv(override=True)

api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# Models to try (from most to least preferred)
models_to_try = [
    'gemini-2.5-flash-lite',
    'gemini-flash-lite-latest',
    'gemini-2.0-flash-lite',
    'gemini-pro-latest',
    'gemini-flash-latest',
    'gemini-2.0-flash',
]

print("Testing models for available quota...\n")

for model_name in models_to_try:
    try:
        print(f"Trying {model_name}...", end=" ")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say 'OK' in one word")
        print(f"[SUCCESS] - Response: {response.text.strip()}")
        print(f"\n*** Use this model: {model_name} ***\n")
        break
    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            print("[QUOTA EXCEEDED]")
        else:
            print(f"[ERROR] {str(e)[:100]}")

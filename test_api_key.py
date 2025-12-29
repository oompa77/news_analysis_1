# -*- coding: utf-8 -*-
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key loaded: {api_key[:20]}..." if api_key else "No API key found")

if api_key:
    try:
        # Configure the API
        genai.configure(api_key=api_key)
        
        # List all available models
        print("\n=== Available Models ===")
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                print(f"[OK] {model.name}")
                print(f"  Display Name: {model.display_name}")
                print(f"  Description: {model.description}")
                print(f"  Supported methods: {model.supported_generation_methods}")
                print()
        
        # Try to use the model
        print("\n=== Testing gemini-1.5-flash ===")
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content("Hello, respond with 'API is working!'")
            print(f"[SUCCESS] {response.text}")
        except Exception as e:
            print(f"[ERROR] Error with gemini-1.5-flash: {e}")
            
            # Try alternative model names
            print("\n=== Trying alternative model names ===")
            alternatives = [
                'models/gemini-1.5-flash',
                'gemini-pro',
                'models/gemini-pro',
                'gemini-1.5-pro',
                'models/gemini-1.5-pro'
            ]
            
            for alt_model in alternatives:
                try:
                    print(f"\nTrying {alt_model}...")
                    model = genai.GenerativeModel(alt_model)
                    response = model.generate_content("Hello")
                    print(f"[SUCCESS] {alt_model} works!")
                    break
                except Exception as e:
                    print(f"[ERROR] {alt_model} failed: {e}")
                    
    except Exception as e:
        print(f"\n[ERROR] Error configuring API: {e}")
else:
    print("Please set GOOGLE_API_KEY in .env file")

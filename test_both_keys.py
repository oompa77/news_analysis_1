"""
Test both Google API Keys
"""
import os
from dotenv import load_dotenv
load_dotenv(override=True)

import google.generativeai as genai

# Test Primary Key
print("="*60)
print("Testing PRIMARY API Key")
print("="*60)
primary_key = os.getenv("GOOGLE_API_KEY")
print(f"Key: {primary_key[:20]}...{primary_key[-4:]}")

try:
    genai.configure(api_key=primary_key)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    response = model.generate_content("Say 'Primary key works!'")
    print("[SUCCESS] Primary API key is working!")
    print(f"Response: {response.text[:50]}...")
except Exception as e:
    print(f"[ERROR] Primary key failed: {e}")

print()

# Test Backup Key
print("="*60)
print("Testing BACKUP API Key")
print("="*60)
backup_key = os.getenv("GOOGLE_API_KEY_BACKUP")
print(f"Key: {backup_key[:20]}...{backup_key[-4:]}")

try:
    genai.configure(api_key=backup_key)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    response = model.generate_content("Say 'Backup key works!'")
    print("[SUCCESS] Backup API key is working!")
    print(f"Response: {response.text[:50]}...")
except Exception as e:
    print(f"[ERROR] Backup key failed: {e}")

print()
print("="*60)
print("Test Complete")
print("="*60)

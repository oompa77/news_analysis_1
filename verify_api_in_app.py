# Direct API key test in Streamlit context
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

# Force reload
load_dotenv(override=True)

print("="*60)
print("API Key Verification in Streamlit Context")
print("="*60)

api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key: {api_key}")
print(f"Length: {len(api_key) if api_key else 0}")

if api_key and len(api_key) > 30:
    print("\n[OK] API key loaded successfully")
    
    # Test with Gemini
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Hello")
        print("[OK] Gemini API working!")
        print(f"Response: {response.text[:100]}")
    except Exception as e:
        print(f"[FAIL] Gemini API error: {e}")
else:
    print("\n[FAIL] API key not loaded or invalid")
    print("\nChecking .env file directly...")
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    with open(env_path, 'r') as f:
        for line in f:
            if 'GOOGLE_API_KEY' in line:
                print(f"Found in .env: {line.strip()}")

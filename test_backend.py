import sys
import os
import json
# Add current directory to path so we can import modules
sys.path.append(os.getcwd())

from modules import gemini_analyzer

# Mock Data
articles = [
    {"title": "Test Article 1 about AI", "press": "Test Press", "date": "2025-01-01"},
    {"title": "Test Article 2 about AI", "press": "Test Press", "date": "2025-01-01"},
    {"title": "Test Article 3 about AI", "press": "Test Press", "date": "2025-01-01"}
]
keyword = "AI Test"
context_summary = "Positive: 2, Negative: 0, Neutral: 1"

print("1. Testing clean_json_text...")
raw_json = '```json\n{"test": "ok"}\n```'
cleaned = gemini_analyzer.clean_json_text(raw_json)
if cleaned == '{"test": "ok"}':
    print("   [PASS] clean_json_text works.")
else:
    print(f"   [FAIL] clean_json_text failed: {cleaned}")

print("\n2. Testing generate_issue_report (Dry Run with Gemini)...")
try:
    # We call the function. It will use the API key from .env (loaded by module)
    # The prompt might be long, but for 3 articles it should be fast.
    response_json_str = gemini_analyzer.generate_issue_report(keyword, articles, context_summary)
    
    # Check if output is valid JSON
    data = json.loads(response_json_str)
    
    if "error" in data:
        print(f"   [FAIL] API returned error: {data['error']}")
        if "traceback" in data:
            print(f"   Traceback: {data['traceback']}")
    else:
        print("   [PASS] Valid JSON received.")
        print("   Keys found:", list(data.keys()))

except Exception as e:
    print(f"   [CRITICAL FAIL] Exception during execution: {e}")
    import traceback
    traceback.print_exc()

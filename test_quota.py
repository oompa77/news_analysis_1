"""
Check API quota and rate limits
"""
import os
from dotenv import load_dotenv
load_dotenv(override=True)

import google.generativeai as genai
import time

def test_key_quota(key_name, api_key):
    print("="*60)
    print(f"Testing {key_name}")
    print("="*60)
    print(f"Key: {api_key[:20]}...{api_key[-4:]}")
    print()
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    # Test multiple requests to check rate limits
    success_count = 0
    error_count = 0
    
    print("Sending 5 test requests...")
    for i in range(5):
        try:
            response = model.generate_content(f"Test request {i+1}: Say 'OK'")
            success_count += 1
            print(f"  Request {i+1}: [SUCCESS]")
        except Exception as e:
            error_count += 1
            print(f"  Request {i+1}: [ERROR] {str(e)[:80]}")
        time.sleep(0.5)  # Small delay between requests
    
    print()
    print(f"Results: {success_count} successful, {error_count} failed")
    print()
    
    return success_count, error_count

# Test Primary Key
primary_key = os.getenv("GOOGLE_API_KEY")
p_success, p_error = test_key_quota("PRIMARY API Key", primary_key)

# Test Backup Key
backup_key = os.getenv("GOOGLE_API_KEY_BACKUP")
b_success, b_error = test_key_quota("BACKUP API Key", backup_key)

# Summary
print("="*60)
print("SUMMARY")
print("="*60)
print(f"Primary Key:  {p_success}/5 successful")
print(f"Backup Key:   {b_success}/5 successful")
print()

if p_success == 5 and b_success == 5:
    print("[EXCELLENT] Both keys are working perfectly!")
elif p_success >= 3 or b_success >= 3:
    print("[WARNING] Some requests failed - possible rate limiting")
else:
    print("[ERROR] Both keys have issues - check quota limits")

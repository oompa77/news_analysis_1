"""
Debug script to check .env file parsing
"""
import os
from pathlib import Path

env_file = Path("c:/Users/oompa/Desktop/Cursor/News Analysis/.env")

print("="*60)
print("Direct .env File Reading Test")
print("="*60)
print()

# Read the file directly
print("Reading .env file directly:")
with open(env_file, 'r', encoding='utf-8') as f:
    content = f.read()
    print(content)
    print()

# Check each line
print("="*60)
print("Line-by-line analysis:")
print("="*60)
with open(env_file, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if 'GOOGLE_API_KEY' in line:
            print(f"Line {i}: {repr(line)}")
            parts = line.split('=')
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                print(f"  Key: {repr(key)}")
                print(f"  Value: {repr(value)}")
                print(f"  Value length: {len(value)}")

print()
print("="*60)
print("Using python-dotenv:")
print("="*60)

from dotenv import load_dotenv, dotenv_values

# Method 1: load_dotenv
load_dotenv(override=True)
api_key = os.getenv("GOOGLE_API_KEY")
print(f"os.getenv result: {repr(api_key)}")
print(f"Length: {len(api_key) if api_key else 0}")

# Method 2: dotenv_values
values = dotenv_values(env_file)
print(f"\ndotenv_values result: {repr(values.get('GOOGLE_API_KEY'))}")

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from modules import github_storage

print("=" * 50)
print("KEYWORD LIST DEBUG")
print("=" * 50)

# Check local files
print("\n1. Local files in data folder:")
if os.path.exists("data"):
    files = os.listdir("data")
    print(f"   Found {len(files)} files:")
    for f in files:
        if f.endswith(".json"):
            keyword = f.replace(".json", "")
            print(f"   - {keyword}")
else:
    print("   data folder not found!")

# Check GitHub credentials
print("\n2. GitHub credentials:")
github_token = os.getenv("GITHUB_TOKEN")
repo_name = os.getenv("REPO_NAME")
print(f"   GITHUB_TOKEN: {'✓ Set' if github_token else '✗ Not set'}")
print(f"   REPO_NAME: {repo_name if repo_name else '✗ Not set'}")

# Test get_repo()
print("\n3. Testing GitHub connection:")
try:
    repo = github_storage.get_repo()
    if repo:
        print(f"   ✓ Connected to: {repo.full_name}")
    else:
        print("   ✗ Not connected (using local mode)")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test get_keyword_list()
print("\n4. Testing get_keyword_list():")
try:
    keywords = github_storage.get_keyword_list()
    print(f"   Found {len(keywords)} keywords:")
    for k in keywords:
        print(f"   - {k}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)

import os
import sys
sys.path.insert(0, 'c:/Users/oompa/Desktop/Cursor/News Analysis')

from modules import github_storage

# Test get_keyword_list
keywords = github_storage.get_keyword_list()
print(f"Total keywords found: {len(keywords)}")
print(f"Keywords: {keywords}")
print()

# Check data folder directly
data_folder = "c:/Users/oompa/Desktop/Cursor/News Analysis/data"
if os.path.exists(data_folder):
    files = [f for f in os.listdir(data_folder) if f.endswith('.json')]
    print(f"Total JSON files in data folder: {len(files)}")
    for f in sorted(files):
        keyword = f.replace('.json', '')
        print(f"  - {keyword}")

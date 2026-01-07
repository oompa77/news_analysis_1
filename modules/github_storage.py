import os
import json

def save_report(keyword, data):
    """
    Saves the report data to local file.
    Path: data/{keyword}.json
    """
    filename = f"data/{keyword}.json"
    content = json.dumps(data, indent=2, ensure_ascii=False)
    
    try:
        os.makedirs("data", exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[SUCCESS] Saved {filename} locally.")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save locally: {e}")
        return False

def load_report(keyword):
    """
    Loads report data from local file.
    """
    filename = f"data/{keyword}.json"
    
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load {filename}: {e}")
            return None
    else:
        print(f"[INFO] File not found: {filename}")
        return None

def get_keyword_list():
    """
    Returns a sorted list of keywords (files) available in local storage.
    """
    keywords = []
    
    if os.path.exists("data"):
        try:
            for file in os.listdir("data"):
                if file.endswith(".json"):
                    keyword = file.replace(".json", "")
                    keywords.append(keyword)
            print(f"[INFO] Found {len(keywords)} keywords in local storage")
        except Exception as e:
            print(f"[ERROR] Failed to list files: {e}")
    else:
        print("[INFO] Data directory does not exist")
    
    return sorted(keywords)

def delete_report(keyword):
    """
    Deletes report data from local storage.
    """
    filename = f"data/{keyword}.json"
    
    if os.path.exists(filename):
        try:
            os.remove(filename)
            print(f"[SUCCESS] Deleted {filename}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to delete {filename}: {e}")
            return False
    else:
        print(f"[WARNING] File not found: {filename}")
        return False

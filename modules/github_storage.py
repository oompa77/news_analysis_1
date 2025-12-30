import os
import json
from github import Github, GithubException
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("REPO_NAME") # e.g., "username/repo"

def get_repo():
    if not GITHUB_TOKEN or not REPO_NAME:
        print("GitHub credentials not found. Using local storage mode.")
        return None
    try:
        g = Github(GITHUB_TOKEN)
        return g.get_repo(REPO_NAME)
    except Exception as e:
        print(f"Error accessing GitHub repo: {e}")
        return None

def save_report(keyword, data):
    """
    Saves the report data to GitHub (or local file if no credentials).
    Path: data/{keyword}.json
    """
    filename = f"data/{keyword}.json"
    content = json.dumps(data, indent=2, ensure_ascii=False)
    
    repo = get_repo()
    
    if repo:
        try:
            try:
                # Try to get existing file to get sha
                contents = repo.get_contents(filename)
                repo.update_file(contents.path, f"Update report for {keyword}", content, contents.sha)
                print(f"Updated {filename} on GitHub.")
            except GithubException:
                # File doesn't exist, create it
                repo.create_file(filename, f"Create report for {keyword}", content)
                print(f"Created {filename} on GitHub.")
            return True
        except Exception as e:
            print(f"Error saving to GitHub: {e}")
            # Fallback to local
    
    # Local Storage Fallback
    try:
        os.makedirs("data", exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Saved {filename} locally.")
        return True
    except Exception as e:
        print(f"Error saving locally: {e}")
        return False

def load_report(keyword):
    """
    Loads report data from GitHub (or local).
    """
    filename = f"data/{keyword}.json"
    repo = get_repo()
    
    if repo:
        try:
            contents = repo.get_contents(filename)
            json_data = contents.decoded_content.decode("utf-8")
            return json.loads(json_data)
        except Exception as e:
            print(f"GitHub load error (might not exist): {e}")
    
    # Local Fallback
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Local load error: {e}")
            
    return None

def get_keyword_list():
    """
    Returns a sorted list of keywords (files) available in storage.
    Combines keywords from both GitHub and local storage.
    """
    keywords = []
    repo = get_repo()
    
    # Try to get keywords from GitHub
    if repo:
        try:
            contents = repo.get_contents("data")
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(repo.get_contents(file_content.path))
                else:
                    if file_content.name.endswith(".json"):
                        keyword = file_content.name.replace(".json", "")
                        if keyword not in keywords:  # Manual dedup
                            keywords.append(keyword)
            print(f"Found {len(keywords)} keywords from GitHub")
        except Exception as e:
            print(f"Error listing files from GitHub: {e}")
    
    # Also check local storage (merge with GitHub results)
    if os.path.exists("data"):
        try:
            local_count = 0
            for file in os.listdir("data"):
                if file.endswith(".json"):
                    keyword = file.replace(".json", "")
                    if keyword not in keywords:  # Manual dedup
                        keywords.append(keyword)
                        local_count += 1
            if local_count > 0:
                print(f"Found {local_count} additional keywords from local storage")
        except Exception as e:
            print(f"Error listing local files: {e}")
    
    print(f"Total keywords: {len(keywords)}")
    return sorted(keywords)  # Return sorted list

def delete_report(keyword):
    """
    Deletes report data from GitHub (or local).
    """
    filename = f"data/{keyword}.json"
    repo = get_repo()
    
    if repo:
        try:
            contents = repo.get_contents(filename)
            repo.delete_file(contents.path, f"Delete report for {keyword}", contents.sha)
            print(f"Deleted {filename} from GitHub.")
            return True
        except Exception as e:
            print(f"GitHub delete error: {e}")
    
    # Local Fallback
    if os.path.exists(filename):
        try:
            os.remove(filename)
            print(f"Deleted {filename} locally.")
            return True
        except Exception as e:
            print(f"Local delete error: {e}")
            return False
    
    return False

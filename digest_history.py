import json
import os
from datetime import datetime

HISTORY_FILE = 'digest_history.json'

def load_digest_history():
    """Loads the digest history from a JSON file."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {HISTORY_FILE}. Returning empty history.")
            return []
    return []

def save_digest_history(history):
    """Saves the digest history to a JSON file."""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving history to {HISTORY_FILE}: {e}")

def add_digest_to_history(url, method, model, detail_level, digest_content, title):
    """Adds a new digest entry to the history."""
    history = load_digest_history()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    new_entry = {
        "timestamp": timestamp,
        "url": url,
        "title": title,
        "method": method,
        "model": model,
        "detail_level": detail_level,
        "digest_content": digest_content
    }
    
    history.insert(0, new_entry) # Add to the beginning of the list
    save_digest_history(history)

def delete_digest_from_history(timestamp):
    """Deletes a digest entry from the history by its timestamp."""
    history = load_digest_history()
    history = [entry for entry in history if entry.get("timestamp") != timestamp]
    save_digest_history(history)

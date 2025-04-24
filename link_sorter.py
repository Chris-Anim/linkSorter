import re
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

def extract_urls_from_text(text):
    # Basic URL pattern
    url_pattern = r'https?://[^\s<>()"\']+'
    return re.findall(url_pattern, text)

def extract_links_from_file(file_path: Path):
    ext = file_path.suffix.lower()
    urls = []

    if ext == ".txt" or ext == ".md":
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        urls = extract_urls_from_text(text)

    elif ext == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        urls = find_urls_in_json(data)

    else:
        raise ValueError(f"Unsupported file extension: {ext}")

    # Normalize and deduplicate
    clean = list({normalized for u in urls if (normalized := normalize_url(u)) is not None})

    return clean

def find_urls_in_json(data):
    """Recursively search for URLs in nested JSON."""
    urls = []
    if isinstance(data, dict):
        for v in data.values():
            urls.extend(find_urls_in_json(v))
    elif isinstance(data, list):
        for item in data:
            urls.extend(find_urls_in_json(item))
    elif isinstance(data, str):
        if data.startswith("http"):
            urls.append(data)
    return urls



def normalize_url(url):
    try:
        parsed = urlparse(url)
        return parsed.geturl().rstrip("/").split("#")[0]
    except ValueError:
        return None  # Invalid URL



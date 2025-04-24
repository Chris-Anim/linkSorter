# summarize_links.py

import re
import requests
from pathlib import Path
from urllib.parse import urlparse
from link_sorter import extract_links_from_file

OUTPUT_DIR = Path("output_md")
OUTPUT_DIR.mkdir(exist_ok=True)
DEFAULT_TAGS = ["unsorted"]
NON_HTML_FILE = Path("nonHtmlLinks.md")


def sanitize_filename(url):
    parsed = urlparse(url)
    return parsed.netloc.replace(".", "-")

def build_prompt(url):
    return f"""
Creates a short summary and useful tags for webpages.

Given this URL, write a 1–2 sentence summary based on what the title or domain suggests. Then list 3–5 tags that might describe it.

URL: {url}

Output format:
SUMMARY: <summary>
TAGS: <tag1>, <tag2>, ...
"""

def call_llama(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    if response.status_code != 200:
        print(f"❌ LLaMA error {response.status_code}")
        return None

    return response.json().get("response", "")

def to_camel_case(tag):
    words = re.split(r'\s+', tag.strip())
    if not words:
        return ""
    return words[0].lower() + ''.join(w.capitalize() for w in words[1:])

def log_non_html_link(url):
    with open(NON_HTML_FILE, "a", encoding="utf-8") as f:
        f.write(f"- {url}\n")
    print(f"⚠️ Skipped non-HTML link: {url}")


def is_valid_html_link(url):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False

    non_html_extensions = [".pdf", ".epub", ".zip", ".jpg", ".png", ".svg", ".docx", ".csv"]
    if any(parsed.path.lower().endswith(ext) for ext in non_html_extensions):
        return False

    return True
   
def parse_response(raw_response):
    if "TAGS:" not in raw_response:
        return raw_response.strip(), DEFAULT_TAGS

    summary_part, tags_part = raw_response.split("TAGS:")
    summary = summary_part.replace("SUMMARY:", "").strip()
    raw_tags = [t.strip() for t in tags_part.strip().split(",") if t.strip()]
    camel_tags = [to_camel_case(tag) for tag in raw_tags]
    return summary, camel_tags if camel_tags else DEFAULT_TAGS

def write_markdown(url, summary, tags):
    name = sanitize_filename(url)
    md_file = OUTPUT_DIR / f"{name}.md"

    content = f"""---
title: "{name}"
url: "{url}"
summary: "{summary}"
tags: [{', '.join(tags)}]
---

# {name}

{summary}
"""
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Saved: {md_file}")

if __name__ == "__main__":
    from sys import argv

    if len(argv) != 2:
        print("Usage: python summarize_links.py <input_file>")
        exit(1)

    file_path = Path(argv[1])
    if not file_path.exists():
        print("❌ File not found:", file_path)
        exit(1)

    links = extract_links_from_file(file_path)
    print(f"🔍 Found {len(links)} unique link(s).")

    for url in links:
        if not is_valid_html_link(url):
            log_non_html_link(url)
            continue
        print(f"🧠 Processing: {url}")
        prompt = build_prompt(url)
        raw = call_llama(prompt)

        if raw is None:
            continue

        summary, tags = parse_response(raw)
        write_markdown(url, summary, tags)

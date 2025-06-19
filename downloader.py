import requests
from bs4 import BeautifulSoup
import argparse
import os
import re
import time
import random

# Random user-agents for disguise
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A372 Safari/604.1"
]

def sanitize_filename(name):
    return "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).rstrip()

def clean_text(text):
    text = re.sub(r'[^\S\r\n]+', ' ', text)  # collapse multiple spaces
    text = text.replace('\u3164', '')        # remove invisible filler (ㅤ)
    return text.strip()

def remove_duplicates(lines):
    seen = set()
    result = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            result.append(line)
    return result

def extract_chapter_text(soup):
    text_div = soup.find("div", class_="text-left")
    if not text_div:
        return []

    lines = []
    found_start = False

    for tag in text_div.find_all(["h2", "p"]):
        text = clean_text(tag.get_text(separator=" ", strip=True))
        if not text:
            continue
        if not found_start and tag.name == "h2":
            found_start = True
        if found_start:
            lines.append(text)

    lines = remove_duplicates(lines)
    return [line for line in lines if line.strip()]

def get_next_chapter_url(soup):
    next_div = soup.find("div", class_="nav-next")
    if next_div and next_div.a and next_div.a.has_attr("href"):
        return next_div.a["href"]
    return None

def download_and_save_chapter(url, visited, output_dir="chapters"):
    print(f"\n>>> Visiting: {url}")
    if url in visited:
        print("Already visited. Stopping loop.")
        return None
    visited.add(url)

    chapter_id = sanitize_filename(url.rstrip('/').split('/')[-1])
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, chapter_id + ".txt")

    if os.path.exists(output_path):
        print(f"Already downloaded: {output_path} — skipping content download.")
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        return get_next_chapter_url(soup)

    # Random delay
    delay = random.uniform(4, 9)
    print(f"Waiting {delay:.2f} seconds to avoid throttling...")
    time.sleep(delay)

    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    lines = extract_chapter_text(soup)

    if not lines:
        print("No content found, skipping.")
        return get_next_chapter_url(soup)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(lines))
    print(f"Saved: {output_path}")

    return get_next_chapter_url(soup)

def crawl_from_chapter(start_url, output_dir="chapters"):
    visited = set()
    current_url = start_url

    while current_url:
        next_url = download_and_save_chapter(current_url, visited, output_dir)
        if not next_url or next_url in visited:
            print("No next chapter or loop detected. Done.")
            break
        current_url = next_url

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crawl ZetroTranslation chapters forward with throttling protection.")
    parser.add_argument("start_url", help="Starting chapter URL")
    args = parser.parse_args()

    crawl_from_chapter(args.start_url)

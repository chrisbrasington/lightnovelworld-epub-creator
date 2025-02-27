import requests
from bs4 import BeautifulSoup
import argparse
import os
import subprocess
import time
import random, re
import tempfile

def sanitize_filename(name):
    return "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).rstrip()

def get_novel_title_and_author(page_path):
    with open(page_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, 'html.parser')
    
    title = soup.select_one("h1.novel-title").text.strip()
    author = soup.select_one("div.author span[itemprop='author']").text.strip()
    return title, author

def download_page(url, output_path):
    subprocess.run([
        "wget", "--user-agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36",
        "-O", output_path, url
    ], check=True)

def get_chapter_urls(page_path):
    with open(page_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, 'html.parser')
    
    chapter_urls = []
    next_page = True
    page_num = 1
    base_url = "https://www.lightnovelworld.com"
    
    while next_page:
        chapter_list = soup.select("ul.chapter-list li a")
        for chapter in chapter_list:
            chapter_url = chapter['href']
            if chapter_url.startswith("//"):
                chapter_url = "https:" + chapter_url
            elif chapter_url.startswith("/"):
                chapter_url = base_url + chapter_url
            chapter_urls.append(chapter_url)
        
        next_link = soup.select_one("a.pagination-next")
        if next_link:
            page_num += 1
            next_page_path = os.path.join(os.path.dirname(page_path), f"chapters_page_{page_num}.html")
            download_page(base_url + next_link['href'], next_page_path)
            with open(next_page_path, "r", encoding="utf-8") as next_file:
                soup = BeautifulSoup(next_file, 'html.parser')
        else:
            next_page = False
    
    return chapter_urls

def get_cover_image(soup, novel_dir):
    cover_path_jpg = os.path.join(novel_dir, "cover.jpg")
    cover_path_png = os.path.join(novel_dir, "cover.png")
    
    if os.path.exists(cover_path_jpg):
        print("Using existing cover.jpg")
        return cover_path_jpg
    elif os.path.exists(cover_path_png):
        print("Using existing cover.png")
        return cover_path_png
    
    cover_element = soup.select_one("div.fixed-img figure.cover img")
    cover_url = cover_element["src"] if cover_element else None
    
    if cover_url:
        if cover_url.startswith("//"):
            cover_url = "https:" + cover_url
        cover_path = os.path.join(novel_dir, "cover.jpg")
        subprocess.run(["wget", "-O", cover_path, cover_url], check=True)
        print("Downloaded cover image.")
        return cover_path
    else:
        print("Cover image not found.")
        return None

def extract_chapter_number(url):
    """Extracts the chapter number from the URL."""
    chapter_number = url.rstrip('/').split('/')[-1]
    return chapter_number

def download_chapter(url, novel_dir, min_delay=5, max_delay=12):
    """Downloads a chapter using wget and saves the text content from the chapter-container."""
    chapter_number = extract_chapter_number(url)
    chapter_file = os.path.join(novel_dir, f"{chapter_number}.txt")

    # Ensure the directory exists
    os.makedirs(novel_dir, exist_ok=True)

    if os.path.exists(chapter_file):
        print(f"Chapter {chapter_number} already exists, skipping download.")
        return

    print(f"Downloading: {url} -> {chapter_file}")

    try:
        # Create a temporary file to store the downloaded HTML
        with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as temp_html_file:
            temp_html_path = temp_html_file.name

            # Use wget to download the page into the temporary file
            subprocess.run([
                "wget", "--user-agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36",
                "-O", temp_html_path,
                url
            ], check=True)

            # Parse the downloaded HTML from the temporary file
            with open(temp_html_path, "r", encoding="utf-8") as file:
                soup = BeautifulSoup(file, 'html.parser')

            # Extract content from the chapter-container
            chapter_content = soup.select_one("#chapter-container")
            
            if chapter_content:
                # Clean the text by stripping extra spaces and newlines
                text_content = chapter_content.get_text("\n", strip=True)

                # Write the content to the .txt file
                with open(chapter_file, "w", encoding="utf-8") as file:
                    file.write(text_content)

                print(f"Saved: {chapter_file}")
            else:
                print(f"Chapter content not found for {chapter_number}")

    except subprocess.CalledProcessError as e:
        print(f"Download failed for {url}: {e}")
        if os.path.exists(chapter_file):
            os.remove(chapter_file)  # Remove any incomplete file
        return

    # Add a random delay before the next download
    delay = random.uniform(min_delay, max_delay)
    print(f"Waiting {delay:.2f} seconds before next download...")
    time.sleep(delay)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape chapter URLs from a light novel page.")
    parser.add_argument("base_url", type=str, help="Base URL of the novel page")
    args = parser.parse_args()
    
    temp_dir = "novels"
    os.makedirs(temp_dir, exist_ok=True)
    
    page_file = os.path.join(temp_dir, "novel_page.html")
    if not os.path.exists(page_file):
        download_page(args.base_url, page_file)
    else:
        print(f"Using cached file: {page_file}")
    
    title, author = get_novel_title_and_author(page_file)
    novel_dir = os.path.join(temp_dir, sanitize_filename(title))
    os.makedirs(novel_dir, exist_ok=True)
    
    new_page_file = os.path.join(novel_dir, "index.html")
    if not os.path.exists(new_page_file):
        os.rename(page_file, new_page_file)
    
    with open(new_page_file, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, 'html.parser')
    
    cover_path = get_cover_image(soup, novel_dir)
    
    chapters_page_url = args.base_url + "/chapters"
    chapters_page_file = os.path.join(novel_dir, "chapters_page_1.html")
    if not os.path.exists(chapters_page_file):
        download_page(chapters_page_url, chapters_page_file)
    
    chapters = get_chapter_urls(chapters_page_file)
    chapters_file = os.path.join(novel_dir, "chapters.txt")
    
    if not os.path.exists(chapters_file):
        with open(chapters_file, "w", encoding="utf-8") as f:
            f.write("\n".join(chapters))
    
    print(f"Title: {title}\nAuthor: {author}")
    print("Chapters saved to", chapters_file)
    
    proceed = input("Download chapters? (y/n): ")
    if proceed.lower() == 'y':
        for chapter_url in chapters:
            download_chapter(chapter_url, novel_dir)
    
    print("All chapters downloaded.")
    proceed = input("Make EPUB? (y/n): ")
    if proceed.lower() == 'y':
        print("EPUB generation will be implemented next.")

import requests
from bs4 import BeautifulSoup
import argparse
import os
import subprocess

def sanitize_filename(name):
    return "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).rstrip()

def get_novel_title_and_author(page_path):
    with open(page_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, 'html.parser')

    title_element = soup.select_one("h1.novel-title")
    author_element = soup.select_one("div.author span[itemprop='author']")

    title = title_element.text.strip() if title_element else "Unknown Title"
    author = author_element.text.strip() if author_element else "Unknown Author"

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

def save_metadata(novel_dir, title, author):
    metadata_file = os.path.join(novel_dir, "metadata.txt")
    with open(metadata_file, "w", encoding="utf-8") as f:
        f.write(f"Title: {title}\nAuthor: {author}\n")

def load_metadata(novel_dir):
    metadata_file = os.path.join(novel_dir, "metadata.txt")
    if os.path.exists(metadata_file):
        with open(metadata_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            title = lines[0].split(": ")[1].strip()
            author = lines[1].split(": ")[1].strip()
            return title, author
    return None, None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape chapter URLs from a light novel page.")
    parser.add_argument("base_url", type=str, help="Base URL of the novel page")
    args = parser.parse_args()

    temp_dir = "novels"
    os.makedirs(temp_dir, exist_ok=True)

    # Determine the novel directory
    page_file = os.path.join(temp_dir, "novel_page.html")
    if not os.path.exists(page_file):
        download_page(args.base_url, page_file)

    # Load metadata if available
    title, author = get_novel_title_and_author(page_file)
    novel_dir = os.path.join(temp_dir, sanitize_filename(title))
    os.makedirs(novel_dir, exist_ok=True)

    existing_title, existing_author = load_metadata(novel_dir)
    if existing_title and existing_author:
        print("Using cached metadata.")
        title, author = existing_title, existing_author
    else:
        save_metadata(novel_dir, title, author)

    new_page_file = os.path.join(novel_dir, "index.html")
    if not os.path.exists(new_page_file):
        os.rename(page_file, new_page_file)

    with open(new_page_file, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, 'html.parser')

    cover_path = get_cover_image(soup, novel_dir)

    # Handle chapters
    chapters_page_url = args.base_url + "/chapters"
    chapters_file = os.path.join(novel_dir, "chapters.txt")
    chapters_page_file = os.path.join(novel_dir, "chapters_page_1.html")

    if os.path.exists(chapters_file):
        print("Using cached chapters.")
        with open(chapters_file, "r", encoding="utf-8") as f:
            chapters = f.read().splitlines()
    else:
        download_page(chapters_page_url, chapters_page_file)
        chapters = get_chapter_urls(chapters_page_file)
        with open(chapters_file, "w", encoding="utf-8") as f:
            f.write("\n".join(chapters))

    print(f"Title: {title}\nAuthor: {author}")
    print("Chapters saved to", chapters_file)

    proceed = input("Proceed with EPUB generation? (y/n): ")
    if proceed.lower() == 'y':
        print("EPUB generation will be implemented next.")

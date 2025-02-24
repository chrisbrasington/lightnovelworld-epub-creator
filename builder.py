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
    while next_page:
        chapter_list = soup.select("ul.chapter-list li a")
        for chapter in chapter_list:
            chapter_urls.append("https://www.lightnovelworld.com" + chapter['href'])
        
        next_link = soup.select_one("a.pagination-next")
        if next_link:
            page_num += 1
            next_page_path = os.path.join(os.path.dirname(page_path), f"chapters_page_{page_num}.html")
            download_page(next_link['href'], next_page_path)
            with open(next_page_path, "r", encoding="utf-8") as next_file:
                soup = BeautifulSoup(next_file, 'html.parser')
        else:
            next_page = False
    
    return chapter_urls

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape chapter URLs from a light novel page.")
    parser.add_argument("base_url", type=str, help="Base URL of the novel page")
    args = parser.parse_args()
    
    temp_dir = "novels"
    os.makedirs(temp_dir, exist_ok=True)
    
    page_file = os.path.join(temp_dir, "novel_page.html")
    download_page(args.base_url, page_file)
    
    title, author = get_novel_title_and_author(page_file)
    novel_dir = os.path.join(temp_dir, sanitize_filename(title))
    os.makedirs(novel_dir, exist_ok=True)
    
    new_page_file = os.path.join(novel_dir, "index.html")
    os.rename(page_file, new_page_file)
    
    chapters_page_url = args.base_url + "/chapters"
    chapters_page_file = os.path.join(novel_dir, "chapters_page_1.html")
    download_page(chapters_page_url, chapters_page_file)
    
    chapters = get_chapter_urls(chapters_page_file)
    print(f"Title: {title}\nAuthor: {author}")
    print("Chapters:", chapters)

import os
import re
from ebooklib import epub

def get_metadata(novel_dir):
    metadata_file = os.path.join(novel_dir, "metadata.txt")
    title, author = "Unknown Title", "Unknown Author"

    if os.path.exists(metadata_file):
        with open(metadata_file, 'r', encoding="utf-8") as file:
            for line in file:
                if line.lower().startswith("title:"):
                    title = line.split(":", 1)[1].strip()
                elif line.lower().startswith("author:"):
                    author = line.split(":", 1)[1].strip()
    else:
        print(f"No metadata.txt found in {novel_dir}.")
        title = input("Enter title: ").strip()
        author = input("Enter author: ").strip()
        with open(metadata_file, 'w', encoding="utf-8") as file:
            file.write(f"Title: {title}\nAuthor: {author}\n")

    return title, author

def chapter_sort_key(filename):
    match = re.search(r'chapter-(\d+)', filename)
    return int(match.group(1)) if match else 99999  # push malformed ones to the end

def create_epub_from_directory(novel_dir):
    novel_title, novel_author = get_metadata(novel_dir)
    print(f"Creating EPUB for {novel_title} by {novel_author}")

    book = epub.EpubBook()
    book.set_title(novel_title)
    book.set_language('en')
    book.add_author(novel_author)

    cover_path = os.path.join(novel_dir, "cover.png")
    if os.path.exists(cover_path):
        book.set_cover("cover.png", open(cover_path, 'rb').read())

    # Title page
    title_page = epub.EpubHtml(title="Title Page", file_name="title.xhtml", lang="en")
    title_page.content = f'''
    <html><head></head><body style="text-align:center;">
        <h1>{novel_title}</h1>
        <h2>by {novel_author}</h2>
    </body></html>
    '''
    book.add_item(title_page)

    # Chapter files from `chapters/`, sorted by chapter number
    chapters_dir = os.path.join(novel_dir, "chapters")
    chapter_files = sorted([
        f for f in os.listdir(chapters_dir)
        if f.endswith(".txt") and f.startswith("chapter-")
    ], key=chapter_sort_key)

    chapter_items = []

    for chapter_file in chapter_files:
        chapter_path = os.path.join(chapters_dir, chapter_file)
        with open(chapter_path, "r", encoding="utf-8") as f:
            content = f.read()

        chapter_title = chapter_file.replace(".txt", "").replace("-", " ").title()
        html_name = chapter_file.replace(".txt", ".xhtml")

        chapter = epub.EpubHtml(title=chapter_title, file_name=html_name, lang='en')
        chapter.content = f"<html><head></head><body><h1>{chapter_title}</h1><p>{content.replace(chr(10), '<br>')}</p></body></html>"

        book.add_item(chapter)
        chapter_items.append(chapter)

    # Optional cover page
    if os.path.exists(cover_path):
        cover_page = epub.EpubHtml(title="Cover", file_name="cover.xhtml", lang="en")
        cover_page.content = f'''
        <html><head></head><body style="text-align:center;">
            <img src="cover.png" alt="Cover Image" style="max-width:100%; height:auto;"/>
        </body></html>
        '''
        book.add_item(cover_page)
        book.spine = [title_page, cover_page, 'nav'] + chapter_items
    else:
        book.spine = [title_page, 'nav'] + chapter_items

    # TOC and required items
    book.toc = [epub.Link(c.file_name, c.title, c.get_id()) for c in chapter_items]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Output EPUB
    output_path = os.path.join(novel_dir, f"{novel_title}.epub")
    epub.write_epub(output_path, book)
    print(f"✅ EPUB created: {output_path}\n")

if __name__ == "__main__":
    novel_dir = "."  # current directory where ./chapters and metadata.txt are located
    chapters_dir = os.path.join(novel_dir, "chapters")

    if os.path.isdir(chapters_dir):
        create_epub_from_directory(novel_dir)
    else:
        print("Error: chapters/ directory not found.")

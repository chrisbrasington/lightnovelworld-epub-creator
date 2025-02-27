import os
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
    
    return title, author

def format_chapter_title(filename):
    """ Converts 'chapter-6-1.txt' -> 'Chapter 6–1' """
    filename = filename.replace(".txt", "").lower()
    
    if filename.startswith("chapter-"):
        return "Chapter " + filename[8:].replace("-", "–")  # Hyphen to en-dash
    
    return filename.replace("-", " ").title()  # Fallback formatting

def create_epub_from_directory(novel_dir, chapters_file):
    novel_title, novel_author = get_metadata(novel_dir)
    print(f"Creating EPUB for {novel_title} by {novel_author}")

    book = epub.EpubBook()
    book.set_title(novel_title)
    book.set_language('en')
    book.add_author(novel_author)

    cover_image_path = os.path.join(novel_dir, "cover.jpg")
    if os.path.exists(cover_image_path):
        with open(cover_image_path, 'rb') as cover_image:
            book.set_cover("cover.jpg", cover_image.read())

    if not os.path.exists(chapters_file):
        print(f"Error: {chapters_file} not found in {novel_dir}. Skipping.")
        return

    with open(chapters_file, 'r', encoding="utf-8") as file:
        chapters = [line.strip() for line in file.readlines() if line.strip()]

    chapter_htmls = []
    toc_entries = []

    for chapter_url in chapters:
        chapter_filename = f"{os.path.splitext(chapter_url.split('/')[-1])[0]}.txt"
        chapter_path = os.path.join(novel_dir, chapter_filename)

        if os.path.exists(chapter_path):
            print(f"Processing {chapter_filename}...")
            
            with open(chapter_path, 'r', encoding="utf-8") as chapter_file:
                chapter_content = chapter_file.read()

            formatted_title = format_chapter_title(chapter_filename)
            chapter_xhtml_filename = f"{os.path.splitext(chapter_filename)[0]}.xhtml"

            chapter_html = epub.EpubHtml(title=formatted_title, 
                                         file_name=chapter_xhtml_filename, 
                                         lang='en')
            formatted_content = f"<html><head></head><body><h1>{formatted_title}</h1><p>{chapter_content.replace(chr(10), '<br>')}</p></body></html>"
            chapter_html.content = formatted_content
 
            book.add_item(chapter_html)
            chapter_htmls.append(chapter_html)
            toc_entries.append(chapter_html)
        else:
            print(f"Missing: {chapter_path}")

    # Generate ToC as a separate XHTML page
    toc_content = "<html><head><title>Table of Contents</title></head><body><h1>Table of Contents</h1><ul>"
    for chapter_html in chapter_htmls:
        toc_content += f'<li><a href="{chapter_html.file_name}">{chapter_html.title}</a></li>'
    toc_content += "</ul></body></html>"

    toc_page = epub.EpubHtml(title="Table of Contents", file_name="toc.xhtml", lang="en")
    toc_page.content = toc_content
    book.add_item(toc_page)

    # Apply CSS styling
    style = '''
    body { font-family: "Times New Roman", serif; line-height: 1.5; }
    h1, h2 { font-family: "Georgia", serif; }
    '''
    css = epub.EpubItem(uid="style", file_name="style.css", media_type="text/css", content=style)
    book.add_item(css)

    for chapter_html in chapter_htmls:
        chapter_html.add_item(css)

    # **Fixed Table of Contents structure**
    book.toc = [
        epub.Link("toc.xhtml", "Table of Contents", "toc"),
        (epub.Section("Chapters"), toc_entries)
    ]

    # Set spine (reading order)
    book.spine = ['nav', toc_page] + chapter_htmls

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub_filename = os.path.join(novel_dir, f"{novel_title}.epub")
    epub.write_epub(epub_filename, book)

    print(f"EPUB file created: {epub_filename}")

if __name__ == "__main__":
    novels_dir = "novels"

    for folder_name in os.listdir(novels_dir):
        novel_dir = os.path.join(novels_dir, folder_name)
        
        if os.path.isdir(novel_dir) and os.path.exists(os.path.join(novel_dir, "chapters.txt")):
            chapters_file = os.path.join(novel_dir, "chapters.txt")
            print(f"Creating EPUB for {novel_dir}...")
            create_epub_from_directory(novel_dir, chapters_file)
        else:
            print(f"Skipping {novel_dir}, no chapters.txt found.")

import os
from ebooklib import epub

def get_metadata(novel_dir):
    """Extracts title and author from metadata.txt"""
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

def create_epub_from_directory(novel_dir, chapters_file):
    """Creates an EPUB file from the given directory."""
    novel_title, novel_author = get_metadata(novel_dir)
    print(f"Creating EPUB for {novel_title} by {novel_author}")

    book = epub.EpubBook()
    book.set_title(novel_title)
    book.set_language('en')
    book.add_author(novel_author)

    # Set cover image if available
    cover_image_path = os.path.join(novel_dir, "cover.jpg")
    if os.path.exists(cover_image_path):
        book.set_cover("cover.jpg", open(cover_image_path, 'rb').read())

    # Title Page
    title_page = epub.EpubHtml(title="Title Page", file_name="title.xhtml", lang="en")
    title_page.content = f'''
    <html><head></head><body style="text-align:center;">
        <h1>{novel_title}</h1>
        <h2>by {novel_author}</h2>
    </body></html>
    '''
    book.add_item(title_page)

    # Read chapters.txt for the chapter order
    if not os.path.exists(chapters_file):
        print(f"Error: {chapters_file} not found in {novel_dir}. Skipping.")
        return

    with open(chapters_file, 'r', encoding="utf-8") as file:
        chapters = [line.strip() for line in file.readlines() if line.strip()]

    chapter_htmls = []
    toc_links = []

    # Process chapters
    for chapter_url in chapters:
        chapter_filename = f"{os.path.splitext(chapter_url.split('/')[-1])[0]}.txt"
        chapter_path = os.path.join(novel_dir, chapter_filename)

        if os.path.exists(chapter_path):
            print(f"Processing {chapter_filename}...")

            with open(chapter_path, 'r', encoding="utf-8") as chapter_file:
                chapter_content = chapter_file.read()

            chapter_title = chapter_filename.replace(".txt", "").replace("-", " ")
            chapter_title = chapter_title.replace('chapter', "Chapter")
            chapter_html = epub.EpubHtml(title=chapter_title, file_name=f"{chapter_title}.xhtml", lang='en')
            chapter_html.content = f"<html><head></head><body><h1>{chapter_title}</h1><p>{chapter_content.replace(chr(10), '<br>')}</p></body></html>"

            book.add_item(chapter_html)
            chapter_htmls.append(chapter_html)
            toc_links.append(epub.Section(chapter_title, chapter_html))
        else:
            print(f"Missing: {chapter_path}")

    # Table of Contents Page
    toc_html = epub.EpubHtml(title="Table of Contents", file_name="toc.xhtml", lang="en")
    toc_html.content = "<html><head></head><body><h1>Table of Contents</h1><ul>"
    for chapter in toc_links:
        toc_html.content += f'<li><a href="{chapter.href}">{chapter.title}</a></li>'
    toc_html.content += "</ul></body></html>"

    book.add_item(toc_html)

    # Add style
    style = '''
    body { font-family: "Times New Roman", serif; line-height: 1.5; }
    h1, h2 { font-family: "Georgia", serif; text-align: center; }
    '''
    css = epub.EpubItem(uid="style", file_name="style.css", media_type="text/css", content=style)
    book.add_item(css)

    for item in [title_page, toc_html] + chapter_htmls:
        item.add_item(css)

    # Organize EPUB spine & TOC order
    book.spine = ['nav', title_page, toc_html] + chapter_htmls
    book.toc = [epub.Section("Chapters", toc_links)]

    # Required items for EPUB
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Write EPUB file
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

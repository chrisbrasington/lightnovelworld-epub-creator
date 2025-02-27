import os
from ebooklib import epub

def get_metadata(novel_dir):
    metadata_file = os.path.join(novel_dir, "metadata.txt")
    
    title = "Unknown Title"
    author = "Unknown Author"
    
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r', encoding="utf-8") as file:
            for line in file:
                if line.lower().startswith("title:"):
                    title = line.split(":", 1)[1].strip()
                elif line.lower().startswith("author:"):
                    author = line.split(":", 1)[1].strip()
    
    return title, author

def format_chapter_title(filename):
    """Converts filenames like 'chapter-6-1.txt' to 'Chapter 6-1'."""
    name, _ = os.path.splitext(filename)  # Remove '.txt'
    return name.replace("chapter-", "Chapter ").capitalize()

def create_epub_from_directory(novel_dir, chapters_file):
    novel_title, novel_author = get_metadata(novel_dir)

    print(f"Creating EPUB for {novel_title} by {novel_author}")

    book = epub.EpubBook()
    book.set_title(novel_title)
    book.set_language('en')
    book.add_author(novel_author)

    # Add cover image if available
    cover_image_path = os.path.join(novel_dir, "cover.jpg")
    if os.path.exists(cover_image_path):
        with open(cover_image_path, 'rb') as cover_image:
            book.set_cover("cover.jpg", cover_image.read())

    if not os.path.exists(chapters_file):
        print(f"Error: {chapters_file} not found in {novel_dir}. Skipping.")
        return

    # Read chapter list from chapters.txt
    with open(chapters_file, 'r', encoding="utf-8") as file:
        chapters = [line.strip() for line in file.readlines() if line.strip()]

    chapter_htmls = []

    for chapter_url in chapters:
        chapter_filename = f"{os.path.splitext(chapter_url.split('/')[-1])[0]}.txt"
        chapter_path = os.path.join(novel_dir, chapter_filename)

        if os.path.exists(chapter_path):
            print(f"Processing {chapter_filename}...")
            
            with open(chapter_path, 'r', encoding="utf-8") as chapter_file:
                chapter_content = chapter_file.read()

            chapter_title = format_chapter_title(chapter_filename)
            chapter_html = epub.EpubHtml(title=chapter_title, 
                                         file_name=f"{os.path.splitext(chapter_filename)[0]}.xhtml", 
                                         lang='en')
            formatted_content = f"<html><head></head><body><h1>{chapter_title}</h1><p>{chapter_content.replace(chr(10), '<br>')}</p></body></html>"
            chapter_html.content = formatted_content
 
            book.add_item(chapter_html)
            chapter_htmls.append(chapter_html)
        else:
            print(f"Missing: {chapter_path}")

    # Add styling
    style = '''
    body { font-family: "Times New Roman", serif; line-height: 1.5; }
    h1, h2 { font-family: "Georgia", serif; }
    '''
    css = epub.EpubItem(uid="style", file_name="style.css", media_type="text/css", content=style)
    book.add_item(css)

    for chapter_html in chapter_htmls:
        chapter_html.add_item(css)

    # Correctly format the Table of Contents
    book.toc = chapter_htmls  # Directly list chapters without extra section

    # Define the spine (without extra ToC page)
    book.spine = ['nav'] + chapter_htmls

    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Write the EPUB file
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

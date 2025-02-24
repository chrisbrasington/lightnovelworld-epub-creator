import os
from ebooklib import epub

def get_metadata(novel_dir):
    # Path to the metadata.txt file
    metadata_file = os.path.join(novel_dir, "metadata.txt")
    
    # Initialize default values
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

def create_epub_from_directory(novel_dir, chapters_file):
    # Get title and author from metadata.txt
    novel_title, novel_author = get_metadata(novel_dir)

    print("  "+novel_dir)
    print("  "+novel_title)
    print("  "+novel_author)

    # Create EPUB object
    book = epub.EpubBook()

    # Set metadata for the book
    book.set_title(novel_title)
    book.set_language('en')
    book.add_author(novel_author)

    # Get the cover image if it exists
    cover_image_path = os.path.join(novel_dir, "cover.jpg")
    if os.path.exists(cover_image_path):
        with open(cover_image_path, 'rb') as cover_image:
            book.set_cover("cover.jpg", cover_image.read())

    # Ensure that the chapters file exists
    if not os.path.exists(chapters_file):
        print(f"Error: {chapters_file} not found in {novel_dir}. Skipping.")
        return

    # Create the table of contents dynamically
    toc_content = "<h1>Table of Contents</h1><ul>"
    
    # Open the chapters file
    with open(chapters_file, 'r', encoding="utf-8") as chapters_file:
        chapters = chapters_file.readlines()
        for chapter in chapters:
            chapter_url = chapter.strip()
            chapter_title = f"Chapter {chapter_url.split('/')[-1]}"

            # print(chapter_title)
            
            # Add chapter to ToC
            toc_content += f'<li><a href="{chapter_title}.xhtml">{chapter_title}</a></li>'
    
    toc_content += "</ul>"
    
    # Add ToC as a separate HTML file to the EPUB
    toc = epub.EpubHtml(title='Table of Contents', file_name='index.xhtml', lang='en')
    toc.content = toc_content  # Set the content directly
    book.add_item(toc)

    # Add chapters to the EPUB
    chapter_htmls = []  # Keep track of chapter HTMLs for the spine

    for chapter in chapters:
        chapter_url = chapter.strip()
        chapter_filename = f"{chapter_url.split('/')[-1]}.txt"
        chapter_path = os.path.join(novel_dir, chapter_filename)

        print(chapter_path)
        
        if os.path.exists(chapter_path):
            print(f"Processing {chapter_filename}...")  # Print the chapter being processed
            
            with open(chapter_path, 'r', encoding="utf-8") as chapter_file:
                chapter_content = chapter_file.read()

                # print(chapter_content)

            chapter_html = epub.EpubHtml(title=chapter_filename, file_name=f"{chapter_filename}.xhtml", lang='en')
            chapter_html.content = chapter_content  # Set the content directly
            book.add_item(chapter_html)

            chapter_htmls.append(chapter_html)  # Add chapter to the list of chapter HTMLs
        else:
            print(f"Missing: {chapter_path}")

    # Define CSS for the EPUB
    style = '''
    body {
        font-family: "Times New Roman", Times, serif;
        line-height: 1.5;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: "Georgia", serif;
    }
    '''
    css = epub.EpubItem(uid="style", file_name="style.css", media_type="text/css", content=style)
    book.add_item(css)

    # Add spine (ensure we only add valid chapter HTMLs)
    book.spine = ['nav'] + [toc] + chapter_htmls

    # Generate the EPUB file
    epub_filename = os.path.join(novel_dir, f"{novel_title}.epub")
    epub.write_epub(epub_filename, book)

    print(f"EPUB file created: {epub_filename}")

if __name__ == "__main__":
    # Path to the 'novels' directory
    novels_dir = "novels"

    # Loop through all subdirectories (novels)
    for folder_name in os.listdir(novels_dir):
        novel_dir = os.path.join(novels_dir, folder_name)
        
        # Check if it's a directory and contains the chapters.txt file
        if os.path.isdir(novel_dir) and os.path.exists(os.path.join(novel_dir, "chapters.txt")):
            chapters_file = os.path.join(novel_dir, "chapters.txt")
            print(f"Creating EPUB for {novel_dir}...")
            create_epub_from_directory(novel_dir, chapters_file)
        else:
            print(f"Skipping {novel_dir}, no chapters.txt found.")

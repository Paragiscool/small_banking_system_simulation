import fitz
import os
import re

def extract_pdf_to_files(pdf_path, output_dir, num_files=25):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    # We will collect all text, trying to keep some structure, but a simple way is to chunk the text.
    # Alternatively, we could group pages.
    # If we have e.g. 100 pages and want 25 files, we can put 4 pages per file.
    
    pages_per_file = max(1, total_pages // num_files)
    
    # Let's try a more semantic approach if possible, but page chunking is safest.
    file_index = 1
    current_text = ""
    start_page = 0
    
    # Or even better, let's just extract all text and chunk it by tokens/words or lines so we get exactly around num_files.
    all_text = []
    for page_num in range(total_pages):
        page = doc.load_page(page_num)
        text = page.get_text()
        all_text.append(text)
        
    full_text = "\n".join(all_text)
    
    # Split the full text into paragraphs or blocks
    paragraphs = full_text.split('\n\n')
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    # Divide paragraphs into num_files files
    chunk_size = max(1, len(paragraphs) // num_files)
    
    for i in range(num_files):
        start_idx = i * chunk_size
        # The last file takes the remaining paragraphs
        end_idx = (i + 1) * chunk_size if i < num_files - 1 else len(paragraphs)
        
        chunk = paragraphs[start_idx:end_idx]
        
        # Try to find a reasonable title from the first paragraph of the chunk
        title_candidate = chunk[0].split('\n')[0][:50]
        title_candidate = re.sub(r'[^A-Za-z0-9 ]+', '', title_candidate).strip()
        title_candidate = title_candidate.replace(' ', '_')
        if not title_candidate:
            title_candidate = "Section"
            
        filename = f"{i+1:02d}_{title_candidate}.txt"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n\n".join(chunk))
            
    print(f"Successfully created {num_files} files in {output_dir}")

if __name__ == '__main__':
    pdf_file = "463549D_Open_Banking_API_Gateway_Developer_Portal_Design.pdf"
    out_dir = "extracted_content"
    extract_pdf_to_files(pdf_file, out_dir, num_files=25)

"""
Script to extract well tops table from a well completion report PDF.
"""

import PyPDF2
import pandas as pd
import re
from pathlib import Path

def extract_text_from_pdf(pdf_path):
    """Extract all text from PDF file."""
    text_by_page = []
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        num_pages = len(pdf_reader.pages)
        print(f"Total pages in PDF: {num_pages}")
        
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            text_by_page.append({
                'page': page_num + 1,
                'text': text
            })
    
    return text_by_page

def find_well_tops_section(text_by_page):
    """Find pages containing well tops information."""
    well_tops_pages = []
    keywords = ['well top', 'formation top', 'stratigraphic', 'tops', 'depth', 'formation']
    
    for page_info in text_by_page:
        text_lower = page_info['text'].lower()
        if any(keyword in text_lower for keyword in keywords):
            well_tops_pages.append(page_info)
    
    return well_tops_pages

def extract_well_tops_table(pdf_path, output_csv='well_tops.csv'):
    """
    Extract well tops table from PDF and save to CSV.
    
    Parameters:
    -----------
    pdf_path : str
        Path to the well completion report PDF
    output_csv : str
        Output CSV filename
    """
    print(f"Processing PDF: {pdf_path}")
    
    # Extract text from PDF
    text_by_page = extract_text_from_pdf(pdf_path)
    
    # Find pages with well tops information
    well_tops_pages = find_well_tops_section(text_by_page)
    
    print(f"\nFound {len(well_tops_pages)} pages potentially containing well tops data")
    
    # Display text from relevant pages for inspection
    for page_info in well_tops_pages:
        print(f"\n{'='*80}")
        print(f"PAGE {page_info['page']}")
        print('='*80)
        print(page_info['text'][:1000])  # Print first 1000 characters
        print("...")
    
    return text_by_page, well_tops_pages

if __name__ == "__main__":
    # Path to the well completion report PDF
    pdf_path = Path("Raw dataset/well completion report anya 105.pdf")
    
    if not pdf_path.exists():
        print(f"Error: PDF file not found at {pdf_path}")
    else:
        text_by_page, well_tops_pages = extract_well_tops_table(pdf_path)
        
        print("\n" + "="*80)
        print("NEXT STEPS:")
        print("="*80)
        print("1. Review the extracted text above to identify the well tops table structure")
        print("2. We'll create a custom parser based on the table format")
        print("3. Extract the data into a structured DataFrame")
        print("4. Export to CSV/Excel")

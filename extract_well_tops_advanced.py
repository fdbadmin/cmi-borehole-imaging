"""
Advanced script to extract well tops table from PDF using pdfplumber.
This tool is better at extracting structured tables from PDFs.
"""

import pdfplumber
import pandas as pd
from pathlib import Path
import re

def extract_tables_from_pdf(pdf_path):
    """Extract all tables from PDF using pdfplumber."""
    all_tables = []
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total pages: {len(pdf.pages)}\n")
        
        for i, page in enumerate(pdf.pages):
            page_num = i + 1
            
            # Extract tables from this page
            tables = page.extract_tables()
            
            if tables:
                print(f"Page {page_num}: Found {len(tables)} table(s)")
                for j, table in enumerate(tables):
                    if table and len(table) > 0:
                        # Check if this might be a well tops table
                        table_text = str(table).lower()
                        if any(keyword in table_text for keyword in ['formation', 'depth', 'top', 'md', 'tvd']):
                            print(f"  Table {j+1} (potential well tops table):")
                            # Show first few rows
                            for row in table[:min(5, len(table))]:
                                print(f"    {row}")
                            
                            all_tables.append({
                                'page': page_num,
                                'table_num': j + 1,
                                'data': table
                            })
    
    return all_tables

def search_for_well_tops_text(pdf_path):
    """Search for well tops information in text."""
    formations_found = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_num = i + 1
            text = page.extract_text()
            
            if text:
                text_lower = text.lower()
                # Look for well tops section
                if 'well tops' in text_lower or 'stratigraphic tops' in text_lower or 'formation tops' in text_lower:
                    print(f"\n{'='*80}")
                    print(f"PAGE {page_num} - Potential Well Tops Section")
                    print('='*80)
                    
                    # Extract the relevant section
                    lines = text.split('\n')
                    for idx, line in enumerate(lines):
                        if 'top' in line.lower() or 'formation' in line.lower():
                            # Print context (5 lines before and after)
                            start = max(0, idx - 5)
                            end = min(len(lines), idx + 10)
                            print('\n'.join(lines[start:end]))
                            print('-' * 40)
                            break
                
                # Look for depth patterns with formation names
                depth_pattern = r'(\d{2,4}(?:\.\d{1,2})?)\s*m?\s*(md|tvd|mdrt|tvdrt)?\s*[:\-]?\s*([A-Z][a-zA-Z\s]+(?:Formation|Sandstone|Coal|Measures))'
                matches = re.finditer(depth_pattern, text, re.IGNORECASE)
                
                for match in matches:
                    formations_found.append({
                        'page': page_num,
                        'depth': match.group(1),
                        'depth_type': match.group(2) or 'MD',
                        'formation': match.group(3).strip()
                    })
    
    return formations_found

def main():
    pdf_path = Path("Raw dataset/well completion report anya 105.pdf")
    
    if not pdf_path.exists():
        print(f"Error: PDF file not found at {pdf_path}")
        return
    
    print("="*80)
    print("EXTRACTING TABLES FROM PDF")
    print("="*80)
    
    # Extract tables
    tables = extract_tables_from_pdf(pdf_path)
    
    print("\n" + "="*80)
    print("SEARCHING FOR WELL TOPS IN TEXT")
    print("="*80)
    
    # Search for well tops in text
    formations = search_for_well_tops_text(pdf_path)
    
    if formations:
        print(f"\n\nFound {len(formations)} potential formation tops:")
        df = pd.DataFrame(formations)
        print(df.to_string(index=False))
        
        # Save to CSV
        output_file = "well_tops_extracted.csv"
        df.to_csv(output_file, index=False)
        print(f"\n✓ Saved to {output_file}")
    
    if tables:
        print(f"\n\nFound {len(tables)} tables that might contain well tops data.")
        print("Review the output above to identify the correct table.")
        
        # Try to save the most promising table
        for table_info in tables:
            try:
                df = pd.DataFrame(table_info['data'])
                output_file = f"table_page{table_info['page']}_num{table_info['table_num']}.csv"
                df.to_csv(output_file, index=False, header=False)
                print(f"✓ Saved table from page {table_info['page']} to {output_file}")
            except Exception as e:
                print(f"✗ Could not save table from page {table_info['page']}: {e}")

if __name__ == "__main__":
    main()

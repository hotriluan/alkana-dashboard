import pdfplumber
import os
import json

pdf_dir = r"c:\dev\alkana-dashboard\demodata_md"
output_dir = r"c:\dev\alkana-dashboard\extracted_pdfs"

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# List of PDFs to process
pdfs = [
    "mvt.pdf",
    "Order type.pdf",
    "Customer group.pdf",
    "distribution Channel.pdf",
    "MRP Controller.pdf",
    "Purchasing Document type.pdf",
    "Purchasing Group.pdf",
    "Purchasing Org.pdf",
    "Sales Office.pdf",
    "plant.pdf",
    "storage location.pdf"
]

for pdf_name in pdfs:
    pdf_path = os.path.join(pdf_dir, pdf_name)
    
    if not os.path.exists(pdf_path):
        print(f"Warning: {pdf_name} not found")
        continue
    
    try:
        print(f"\n{'='*60}")
        print(f"Processing: {pdf_name}")
        print(f"{'='*60}")
        
        with pdfplumber.open(pdf_path) as pdf:
            all_text = []
            all_tables = []
            
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"\n--- Page {page_num} ---")
                
                # Extract text
                text = page.extract_text()
                if text and text.strip():
                    all_text.append(f"=== Page {page_num} ===\n{text}\n")
                    print(f"Text found: {len(text)} characters")
                
                # Extract tables
                tables = page.extract_tables()
                if tables:
                    print(f"Tables found: {len(tables)}")
                    for table_num, table in enumerate(tables, 1):
                        all_tables.append({
                            'page': page_num,
                            'table_num': table_num,
                            'data': table
                        })
            
            # Save text
            if all_text:
                output_file = os.path.join(output_dir, pdf_name.replace('.pdf', '_text.txt'))
                with open(output_file, 'w', encoding='utf-8') as out:
                    out.write('\n'.join(all_text))
                print(f"✓ Text saved: {output_file}")
            
            # Save tables as markdown
            if all_tables:
                output_file = os.path.join(output_dir, pdf_name.replace('.pdf', '_tables.md'))
                with open(output_file, 'w', encoding='utf-8') as out:
                    out.write(f"# {pdf_name}\n\n")
                    
                    for table_info in all_tables:
                        out.write(f"## Page {table_info['page']} - Table {table_info['table_num']}\n\n")
                        
                        table = table_info['data']
                        if table and len(table) > 0:
                            # Write header
                            if table[0]:
                                header = [str(cell) if cell else '' for cell in table[0]]
                                out.write('| ' + ' | '.join(header) + ' |\n')
                                out.write('| ' + ' | '.join(['---' for _ in header]) + ' |\n')
                            
                            # Write data rows
                            for row in table[1:]:
                                if row:
                                    row_data = [str(cell) if cell else '' for cell in row]
                                    out.write('| ' + ' | '.join(row_data) + ' |\n')
                        
                        out.write('\n')
                
                print(f"✓ Tables saved: {output_file}")
            
            # Also save raw table data as JSON
            if all_tables:
                output_file = os.path.join(output_dir, pdf_name.replace('.pdf', '_tables.json'))
                with open(output_file, 'w', encoding='utf-8') as out:
                    json.dump(all_tables, out, indent=2, ensure_ascii=False)
                print(f"✓ Raw tables saved: {output_file}")
            
    except Exception as e:
        print(f"✗ Error processing {pdf_name}: {str(e)}")
        import traceback
        traceback.print_exc()

print(f"\n{'='*60}")
print(f"Extraction complete. Files saved to: {output_dir}")
print(f"{'='*60}")

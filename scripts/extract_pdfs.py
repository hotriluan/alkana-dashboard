import PyPDF2
import os

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
        # Open PDF
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Extract text from all pages
            text_content = []
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                text_content.append(f"=== Page {page_num + 1} ===\n{text}\n")
            
            # Save to text file
            output_file = os.path.join(output_dir, pdf_name.replace('.pdf', '.txt'))
            with open(output_file, 'w', encoding='utf-8') as out:
                out.write('\n'.join(text_content))
            
            print(f"✓ Extracted: {pdf_name} ({len(pdf_reader.pages)} pages)")
            
    except Exception as e:
        print(f"✗ Error processing {pdf_name}: {str(e)}")

print(f"\nExtraction complete. Files saved to: {output_dir}")

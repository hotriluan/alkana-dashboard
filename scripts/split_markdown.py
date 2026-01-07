
import os

INPUT_FILE = r'c:\dev\alkana-dashboard\demodata_md\zrsd006.md'
OUTPUT_DIR = r'c:\dev\alkana-dashboard\demodata_md'
LINES_PER_CHUNK = 2000
HEADER_LINES = 4 # Number of lines to repeat at the top of each split (Title + Table Header)

def split_markdown():
    print(f"Splitting {INPUT_FILE}...")
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    total_lines = len(lines)
    print(f"Total lines: {total_lines}")
    
    header = lines[:HEADER_LINES]
    content = lines[HEADER_LINES:]
    
    # Calculate chunks
    # We want chunks of roughly LINES_PER_CHUNK content lines
    # But for simplicity, we just iterate.
    
    chunk_index = 1
    for i in range(0, len(content), LINES_PER_CHUNK):
        chunk_content = content[i : i + LINES_PER_CHUNK]
        
        output_filename = f"zrsd006_part{chunk_index}.md"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as out_f:
            # Write header
            out_f.writelines(header)
            # Write chunk content
            out_f.writelines(chunk_content)
            
        print(f"Created {output_filename} ({len(chunk_content) + len(header)} lines)")
        chunk_index += 1

if __name__ == "__main__":
    split_markdown()

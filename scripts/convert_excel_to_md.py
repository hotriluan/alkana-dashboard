import pandas as pd
import os
import glob

# Paths
INPUT_DIR = r"c:\dev\alkana-dashboard\demodata"
OUTPUT_DIR = r"c:\dev\alkana-dashboard\demodata_md"

# Ensure output directory exists
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def convert_excel_to_md(file_path):
    try:
        filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(filename)[0]
        output_path = os.path.join(OUTPUT_DIR, f"{name_without_ext}.md")

        print(f"Processing: {filename}...")
        
        # Read Excel file
        # Using openpyxl engine for xlsx files
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # Convert to Markdown
        markdown_content = f"# Data from {filename}\n\n"
        markdown_content += df.to_markdown(index=False, tablefmt="github")
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
            
        print(f"Success: Saved to {output_path}")
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main():
    # Find all xlsx files (case insensitive search not directly supported by glob in windows traditionally, 
    # but strictly speaking glob uses OS specific rules. We'll grab .XLSX and .xlsx just in case or browse all)
    
    files = glob.glob(os.path.join(INPUT_DIR, "*.XLSX")) + glob.glob(os.path.join(INPUT_DIR, "*.xlsx"))
    # Remove duplicates if filesystem is case insensitive
    files = list(set(files))
    
    if not files:
        print("No Excel files found in demodata.")
        return

    print(f"Found {len(files)} files.")
    for file in files:
        convert_excel_to_md(file)

if __name__ == "__main__":
    main()

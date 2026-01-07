with open('src/db/models.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Checking for missing row_hash after raw_data:")
for i, line in enumerate(lines):
    if 'raw_data = Column(JSONB)' in line:
        if i+1 < len(lines) and 'row_hash' not in lines[i+1]:
            print(f"Line {i+1}: Missing row_hash after: {line.strip()}")
        else:
            print(f"Line {i+1}: Has row_hash: {line.strip()}")

"""Fix all duplicate row_hash entries in models.py"""

with open('src/db/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all instances where row_hash appears twice on same line
content = content.replace('raw_data = Column(JSONB)    row_hash = Column(String(32))  # MD5 hash for change detection    row_hash = Column(String(32))  # MD5 hash for change detection', 
                          'raw_data = Column(JSONB)\n    row_hash = Column(String(32))  # MD5 hash for change detection')

# Save
with open('src/db/models.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed duplicate row_hash entries")

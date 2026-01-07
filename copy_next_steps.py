import os
import shutil

source = r"plans\2025-12-25-fullstack-web-dashboard\NEXT_STEPS.md"
dest = r"next_steps_content.txt"

try:
    if os.path.exists(source):
        shutil.copy2(source, dest)
        print(f"Successfully copied {source} to {dest}")
    else:
        print(f"Source file not found: {source}")
except Exception as e:
    print(f"Error copying file: {e}")

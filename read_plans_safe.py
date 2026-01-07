import os
import sys

# Ensure stdout uses UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

plan_dir = r"plans/2025-12-25-fullstack-web-dashboard"
files_to_read = [
    "NEXT_STEPS.md",
    "GAP_ANALYSIS_SUMMARY.md",
    "plan.md",
    "COMPREHENSIVE_GAP_ANALYSIS.md"
]

for filename in files_to_read:
    filepath = os.path.join(plan_dir, filename)
    print(f"\n{'='*40}")
    print(f"FILE: {filename}")
    print(f"{'='*40}\n")
    
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                print(f.read())
        except Exception as e:
            print(f"Error reading {filename}: {e}")
    else:
        print(f"File not found: {filepath}")

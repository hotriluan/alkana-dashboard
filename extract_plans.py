"""
Extract key sections from plan files for analysis
"""
import os
import sys

# Force UTF-8 output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

plan_dir = r"plans\2025-12-25-fullstack-web-dashboard"
files = ["NEXT_STEPS.md", "GAP_ANALYSIS_SUMMARY.md", "plan.md"]

for filename in files:
    filepath = os.path.join(plan_dir, filename)
    if os.path.exists(filepath):
        print(f"\n{'='*80}")
        print(f"FILE: {filename}")
        print(f"{'='*80}\n")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:150]  # First 150 lines
                print(''.join(lines))
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"File not found: {filename}")

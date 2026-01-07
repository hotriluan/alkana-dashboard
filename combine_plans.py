import sys
import os

# Read all important plan files and save to a combined output
plan_dir = r"plans\2025-12-25-fullstack-web-dashboard"
output_file = r"temp_plans_combined.txt"

files_to_read = [
    "NEXT_STEPS.md",
    "GAP_ANALYSIS_SUMMARY.md",
    "COMPREHENSIVE_GAP_ANALYSIS.md",
    "plan.md"
]

with open(output_file, 'w', encoding='utf-8') as out:
    for filename in files_to_read:
        filepath = os.path.join(plan_dir, filename)
        if os.path.exists(filepath):
            out.write(f"\n{'='*80}\n")
            out.write(f"FILE: {filename}\n")
            out.write(f"{'='*80}\n\n")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    out.write(content)
                    out.write("\n\n")
            except Exception as e:
                out.write(f"Error reading {filename}: {e}\n\n")
        else:
            out.write(f"File not found: {filename}\n\n")

print(f"Combined plans saved to: {output_file}")
print(f"File size: {os.path.getsize(output_file)} bytes")

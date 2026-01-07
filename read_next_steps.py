import sys

# Read the NEXT_STEPS.md file
file_path = r"plans\2025-12-25-fullstack-web-dashboard\NEXT_STEPS.md"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    print(content)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)

import pandas as pd
from datetime import datetime

def safe_datetime(val):
    """Safely convert value to datetime"""
    if pd.isna(val):
        return None
    try:
        if isinstance(val, datetime):
            return val
        result = pd.to_datetime(val)
        print(f"  Converted '{val}' -> {result}")
        return result
    except Exception as e:
        print(f"  ❌ Failed '{val}': {e}")
        return None

# Test with different formats
print("🧪 TEST SAFE_DATETIME FUNCTION")
print("=" * 80)

test_values = [
    "2026-01-13 00:00:00",
    datetime(2026, 1, 13),
    "2026-01-13",
    None,
    "",
    pd.NaT,
]

for val in test_values:
    print(f"\nInput: {repr(val)} (type: {type(val).__name__})")
    result = safe_datetime(val)
    print(f"Output: {result}")

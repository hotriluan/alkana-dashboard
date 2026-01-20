#!/usr/bin/env python
import sys

# Clear modules
for k in list(sys.modules.keys()):
    if 'src' in k or 'api' in k:
        try:
            del sys.modules[k]
        except:
            pass

# Fresh import
from src.api.main import app

print("All leadtime routes in app:")
leadtime_routes = [r for r in app.routes if hasattr(r, 'path') and 'leadtime' in r.path]
if not leadtime_routes:
    print("  NO ROUTES FOUND!")
    print("\nAll routes in app:")
    for route in app.routes:
        if hasattr(route, 'path'):
            print(f"  {route.path}")
else:
    for route in leadtime_routes:
        print(f"  {route.path} - {route.methods if hasattr(route, 'methods') else 'N/A'}")

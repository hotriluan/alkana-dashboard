#!/usr/bin/env python3
"""
Debug Inventory API Response

Checks if top-movers-and-dead-stock returns valid data
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.db.connection import SessionLocal
from src.core.inventory_analytics import InventoryAnalytics
import json


def debug_inventory_data():
    """Debug inventory velocity data"""
    db = SessionLocal()
    try:
        analytics = InventoryAnalytics(db)
        
        print("=" * 60)
        print("INVENTORY VELOCITY DEBUG")
        print("=" * 60)
        
        # Get data
        top_movers, dead_stock = analytics.get_top_movers_and_dead_stock(
            start_date=None,  # Default 90 days
            end_date=None,
            limit=10,
            category='ALL_CORE'
        )
        
        print(f"\n📊 Top Movers: {len(top_movers)} items")
        for i, item in enumerate(top_movers[:5], 1):
            print(f"  {i}. {item.material_code[:30]:30s} | "
                  f"Velocity: {item.velocity_score:3d} | "
                  f"Stock: {item.stock_kg:10,.0f} kg")
        
        print(f"\n🔴 Dead Stock: {len(dead_stock)} items")
        for i, item in enumerate(dead_stock[:5], 1):
            print(f"  {i}. {item.material_code[:30]:30s} | "
                  f"Velocity: {item.velocity_score:3d} | "
                  f"Stock: {item.stock_kg:10,.0f} kg")
        
        # Check for zero velocity in top movers
        if top_movers:
            zero_velocity = [m for m in top_movers if m.velocity_score == 0]
            if zero_velocity:
                print(f"\n⚠️  WARNING: {len(zero_velocity)} top movers have zero velocity!")
        
        # Sample JSON output
        print("\n" + "=" * 60)
        print("SAMPLE JSON RESPONSE:")
        print("=" * 60)
        response = {
            "top_movers": [m.dict() for m in top_movers[:3]],
            "dead_stock": [m.dict() for m in dead_stock[:3]]
        }
        print(json.dumps(response, indent=2, default=str))
        
    finally:
        db.close()


if __name__ == "__main__":
    try:
        debug_inventory_data()
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

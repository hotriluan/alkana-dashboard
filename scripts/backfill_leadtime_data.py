"""
Backfill Lead-time Data for Existing Production Orders

Calculates and populates lead-time data for all existing records in fact_production.
Uses LeadTimeCalculator to compute MTO/MTS lead-times.

Run: python scripts/backfill_leadtime_data.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from src.db.connection import engine, SessionLocal
from src.db.models import FactProduction
import pandas as pd
from datetime import datetime

def load_movement_data():
    """Load MB51 movement data for lead-time calculation"""
    query = """
        SELECT 
            batch,
            plant_code,
            mvt_type,
            posting_date,
            purchase_order,
            reference
        FROM fact_inventory
        WHERE mvt_type IN (101, 601)
        ORDER BY posting_date
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df

def load_po_data():
    """Load purchase order data"""
    query = """
        SELECT 
            purch_order,
            purch_date
        FROM fact_purchase_order
        WHERE purch_order LIKE '44%'
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df

def load_delivery_data():
    """Load delivery data"""
    query = """
        SELECT 
            delivery,
            actual_gi_date
        FROM fact_delivery
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df

def calculate_leadtime_simple(order):
    """
    Simplified lead-time calculation without full LeadTimeCalculator
    Calculates only production time for now (Release → Finish)
    """
    release_date = order.get('release_date')
    finish_date = order.get('actual_finish_date')
    
    if not release_date or not finish_date:
        return {
            'production_time_days': None,
            'total_leadtime_days': None,
            'leadtime_status': 'UNKNOWN'
        }
    
    # Calculate production time (handles both date and datetime objects)
    try:
        if hasattr(release_date, 'date'):
            release_date = release_date.date()
        if hasattr(finish_date, 'date'):
            finish_date = finish_date.date()
        
        production_time = (finish_date - release_date).days
    except Exception as e:
        print(f"   ⚠️  Error calculating time for order {order.get('batch')}: {e}")
        return {
            'production_time_days': None,
            'total_leadtime_days': None,
            'leadtime_status': 'UNKNOWN'
        }
    
    # Determine status (simplified)
    status = 'UNKNOWN'
    if production_time is not None:
        target = 21 if order.get('is_mto') else 14
        if production_time <= target:
            status = 'ON_TIME'
        elif production_time <= target * 1.2:
            status = 'DELAYED'
        else:
            status = 'CRITICAL'
    
    return {
        'production_time_days': production_time,
        'total_leadtime_days': production_time,  # For now, only production time
        'leadtime_status': status
    }

def backfill_leadtime_data():
    """Backfill lead-time data for all production orders with full stage calculation"""
    
    print("="*70)
    print("BACKFILL LEAD-TIME DATA - FULL CALCULATION")
    print("="*70)
    
    db = SessionLocal()
    
    try:
        # Get all production orders
        print("\n📊 Loading production orders...")
        orders = db.query(FactProduction).all()
        print(f"   Found {len(orders)} production orders")
        
        if len(orders) == 0:
            print("   ⚠️  No production orders found. Exiting.")
            return
        
        # Load movement data for transit and storage calculations
        print("\n📦 Loading inventory movements (MVT 101, 601)...")
        movements_query = text("""
            SELECT batch, plant_code, mvt_type, posting_date, purchase_order, reference
            FROM fact_inventory
            WHERE mvt_type IN (101, 601) AND batch IS NOT NULL
            ORDER BY batch, posting_date
        """)
        movements_df = pd.read_sql(movements_query, db.connection())
        print(f"   Loaded {len(movements_df)} movements")
        
        # Load purchase order data for preparation time
        print("\n📋 Loading purchase orders (PO starting with 44)...")
        po_query = text("""
            SELECT purch_order, purch_date
            FROM fact_purchase_order
            WHERE purch_order LIKE '44%'
        """)
        po_df = pd.read_sql(po_query, db.connection())
        print(f"   Loaded {len(po_df)} purchase orders")
        
        # Load delivery data for delivery time
        print("\n🚚 Loading delivery documents...")
        delivery_query = text("""
            SELECT delivery, actual_gi_date
            FROM fact_delivery
            WHERE actual_gi_date IS NOT NULL
        """)
        delivery_df = pd.read_sql(delivery_query, db.connection())
        print(f"   Loaded {len(delivery_df)} deliveries")
        
        # Process each order
        print("\n🔄 Calculating lead-times (all stages)...")
        updated_count = 0
        skipped_count = 0
        stats = {
            'prep': 0, 'prod': 0, 'transit': 0, 'storage': 0, 'delivery': 0
        }
        
        for i, order in enumerate(orders, 1):
            if i % 100 == 0:
                print(f"   Progress: {i}/{len(orders)} ({i*100//len(orders)}%)")
            
            # Get order dates
            release_date = order.release_date
            finish_date = order.actual_finish_date
            batch = order.batch
            plant = order.plant_code
            is_mto = order.is_mto
            
            # Initialize all times as None
            prep_time = None
            production_time = None
            transit_time = None
            storage_time = None
            delivery_time = None
            
            # 1. PRODUCTION TIME (always calculate if dates available)
            if release_date and finish_date:
                try:
                    production_time = (finish_date - release_date).days
                    stats['prod'] += 1
                except:
                    pass
            
            # 2. TRANSIT TIME (Finish → Receipt MVT 101)
            if finish_date and batch:
                mvt_101 = movements_df[
                    (movements_df['batch'] == batch) &
                    (movements_df['mvt_type'] == 101)
                ]
                if not mvt_101.empty:
                    receipt_date = mvt_101['posting_date'].min()
                    try:
                        # Convert pandas Timestamp to date
                        if isinstance(receipt_date, pd.Timestamp):
                            receipt_date_clean = receipt_date.date()
                        elif hasattr(receipt_date, 'date'):
                            receipt_date_clean = receipt_date.date()
                        else:
                            receipt_date_clean = receipt_date
                        
                        # finish_date is already datetime.date from SQLAlchemy
                        transit_time = (receipt_date_clean - finish_date).days
                        
                        # Only count if >= 0 (negative means data error)
                        if transit_time >= 0:
                            stats['transit'] += 1
                        else:
                            transit_time = None
                    except Exception as e:
                        transit_time = None
            
            # 3. STORAGE TIME (Receipt → Issue MVT 601)
            if batch:
                mvt_101 = movements_df[
                    (movements_df['batch'] == batch) &
                    (movements_df['mvt_type'] == 101)
                ]
                mvt_601 = movements_df[
                    (movements_df['batch'] == batch) &
                    (movements_df['mvt_type'] == 601)
                ]
                
                if not mvt_101.empty and not mvt_601.empty:
                    receipt_date = mvt_101['posting_date'].min()
                    issue_date = mvt_601['posting_date'].min()
                    try:
                        storage_time = (issue_date - receipt_date).days
                        if storage_time < 0:
                            storage_time = 0
                        stats['storage'] += 1
                    except:
                        pass
            
            # 4. PREPARATION TIME (MTO only: PO Date → Release)
            if is_mto and batch:
                # Find PO from MVT 101 with PO starting with '44'
                mvt_101_po = movements_df[
                    (movements_df['batch'] == batch) &
                    (movements_df['mvt_type'] == 101) &
                    (movements_df['purchase_order'].notna()) &
                    (movements_df['purchase_order'].astype(str).str.startswith('44'))
                ]
                
                if not mvt_101_po.empty and release_date:
                    po_number = mvt_101_po['purchase_order'].iloc[0]
                    po_info = po_df[po_df['purch_order'] == po_number]
                    
                    if not po_info.empty:
                        po_date = po_info['purch_date'].iloc[0]
                        try:
                            prep_time = (release_date - po_date).days
                            if prep_time < 0:
                                prep_time = 0
                            stats['prep'] += 1
                        except:
                            pass
            
            # 5. DELIVERY TIME (MTO only: Issue → Actual GI)
            if is_mto and batch:
                mvt_601 = movements_df[
                    (movements_df['batch'] == batch) &
                    (movements_df['mvt_type'] == 601)
                ]
                
                if not mvt_601.empty:
                    issue_date = mvt_601['posting_date'].min()
                    delivery_ref = mvt_601['reference'].iloc[0] if 'reference' in mvt_601.columns and not mvt_601['reference'].isna().all() else None
                    
                    if delivery_ref:
                        delivery_info = delivery_df[delivery_df['delivery'] == delivery_ref]
                        if not delivery_info.empty:
                            gi_date = delivery_info['actual_gi_date'].iloc[0]
                            try:
                                delivery_time = (gi_date - issue_date).days
                                if delivery_time < 0:
                                    delivery_time = 0
                                stats['delivery'] += 1
                            except:
                                pass
            
            # Calculate total and status
            total_time = sum(filter(None, [prep_time, production_time, transit_time, storage_time, delivery_time]))
            
            if total_time > 0:
                # Determine status
                target = 21 if is_mto else 14
                if total_time <= target:
                    status = 'ON_TIME'
                elif total_time <= target * 1.2:
                    status = 'DELAYED'
                else:
                    status = 'CRITICAL'
                
                # Update order
                order.prep_time_days = prep_time
                order.production_time_days = production_time
                order.transit_time_days = transit_time
                order.storage_time_days = storage_time
                order.delivery_time_days = delivery_time
                order.total_leadtime_days = total_time
                order.leadtime_status = status
                updated_count += 1
            else:
                skipped_count += 1
        
        # Commit changes
        print("\n💾 Saving changes to database...")
        db.commit()
        
        print("\n" + "="*70)
        print("BACKFILL COMPLETE")
        print("="*70)
        print(f"✅ Updated: {updated_count} orders")
        print(f"⏭️  Skipped: {skipped_count} orders (no calculable data)")
        print(f"📊 Total: {len(orders)} orders")
        
        print("\n📈 Stage Coverage:")
        print(f"   Preparation: {stats['prep']} orders")
        print(f"   Production: {stats['prod']} orders")
        print(f"   Transit: {stats['transit']} orders")
        print(f"   Storage: {stats['storage']} orders")
        print(f"   Delivery: {stats['delivery']} orders")
        
        # Verify results
        print("\n🔍 Verification:")
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(total_leadtime_days) as with_leadtime,
                ROUND(AVG(prep_time_days), 1) as avg_prep,
                ROUND(AVG(production_time_days), 1) as avg_prod,
                ROUND(AVG(transit_time_days), 1) as avg_transit,
                ROUND(AVG(storage_time_days), 1) as avg_storage,
                ROUND(AVG(delivery_time_days), 1) as avg_delivery,
                ROUND(AVG(total_leadtime_days), 1) as avg_total
            FROM fact_production
            WHERE total_leadtime_days IS NOT NULL
        """)).fetchone()
        
        print(f"   Total orders: {result[0]}")
        print(f"   With lead-time: {result[1]}")
        print(f"   Avg Preparation: {result[2]} days")
        print(f"   Avg Production: {result[3]} days")
        print(f"   Avg Transit: {result[4]} days")
        print(f"   Avg Storage: {result[5]} days")
        print(f"   Avg Delivery: {result[6]} days")
        print(f"   Avg Total: {result[7]} days")
        
        print("\n✅ Next step: Refresh the Lead Time Analysis dashboard")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    backfill_leadtime_data()

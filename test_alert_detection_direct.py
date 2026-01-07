"""
Test alert detection directly with debug output
"""
import pandas as pd
from datetime import datetime
from src.db.connection import SessionLocal
from src.db.models import RawMb51, FactProduction
from src.core.alerts import AlertDetector
from src.core.uom_converter import UomConverter

print("=" * 80)
print("DIRECT TEST: Alert Detection for Batch 25L2502310")
print("=" * 80)

db = SessionLocal()

# Load MB51 data
print("\n1. Loading MB51 data...")
mb51_records = db.query(RawMb51).all()
data = []
for r in mb51_records:
    row = {c.name: getattr(r, c.name) for c in r.__table__.columns}
    data.append(row)

mb51_df = pd.DataFrame(data)
print(f"   Loaded {len(mb51_df)} MB51 records")

# Normalize (convert MVT to int)
print("\n2. Normalizing MB51 data...")
if 'col_1_mvt_type' in mb51_df.columns:
    print(f"   Before: MVT type = {mb51_df['col_1_mvt_type'].dtype}")
    mb51_df['col_1_mvt_type'] = pd.to_numeric(mb51_df['col_1_mvt_type'], errors='coerce').fillna(0).astype(int)
    print(f"   After: MVT type = {mb51_df['col_1_mvt_type'].dtype}")

# Check batch 25L2502310 in MB51
print("\n3. Checking batch 25L2502310 in MB51...")
batch_data = mb51_df[mb51_df['col_6_batch'] == '25L2502310']
mvt_101_1401 = batch_data[(batch_data['col_1_mvt_type'] == 101) & (batch_data['col_2_plant'] == 1401)]
print(f"   Total movements: {len(batch_data)}")
print(f"   MVT 101 @ Plant 1401: {len(mvt_101_1401)}")
if not mvt_101_1401.empty:
    print(f"   Posting date: {mvt_101_1401['col_0_posting_date'].values[0]}")

# Check FactProduction
print("\n4. Checking FactProduction...")
prod = db.query(FactProduction).filter(FactProduction.batch == '25L2502310').first()
if prod:
    print(f"   Actual finish date: {prod.actual_finish_date}")
    print(f"   MRP Controller: {prod.mrp_controller}")
else:
    print("   NOT FOUND")

# Run alert detection
print("\n5. Running alert detection...")
uom_converter = UomConverter()
detector = AlertDetector(
    mb51_df=mb51_df,
    uom_converter=uom_converter,
    stuck_threshold_hours=48
)

alerts = detector.detect_stuck_in_transit(plant=1401)

print(f"\n6. Results:")
print(f"   Total alerts: {len(alerts)}")

# Find alert for batch 25L2502310
batch_alerts = [a for a in alerts if a.batch == '25L2502310']
if batch_alerts:
    alert = batch_alerts[0]
    print(f"\n   FOUND ALERT FOR 25L2502310:")
    print(f"   Alert type: {alert.alert_type}")
    print(f"   Stuck hours: {alert.metric_value}")
    print(f"   Severity: {alert.severity}")
    print(f"   Message: {alert.message}")
else:
    print(f"\n   NO ALERT for 25L2502310")
    print(f"   (Expected if transit time < 48h)")

db.close()

print("\n" + "=" * 80)

import pandas as pd

# Load MB51 data
mb51_df = pd.read_excel('demodata/mb51.XLSX')

print("=== MB51 COLUMN NAMES ===\n")
print(mb51_df.columns.tolist())

print("\n=== SAMPLE DATA ===\n")
print(mb51_df.head(2))

# Check batch 25L2535110
batch = '25L2535110'

print(f"\n=== BATCH {batch} ===\n")

# Find the batch column
batch_col = [col for col in mb51_df.columns if 'batch' in col.lower()][0]
mvt_col = [col for col in mb51_df.columns if 'move' in col.lower() or 'mvt' in col.lower()][0]
plant_col = [col for col in mb51_df.columns if 'plant' in col.lower()][0]
qty_col = [col for col in mb51_df.columns if 'qty' in col.lower() and 'entry' in col.lower()][0]
uom_col = [col for col in mb51_df.columns if 'unit' in col.lower() and 'entry' in col.lower()][0]
mat_desc_col = [col for col in mb51_df.columns if 'material' in col.lower() and 'desc' in col.lower()][0]

print(f"Batch column: {batch_col}")
print(f"MVT column: {mvt_col}")
print(f"Plant column: {plant_col}")
print(f"Qty column: {qty_col}")
print(f"UOM column: {uom_col}")

batch_data = mb51_df[mb51_df[batch_col] == batch].copy()

print(f"\nTotal transactions: {len(batch_data)}\n")

for idx, row in batch_data.iterrows():
    print(f"MVT {row[mvt_col]} @ Plant {row[plant_col]}")
    print(f"  {row[mat_desc_col]}")
    print(f"  Qty: {row[qty_col]} {row[uom_col]}")
    print()

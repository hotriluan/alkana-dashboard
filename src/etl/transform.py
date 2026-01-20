"""
Transform Module - Raw to Warehouse transformation

Applies all business logic:
1. Stack Netting (601↔602)
2. UOM Conversion (PC→KG)
3. MTO Classification (SO + P01)
4. Order Status Detection
5. Yield Tracking (P03→P02→P01)
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import hashlib
import json
from sqlalchemy import func, text

from sqlalchemy.orm import Session

from src.db.models import (
    # Raw tables
    RawCooispi, RawMb51, RawZrmm024, RawZrsd002,
    RawZrsd004, RawZrsd006, RawZrfi005, RawTarget,
    # Fact tables
    FactProduction, FactInventory, FactPurchaseOrder,
    FactBilling, FactDelivery, FactArAging, FactTarget,
    # FactProductionChain - REMOVED 2026-01-12 (genealogy decommissioned)
    FactAlert, FactLeadTime,
    # Dimension tables
    DimMaterial, DimUomConversion, DimPlant, DimMvt,
)
from src.core.netting import StackNettingEngine, get_stock_impact
from src.core.uom_converter import UomConverter
from src.core.business_logic import OrderClassifier, LeadTimeCalculator
from src.core.alerts import AlertDetector
from src.config import PLANT_ROLES, MVT_REVERSAL_PAIRS, STOCK_IMPACT


def clean_value(value):
    """Clean and normalize values for database insertion"""
    if pd.isna(value):
        return None
    
    if isinstance(value, str):
        value = value.strip()
        if value == '':
            return None
    
    # Handle numpy types
    if isinstance(value, (np.integer, np.floating)):
        try:
            return value.item()  # Convert to Python native type
        except (ValueError, TypeError):
            pass
    
    return value


def safe_convert(value):
    """
    Safely convert pandas/numpy types to Python native types for SQL
    
    Handles:
    - pandas NaN → None
    - numpy int64/float64 → Python int/float
    - pandas Timestamp → Python date (not datetime!)
    - None → None
    """
    if value is None:
        return None
    
    if pd.isna(value):
        return None
    
    # Handle pandas Timestamp - convert to DATE not DATETIME
    if isinstance(value, pd.Timestamp):
        return value.date()  # Return date() not datetime()
    
    # Handle numpy types
    if isinstance(value, (np.integer, np.floating)):
        try:
            return value.item()
        except (ValueError, TypeError, AttributeError):
            return None
    
    # Handle strings
    if isinstance(value, str):
        value = value.strip()
        return None if value == '' else value
    
    return value



def compute_row_hash(data: Dict) -> str:
    """Compute MD5 hash for change detection"""
    json_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.md5(json_str.encode()).hexdigest()


class Transformer:
    """
    Transform raw data to warehouse with business logic applied
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.classifier = OrderClassifier()
        self.uom_converter = UomConverter()
        self.netting_engine = None  # Will be initialized when needed
    
    def truncate_warehouse(self):
        """Truncate warehouse fact and dimension tables to prevent duplication"""
        print("Truncating warehouse tables...")
        
        from sqlalchemy import text
        
        # List of tables to truncate (ALL fact and dim tables, not raw)
        tables = [
            # Fact tables
            'fact_production',
            'fact_inventory',
            'fact_purchase_order',
            'fact_billing',
            'fact_delivery',
            'fact_ar_aging',
            'fact_target',
            'fact_production_chain',
            'fact_mto_orders',
            'fact_alerts',
            'fact_lead_time',
            # Dimension tables
            'dim_uom_conversion',
            'dim_plant',
            'dim_mvt',
            'dim_dist_channel'
        ]
        
        for table in tables:
            try:
                self.db.execute(text(f'TRUNCATE TABLE {table} RESTART IDENTITY CASCADE'))
                self.db.commit()
                print(f"  ✓ Truncated {table}")
            except Exception as e:
                self.db.rollback()
                print(f"  ⚠ Skipped {table}: table may not exist yet")
        
        print("✓ Warehouse truncated")
    
    def load_raw_to_df(self, model_class) -> pd.DataFrame:
        """Load raw table to DataFrame"""
        records = self.db.query(model_class).all()
        if not records:
            return pd.DataFrame()
        
        # Convert to dict and DataFrame
        data = []
        for r in records:
            row = {c.name: getattr(r, c.name) for c in r.__table__.columns}
            data.append(row)
        
        return pd.DataFrame(data)
    
    def normalize_mb51_df(self, mb51_df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize MB51 DataFrame for processing
        
        CRITICAL FIX: Convert Movement Type from STRING to INT
        - Excel data has '101', '601' as strings
        - Netting engine expects 101, 601 as integers
        - Without conversion, filters don't match and alerts fail
        """
        if mb51_df.empty:
            return mb51_df
        
        df = mb51_df.copy()
        
        # Convert Movement Type to int (handle both string and numeric)
        if 'col_1_mvt_type' in df.columns:
            df['col_1_mvt_type'] = pd.to_numeric(df['col_1_mvt_type'], errors='coerce').fillna(0).astype(int)
        
        return df
    
    def seed_dimension_tables(self):
        """Seed dimension tables with reference data"""
        print("Seeding dimension tables...")
        
        # dim_plant
        for plant_code, role in PLANT_ROLES.items():
            existing = self.db.query(DimPlant).filter_by(plant_code=plant_code).first()
            if not existing:
                self.db.add(DimPlant(
                    plant_code=plant_code,
                    plant_name=f"Plant {plant_code}",
                    plant_role=role,
                    description=f"{role} - Plant {plant_code}"
                ))
        
        # dim_mvt
        for mvt_code, reversal in MVT_REVERSAL_PAIRS.items():
            existing = self.db.query(DimMvt).filter_by(mvt_code=mvt_code).first()
            if not existing:
                self.db.add(DimMvt(
                    mvt_code=mvt_code,
                    description=f"MVT {mvt_code}",
                    stock_impact=STOCK_IMPACT.get(mvt_code, 0),
                    reversal_mvt=reversal,
                    category=self._get_mvt_category(mvt_code)
                ))
        
        self.db.commit()
        print("  ✓ Dimension tables seeded")
    
    def _get_mvt_category(self, mvt_code: int) -> str:
        """Get MVT category"""
        if mvt_code in (101, 102):
            return 'GOODS_RECEIPT'
        elif mvt_code in (201, 202):
            return 'GOODS_ISSUE_COST_CENTER'
        elif mvt_code in (261, 262):
            return 'GOODS_ISSUE_PRODUCTION'
        elif mvt_code in (301, 302, 311, 312, 351, 352):
            return 'TRANSFER'
        elif mvt_code in (601, 602):
            return 'DELIVERY'
        else:
            return 'OTHER'
    
    def transform_cooispi(self):
        """Transform raw_cooispi to fact_production"""
        print("Transforming cooispi → fact_production...")
        
        raw_df = self.load_raw_to_df(RawCooispi)
        if raw_df.empty:
            print("  ⚠ No data in raw_cooispi")
            return
        
        count = 0
        for _, row in raw_df.iterrows():
            # Apply business logic
            is_mto = self.classifier.is_mto(row)
            order_status = self.classifier.get_order_status(row)
            
            # Normalize quantities to KG using UOM converter
            material_code = row.get('material_number')
            uom = row.get('unit_of_measure')
            order_qty = row.get('order_quantity')
            delivered_qty = row.get('delivered_quantity')
            
            order_qty_kg = None
            delivered_qty_kg = None
            
            if material_code and uom:
                kg_per_unit = self.uom_converter.get_kg_per_unit(str(material_code))
                if kg_per_unit:
                    if order_qty:
                        order_qty_kg = float(order_qty) * kg_per_unit if uom == 'PC' else float(order_qty)
                    if delivered_qty:
                        delivered_qty_kg = float(delivered_qty) * kg_per_unit if uom == 'PC' else float(delivered_qty)
            
            # Compute hash for change detection
            hash_data = {
                'order': row.get('order'),
                'batch': row.get('batch'),
                'plant': row.get('plant'),
                'delivered_qty': row.get('delivered_quantity'),
                'status': row.get('system_status')
            }
            row_hash = compute_row_hash(hash_data)
            
            # Check if exists
            existing = self.db.query(FactProduction).filter_by(
                order_number=row.get('order'),
                plant_code=row.get('plant')
            ).first()
            
            if existing:
                if existing.row_hash != row_hash:
                    # Update
                    existing.is_mto = is_mto
                    existing.order_status = order_status
                    existing.row_hash = row_hash
                    existing.updated_at = datetime.utcnow()
            else:
                # Insert
                fact = FactProduction(
                    plant_code=clean_value(row.get('plant')),
                    sales_order=clean_value(row.get('sales_order')),
                    order_number=clean_value(row.get('order')),
                    order_type=clean_value(row.get('order_type')),
                    material_code=clean_value(row.get('material_number')),
                    material_description=clean_value(row.get('material_description')),
                    release_date=clean_value(row.get('release_date_actual')),
                    actual_finish_date=clean_value(row.get('actual_finish_date')),
                    bom_alternative=clean_value(row.get('bom_alternative')),
                    batch=clean_value(row.get('batch')),
                    system_status=clean_value(row.get('system_status')),
                    mrp_controller=clean_value(row.get('mrp_controller')),
                    order_qty=clean_value(row.get('order_quantity')),
                    delivered_qty=clean_value(row.get('delivered_quantity')),
                    uom=clean_value(row.get('unit_of_measure')),
                    order_qty_kg=clean_value(order_qty_kg),
                    delivered_qty_kg=clean_value(delivered_qty_kg),
                    is_mto=is_mto,
                    order_status=order_status,
                    row_hash=row_hash,
                    raw_id=clean_value(row.get('id'))
                )
                self.db.add(fact)
                count += 1
        
        self.db.commit()
        print(f"  ✓ Transformed {count} production orders")
    
    def transform_mb51(self):
        """Transform raw_mb51 to fact_inventory (INDIVIDUAL transactions with REAL movement types)"""
        print("Transforming mb51 to fact_inventory (individual transactions)...")
        
        # STEP 1: AUTO-POPULATE dim_material FIRST (Material Master Discovery)
        print("  [1/2] Populating dim_material from unique materials...")
        populate_sql = text("""
            INSERT INTO dim_material (material_code, material_description)
            SELECT DISTINCT 
                col_4_material, 
                MAX(col_5_material_desc) 
            FROM raw_mb51 
            WHERE col_4_material IS NOT NULL 
            GROUP BY col_4_material
            ON CONFLICT (material_code) 
            DO UPDATE SET material_description = EXCLUDED.material_description;
        """)
        result = self.db.execute(populate_sql)
        self.db.commit()
        print(f"    ✓ Populated/updated {result.rowcount} materials in dim_material")
        
        # STEP 2: Transform individual transactions (NO AGGREGATION)
        print("  [2/2] Creating individual fact_inventory transactions...")
        raw_df = self.load_raw_to_df(RawMb51)
        if raw_df.empty:
            print("    ⚠ No data in raw_mb51")
            return
        
        # Filter only valid rows (has material and mvt_type)
        raw_df = raw_df[
            (raw_df['col_4_material'].notna()) & 
            (raw_df['col_1_mvt_type'].notna())
        ].copy()
        
        # Add stock impact for each transaction
        raw_df['stock_impact'] = raw_df['col_1_mvt_type'].apply(
            lambda x: get_stock_impact(x) if pd.notna(x) else 0
        )
        
        # Convert qty to KG for each transaction
        def convert_to_kg(row):
            material = row.get('col_4_material')
            uom = row.get('col_8_uom')
            qty = row.get('col_7_qty')
            
            if pd.isna(qty):
                return 0.0
            
            # If already in KG, return as-is
            if uom == 'KG':
                return float(qty)
            
            # If in PC, need conversion
            if uom == 'PC' and not pd.isna(material):
                kg_per_unit = self.uom_converter.get_kg_per_unit(str(material))
                if kg_per_unit:
                    return float(qty) * kg_per_unit
            
            # Default: can't convert, return 0
            return 0.0
        
        raw_df['qty_kg'] = raw_df.apply(convert_to_kg, axis=1)
        
        # Create INDIVIDUAL fact records (preserve real mvt_types: 601, 101, 261, etc.)
        count = 0
        skipped = 0
        for _, row in raw_df.iterrows():
            material = safe_convert(row['col_4_material'])
            mvt_type = safe_convert(row['col_1_mvt_type'])
            
            # Skip if no material or mvt_type
            if material is None or mvt_type is None:
                skipped += 1
                continue
            
            # Convert all fields
            posting_date = safe_convert(row['col_0_posting_date'])
            plant = safe_convert(row['col_2_plant'])
            sloc = safe_convert(row['col_3_sloc'])
            material_desc = safe_convert(row['col_5_material_desc'])
            batch = safe_convert(row['col_6_batch'])
            qty = safe_convert(row['col_7_qty'])
            uom = safe_convert(row['col_8_uom'])
            qty_kg = safe_convert(row['qty_kg'])
            cost_center = safe_convert(row['col_9_cost_center'])
            gl_account = safe_convert(row['col_10_gl_account'])
            material_doc = safe_convert(row['col_11_material_doc'])
            reference = safe_convert(row['col_12_reference'])
            outbound_delivery = safe_convert(row['col_13_outbound_delivery'])
            purchase_order = safe_convert(row['col_15_purchase_order'])
            stock_impact = safe_convert(row['stock_impact'])
            raw_id = safe_convert(row['id'])
            
            # Compute unique hash for this transaction
            hash_data = {
                'material': material,
                'mvt_type': mvt_type,
                'posting_date': str(posting_date) if posting_date else None,
                'batch': batch,
                'material_doc': material_doc
            }
            row_hash = compute_row_hash(hash_data)
            
            # Create fact record with REAL movement type (not 999!)
            fact = FactInventory(
                posting_date=posting_date,
                mvt_type=mvt_type,  # PRESERVE REAL mvt_type (601, 101, 261, etc.)
                plant_code=plant,
                sloc_code=sloc,
                material_code=material,
                material_description=material_desc,
                batch=batch,
                qty=qty,
                uom=uom,
                qty_kg=qty_kg,
                cost_center=cost_center,
                gl_account=gl_account,
                material_document=material_doc,
                reference=reference,
                outbound_delivery=outbound_delivery,
                purchase_order=purchase_order,
                stock_impact=stock_impact,
                row_hash=row_hash,
                raw_id=raw_id
            )
            self.db.add(fact)
            count += 1
            
            # Commit in batches for large datasets
            if count % 5000 == 0:
                self.db.commit()
                print(f"    ... {count} transactions processed")
        
        self.db.commit()
        print(f"  ✓ Transformed {count} individual inventory transactions (skipped {skipped} invalid rows)")
        print(f"    Movement types preserved: 601, 101, 261, etc. (NO aggregation, NO mvt_type=999)")

    
    def transform_zrmm024(self):
        """Transform raw_zrmm024 to fact_purchase_order"""
        print("Transforming zrmm024 → fact_purchase_order...")
        
        raw_df = self.load_raw_to_df(RawZrmm024)
        if raw_df.empty:
            print("  ⚠ No data in raw_zrmm024")
            return
        
        count = 0
        for _, row in raw_df.iterrows():
            po_number = row.get('purch_order')
            
            # Skip rows with null PO number (critical field)
            if pd.isna(po_number):
                continue
                
            is_sales_po = self.classifier.is_sales_po(po_number)
            
            hash_data = {'po': po_number, 'item': row.get('item')}
            row_hash = compute_row_hash(hash_data)
            
            fact = FactPurchaseOrder(
                purch_order=po_number,
                item=clean_value(row.get('item')),
                purch_date=clean_value(row.get('purch_date')),
                is_sales_po=is_sales_po,
                row_hash=row_hash,
                raw_id=clean_value(row.get('id'))
            )
            self.db.add(fact)
            count += 1
        
        self.db.commit()
        print(f"  ✓ Transformed {count} purchase orders")
    
    def transform_zrsd002(self):
        """Transform raw_zrsd002 to fact_billing"""
        print("Transforming zrsd002 → fact_billing...")
        
        raw_df = self.load_raw_to_df(RawZrsd002)
        if raw_df.empty:
            print("  ⚠ No data in raw_zrsd002")
            return
        
        # Clear existing fact_billing rows to avoid unique constraint collisions on reruns
        deleted_billing = self.db.query(FactBilling).delete(synchronize_session=False)
        if deleted_billing:
            print(f"  🔄 Cleared {deleted_billing} existing billing rows")
        
        count = 0
        for _, row in raw_df.iterrows():
            billing_document = row.get('billing_document')
            
            # Skip rows with null billing_document (critical field)
            if pd.isna(billing_document):
                continue
            
            billing_date = row.get('billing_date')
            semester_info = self.classifier.get_semester(billing_date)
            
            # Normalize billing_qty to KG
            material_code = row.get('material')
            sales_unit = row.get('sales_unit')
            billing_qty = row.get('billing_qty')
            
            billing_qty_kg = None
            if material_code and sales_unit and billing_qty:
                kg_per_unit = self.uom_converter.get_kg_per_unit(str(material_code))
                if kg_per_unit:
                    billing_qty_kg = float(billing_qty) * kg_per_unit if sales_unit == 'PC' else float(billing_qty)
            
            hash_data = {
                'doc': billing_document,
                'item': row.get('billing_item'),
                'net_value': row.get('net_value')
            }
            row_hash = compute_row_hash(hash_data)
            
            fact = FactBilling(
                billing_date=billing_date,
                billing_document=clean_value(billing_document),
                billing_item=clean_value(row.get('billing_item')),
                sloc=clean_value(row.get('sloc')),
                sales_office=clean_value(row.get('sales_office')),
                dist_channel=clean_value(row.get('dist_channel')),
                customer_name=clean_value(row.get('customer_name')),
                cust_group=clean_value(row.get('cust_group')),
                salesman_name=clean_value(row.get('salesman_name')),
                material_code=clean_value(row.get('material')),
                material_description=clean_value(row.get('material_desc')),
                prod_hierarchy=clean_value(row.get('prod_hierarchy')),
                billing_qty=clean_value(row.get('billing_qty')),
                sales_unit=clean_value(row.get('sales_unit')),
                billing_qty_kg=clean_value(billing_qty_kg),
                currency=clean_value(row.get('currency')),
                exchange_rate=clean_value(row.get('exchange_rate')),
                price=clean_value(row.get('price')),
                total_price=clean_value(row.get('total_price')),
                discount_item=clean_value(row.get('discount_item')),
                net_value=clean_value(row.get('net_value')),
                tax=clean_value(row.get('tax')),
                total=clean_value(row.get('total')),
                net_weight=clean_value(row.get('net_weight')),
                weight_unit=clean_value(row.get('weight_unit')),
                volume=clean_value(row.get('volume')),
                volume_unit=clean_value(row.get('volume_unit')),
                so_number=clean_value(row.get('so_number')),
                so_date=clean_value(row.get('so_date')),
                doc_reference_od=clean_value(row.get('doc_reference_od')),
                semester=semester_info['semester'] if semester_info else None,
                year=semester_info['year'] if semester_info else None,
                row_hash=row_hash,
                raw_id=clean_value(row.get('id'))
            )
            self.db.add(fact)
            count += 1
        
        self.db.commit()
        print(f"  ✓ Transformed {count} billing records")
    
    def transform_zrsd004(self):
        """Transform raw_zrsd004 to fact_delivery with upsert logic"""
        print("Transforming zrsd004 → fact_delivery...")
        
        raw_df = self.load_raw_to_df(RawZrsd004)
        if raw_df.empty:
            print("  ⚠ No data in raw_zrsd004")
            return
        
        inserted = 0
        updated = 0
        skipped = 0
        
        for _, row in raw_df.iterrows():
            delivery_number = row.get('delivery')
            
            # Skip rows with null delivery_number (critical field)
            if pd.isna(delivery_number):
                continue
            
            # Normalize delivery_qty to KG
            material_code = row.get('material')
            delivery_qty = row.get('delivery_qty')
            
            delivery_qty_kg = None
            if material_code and delivery_qty:
                kg_per_unit = self.uom_converter.get_kg_per_unit(str(material_code))
                if kg_per_unit:
                    # Assume PC unit for delivery, normalize if needed
                    delivery_qty_kg = float(delivery_qty) * kg_per_unit
            
            hash_data = {
                'delivery': delivery_number,
                'item': row.get('line_item'),
                'qty': row.get('delivery_qty')
            }
            row_hash = compute_row_hash(hash_data)
            
            # Check if record exists (business key: delivery + line_item)
            existing = self.db.query(FactDelivery).filter_by(
                delivery=clean_value(delivery_number),
                line_item=clean_value(row.get('line_item'))
            ).first()
            
            if existing:
                # Check if data changed
                if existing.row_hash == row_hash:
                    skipped += 1
                    continue
                
                # Update existing record
                existing.delivery_date = clean_value(row.get('delivery_date'))
                existing.actual_gi_date = clean_value(row.get('actual_gi_date'))
                existing.so_reference = clean_value(row.get('so_reference'))
                existing.shipping_point = clean_value(row.get('shipping_point'))
                existing.sloc = clean_value(row.get('sloc'))
                existing.sales_office = clean_value(row.get('sales_office'))
                existing.dist_channel = clean_value(row.get('dist_channel'))
                existing.cust_group = clean_value(row.get('cust_group'))
                existing.sold_to_party = clean_value(row.get('sold_to_party'))
                existing.ship_to_party = clean_value(row.get('ship_to_party'))
                existing.ship_to_name = clean_value(row.get('ship_to_name'))
                existing.ship_to_city = clean_value(row.get('ship_to_city'))
                existing.salesman_id = clean_value(row.get('salesman_id'))
                existing.salesman_name = clean_value(row.get('salesman_name'))
                existing.material_code = clean_value(row.get('material'))
                existing.material_description = clean_value(row.get('material_desc'))
                existing.delivery_qty = clean_value(row.get('delivery_qty'))
                existing.delivery_qty_kg = clean_value(delivery_qty_kg)
                existing.tonase = clean_value(row.get('tonase'))
                existing.tonase_unit = clean_value(row.get('tonase_unit'))
                existing.net_weight = clean_value(row.get('net_weight'))
                existing.volume = clean_value(row.get('volume'))
                existing.prod_hierarchy = clean_value(row.get('prod_hierarchy'))
                existing.row_hash = row_hash
                existing.raw_id = clean_value(row.get('id'))
                updated += 1
            else:
                # Insert new record
                fact = FactDelivery(
                    delivery_date=clean_value(row.get('delivery_date')),
                    actual_gi_date=clean_value(row.get('actual_gi_date')),
                    delivery=clean_value(delivery_number),
                    line_item=clean_value(row.get('line_item')),
                    so_reference=clean_value(row.get('so_reference')),
                    shipping_point=clean_value(row.get('shipping_point')),
                    sloc=clean_value(row.get('sloc')),
                    sales_office=clean_value(row.get('sales_office')),
                    dist_channel=clean_value(row.get('dist_channel')),
                    cust_group=clean_value(row.get('cust_group')),
                    sold_to_party=clean_value(row.get('sold_to_party')),
                    ship_to_party=clean_value(row.get('ship_to_party')),
                    ship_to_name=clean_value(row.get('ship_to_name')),
                    ship_to_city=clean_value(row.get('ship_to_city')),
                    salesman_id=clean_value(row.get('salesman_id')),
                    salesman_name=clean_value(row.get('salesman_name')),
                    material_code=clean_value(row.get('material')),
                    material_description=clean_value(row.get('material_desc')),
                    delivery_qty=clean_value(row.get('delivery_qty')),
                    delivery_qty_kg=clean_value(delivery_qty_kg),
                    tonase=clean_value(row.get('tonase')),
                    tonase_unit=clean_value(row.get('tonase_unit')),
                    net_weight=clean_value(row.get('net_weight')),
                    volume=clean_value(row.get('volume')),
                    prod_hierarchy=clean_value(row.get('prod_hierarchy')),
                    row_hash=row_hash,
                    raw_id=clean_value(row.get('id'))
                )
                self.db.add(fact)
                inserted += 1
        
        self.db.commit()
        print(f"  ✓ Transformed {inserted} new, {updated} updated, {skipped} skipped")
    
    def transform_zrfi005(self, target_date: Optional[str] = None):
        """
        Transform raw_zrfi005 to fact_ar_aging
        
        Args:
            target_date: Optional snapshot date (YYYY-MM-DD) to transform.
                        If None, uses the latest snapshot_date.
        
        Business Rule: Support multiple historical snapshots
        - Raw table keeps all historical snapshots (never delete)
        - Fact table is rebuilt per snapshot (clear old, rebuild new for that date)
        - Users can select which snapshot to view via API parameter
        """
        print("Transforming zrfi005 → fact_ar_aging...")
        
        # Determine which snapshot to use
        from sqlalchemy import func
        from datetime import datetime as dt
        
        if target_date:
            # Convert string to date
            try:
                snapshot_to_use = dt.strptime(target_date, '%Y-%m-%d').date()
            except ValueError:
                print(f"  ❌ Invalid date format: {target_date}. Expected YYYY-MM-DD")
                return
        else:
            # Find the latest snapshot_date in raw data
            snapshot_to_use = self.db.query(
                func.max(RawZrfi005.snapshot_date)
            ).filter(
                RawZrfi005.snapshot_date != None
            ).scalar()
        
        if not snapshot_to_use:
            print("  ⚠ No data with snapshot_date in raw_zrfi005")
            return
        
        print(f"  📅 Transforming snapshot: {snapshot_to_use}")
        
        # Clear fact records for THIS snapshot only (keep other snapshots)
        deleted = self.db.query(FactArAging).filter(
            FactArAging.snapshot_date == snapshot_to_use
        ).delete(synchronize_session=False)
        self.db.commit()
        if deleted > 0:
            print(f"  ⚠ Cleared {deleted} records for snapshot {snapshot_to_use}")
        
        # Load only the specified snapshot
        raw_df = pd.read_sql(
            self.db.query(RawZrfi005).filter(
                RawZrfi005.snapshot_date == snapshot_to_use
            ).statement,
            self.db.bind
        )
        
        if raw_df.empty:
            print(f"  ⚠ No data for snapshot {snapshot_to_use}")
            return
        
        print(f"  📊 Processing {len(raw_df)} records from {snapshot_to_use}")
        
        count = 0
        for _, row in raw_df.iterrows():
            customer_code = row.get('customer_name')
            
            # Skip rows with null customer_code (critical field)
            if pd.isna(customer_code):
                continue
            
            hash_data = {
                'customer': customer_code,
                'salesman': row.get('salesman_name'),
                'total_target': row.get('total_target')
            }
            row_hash = compute_row_hash(hash_data)
            
            fact = FactArAging(
                dist_channel=clean_value(row.get('dist_channel')),
                cust_group=clean_value(row.get('cust_group')),
                salesman_name=clean_value(row.get('salesman_name')),
                customer_name=clean_value(customer_code),
                currency=clean_value(row.get('currency')),
                target_1_30=clean_value(row.get('target_1_30')),
                target_31_60=clean_value(row.get('target_31_60')),
                target_61_90=clean_value(row.get('target_61_90')),
                target_91_120=clean_value(row.get('target_91_120')),
                target_121_180=clean_value(row.get('target_121_180')),
                target_over_180=clean_value(row.get('target_over_180')),
                total_target=clean_value(row.get('total_target')),
                realization_not_due=clean_value(row.get('realization_not_due')),
                realization_1_30=clean_value(row.get('realization_1_30')),
                realization_31_60=clean_value(row.get('realization_31_60')),
                realization_61_90=clean_value(row.get('realization_61_90')),
                realization_91_120=clean_value(row.get('realization_91_120')),
                realization_121_180=clean_value(row.get('realization_121_180')),
                realization_over_180=clean_value(row.get('realization_over_180')),
                total_realization=clean_value(row.get('total_realization')),
                report_date=datetime.now().date(),
                snapshot_date=clean_value(row.get('snapshot_date')),  # Preserve snapshot_date from raw
                row_hash=row_hash,
                raw_id=clean_value(row.get('id'))
            )
            self.db.add(fact)
            count += 1
        
        self.db.commit()
        print(f"  ✓ Transformed {count} AR aging records")
    
    def transform_target(self):
        """Transform raw_target to fact_target"""
        print("Transforming target → fact_target...")
        
        raw_df = self.load_raw_to_df(RawTarget)
        if raw_df.empty:
            print("  ⚠ No data in raw_target")
            return
        
        count = 0
        for _, row in raw_df.iterrows():
            salesman_name = row.get('salesman_name')
            
            # Skip rows with null salesman_name (critical field)
            if pd.isna(salesman_name):
                continue
            
            hash_data = {
                'salesman': salesman_name,
                'semester': row.get('semester'),
                'year': row.get('year'),
                'target': row.get('target')
            }
            row_hash = compute_row_hash(hash_data)
            
            fact = FactTarget(
                salesman_name=clean_value(salesman_name),
                semester=clean_value(row.get('semester')),
                year=clean_value(row.get('year')),
                target=clean_value(row.get('target')),
                row_hash=row_hash,
                raw_id=clean_value(row.get('id'))
            )
            self.db.add(fact)
            count += 1
        
        self.db.commit()
        print(f"  ✓ Transformed {count} target records")
    
    def build_uom_conversion(self):
        """Build UOM conversion table from billing data"""
        print("Building UOM conversion table...")
        
        billing_df = self.load_raw_to_df(RawZrsd002)
        delivery_df = self.load_raw_to_df(RawZrsd004)
        
        if billing_df.empty:
            print("  ⚠ No billing data for UOM conversion")
            return
        
        # Build conversion table
        conversion_df = self.uom_converter.build_from_billing(billing_df, delivery_df)
        
        if conversion_df.empty:
            return
        
        # Save to dim_uom_conversion
        count = 0
        updated = 0
        for _, row in conversion_df.iterrows():
            existing = self.db.query(DimUomConversion).filter_by(
                material_code=row['material']
            ).first()
            
            if existing:
                existing.kg_per_unit = row['kg_per_unit']
                existing.sample_count = row['sample_count']
                existing.variance_pct = row.get('variance_pct')
                existing.last_updated = datetime.utcnow()
                updated += 1
            else:
                dim = DimUomConversion(
                    material_code=row['material'],
                    material_description=row.get('material_desc', ''),
                    kg_per_unit=row['kg_per_unit'],
                    sample_count=row['sample_count'],
                    source='billing',
                    variance_pct=row.get('variance_pct')
                )
                self.db.add(dim)
                count += 1
        
        self.db.commit()
        print(f"Built UOM conversion table: {count + updated} materials (new: {count}, updated: {updated})")
    
    def transform_all(self):
        """Run all transformations"""
        print("=" * 60)
        print("TRANSFORMING RAW → WAREHOUSE")
        print("=" * 60)
        
        # 1. Seed dimensions
        self.seed_dimension_tables()
        
        # 2. Build UOM conversion
        self.build_uom_conversion()
        
        # 3. Transform fact tables
        self.transform_cooispi()
        self.transform_mb51()
        self.transform_zrmm024()
        self.transform_zrsd002()
        self.transform_zrsd004()
        self.transform_zrfi005()
        self.transform_target()
        
        # 4. Build production chains (P03→P02→P01)
        self.build_production_chains()
        
        # 4.5. Calculate P02→P01 Yields (NEW)
        self.calculate_p02_p01_yields()
        
        # 5. Lead Time Analysis
        self.transform_lead_time()
        
        # 6. Detect alerts (stuck transit, low yield)
        self.detect_alerts()
        
        print("=" * 60)
    
    def transform_lead_time(self):
        """Calculate Lead Time Metrics (Purchase + Production + Storage)"""
        print("Calculating Lead Time metrics...")
        count = 0 

        # Remove previous lead time facts to avoid unique constraint collisions on reruns
        deleted_lt = self.db.query(FactLeadTime).delete(synchronize_session=False)
        if deleted_lt:
            print(f"  🔄 Cleared {deleted_lt} existing lead time rows")
        
        # Track seen (order_number, batch) pairs to avoid duplicate inserts in one run
        seen_pairs = set()

        # ---------------------------------------------------------
        # 0. PREPARE OUTBOUND DATA (For Storage Time)
        # ---------------------------------------------------------
        # Get MIN posting date for MVT 601 (Delivery) per Batch
        outbound_df = pd.read_sql(
            self.db.query(RawMb51.col_6_batch, func.min(RawMb51.col_0_posting_date).label('issue_date'))
            .filter(RawMb51.col_1_mvt_type == 601)
            .filter(RawMb51.col_6_batch.isnot(None))
            .group_by(RawMb51.col_6_batch).statement,
            self.db.bind
        )
        
        # Create Lookup: Batch -> Issue Date
        batch_issue_map = {}
        if not outbound_df.empty:
            for _, row in outbound_df.iterrows():
                b = str(row['col_6_batch']).strip()
                d = safe_convert(row['issue_date'])
                if b and d:
                    if isinstance(d, datetime): d = d.date()
                    batch_issue_map[b] = d
        
        print(f"  [OK] Indexed {len(batch_issue_map)} outbound batches for storage calc")

        # ---------------------------------------------------------
        # 0B. PREPARE BACKTRACKING DATA (For Preparation Time - MTO)
        # ---------------------------------------------------------
        # 1. Map: Batch -> PO Number (from RawMb51 101 where PO like '44%')
        backtrack_data = pd.read_sql(
            self.db.query(RawMb51.col_6_batch, RawMb51.col_15_purchase_order)
            .filter(RawMb51.col_1_mvt_type == 101)
            .filter(RawMb51.col_15_purchase_order.like('44%'))
            .statement,
            self.db.bind
        )
        
        batch_po_map = {}
        if not backtrack_data.empty:
            for _, row in backtrack_data.iterrows():
                b = str(row['col_6_batch']).strip()
                p = str(row['col_15_purchase_order']).strip()
                if b and p:
                    batch_po_map[b] = p
                    
        # 2. Map: PO Number -> PO Date (from FactPurchaseOrder)
        po_date_data = pd.read_sql(
            self.db.query(FactPurchaseOrder.purch_order, FactPurchaseOrder.purch_date)
            .filter(FactPurchaseOrder.purch_order.isnot(None))
            .statement,
            self.db.bind
        )
        
        po_date_map = {}
        if not po_date_data.empty:
            for _, row in po_date_data.iterrows():
                p = str(row['purch_order']).strip()
                d = safe_convert(row['purch_date'])
                if p and d:
                    if isinstance(d, datetime): d = d.date()
                    po_date_map[p] = d

        print(f"  [OK] Indexed {len(batch_po_map)} batches for backtracking")
        
        # ---------------------------------------------------------
        # 0C. PREPARE CHANNEL DATA (For Distribution Channel)
        # ---------------------------------------------------------
        # Map 1: Sales Order -> Channel Code (from FactBilling) - for MTO
        channel_data = pd.read_sql(
            self.db.query(FactBilling.so_number, FactBilling.dist_channel)
            .filter(FactBilling.so_number.isnot(None))
            .filter(FactBilling.dist_channel.isnot(None))
            .statement,
            self.db.bind
        )
        
        so_channel_map = {}
        if not channel_data.empty:
            for _, row in channel_data.iterrows():
                so = str(row['so_number']).strip()
                ch = str(row['dist_channel']).strip()
                if so and ch:
                    so_channel_map[so] = ch
                    
        print(f"  [OK] Indexed {len(so_channel_map)} sales orders for channel lookup")
        
        # Map 2: Material -> Channel Code (from RawZrsd006) - for MTS
        # Note: zrsd006 loader doesn't populate material column, use raw_data instead
        from src.db.models import RawZrsd006
        import json
        
        zrsd006_records = self.db.query(RawZrsd006.raw_data).all()
        
        material_channel_map = {}
        for record in zrsd006_records:
            if record.raw_data:
                data = json.loads(record.raw_data) if isinstance(record.raw_data, str) else record.raw_data
                mat = data.get('Material Code')
                ch = data.get('Distribution Channel')
                
                if mat and ch:
                    mat_str = str(mat).strip()
                    ch_str = str(ch).strip()
                    if mat_str and ch_str:
                        material_channel_map[mat_str] = ch_str
                    
        print(f"  [OK] Indexed {len(material_channel_map)} materials for channel lookup")
        
        # Track processed batches to avoid duplicates (Production takes priority)
        processed_batches = set()
        
        # ---------------------------------------------------------
        # 1. PRODUCTION ORDERS (MTO/MTS Internal) → Production Time
        # PROCESS FIRST to ensure correct classification
        # ---------------------------------------------------------
        prod_df = pd.read_sql(
            self.db.query(FactProduction).filter(FactProduction.actual_finish_date.isnot(None)).statement,
            self.db.bind
        )
        
        if not prod_df.empty:
            for _, row in prod_df.iterrows():
                start = safe_convert(row.get('release_date'))
                end = safe_convert(row.get('actual_finish_date'))
                batch = safe_convert(row.get('batch'))
                sales_order = safe_convert(row.get('sales_order'))
                is_mto = row.get('is_mto', False)
                
                if not start or not end: continue
                if isinstance(start, datetime): start = start.date()
                if isinstance(end, datetime): end = end.date()
                
                prod_days = (end - start).days
                if prod_days < 0: continue
                
                # Calculate Transit Time (Factory → DC for P01 batches)
                # Transit = Time from production finish (Factory) to MVT 101 at DC (1401)
                transit_days = 0
                mrp_controller = safe_convert(row.get('mrp_controller'))
                if batch and mrp_controller == 'P01':
                    # Get MVT 101 at DC (plant 1401) for this batch
                    dc_receipt = self.db.query(func.min(RawMb51.col_0_posting_date))\
                        .filter(RawMb51.col_6_batch == batch)\
                        .filter(RawMb51.col_1_mvt_type == 101)\
                        .filter(RawMb51.col_2_plant == 1401)\
                        .scalar()
                    
                    if dc_receipt:
                        if isinstance(dc_receipt, datetime):
                            dc_receipt = dc_receipt.date()
                        if dc_receipt >= end:
                            transit_days = (dc_receipt - end).days
                
                # Calculate Storage Time (DC receipt to DC issue)
                # Note: For batches with transit, storage starts from DC receipt, not production finish
                storage_days = 0
                storage_start = end
                if transit_days > 0:
                    # Storage starts after transit completes
                    storage_start = end + timedelta(days=transit_days)
                
                if batch and batch in batch_issue_map:
                    issue_date = batch_issue_map[batch]
                    if issue_date >= storage_start:
                        storage_days = (issue_date - storage_start).days
                
                # Calculate Preparation Time (MTO only)
                prep_days = 0
                order_type = 'MTS'
                if is_mto:
                    order_type = 'MTO'
                    # Backtracking Strategy: Batch → PO (44xx) → PO Date
                    if batch and batch in batch_po_map:
                        po_num = batch_po_map[batch]
                        if po_num in po_date_map:
                            po_date = po_date_map[po_num]
                            if start >= po_date:
                                prep_days = (start - po_date).days
                
                # Lookup Channel Code
                channel_code = None
                material_code = safe_convert(row.get('material_code'))
                
                if is_mto:
                    # MTO: Try Sales Order first
                    if sales_order and sales_order in so_channel_map:
                        channel_code = so_channel_map[sales_order]
                
                # Fallback to Material-based channel (for both MTO without SO match, and MTS)
                if not channel_code and material_code and material_code in material_channel_map:
                    channel_code = material_channel_map[material_code]
                
                order_number = safe_convert(row.get('order_number'))

                # Skip duplicates within the same run (unique key: order_number + batch)
                if order_number and batch and (order_number, batch) in seen_pairs:
                    continue
                if order_number and batch:
                    seen_pairs.add((order_number, batch))

                fact = FactLeadTime(
                    material_code=safe_convert(row.get('material_code')),
                    plant_code=safe_convert(row.get('plant_code')),
                    order_number=order_number,
                    order_type=order_type,
                    batch=batch,
                    channel_code=channel_code,
                    start_date=start,
                    end_date=end,
                    lead_time_days=prod_days + transit_days + storage_days + prep_days, # Total
                    production_days=prod_days, # Map to Production
                    transit_days=transit_days, # Map to Transit (Factory → DC)
                    storage_days=storage_days, # Map to Storage
                    preparation_days=prep_days # Map to Preparation
                )
                self.db.add(fact)
                count += 1
                
                # Batch commit every 1000 records to avoid memory issues
                if count % 1000 == 0:
                    self.db.commit()
                
                # Track this batch as processed (Production takes priority over Purchase)
                if batch:
                    processed_batches.add(batch)

        # ---------------------------------------------------------
        # 2. PURCHASE ORDERS (External) → Transit Time
        # ONLY for batches NOT in Production
        # ---------------------------------------------------------
        raw_mb51 = pd.read_sql(
            self.db.query(RawMb51).filter(RawMb51.col_1_mvt_type == 101).statement,
            self.db.bind
        )
        raw_po = pd.read_sql(self.db.query(FactPurchaseOrder).statement, self.db.bind)
        
        if not raw_mb51.empty and not raw_po.empty:
            raw_mb51['po_number'] = raw_mb51['col_15_purchase_order'].apply(lambda x: str(x).strip() if x else None)
            merged_po = pd.merge(
                raw_mb51[raw_mb51['po_number'].notna()],
                raw_po[['purch_order', 'purch_date']],
                left_on='po_number',
                right_on='purch_order',
                how='inner'
            )
            
            for _, row in merged_po.iterrows():
                batch = safe_convert(row.get('col_6_batch'))
                
                # SKIP if this batch was already processed as Production Order
                if batch and batch in processed_batches:
                    continue
                    
                gr_date = safe_convert(row.get('col_0_posting_date'))
                po_date = safe_convert(row.get('purch_date'))
                
                if not gr_date or not po_date: continue
                if isinstance(gr_date, datetime): gr_date = gr_date.date()
                if isinstance(po_date, datetime): po_date = po_date.date()
                
                transit_days = (gr_date - po_date).days
                if transit_days < 0: continue
                
                # Calculate Storage Time
                storage_days = 0
                if batch and batch in batch_issue_map:
                    issue_date = batch_issue_map[batch]
                    if issue_date >= gr_date:
                        storage_days = (issue_date - gr_date).days
                
                order_number = safe_convert(row.get('po_number'))

                # Skip duplicates within the same run (unique key: order_number + batch)
                if order_number and batch and (order_number, batch) in seen_pairs:
                    continue
                if order_number and batch:
                    seen_pairs.add((order_number, batch))

                fact = FactLeadTime(
                    material_code=safe_convert(row.get('col_4_material')),
                    plant_code=safe_convert(row.get('col_2_plant')),
                    order_number=order_number,
                    order_type='PURCHASE', # External
                    batch=batch, # Capture Batch!
                    start_date=po_date,
                    end_date=gr_date,
                    lead_time_days=transit_days + storage_days, # Total
                    transit_days=transit_days, # Map to Transit
                    storage_days=storage_days, # Map to Storage
                    # Others 0
                )
                self.db.add(fact)
                count += 1
                
                # Batch commit every 1000 records
                if count % 1000 == 0:
                    self.db.commit()
                
        self.db.commit()
        print(f"  [OK] Calculated {count} lead time records (Production + Purchase + Storage)")

        print("TRANSFORMATION COMPLETE")
        print("=" * 60)
    
    def build_production_chains(self):
        """Production chain analysis removed - yield module decommissioned"""
        print("Building production chains (P03→P02→P01)...")
        print("  ⚠ Production chain analysis removed (yield module decommissioned)")
        print("  ✓ Skipped production chain building")
    
    def calculate_p02_p01_yields(self):
        """P02→P01 yield calculation removed - yield module decommissioned"""
        print("Calculating P02→P01 yields...")
        print("  ⚠ Yield calculation removed (yield module decommissioned)")
        print("  ✓ Skipped yield calculations")
    
    def detect_alerts(self):
        """Detect and insert alerts (stuck transit only - yield alerts removed)"""
        print("Detecting alerts...")
        
        mb51_df = self.normalize_mb51_df(self.load_raw_to_df(RawMb51))
        
        if mb51_df.empty:
            print("  ⚠ No mb51 data for alert detection")
            return
        
        detector = AlertDetector(
            mb51_df=mb51_df,
            production_chain_df=None,  # No longer used - yield module decommissioned
            uom_converter=self.uom_converter
        )
        
        # Detect stuck in transit (Factory → DC, so check at DC plant 1401)
        stuck_alerts = detector.detect_stuck_in_transit(plant=1401)
        
        # Yield alerts removed - decommissioned
        
        # Insert alerts
        all_alerts = stuck_alerts
        count = 0
        
        for alert in all_alerts:
            try:
                # Check if similar alert already exists (prevent duplicates)
                existing = self.db.query(FactAlert).filter_by(
                    alert_type=alert.alert_type,
                    entity_id=alert.entity_id
                ).first()
                
                if not existing:
                    # Map alert data to FactAlert columns
                    # STUCK_IN_TRANSIT/DELAYED_TRANSIT → stuck_hours
                    # LOW_YIELD → yield_pct
                    fact = FactAlert(
                        alert_type=alert.alert_type,
                        severity=alert.severity,
                        entity_type=alert.entity_type,
                        entity_id=alert.entity_id,
                        batch=alert.batch,
                        material=alert.material,
                        plant=alert.plant,
                        stuck_hours=alert.metric_value if alert.alert_type in ('STUCK_IN_TRANSIT', 'DELAYED_TRANSIT') else None,
                        yield_pct=alert.metric_value if alert.alert_type == 'LOW_YIELD' else None,
                        message=alert.message,  # ← FIX: Add message field
                        detected_at=alert.detected_at,
                        status='ACTIVE'
                    )
                    self.db.add(fact)
                    count += 1
            except Exception as e:
                print(f"  ⚠ Error inserting alert: {e}")
        
        self.db.commit()
        print(f"  ✓ Detected {count} new alerts")

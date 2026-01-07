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
from datetime import datetime
import hashlib
import json
from sqlalchemy import func

from sqlalchemy.orm import Session

from src.db.models import (
    # Raw tables
    RawCooispi, RawMb51, RawZrmm024, RawZrsd002,
    RawZrsd004, RawZrsd006, RawZrfi005, RawTarget,
    # Fact tables
    FactProduction, FactInventory, FactPurchaseOrder,
    FactBilling, FactDelivery, FactArAging, FactTarget,
    FactProductionChain, FactAlert, FactLeadTime,
    # Dimension tables
    DimMaterial, DimUomConversion, DimPlant, DimMvt,
)
from src.core.netting import StackNettingEngine, get_stock_impact
from src.core.uom_converter import UomConverter
from src.core.business_logic import OrderClassifier, LeadTimeCalculator
from src.core.yield_tracker import YieldTracker
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
        """Transform raw_mb51 to fact_inventory (AGGREGATED by Material+Plant)"""
        print("Transforming mb51 to fact_inventory (aggregated)...")
        
        raw_df = self.load_raw_to_df(RawMb51)
        if raw_df.empty:
            print("  ⚠ No data in raw_mb51")
            return
        
        # Filter valid movement types
        raw_df = raw_df[raw_df['col_1_mvt_type'].notna()].copy()
        
        # Add stock impact
        raw_df['stock_impact'] = raw_df['col_1_mvt_type'].apply(
            lambda x: get_stock_impact(x) if pd.notna(x) else 0
        )
        
        # Convert to KG
        def convert_to_kg(row):
            material = row.get('col_4_material')
            uom = row.get('col_8_uom')
            qty = row.get('col_7_qty')
            
            if pd.isna(material) or pd.isna(qty):
                return 0.0  # Return 0 instead of None for aggregation
                
            kg_per_unit = self.uom_converter.get_kg_per_unit(str(material))
            if kg_per_unit:
                return float(qty) * kg_per_unit if uom == 'PC' else float(qty)
            return 0.0
        
        raw_df['qty_kg'] = raw_df.apply(convert_to_kg, axis=1)
        
        # AGGREGATE by Material + Plant
        agg_df = raw_df.groupby(['col_4_material', 'col_2_plant'], dropna=False).agg({
            'col_0_posting_date': 'max',
            'col_5_material_desc': 'first',
            'col_7_qty': 'sum',
            'qty_kg': 'sum',
            'stock_impact': 'sum',
            'id': 'first'
        }).reset_index()
        
        count = 0
        skipped = 0
        for _, row in agg_df.iterrows():
            material = safe_convert(row['col_4_material'])
            plant = safe_convert(row['col_2_plant'])
            
            # Skip if no material or plant
            if material is None or plant is None:
                skipped += 1
                continue
            
            # Use safe_convert for ALL values
            posting_date = safe_convert(row['col_0_posting_date'])
            material_desc = safe_convert(row['col_5_material_desc'])
            qty = safe_convert(row['col_7_qty'])
            qty_kg = safe_convert(row['qty_kg'])
            stock_impact = safe_convert(row['stock_impact'])
            raw_id = safe_convert(row['id'])
            
            # Compute hash
            hash_data = {
                'material': material,
                'plant': plant,
                'net_stock': stock_impact if stock_impact is not None else 0
            }
            row_hash = compute_row_hash(hash_data)
            
            fact = FactInventory(
                posting_date=posting_date,
                mvt_type=999,  # Special code for aggregated records
                plant_code=plant,
                sloc_code=None,
                material_code=material,
                material_description=material_desc,
                batch=None,
                qty=qty,
                uom='KG',
                qty_kg=qty_kg,
                cost_center=None,
                gl_account=None,
                material_document=None,
                reference=None,
                outbound_delivery=None,
                purchase_order=None,
                stock_impact=stock_impact,
                row_hash=row_hash,
                raw_id=raw_id
            )
            self.db.add(fact)
            count += 1
        
        self.db.commit()
        print(f"  ✓ Transformed {count} aggregated inventory records (from {len(raw_df)} movements, skipped {skipped})")

    
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
        """Transform raw_zrsd004 to fact_delivery"""
        print("Transforming zrsd004 → fact_delivery...")
        
        raw_df = self.load_raw_to_df(RawZrsd004)
        if raw_df.empty:
            print("  ⚠ No data in raw_zrsd004")
            return
        
        count = 0
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
            
            fact = FactDelivery(
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
            count += 1
        
        self.db.commit()
        print(f"  ✓ Transformed {count} delivery records")
    
    def transform_zrfi005(self, target_date: Optional[str] = None):
        """
        Transform raw_zrfi005 to fact_ar_aging
        
        Args:
            target_date: Optional snapshot date (YYYY-MM-DD) to transform.
                        If None, uses the latest snapshot_date.
        
        Business Rule: Only transform ONE snapshot at a time
        - Multiple snapshots can exist in raw_zrfi005 (historical data)
        - Dashboard should show one snapshot at a time based on user selection
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
        
        # Truncate fact table first to avoid duplicates
        deleted = self.db.query(FactArAging).delete()
        self.db.commit()
        if deleted > 0:
            print(f"  ⚠ Cleared {deleted} existing records from fact_ar_aging")
        
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
        for _, row in conversion_df.iterrows():
            existing = self.db.query(DimUomConversion).filter_by(
                material_code=row['material']
            ).first()
            
            if existing:
                existing.kg_per_unit = row['kg_per_unit']
                existing.sample_count = row['sample_count']
                existing.variance_pct = row.get('variance_pct')
                existing.last_updated = datetime.utcnow()
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
        print(f"  ✓ Built UOM conversion for {count} materials")
    
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
                
                # Calculate Storage Time
                storage_days = 0
                if batch and batch in batch_issue_map:
                    issue_date = batch_issue_map[batch]
                    if issue_date >= end:
                        storage_days = (issue_date - end).days
                
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
                
                fact = FactLeadTime(
                    material_code=safe_convert(row.get('material_code')),
                    plant_code=safe_convert(row.get('plant_code')),
                    order_number=safe_convert(row.get('order_number')),
                    order_type=order_type,
                    batch=batch,
                    channel_code=channel_code,
                    start_date=start,
                    end_date=end,
                    lead_time_days=prod_days + storage_days + prep_days, # Total
                    production_days=prod_days, # Map to Production
                    storage_days=storage_days, # Map to Storage
                    preparation_days=prep_days, # Map to Preparation
                    transit_days=0
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
                
                fact = FactLeadTime(
                    material_code=safe_convert(row.get('col_4_material')),
                    plant_code=safe_convert(row.get('col_2_plant')),
                    order_number=safe_convert(row.get('po_number')),
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
        """Build fact_production_chain from cooispi + mb51"""
        print("Building production chains (P03→P02→P01)...")
        
        cooispi_df = self.load_raw_to_df(RawCooispi)
        mb51_df = self.normalize_mb51_df(self.load_raw_to_df(RawMb51))
        
        if cooispi_df.empty or mb51_df.empty:
            print("  ⚠ Missing data for production chain analysis")
            return
        
        tracker = YieldTracker(cooispi_df, mb51_df, self.uom_converter)
        
        # Find all P01 orders
        p01_orders = tracker.find_p01_orders()
        
        if p01_orders.empty:
            print("  ⚠ No P01 orders found")
            return
        
        count = 0
        for _, p01_row in p01_orders.iterrows():
            try:
                # Build chain
                chain = tracker.build_chain_from_p01(p01_row['order'])
                
                if chain and chain.chain_complete:
                    # Insert into fact_production_chain
                    fact = FactProductionChain(
                        p01_order=chain.p01.order if chain.p01 else None,
                        p01_batch=chain.p01.batch if chain.p01 else None,
                        p01_material=chain.p01.material if chain.p01 else None,
                        p01_output_qty=chain.p01.output_qty if chain.p01 else None,
                        p01_output_kg=chain.p01.output_kg if chain.p01 else None,
                        p02_order=chain.p02.order if chain.p02 else None,
                        p02_batch=chain.p02.batch if chain.p02 else None,
                        p02_material=chain.p02.material if chain.p02 else None,
                        p02_yield_pct=chain.p02.yield_pct if chain.p02 else None,
                        p03_order=chain.p03.order if chain.p03 else None,
                        p03_batch=chain.p03.batch if chain.p03 else None,
                        p03_material=chain.p03.material if chain.p03 else None,
                        p03_yield_pct=chain.p03.yield_pct if chain.p03 else None,
                        total_yield_pct=chain.total_yield_pct,
                        total_loss_kg=chain.total_loss_kg,
                        chain_complete=chain.chain_complete
                    )
                    self.db.add(fact)
                    count += 1
            except Exception as e:
                print(f"  ⚠ Error building chain for order {p01_row.get('order')}: {e}")
        
        self.db.commit()
        print(f"  ✓ Built {count} production chains")
    
    def calculate_p02_p01_yields(self):
        """Calculate P02→P01 yields using dual validation"""
        print("Calculating P02→P01 yields...")
        
        from src.db.models import FactP02P01Yield
        from src.core.p02_p01_yield import find_all_p02_p01_pairs
        
        mb51_df = self.normalize_mb51_df(self.load_raw_to_df(RawMb51))
        
        if mb51_df.empty:
            print("  ⚠ No MB51 data for yield calculation")
            return
        
        # Find all valid P02→P01 pairs
        yield_pairs = find_all_p02_p01_pairs(mb51_df, self.uom_converter)
        
        count = 0
        for yield_data in yield_pairs:
            try:
                fact = FactP02P01Yield(
                    p02_batch=yield_data.p02_batch,
                    p01_batch=yield_data.p01_batch,
                    p02_material_code=yield_data.p02_material_code,
                    p02_material_desc=yield_data.p02_material_desc,
                    p01_material_code=yield_data.p01_material_code,
                    p01_material_desc=yield_data.p01_material_desc,
                    p02_consumed_kg=yield_data.p02_consumed_kg,
                    p01_produced_kg=yield_data.p01_produced_kg,
                    yield_pct=yield_data.yield_pct,
                    loss_kg=yield_data.loss_kg,
                    production_date=yield_data.production_date
                )
                self.db.add(fact)
                count += 1
            except Exception as e:
                print(f"  ⚠ Error inserting yield data: {e}")
        
        self.db.commit()
        print(f"  ✓ Calculated {count} P02→P01 yields")
    
    def detect_alerts(self):
        """Detect and insert alerts (stuck transit, low yield)"""
        print("Detecting alerts...")
        
        mb51_df = self.normalize_mb51_df(self.load_raw_to_df(RawMb51))
        
        if mb51_df.empty:
            print("  ⚠ No mb51 data for alert detection")
            return
        
        # Load production chains
        production_chain_df = pd.read_sql_table('fact_production_chain', self.db.bind)
        
        detector = AlertDetector(
            mb51_df=mb51_df,
            production_chain_df=production_chain_df if not production_chain_df.empty else None,
            uom_converter=self.uom_converter
        )
        
        # Detect stuck in transit (Factory → DC, so check at DC plant 1401)
        stuck_alerts = detector.detect_stuck_in_transit(plant=1401)
        
        # Detect low yield (using view_yield_dashboard, not production chains)
        low_yield_alerts = detector.detect_low_yield()
        
        # Insert alerts
        all_alerts = stuck_alerts + low_yield_alerts
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

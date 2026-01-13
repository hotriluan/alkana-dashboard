"""
SQLAlchemy ORM Models for Alkana Dashboard

Architecture: ELT 3-Layer
- Layer 1: Raw Tables (raw_*) - Staging, audit trail
- Layer 3: Warehouse Tables (fact_*, dim_*) - Analytics

Note: User/Role models in auth_models.py (separation of concerns)
"""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, 
    Numeric, Text, Boolean, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from src.db.connection import Base


# =============================================================================
# LAYER 1: RAW DATA LAKE (Staging Tables)
# Purpose: Load ALL data AS-IS for audit trail and re-processing
# =============================================================================

class RawCooispi(Base):
    """Raw Production Orders from cooispi.XLSX - ALL COLUMNS"""
    __tablename__ = "raw_cooispi"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # ALL columns from Excel - no filtering
    plant = Column(Integer)
    sales_order = Column(String(50))
    order = Column(String(50))
    order_type = Column(String(20))
    material_number = Column(String(50))
    release_date_actual = Column(DateTime)
    actual_finish_date = Column(DateTime)
    material_description = Column(String(200))
    bom_alternative = Column(Integer)
    batch = Column(String(50))
    system_status = Column(String(200))
    mrp_controller = Column(String(20))
    order_quantity = Column(Numeric(18, 4))
    delivered_quantity = Column(Numeric(18, 4))
    unit_of_measure = Column(String(20))
    
    # Additional columns that may exist
    extra_col_1 = Column(String(200))
    extra_col_2 = Column(String(200))
    extra_col_3 = Column(String(200))
    
    # Metadata
    source_file = Column(String(100))
    source_row = Column(Integer)  # Original Excel row number
    loaded_at = Column(DateTime, default=datetime.utcnow)
    raw_data = Column(JSONB)  # Store entire row as JSON for safety
    row_hash = Column(String(32))  # MD5 hash for change detection


class RawMb51(Base):
    """Raw Material Movements from mb51.XLSX - NO HEADER FILE, ALL COLUMNS"""
    __tablename__ = "raw_mb51"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Index-based columns (NO HEADER in source)
    col_0_posting_date = Column(DateTime)        # Index 0
    col_1_mvt_type = Column(Integer)             # Index 1
    col_2_plant = Column(Integer)                # Index 2
    col_3_sloc = Column(Integer)                 # Index 3
    col_4_material = Column(String(50))          # Index 4
    col_5_material_desc = Column(String(200))    # Index 5
    col_6_batch = Column(String(50))             # Index 6
    col_7_qty = Column(Numeric(18, 4))           # Index 7
    col_8_uom = Column(String(20))               # Index 8
    col_9_cost_center = Column(String(50))       # Index 9
    col_10_gl_account = Column(String(50))       # Index 10
    col_11_material_doc = Column(String(50))     # Index 11
    col_12_reference = Column(String(100))       # Index 12
    col_13_outbound_delivery = Column(String(50))# Index 13
    col_14 = Column(String(100))                 # Index 14 (unknown)
    col_15_purchase_order = Column(String(50))   # Index 15
    
    # Metadata
    source_file = Column(String(100))
    source_row = Column(Integer)
    loaded_at = Column(DateTime, default=datetime.utcnow)
    raw_data = Column(JSONB)
    row_hash = Column(String(32))  # MD5 hash for change detection


class RawZrmm024(Base):
    """Raw Purchase Orders from zrmm024.XLSX - ALL 58 COLUMNS"""
    __tablename__ = "raw_zrmm024"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Key columns we know
    purch_order = Column(String(50))
    item = Column(Integer)
    purch_date = Column(DateTime)
    suppl_plant = Column(Integer)
    dest_plant = Column(Integer)
    material = Column(String(50))
    material_desc = Column(String(200))
    qty_order = Column(Numeric(18, 4))
    gross_weight = Column(Numeric(18, 4))
    tonnage_order = Column(Numeric(18, 4))
    qty_order_tol = Column(Numeric(18, 4))
    delivery_date = Column(DateTime)
    qty_gi = Column(Numeric(18, 4))
    tonnage_gi = Column(Numeric(18, 4))
    qty_receipt = Column(Numeric(18, 4))
    
    # Store ALL columns as JSON (58 columns is too many to define individually)
    source_file = Column(String(100))
    source_row = Column(Integer)
    loaded_at = Column(DateTime, default=datetime.utcnow)
    raw_data = Column(JSONB)  # ALL 58 columns stored here
    row_hash = Column(String(32))  # MD5 hash for change detection


class RawZrsd002(Base):
    """Raw Billing Documents from zrsd002.XLSX - ALL 30 COLUMNS"""
    __tablename__ = "raw_zrsd002"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Key billing columns
    billing_date = Column(DateTime)
    billing_document = Column(String(50))
    billing_item = Column(Integer)
    sloc = Column(String(20))
    sales_office = Column(String(20))
    dist_channel = Column(String(20))
    customer_name = Column(String(200))
    cust_group = Column(String(20))
    salesman_name = Column(String(100))
    material = Column(String(50))
    material_desc = Column(String(200))
    prod_hierarchy = Column(String(100))
    billing_qty = Column(Numeric(18, 4))
    sales_unit = Column(String(20))
    currency = Column(String(10))
    exchange_rate = Column(Numeric(18, 6))
    price = Column(Numeric(18, 4))
    total_price = Column(Numeric(18, 4))
    discount_item = Column(Numeric(18, 4))
    net_value = Column(Numeric(18, 4))
    tax = Column(Numeric(18, 4))
    total = Column(Numeric(18, 4))
    net_weight = Column(Numeric(18, 4))
    weight_unit = Column(String(20))
    volume = Column(Numeric(18, 4))
    volume_unit = Column(String(20))
    so_number = Column(String(50))
    so_date = Column(DateTime)
    doc_reference_od = Column(String(50))
    
    # Metadata
    source_file = Column(String(100))
    source_row = Column(Integer)
    loaded_at = Column(DateTime, default=datetime.utcnow)
    raw_data = Column(JSONB)
    row_hash = Column(String(32))  # MD5 hash for change detection


class RawZrsd004(Base):
    """Raw Delivery Documents from zrsd004.XLSX - ALL 23 COLUMNS"""
    __tablename__ = "raw_zrsd004"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Key delivery columns
    actual_gi_date = Column(DateTime)
    delivery = Column(String(50))
    line_item = Column(Integer)
    so_reference = Column(String(50))
    shipping_point = Column(String(20))
    sloc = Column(String(20))
    sales_office = Column(String(20))
    dist_channel = Column(String(20))
    cust_group = Column(String(20))
    sold_to_party = Column(String(50))
    ship_to_party = Column(String(50))
    ship_to_name = Column(String(200))
    ship_to_city = Column(String(100))
    salesman_id = Column(String(50))
    salesman_name = Column(String(100))
    material = Column(String(50))
    material_desc = Column(String(200))
    delivery_qty = Column(Numeric(18, 4))
    tonase = Column(Numeric(18, 4))
    tonase_unit = Column(String(20))
    net_weight = Column(Numeric(18, 4))
    volume = Column(Numeric(18, 4))
    prod_hierarchy = Column(String(100))
    
    # Metadata
    source_file = Column(String(100))
    source_row = Column(Integer)
    loaded_at = Column(DateTime, default=datetime.utcnow)
    raw_data = Column(JSONB)
    row_hash = Column(String(32))  # MD5 hash for change detection


class RawZrsd006(Base):
    """Raw Material Master from zrsd006.XLSX - ALL COLUMNS"""
    __tablename__ = "raw_zrsd006"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Product hierarchy columns
    material = Column(String(50))
    material_desc = Column(String(200))
    dist_channel = Column(String(20))
    uom = Column(String(20))
    ph1 = Column(String(50))
    ph1_desc = Column(String(100))
    ph2 = Column(String(50))
    ph2_desc = Column(String(100))
    ph3 = Column(String(50))
    ph3_desc = Column(String(100))
    ph4 = Column(String(50))
    ph4_desc = Column(String(100))
    ph5 = Column(String(50))
    ph5_desc = Column(String(100))
    ph6 = Column(String(50))
    ph6_desc = Column(String(100))
    ph7 = Column(String(50))
    ph7_desc = Column(String(100))
    
    # Metadata
    source_file = Column(String(100))
    source_row = Column(Integer)
    loaded_at = Column(DateTime, default=datetime.utcnow)
    raw_data = Column(JSONB)
    row_hash = Column(String(32))  # MD5 hash for change detection


class RawZrfi005(Base):
    """Raw AR Aging from ZRFI005.XLSX - ALL 20 COLUMNS"""
    __tablename__ = "raw_zrfi005"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # AR Aging columns
    dist_channel = Column(String(20))
    cust_group = Column(String(20))
    salesman_name = Column(String(100))
    customer_name = Column(String(200))
    currency = Column(String(10))
    target_1_30 = Column(Numeric(18, 4))
    target_31_60 = Column(Numeric(18, 4))
    target_61_90 = Column(Numeric(18, 4))
    target_91_120 = Column(Numeric(18, 4))
    target_121_180 = Column(Numeric(18, 4))
    target_over_180 = Column(Numeric(18, 4))
    total_target = Column(Numeric(18, 4))
    realization_not_due = Column(Numeric(18, 4))
    realization_1_30 = Column(Numeric(18, 4))
    realization_31_60 = Column(Numeric(18, 4))
    realization_61_90 = Column(Numeric(18, 4))
    realization_91_120 = Column(Numeric(18, 4))
    realization_121_180 = Column(Numeric(18, 4))
    realization_over_180 = Column(Numeric(18, 4))
    total_realization = Column(Numeric(18, 4))
    
    # Snapshot date for daily AR uploads
    snapshot_date = Column(Date)
    
    # Metadata
    source_file = Column(String(100))
    source_row = Column(Integer)
    loaded_at = Column(DateTime, default=datetime.utcnow)
    raw_data = Column(JSONB)
    row_hash = Column(String(64))  # MD5 hash for change detection


class RawTarget(Base):
    """Raw Sales Targets from target.xlsx - ALL 4 COLUMNS"""
    __tablename__ = "raw_target"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Target columns
    salesman_name = Column(String(100))
    semester = Column(Integer)
    year = Column(Integer)
    target = Column(Numeric(18, 4))
    
    # Metadata
    source_file = Column(String(100))
    source_row = Column(Integer)
    loaded_at = Column(DateTime, default=datetime.utcnow)
    raw_data = Column(JSONB)
    row_hash = Column(String(32))  # MD5 hash for change detection


class UploadHistory(Base):
    """Upload history tracking for file uploads via API"""
    __tablename__ = "upload_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # File information
    file_name = Column(String(255), nullable=False)  # UUID filename
    original_name = Column(String(255), nullable=False)  # User's filename
    file_type = Column(String(50), nullable=False)  # COOISPI, MB51, ZRFI005, etc.
    file_size = Column(Integer)  # Bytes
    file_hash = Column(String(64))  # MD5 hash of file
    
    # Processing status
    status = Column(String(20), nullable=False, default='pending')  # pending, processing, completed, failed
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime)
    
    # Processing statistics
    rows_loaded = Column(Integer, default=0)
    rows_updated = Column(Integer, default=0)
    rows_skipped = Column(Integer, default=0)
    rows_failed = Column(Integer, default=0)
    
    # Error tracking
    error_message = Column(Text)
    
    # User tracking (future: link to User model)
    uploaded_by = Column(String(100))
    
    # AR snapshot tracking
    snapshot_date = Column(Date)  # For ZRFI005 daily snapshots


# =============================================================================
# LAYER 3: DATA WAREHOUSE (Star Schema)
# =============================================================================

class FactProduction(Base):
    """Fact: Production Orders (from cooispi)"""
    __tablename__ = "fact_production"
    
    id = Column(Integer, primary_key=True)
    plant_code = Column(Integer, nullable=False, index=True)
    sales_order = Column(String(50), index=True)
    order_number = Column(String(50), nullable=False)
    order_type = Column(String(20))
    material_code = Column(String(50), index=True)
    material_description = Column(String(200))
    release_date = Column(Date)
    actual_finish_date = Column(Date)
    bom_alternative = Column(Integer)
    batch = Column(String(50), index=True)
    system_status = Column(String(200))
    mrp_controller = Column(String(20), index=True)
    order_qty = Column(Numeric(18, 4))
    order_qty_kg = Column(Numeric(18, 4))  # Normalized to KG
    delivered_qty = Column(Numeric(18, 4))
    delivered_qty_kg = Column(Numeric(18, 4))  # Normalized
    uom = Column(String(20))
    
    # Derived fields
    is_mto = Column(Boolean, default=False)  # MTO dual logic
    order_status = Column(String(20))  # CANCELLED/WIP/COMPLETED/IN_TRANSIT
    
    # Lead-time tracking (Phase 6.1 - NEXT_STEPS.md)
    # MTO: 5 stages (Preparation → Production → Transit → Storage → Delivery)
    # MTS: 3 stages (Production → Transit → Storage)
    prep_time_days = Column(Integer)  # MTO only: PO Date → Release
    production_time_days = Column(Integer)  # Release → Finish
    transit_time_days = Column(Integer)  # Finish → Receipt (MVT 101)
    storage_time_days = Column(Integer)  # Receipt → Issue (MVT 601 netted)
    delivery_time_days = Column(Integer)  # MTO only: Issue → Actual GI
    total_leadtime_days = Column(Integer)  # Sum of all components
    leadtime_status = Column(String(20))  # ON_TIME, DELAYED, CRITICAL, UNKNOWN
    
    # Audit
    row_hash = Column(String(32))
    raw_id = Column(Integer)  # Link to raw_cooispi
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


class FactInventory(Base):
    """Fact: Material Movements (from mb51)"""
    __tablename__ = "fact_inventory"
    
    id = Column(Integer, primary_key=True)
    posting_date = Column(Date, nullable=False, index=True)
    mvt_type = Column(Integer, nullable=False, index=True)
    plant_code = Column(Integer, nullable=False, index=True)
    sloc_code = Column(Integer)
    material_code = Column(String(50), index=True)
    material_description = Column(String(200))
    batch = Column(String(50), index=True)
    qty = Column(Numeric(18, 4))
    qty_kg = Column(Numeric(18, 4))  # Normalized
    uom = Column(String(20))
    cost_center = Column(String(50))
    gl_account = Column(String(50))
    material_document = Column(String(50))
    reference = Column(String(100), index=True)
    outbound_delivery = Column(String(50))
    purchase_order = Column(String(50), index=True)
    
    # Derived fields
    stock_impact = Column(Integer)  # +1, -1, 0
    is_netted = Column(Boolean, default=False)  # After netting algorithm
    net_qty = Column(Numeric(18, 4))  # Quantity after netting
    
    # Audit
    row_hash = Column(String(32))
    raw_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class FactPurchaseOrder(Base):
    """Fact: Purchase Orders (from zrmm024)"""
    __tablename__ = "fact_purchase_order"
    
    id = Column(Integer, primary_key=True)
    purch_order = Column(String(50), nullable=False, index=True)
    item = Column(Integer, nullable=False)
    purch_date = Column(Date)
    suppl_plant = Column(Integer)
    dest_plant = Column(Integer)
    material_code = Column(String(50), index=True)
    material_description = Column(String(200))
    qty_order = Column(Numeric(18, 4))
    gross_weight = Column(Numeric(18, 4))
    tonnage_order = Column(Numeric(18, 4))
    qty_order_tol = Column(Numeric(18, 4))
    delivery_date = Column(Date)
    qty_gi = Column(Numeric(18, 4))
    tonnage_gi = Column(Numeric(18, 4))
    qty_receipt = Column(Numeric(18, 4))
    
    # Derived: Is this a sales PO (starts with 44)?
    is_sales_po = Column(Boolean, default=False)
    
    # Audit
    row_hash = Column(String(32))
    raw_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class FactBilling(Base):
    """Fact: Billing Documents (from zrsd002)"""
    __tablename__ = "fact_billing"
    
    id = Column(Integer, primary_key=True)
    billing_date = Column(Date, index=True)
    billing_document = Column(String(50), nullable=False)
    billing_item = Column(Integer, nullable=False)
    sloc = Column(String(20))
    sales_office = Column(String(20))
    dist_channel = Column(String(20))
    customer_name = Column(String(200))
    cust_group = Column(String(20))
    salesman_name = Column(String(100), index=True)
    material_code = Column(String(50), index=True)
    material_description = Column(String(200))
    prod_hierarchy = Column(String(100))
    billing_qty = Column(Numeric(18, 4))
    billing_qty_kg = Column(Numeric(18, 4))  # Normalized
    sales_unit = Column(String(20))
    currency = Column(String(10))
    exchange_rate = Column(Numeric(18, 6))
    price = Column(Numeric(18, 4))
    total_price = Column(Numeric(18, 4))
    discount_item = Column(Numeric(18, 4))
    net_value = Column(Numeric(18, 4))
    tax = Column(Numeric(18, 4))
    total = Column(Numeric(18, 4))
    net_weight = Column(Numeric(18, 4))
    weight_unit = Column(String(20))
    volume = Column(Numeric(18, 4))
    volume_unit = Column(String(20))
    so_number = Column(String(50), index=True)
    so_date = Column(Date)
    doc_reference_od = Column(String(50), index=True)
    
    # Derived
    semester = Column(Integer)
    year = Column(Integer)
    
    # Audit
    row_hash = Column(String(32))
    raw_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class FactDelivery(Base):
    """Fact: Delivery Documents (from zrsd004)"""
    __tablename__ = "fact_delivery"
    
    id = Column(Integer, primary_key=True)
    actual_gi_date = Column(Date, index=True)
    delivery = Column(String(50), nullable=False)
    line_item = Column(Integer, nullable=False)
    so_reference = Column(String(50), index=True)
    shipping_point = Column(String(20))
    sloc = Column(String(20))
    sales_office = Column(String(20))
    dist_channel = Column(String(20))
    cust_group = Column(String(20))
    sold_to_party = Column(String(50))
    ship_to_party = Column(String(50))
    ship_to_name = Column(String(200))
    ship_to_city = Column(String(100))
    salesman_id = Column(String(50))
    salesman_name = Column(String(100), index=True)
    material_code = Column(String(50), index=True)
    material_description = Column(String(200))
    delivery_qty = Column(Numeric(18, 4))
    delivery_qty_kg = Column(Numeric(18, 4))  # Normalized
    tonase = Column(Numeric(18, 4))
    tonase_unit = Column(String(20))
    net_weight = Column(Numeric(18, 4))
    volume = Column(Numeric(18, 4))
    prod_hierarchy = Column(String(100))
    
    # Audit
    row_hash = Column(String(32))
    raw_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class FactArAging(Base):
    """Fact: AR Aging (from zrfi005)"""
    __tablename__ = "fact_ar_aging"
    
    id = Column(Integer, primary_key=True)
    dist_channel = Column(String(20))
    cust_group = Column(String(20))
    salesman_name = Column(String(100), index=True)
    customer_name = Column(String(200), nullable=False, index=True)
    currency = Column(String(10))
    target_1_30 = Column(Numeric(18, 4))
    target_31_60 = Column(Numeric(18, 4))
    target_61_90 = Column(Numeric(18, 4))
    target_91_120 = Column(Numeric(18, 4))
    target_121_180 = Column(Numeric(18, 4))
    target_over_180 = Column(Numeric(18, 4))
    total_target = Column(Numeric(18, 4))
    realization_not_due = Column(Numeric(18, 4))
    realization_1_30 = Column(Numeric(18, 4))
    realization_31_60 = Column(Numeric(18, 4))
    realization_61_90 = Column(Numeric(18, 4))
    realization_91_120 = Column(Numeric(18, 4))
    realization_121_180 = Column(Numeric(18, 4))
    realization_over_180 = Column(Numeric(18, 4))
    total_realization = Column(Numeric(18, 4))
    
    # Metadata
    report_date = Column(Date)
    snapshot_date = Column(Date, index=True)  # When this AR snapshot was taken
    row_hash = Column(String(32))
    raw_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class FactTarget(Base):
    """Fact: Sales Targets"""
    __tablename__ = "fact_target"
    
    id = Column(Integer, primary_key=True)
    salesman_name = Column(String(100), nullable=False, index=True)
    semester = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    target = Column(Numeric(18, 4))
    
    row_hash = Column(String(32))
    raw_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# LEGACY TABLES (DECOMMISSIONED 2026-01-12 - Deep Clean Operation)
# ============================================================================
# class FactProductionChain(Base):
#     """Fact: Yield Tracking P03→P02→P01 (REMOVED - genealogy decommissioned)"""
#     __tablename__ = "fact_production_chain"
#     ...

# class FactP02P01Yield(Base):
#     """P02→P01 Yield Tracking (REMOVED - genealogy decommissioned)"""
#     __tablename__ = "fact_p02_p01_yield"
#     ...


# ============================================================================
# LEGACY TABLES (DECOMMISSIONED 2026-01-12 - Deep Clean Operation)
# ============================================================================
# class FactProductionChain(Base):
#     """Fact: Yield Tracking P03→P02→P01 (REMOVED - genealogy decommissioned)"""
#     __tablename__ = "fact_production_chain"
#     ...

# class FactP02P01Yield(Base):
#     """P02→P01 Yield Tracking (REMOVED - genealogy decommissioned)"""
#     __tablename__ = "fact_p02_p01_yield"
#     ...


# =============================================================================
# DIMENSION TABLES
# =============================================================================

class DimMaterial(Base):
    """Dimension: Material Master with Product Hierarchy"""
    __tablename__ = "dim_material"
    
    material_code = Column(String(50), primary_key=True)
    material_description = Column(String(200))
    dist_channel = Column(String(20))
    uom = Column(String(20))
    ph1 = Column(String(50))
    ph1_desc = Column(String(100))
    ph2 = Column(String(50))
    ph2_desc = Column(String(100))
    ph3 = Column(String(50))
    ph3_desc = Column(String(100))
    ph4 = Column(String(50))
    ph4_desc = Column(String(100))
    ph5 = Column(String(50))
    ph5_desc = Column(String(100))
    ph6 = Column(String(50))
    ph6_desc = Column(String(100))
    ph7 = Column(String(50))
    ph7_desc = Column(String(100))
    
    row_hash = Column(String(32))
    created_at = Column(DateTime, default=datetime.utcnow)


class DimUomConversion(Base):
    """Dimension: UOM Conversion (PC to KG)"""
    __tablename__ = "dim_uom_conversion"
    
    material_code = Column(String(50), primary_key=True)
    material_description = Column(String(200))
    mrp_controller = Column(String(20))
    base_uom = Column(String(20))
    kg_per_unit = Column(Numeric(18, 6))
    source = Column(String(20), default='billing')
    sample_count = Column(Integer)
    variance_pct = Column(Numeric(10, 2))  # Changed from (5,2) to (10,2) to handle larger variance values
    last_updated = Column(DateTime, default=datetime.utcnow)


class DimPlant(Base):
    """Dimension: Plant"""
    __tablename__ = "dim_plant"
    
    plant_code = Column(Integer, primary_key=True)
    plant_name = Column(String(50))
    plant_role = Column(String(20))  # FACTORY, DC, OTHER
    description = Column(String(200))


class DimStorageLocation(Base):
    """Dimension: Storage Location"""
    __tablename__ = "dim_storage_location"
    
    sloc_code = Column(Integer, primary_key=True)
    plant_code = Column(Integer)
    sloc_name = Column(String(50))
    description = Column(String(200))


class DimMvt(Base):
    """Dimension: Movement Type"""
    __tablename__ = "dim_mvt"
    
    mvt_code = Column(Integer, primary_key=True)
    description = Column(String(200))
    stock_impact = Column(Integer)  # +1, -1, 0
    reversal_mvt = Column(Integer)
    category = Column(String(50))


class DimCustomerGroup(Base):
    """Dimension: Customer Group"""
    __tablename__ = "dim_customer_group"
    
    group_code = Column(String(20), primary_key=True)
    description = Column(String(200))


class DimDistChannel(Base):
    """Dimension: Distribution Channel"""
    __tablename__ = "dim_dist_channel"
    
    channel_code = Column(String(20), primary_key=True)
    description = Column(String(200))


# =============================================================================
# ALERT TABLE
# =============================================================================

class FactAlert(Base):
    """Fact: System Alerts"""
    __tablename__ = "fact_alerts"
    
    id = Column(Integer, primary_key=True)
    alert_type = Column(String(50), nullable=False)  # STUCK_IN_TRANSIT, LOW_YIELD
    severity = Column(String(20))  # CRITICAL, HIGH, MEDIUM
    status = Column(String(20), default='ACTIVE')  # ACTIVE, RESOLVED
    
    # Related entity
    entity_type = Column(String(50))  # BATCH, ORDER, etc.
    entity_id = Column(String(50))
    
    # Alert details
    batch = Column(String(50))
    material = Column(String(50))
    plant = Column(Integer)
    
    # Metrics
    stuck_hours = Column(Numeric(10, 2))
    yield_pct = Column(Numeric(5, 2))
    loss_kg = Column(Numeric(18, 4))
    
    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    # Description
    message = Column(Text)

class FactLeadTime(Base):
    """Fact: Lead Time Analysis (Unified MTO/MTS/Purchase)"""
    __tablename__ = "fact_lead_time"
    
    id = Column(Integer, primary_key=True)
    material_code = Column(String(50), index=True)
    plant_code = Column(Integer, index=True)
    
    # Order Identifiers
    order_number = Column(String(50), index=True) # PO or Prod Order
    order_type = Column(String(20)) # PURCHASE, MTO, MTS
    batch = Column(String(50), index=True)
    channel_code = Column(String(10), index=True)  # Distribution Channel
    vendor = Column(String(100))
    
    # Dates
    start_date = Column(Date) # PO Date or Release Date
    end_date = Column(Date)   # GR Date or Finish Date
    
    # Stage Metrics (in Days)
    lead_time_days = Column(Integer) # Total
    preparation_days = Column(Integer, default=0)
    production_days = Column(Integer, default=0)
    transit_days = Column(Integer, default=0)
    storage_days = Column(Integer, default=0)
    delivery_days = Column(Integer, default=0)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)


# class FactP02P01Yield(Base):
#     """P02→P01 Yield Tracking - DECOMMISSIONED 2026-01-12"""
#     __tablename__ = "fact_p02_p01_yield"
#     ...


# =============================================================================
# V2 PRODUCTION PERFORMANCE (Isolated - ADR-2026-01-07)
# Source: zrpp062.XLSX - Production Variance Analysis
# =============================================================================

class RawZrpp062(Base):
    """Raw Production Performance from zrpp062.XLSX - V2 Isolated"""
    __tablename__ = "raw_zrpp062"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Key Identifiers
    process_order = Column(String(50))
    batch = Column(String(50))
    material = Column(String(50))
    material_description = Column(String(200))
    order_sfg_liquid = Column(String(50))  # Parent order (leading zeros stripped)
    
    # Hierarchy
    mrp_controller = Column(String(50))
    product_group_1 = Column(String(100))
    product_group_2 = Column(String(100))
    
    # Order Details
    qty_order_sfg_liquid = Column(Numeric(18, 4))
    process_order_qty = Column(Numeric(18, 4))
    uom = Column(String(20))
    bom_alt = Column(String(20))
    bom_text = Column(String(200))
    group_recipe = Column(String(100))
    
    # Metrics - Input
    gi_packaging_to_order = Column(Numeric(18, 4))
    gi_sfg_liquid_to_order = Column(Numeric(18, 4))
    
    # Metrics - Output
    gr_qty_to_0201 = Column(Numeric(18, 4))
    tonase_alkana_0201 = Column(Numeric(18, 4))  # output_actual_kg
    gr_by_product = Column(Numeric(18, 4))
    
    # Quality - SG (Specific Gravity)
    sg_theoretical = Column(Numeric(10, 4))
    sg_actual = Column(Numeric(10, 4))
    bar_sfg = Column(Numeric(18, 4))
    qty_allowance = Column(Numeric(18, 4))
    
    # Variance Metrics
    variant_prod_sfg_pct = Column(Numeric(10, 4))
    variant_fg_pc = Column(Numeric(18, 4))
    variant_fg_pct = Column(Numeric(10, 4))
    loss_kg = Column(Numeric(18, 4))  # Lossess FG Result (Kg)
    loss_pct = Column(Numeric(10, 4))  # Lossess FG Result (%)
    pc_to_kg_actual = Column(Numeric(18, 6))
    
    # Status
    system_status = Column(String(100))
    ud_status = Column(String(100))
    
    # Personnel
    pd_manager = Column(String(100))
    pd_leader = Column(String(100))
    
    # Date (ADR decision: add posting_date since CSV lacks date)
    posting_date = Column(Date)
    
    # Metadata
    source_file = Column(String(100))
    source_row = Column(Integer)
    loaded_at = Column(DateTime, default=datetime.utcnow)
    raw_data = Column(JSONB)


class DimProductHierarchy(Base):
    """Dimension: Product Master Data with PH Levels (Brand/Grade Categorization)"""
    __tablename__ = "dim_product_hierarchy"
    
    material_code = Column(String(50), primary_key=True)  # Cleaned (no leading zeros)
    material_description = Column(Text)
    
    # Product Hierarchy Levels
    ph_level_1 = Column(String(100), index=True)  # Industry (e.g., Decorative)
    ph_level_2 = Column(String(100), index=True)  # Product Line (e.g., Water based)
    ph_level_3 = Column(String(100), index=True)  # Brand/Grade (e.g., Premium, Economy)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FactProductionPerformanceV2(Base):
    """Fact: Production Performance V2/V3 - Variance Analysis with Historical Tracking"""
    __tablename__ = "fact_production_performance_v2"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Identifiers
    process_order_id = Column(String(50), nullable=False)
    batch_id = Column(String(50))
    material_code = Column(String(50))
    material_description = Column(String(200))
    parent_order_id = Column(String(50))  # Link to Order SFG Liquid
    
    # Hierarchy (for filtering)
    mrp_controller = Column(String(50))
    product_group_1 = Column(String(100))
    product_group_2 = Column(String(100))
    
    # Metrics - Production
    output_actual_kg = Column(Numeric(15, 3))  # Tonase Alkana(0201)
    input_actual_kg = Column(Numeric(15, 3))   # GI SFG Liquid to Order
    process_order_qty = Column(Numeric(15, 3))
    
    # Metrics - Loss
    loss_kg = Column(Numeric(15, 3))           # Lossess FG Result (Kg)
    loss_pct = Column(Numeric(10, 4))          # Lossess FG Result (%)
    
    # Quality - SG
    sg_theoretical = Column(Numeric(10, 4))
    sg_actual = Column(Numeric(10, 4))
    
    # Variance
    variant_prod_sfg_pct = Column(Numeric(10, 4))
    variant_fg_pct = Column(Numeric(10, 4))
    
    # Date (for filtering) - V3: reference_date is the reporting period (1st of month)
    posting_date = Column(Date, index=True)
    reference_date = Column(Date, index=True, default=date.today)  # V3: Reporting period
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # V3: Track updates
    
    # Unique constraint for upsert (ADR decision - V3)
    __table_args__ = (
        UniqueConstraint('process_order_id', 'batch_id', name='uq_prod_yield_v3'),
        Index('idx_fact_perf_v2_material', 'material_code'),
        Index('idx_fact_perf_v2_parent', 'parent_order_id'),
        Index('idx_fact_perf_v2_loss', 'loss_kg'),
        Index('idx_yield_ref_date', 'reference_date'),
        {'sqlite_autoincrement': True},
    )

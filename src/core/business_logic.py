"""
Business Logic - Order Classification, Status Detection, Lead-time

Implements core business rules:
- MTO Dual Logic: Sales Order NOT NULL AND MRP Controller = P01
- Order Status: CANCELLED, WIP, COMPLETED, IN_TRANSIT
- PO Filter: Only PO starting with '44' for sales orders
"""
import pandas as pd
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.config import MTO_MRP_CONTROLLER, PLANT_ROLES
from src.core.netting import StackNettingEngine


@dataclass
class LeadTimeResult:
    """Lead-time calculation result"""
    batch: str
    order: str
    order_type: str  # MTO or MTS
    
    # Time components (days)
    preparation_time: Optional[int]  # PO Date → Release Date (MTO only)
    production_time: Optional[int]   # Release Date → Actual Finish
    transit_time: Optional[int]      # Actual Finish → Receipt (MVT 101)
    storage_time: Optional[int]      # Receipt → Issue (MVT 601)
    delivery_time: Optional[int]     # Issue → Actual GI Date (MTO only)
    total_time: Optional[int]
    
    # Key dates
    po_date: Optional[datetime]
    release_date: Optional[datetime]
    finish_date: Optional[datetime]
    receipt_date: Optional[datetime]
    issue_date: Optional[datetime]
    gi_date: Optional[datetime]
    
    # Status
    status: str
    is_valid: bool
    error_message: Optional[str]


class OrderClassifier:
    """
    Order Classification and Status Detection
    
    MTO Dual Logic:
    - Rule 1: Sales Order NOT NULL (có đơn hàng)
    - Rule 2: MRP Controller = P01 (Packaged FG)
    
    Only P01 + SO represents true customer order fulfillment
    """
    
    @staticmethod
    def is_mto(row: pd.Series) -> bool:
        """
        Check if order is Make-to-Order (MTO)
        
        DUAL LOGIC:
        1. Sales Order NOT NULL
        2. MRP Controller = P01
        
        Why dual logic:
        - P02/P03 may have SO but are intermediates
        - P01 without SO is MTS
        """
        # Check Sales Order
        sales_order = row.get('sales_order') or row.get('Sales Order')
        has_sales_order = (
            pd.notna(sales_order) and 
            str(sales_order).strip() != '' and
            str(sales_order).lower() not in ('nan', 'none', 'null')
        )
        
        # Check MRP Controller
        mrp = row.get('mrp_controller') or row.get('MRP controller')
        is_p01 = str(mrp).strip().upper() == MTO_MRP_CONTROLLER
        
        return has_sales_order and is_p01
    
    @staticmethod
    def get_order_status(row: pd.Series) -> str:
        """
        Determine production order status
        
        Logic:
        - CANCELLED: Finish date có nhưng Delivered Qty = 0
        - WIP: No finish date, Delivered Qty = 0
        - COMPLETED: Finish date có và Delivered Qty > 0
        - IN_TRANSIT: No finish date but Delivered Qty > 0 (đang giao)
        """
        finish_date = row.get('actual_finish_date') or row.get('Actual finish date')
        delivered_qty = row.get('delivered_quantity') or row.get('Delivered quantity (GMEIN)') or 0
        
        has_finish_date = pd.notna(finish_date)
        
        try:
            delivered_qty = float(delivered_qty) if pd.notna(delivered_qty) else 0
        except:
            delivered_qty = 0
        
        if has_finish_date and delivered_qty == 0:
            return 'CANCELLED'
        elif not has_finish_date and delivered_qty == 0:
            return 'WIP'
        elif has_finish_date and delivered_qty > 0:
            return 'COMPLETED'
        else:
            return 'IN_TRANSIT'
    
    @staticmethod
    def is_sales_po(po_number: str) -> bool:
        """
        Check if Purchase Order is a sales PO (starts with '44')
        
        CRITICAL RULE: Only PO starting with '44' is for sales
        Other POs are for:
        - Material purchase
        - Internal transfer
        - Subcontracting
        """
        if pd.isna(po_number):
            return False
        
        po_str = str(po_number).strip()
        return po_str.startswith('44')
    
    @staticmethod
    def get_plant_role(plant_code: int) -> str:
        """Get plant role: FACTORY, DC, or OTHER"""
        return PLANT_ROLES.get(plant_code, 'UNKNOWN')
    
    @staticmethod
    def get_semester(date: datetime) -> Optional[Dict]:
        """
        Map date to semester
        
        Semester 1: January 1 - June 30
        Semester 2: July 1 - December 31
        """
        if pd.isna(date):
            return None
        
        try:
            if isinstance(date, str):
                date = pd.to_datetime(date)
            
            month = date.month
            year = date.year
            semester = 1 if month <= 6 else 2
            
            return {
                'year': year,
                'semester': semester,
                'period_start': datetime(year, 1 if semester == 1 else 7, 1),
                'period_end': datetime(year, 6, 30) if semester == 1 else datetime(year, 12, 31)
            }
        except:
            return None


class LeadTimeCalculator:
    """
    Lead-time Calculator
    
    MTS Lead-time (Make-to-Stock):
    - Production Time: Release → Finish
    - Transit Time: Finish → Receipt (MVT 101)
    - Storage Time: Receipt → Issue (MVT 601)
    
    MTO Lead-time (Make-to-Order):
    - Preparation Time: PO Date → Release (only for sales PO '44')
    - Production Time: Release → Finish
    - Transit Time: Finish → Receipt
    - Storage Time: Receipt → Issue
    - Delivery Time: Issue → Actual GI Date
    """
    
    def __init__(
        self, 
        cooispi_df: pd.DataFrame,
        mb51_df: pd.DataFrame,
        zrmm024_df: Optional[pd.DataFrame] = None,
        zrsd004_df: Optional[pd.DataFrame] = None
    ):
        self.orders = cooispi_df
        self.netting_engine = StackNettingEngine(mb51_df)
        self.movements = mb51_df
        self.po_data = zrmm024_df
        self.delivery_data = zrsd004_df
        
        self.classifier = OrderClassifier()
    
    def _safe_days(self, date1: Optional[datetime], date2: Optional[datetime]) -> Optional[int]:
        """Calculate days between two dates, handling None"""
        if date1 is None or date2 is None:
            return None
        try:
            if isinstance(date1, str):
                date1 = pd.to_datetime(date1)
            if isinstance(date2, str):
                date2 = pd.to_datetime(date2)
            return (date2 - date1).days
        except:
            return None
    
    def _find_po_date(self, batch: str, plant: int) -> Optional[datetime]:
        """
        Find PO Date from MB51 → ZRMM024
        
        CRITICAL: Only consider PO starting with '44' (sales orders)
        """
        if self.po_data is None:
            return None
        
        # Find MVT 101 with PO starting with '44'
        mvt_101 = self.movements[
            (self.movements.get('col_6_batch', '') == batch) &
            (self.movements.get('col_1_mvt_type', 0) == 101)
        ]
        
        for _, row in mvt_101.iterrows():
            po_number = row.get('col_15_purchase_order')
            if self.classifier.is_sales_po(po_number):
                # Find in ZRMM024
                po_info = self.po_data[
                    self.po_data.get('purch_order', '') == po_number
                ]
                if not po_info.empty:
                    return pd.to_datetime(po_info.iloc[0].get('purch_date'))
        
        return None
    
    def _find_gi_date(self, batch: str, delivery_ref: str) -> Optional[datetime]:
        """Find Actual GI Date from ZRSD004"""
        if self.delivery_data is None:
            return None
        
        if pd.isna(delivery_ref):
            return None
        
        delivery = self.delivery_data[
            self.delivery_data.get('delivery', '') == str(delivery_ref)
        ]
        
        if not delivery.empty:
            return pd.to_datetime(delivery.iloc[0].get('actual_gi_date'))
        
        return None
    
    def calculate_mts_leadtime(self, order_row: pd.Series) -> LeadTimeResult:
        """
        Calculate lead-time for MTS (Make-to-Stock) order
        
        Components:
        1. Production Time: Release → Finish
        2. Transit Time: Finish → Receipt (MVT 101)
        3. Storage Time: Receipt → Issue (MVT 601)
        """
        batch = order_row.get('batch') or order_row.get('Batch')
        plant = int(order_row.get('plant') or order_row.get('Plant') or 0)
        order = order_row.get('order') or order_row.get('Order')
        
        release_date = pd.to_datetime(order_row.get('release_date_actual') or order_row.get('Release date (actual)'))
        finish_date = pd.to_datetime(order_row.get('actual_finish_date') or order_row.get('Actual finish date'))
        
        # 1. Production Time
        production_time = self._safe_days(release_date, finish_date)
        
        # 2. Receipt Date (MVT 101 after netting)
        receipt_date = self.netting_engine.get_valid_receipt_date(batch, plant)
        transit_time = self._safe_days(finish_date, receipt_date)
        
        # 3. Issue Date (MVT 601 after netting)
        issue_date = self.netting_engine.get_valid_issue_date(batch, plant)
        storage_time = self._safe_days(receipt_date, issue_date)
        
        # Total
        times = [t for t in [production_time, transit_time, storage_time] if t is not None]
        total_time = sum(times) if times else None
        
        return LeadTimeResult(
            batch=batch,
            order=order,
            order_type='MTS',
            preparation_time=None,  # N/A for MTS
            production_time=production_time,
            transit_time=transit_time,
            storage_time=storage_time,
            delivery_time=None,  # N/A for MTS
            total_time=total_time,
            po_date=None,
            release_date=release_date,
            finish_date=finish_date,
            receipt_date=receipt_date,
            issue_date=issue_date,
            gi_date=None,
            status=self.classifier.get_order_status(order_row),
            is_valid=total_time is not None,
            error_message=None
        )
    
    def calculate_mto_leadtime(self, order_row: pd.Series) -> LeadTimeResult:
        """
        Calculate lead-time for MTO (Make-to-Order) order
        
        Components:
        1. Preparation Time: PO Date → Release (PO starts with '44')
        2. Production Time: Release → Finish
        3. Transit Time: Finish → Receipt (MVT 101)
        4. Storage Time: Receipt → Issue (MVT 601)
        5. Delivery Time: Issue → Actual GI Date
        """
        batch = order_row.get('batch') or order_row.get('Batch')
        plant = int(order_row.get('plant') or order_row.get('Plant') or 0)
        order = order_row.get('order') or order_row.get('Order')
        
        release_date = pd.to_datetime(order_row.get('release_date_actual') or order_row.get('Release date (actual)'))
        finish_date = pd.to_datetime(order_row.get('actual_finish_date') or order_row.get('Actual finish date'))
        
        # 1. PO Date (only for PO '44')
        po_date = self._find_po_date(batch, plant)
        preparation_time = self._safe_days(po_date, release_date)
        
        # 2. Production Time
        production_time = self._safe_days(release_date, finish_date)
        
        # 3. Receipt Date
        receipt_date = self.netting_engine.get_valid_receipt_date(batch, plant)
        transit_time = self._safe_days(finish_date, receipt_date)
        
        # 4. Issue Date
        issue_date = self.netting_engine.get_valid_issue_date(batch, plant)
        storage_time = self._safe_days(receipt_date, issue_date)
        
        # 5. Delivery Time (from MVT 601 reference to ZRSD004)
        delivery_ref = None
        mvt_601 = self.movements[
            (self.movements.get('col_6_batch', '') == batch) &
            (self.movements.get('col_1_mvt_type', 0) == 601)
        ]
        if not mvt_601.empty:
            delivery_ref = mvt_601.iloc[0].get('col_12_reference')
        
        gi_date = self._find_gi_date(batch, delivery_ref)
        delivery_time = self._safe_days(issue_date, gi_date)
        
        # Total
        times = [t for t in [preparation_time, production_time, transit_time, storage_time, delivery_time] if t is not None]
        total_time = sum(times) if times else None
        
        return LeadTimeResult(
            batch=batch,
            order=order,
            order_type='MTO',
            preparation_time=preparation_time,
            production_time=production_time,
            transit_time=transit_time,
            storage_time=storage_time,
            delivery_time=delivery_time,
            total_time=total_time,
            po_date=po_date,
            release_date=release_date,
            finish_date=finish_date,
            receipt_date=receipt_date,
            issue_date=issue_date,
            gi_date=gi_date,
            status=self.classifier.get_order_status(order_row),
            is_valid=total_time is not None,
            error_message=None
        )
    
    def calculate_leadtime(self, order_row: pd.Series) -> LeadTimeResult:
        """
        Calculate lead-time for an order (auto-detect MTO/MTS)
        """
        if self.classifier.is_mto(order_row):
            return self.calculate_mto_leadtime(order_row)
        else:
            return self.calculate_mts_leadtime(order_row)
    
    def calculate_all_leadtimes(self) -> pd.DataFrame:
        """Calculate lead-times for all orders"""
        results = []
        
        for _, row in self.orders.iterrows():
            result = self.calculate_leadtime(row)
            results.append({
                'batch': result.batch,
                'order': result.order,
                'order_type': result.order_type,
                'status': result.status,
                'preparation_time': result.preparation_time,
                'production_time': result.production_time,
                'transit_time': result.transit_time,
                'storage_time': result.storage_time,
                'delivery_time': result.delivery_time,
                'total_time': result.total_time,
                'po_date': result.po_date,
                'release_date': result.release_date,
                'finish_date': result.finish_date,
                'receipt_date': result.receipt_date,
                'issue_date': result.issue_date,
                'gi_date': result.gi_date,
                'is_valid': result.is_valid
            })
        
        return pd.DataFrame(results)

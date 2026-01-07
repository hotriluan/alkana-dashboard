"""
Lead-time Calculation Engine

Implements IMPLEMENTATION_PLAN.md Section 11 logic for MTO/MTS lead-time tracking.

MTS Lead-time (3 stages):
1. Production Time: Release → Finish
2. Transit Time: Finish → Receipt (MVT 101)
3. Storage Time: Receipt → Issue (MVT 601 with stack netting)

MTO Lead-time (5 stages):
1. Preparation Time: PO Date → Release
2. Production Time: Release → Finish
3. Transit Time: Finish → Receipt (MVT 101)
4. Storage Time: Receipt → Issue (MVT 601)
5. Delivery Time: Issue → Actual GI Date (from ZRSD004)

Reference: NEXT_STEPS.md Phase 6.1.2
"""
from datetime import datetime, timedelta
from typing import Dict, Optional
import pandas as pd


class LeadTimeCalculator:
    """Calculate lead-time components for MTO and MTS orders"""
    
    def __init__(self, mb51_df: pd.DataFrame, zrmm024_df: pd.DataFrame, zrsd004_df: pd.DataFrame):
        """
        Initialize calculator with required data sources
        
        Args:
            mb51_df: Material movements (fact_inventory)
            zrmm024_df: Purchase orders (fact_purchase_order)
            zrsd004_df: Delivery documents (fact_delivery)
        """
        self.mb51_df = mb51_df
        self.zrmm024_df = zrmm024_df
        self.zrsd004_df = zrsd004_df
    
    def calculate_mts_leadtime(self, production_order: Dict) -> Dict[str, Optional[int]]:
        """
        Calculate lead-time for Make-to-Stock orders (3 components)
        
        Args:
            production_order: Dict with keys: batch, plant_code, release_date, actual_finish_date
        
        Returns:
            Dict with lead-time components and status
        """
        batch = production_order.get('batch')
        plant = production_order.get('plant_code')
        release_date = production_order.get('release_date')
        finish_date = production_order.get('actual_finish_date')
        
        if not finish_date or not release_date:
            return self._empty_result()
        
        # 1. Production Time (always available)
        production_time = (finish_date - release_date).days if isinstance(finish_date, datetime) and isinstance(release_date, datetime) else None
        
        # 2. Transit Time (Finish → Receipt at warehouse)
        mvt_101 = self.mb51_df[
            (self.mb51_df['batch'] == batch) &
            (self.mb51_df['plant_code'] == plant) &
            (self.mb51_df['mvt_type'] == 101)
        ]
        
        transit_time = None
        receipt_date = None
        if not mvt_101.empty:
            receipt_date = mvt_101['posting_date'].min()
            if isinstance(receipt_date, datetime) and isinstance(finish_date, datetime):
                transit_time = (receipt_date - finish_date).days
        
        # 3. Storage Time (Receipt → Valid Issue after netting)
        storage_time = None
        if receipt_date:
            issue_date = self._get_valid_issue_date(batch, plant)
            if issue_date and isinstance(issue_date, datetime) and isinstance(receipt_date, datetime):
                storage_time = (issue_date - receipt_date).days
        
        total_time = sum(filter(None, [production_time, transit_time, storage_time]))
        
        return {
            'prep_time_days': None,  # MTS has no preparation
            'production_time_days': production_time,
            'transit_time_days': transit_time,
            'storage_time_days': storage_time,
            'delivery_time_days': None,  # MTS tracks only to issue, not delivery
            'total_leadtime_days': total_time if total_time > 0 else None,
            'leadtime_status': self._get_status(total_time, target_days=14)
        }
    
    def calculate_mto_leadtime(self, production_order: Dict) -> Dict[str, Optional[int]]:
        """
        Calculate lead-time for Make-to-Order orders (5 components)
        
        Args:
            production_order: Dict with keys: batch, plant_code, release_date, actual_finish_date
        
        Returns:
            Dict with lead-time components and status
        """
        batch = production_order.get('batch')
        plant = production_order.get('plant_code')
        release_date = production_order.get('release_date')
        finish_date = production_order.get('actual_finish_date')
        
        if not finish_date or not release_date:
            return self._empty_result()
        
        # 1. Find Purchase Order from MB51 (MVT 101 with PO starting '44')
        mvt_101_po = self.mb51_df[
            (self.mb51_df['batch'] == batch) &
            (self.mb51_df['mvt_type'] == 101) &
            (self.mb51_df['purchase_order'].astype(str).str.startswith('44', na=False))
        ]
        
        if mvt_101_po.empty:
            # Cannot trace PO, fallback to MTS logic
            return self.calculate_mts_leadtime(production_order)
        
        po_number = mvt_101_po['purchase_order'].iloc[0]
        
        # 2. Get PO Date from ZRMM024
        po_info = self.zrmm024_df[self.zrmm024_df['purch_order'] == po_number]
        
        if po_info.empty:
            return self.calculate_mts_leadtime(production_order)
        
        po_date = po_info['purch_date'].iloc[0]
        
        # 3. Preparation Time (PO → Release)
        prep_time = None
        if po_date and isinstance(po_date, datetime) and isinstance(release_date, datetime):
            prep_time = (release_date - po_date).days
        
        # 4. Production Time (Release → Finish)
        production_time = None
        if isinstance(finish_date, datetime) and isinstance(release_date, datetime):
            production_time = (finish_date - release_date).days
        
        # 5. Transit Time (Finish → Receipt)
        receipt_date = mvt_101_po['posting_date'].min()
        transit_time = None
        if isinstance(receipt_date, datetime) and isinstance(finish_date, datetime):
            transit_time = (receipt_date - finish_date).days
        
        # 6. Storage Time (Receipt → Valid Issue after netting)
        storage_time = None
        issue_date = self._get_valid_issue_date(batch, plant)
        if issue_date and receipt_date and isinstance(issue_date, datetime) and isinstance(receipt_date, datetime):
            storage_time = (issue_date - receipt_date).days
        
        # 7. Delivery Time (Issue → Actual GI)
        delivery_time = None
        if issue_date:
            # Find delivery reference from MB51
            mvt_601 = self.mb51_df[
                (self.mb51_df['batch'] == batch) &
                (self.mb51_df['mvt_type'] == 601)
            ]
            
            if not mvt_601.empty:
                delivery_ref = mvt_601['reference'].iloc[0] if 'reference' in mvt_601.columns else None
                if delivery_ref:
                    delivery = self.zrsd004_df[
                        self.zrsd004_df['delivery'] == delivery_ref
                    ]
                    if not delivery.empty:
                        gi_date = delivery['actual_gi_date'].iloc[0]
                        if isinstance(gi_date, datetime) and isinstance(issue_date, datetime):
                            delivery_time = (gi_date - issue_date).days
        
        total_time = sum(filter(None, [
            prep_time, production_time, transit_time, 
            storage_time, delivery_time
        ]))
        
        return {
            'prep_time_days': prep_time,
            'production_time_days': production_time,
            'transit_time_days': transit_time,
            'storage_time_days': storage_time,
            'delivery_time_days': delivery_time,
            'total_leadtime_days': total_time if total_time > 0 else None,
            'leadtime_status': self._get_status(total_time, target_days=21)  # MTO has longer target
        }
    
    def _get_valid_issue_date(self, batch: str, plant: int) -> Optional[datetime]:
        """
        Get first valid MVT 601 date after stack netting
        
        TODO: Integrate with StackNettingEngine for accurate netting
        For now, return first 601 date
        """
        mvt_601 = self.mb51_df[
            (self.mb51_df['batch'] == batch) &
            (self.mb51_df['plant_code'] == plant) &
            (self.mb51_df['mvt_type'] == 601)
        ]
        return mvt_601['posting_date'].min() if not mvt_601.empty else None
    
    def _get_status(self, total_days: Optional[int], target_days: int) -> str:
        """
        Determine lead-time status based on target
        
        Args:
            total_days: Total lead-time in days
            target_days: Target lead-time (14 for MTS, 21 for MTO)
        
        Returns:
            Status: ON_TIME, DELAYED, CRITICAL, or UNKNOWN
        """
        if total_days is None or total_days == 0:
            return 'UNKNOWN'
        if total_days <= target_days:
            return 'ON_TIME'
        elif total_days <= target_days * 1.2:  # 20% tolerance
            return 'DELAYED'
        else:
            return 'CRITICAL'
    
    def _empty_result(self) -> Dict[str, Optional[int]]:
        """Return empty result structure"""
        return {
            'prep_time_days': None,
            'production_time_days': None,
            'transit_time_days': None,
            'storage_time_days': None,
            'delivery_time_days': None,
            'total_leadtime_days': None,
            'leadtime_status': 'UNKNOWN'
        }

"""
Stack-based MVT Netting Engine (LIFO)

Implements "Cặp Đôi Bù Trừ" principle using Stack (LIFO) algorithm
- SAP reversals cancel the MOST RECENT transaction
- 601 (GI for Delivery) ↔ 602 (Reversal)
"""
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass

from src.config import MVT_REVERSAL_PAIRS, STOCK_IMPACT


@dataclass
class NettingResult:
    """Result of netting operation for a batch"""
    batch: str
    plant: int
    material: str
    forward_mvt: int
    reverse_mvt: int
    
    # Original counts
    total_forward: int
    total_reverse: int
    
    # After netting
    remaining_forward: int
    netted_count: int
    
    # Valid transactions after netting
    remaining_transactions: pd.DataFrame
    last_valid_date: Optional[datetime]
    net_quantity: float
    
    # Status
    is_fully_reversed: bool


class StackNettingEngine:
    """
    Stack-based (LIFO) Netting Engine
    
    Algorithm:
    1. Sort transactions by Posting Date ASC
    2. Process chronologically:
       - Forward MVT → PUSH to stack
       - Reverse MVT → POP from stack (cancel most recent)
    3. Return remaining items in stack
    """
    
    def __init__(self, mb51_df: pd.DataFrame):
        """
        Initialize with MB51 dataframe
        
        Expected columns (index-based from raw_mb51):
        - col_0_posting_date: datetime
        - col_1_mvt_type: int
        - col_2_plant: int
        - col_6_batch: str
        - col_4_material: str
        - col_7_qty: float
        """
        self.mb51_df = mb51_df.copy()
        
        # Standardize column names for easier processing
        self.df = self.mb51_df.rename(columns={
            'col_0_posting_date': 'posting_date',
            'col_1_mvt_type': 'mvt_type',
            'col_2_plant': 'plant',
            'col_6_batch': 'batch',
            'col_4_material': 'material',
            'col_7_qty': 'qty',
            'col_11_material_doc': 'material_doc',
            'col_12_reference': 'reference',
            'col_15_purchase_order': 'purchase_order',
        })
        
        # Convert types
        self.df['posting_date'] = pd.to_datetime(self.df['posting_date'], errors='coerce')
        self.df['mvt_type'] = pd.to_numeric(self.df['mvt_type'], errors='coerce').astype('Int64')
        self.df['plant'] = pd.to_numeric(self.df['plant'], errors='coerce').astype('Int64')
        self.df['qty'] = pd.to_numeric(self.df['qty'], errors='coerce')
    
    def apply_stack_netting(
        self, 
        batch: str, 
        plant: int, 
        mvt_forward: int = 601, 
        mvt_reverse: int = 602
    ) -> NettingResult:
        """
        Apply Stack (LIFO) netting for a specific batch and plant
        
        Example:
        Date       MVT   Action           Stack
        Jan 1      601   PUSH             [txn1]
        Jan 2      601   PUSH             [txn1, txn2]
        Jan 3      602   POP (cancel txn2) [txn1]
        Result: txn1 remains (valid delivery)
        
        CRITICAL: Filter by Plant BEFORE netting
        - Plant 1201 (Factory) and Plant 1401 (DC) have separate inventories
        - NEVER mix cross-plant transactions
        """
        # Filter by batch AND plant
        mask = (
            (self.df['batch'] == batch) & 
            (self.df['plant'] == plant) &
            (self.df['mvt_type'].isin([mvt_forward, mvt_reverse]))
        )
        filtered_df = self.df[mask].copy()
        
        if filtered_df.empty:
            return NettingResult(
                batch=batch,
                plant=plant,
                material='',
                forward_mvt=mvt_forward,
                reverse_mvt=mvt_reverse,
                total_forward=0,
                total_reverse=0,
                remaining_forward=0,
                netted_count=0,
                remaining_transactions=pd.DataFrame(),
                last_valid_date=None,
                net_quantity=0,
                is_fully_reversed=True
            )
        
        # Get material from first row
        material = filtered_df['material'].iloc[0] if not filtered_df.empty else ''
        
        # Count original transactions
        total_forward = len(filtered_df[filtered_df['mvt_type'] == mvt_forward])
        total_reverse = len(filtered_df[filtered_df['mvt_type'] == mvt_reverse])
        
        # Sort chronologically
        filtered_df = filtered_df.sort_values('posting_date')
        
        # Stack for LIFO processing
        stack: List[pd.Series] = []
        
        for idx, row in filtered_df.iterrows():
            if row['mvt_type'] == mvt_forward:
                # Forward movement: push to stack
                stack.append(row)
            elif row['mvt_type'] == mvt_reverse:
                # Reverse movement: pop from stack (cancel most recent)
                if stack:
                    stack.pop()  # LIFO: remove last item
        
        # Convert remaining stack to DataFrame
        if stack:
            remaining_df = pd.DataFrame(stack)
            last_valid_date = remaining_df['posting_date'].max()
            net_quantity = abs(remaining_df['qty'].sum())
            is_fully_reversed = False
        else:
            remaining_df = pd.DataFrame()
            last_valid_date = None
            net_quantity = 0
            is_fully_reversed = True
        
        return NettingResult(
            batch=batch,
            plant=plant,
            material=material,
            forward_mvt=mvt_forward,
            reverse_mvt=mvt_reverse,
            total_forward=total_forward,
            total_reverse=total_reverse,
            remaining_forward=len(stack),
            netted_count=min(total_forward, total_reverse),
            remaining_transactions=remaining_df,
            last_valid_date=last_valid_date,
            net_quantity=net_quantity,
            is_fully_reversed=is_fully_reversed
        )
    
    def get_valid_issue_date(self, batch: str, plant: int) -> Optional[datetime]:
        """
        Get the LAST valid issue date after netting MVT 601/602
        
        Returns: Latest Posting Date of remaining MVT 601
        Returns None if fully reversed
        """
        result = self.apply_stack_netting(batch, plant, 601, 602)
        return result.last_valid_date
    
    def get_valid_receipt_date(self, batch: str, plant: int) -> Optional[datetime]:
        """
        Get the FIRST valid receipt date after netting MVT 101/102
        
        Returns: Earliest Posting Date of remaining MVT 101
        """
        result = self.apply_stack_netting(batch, plant, 101, 102)
        if result.remaining_transactions.empty:
            return None
        return result.remaining_transactions['posting_date'].min()
    
    def calculate_net_quantity(
        self, 
        batch: str, 
        plant: int, 
        mvt_forward: int = 601, 
        mvt_reverse: int = 602
    ) -> float:
        """
        Calculate net quantity after netting
        
        Formula: Sum(forward qty) - Sum(reverse qty)
        """
        result = self.apply_stack_netting(batch, plant, mvt_forward, mvt_reverse)
        return result.net_quantity
    
    def get_delivery_status(self, batch: str, plant: int) -> str:
        """
        Determine delivery status from netting result
        
        Returns:
        - FULLY_REVERSED: All deliveries cancelled
        - PARTIALLY_REVERSED: Some deliveries cancelled
        - DELIVERED: No reversals
        """
        result = self.apply_stack_netting(batch, plant, 601, 602)
        
        if result.is_fully_reversed:
            return 'FULLY_REVERSED'
        elif result.netted_count > 0:
            return 'PARTIALLY_REVERSED'
        else:
            return 'DELIVERED'
    
    def get_valid_issue_date(
        self,
        batch: str,
        plant: int,
        mvt_forward: int = 601,
        mvt_reverse: int = 602
    ) -> Optional[datetime]:
        """
        Get the last valid issue date after netting (601)
        
        Returns the most recent posting date for valid 601 movements
        """
        result = self.apply_stack_netting(batch, plant, mvt_forward, mvt_reverse)
        if result.remaining_transactions.empty:
            return None
        return result.last_valid_date
    
    def get_all_batches(self, plant: Optional[int] = None) -> List[str]:
        """Get all unique batches, optionally filtered by plant"""
        if plant:
            return self.df[self.df['plant'] == plant]['batch'].dropna().unique().tolist()
        return self.df['batch'].dropna().unique().tolist()
    
    def apply_netting_all_batches(
        self, 
        plant: Optional[int] = None,
        mvt_forward: int = 601,
        mvt_reverse: int = 602
    ) -> pd.DataFrame:
        """
        Apply netting to all batches and return summary DataFrame
        
        Returns DataFrame with columns:
        - batch, plant, material
        - total_forward, total_reverse, remaining, netted
        - last_valid_date, net_quantity, is_fully_reversed
        """
        results = []
        
        # Get unique batch-plant combinations
        if plant:
            combinations = self.df[self.df['plant'] == plant][['batch', 'plant']].drop_duplicates()
        else:
            combinations = self.df[['batch', 'plant']].drop_duplicates()
        
        for _, row in combinations.iterrows():
            batch = row['batch']
            plant_code = row['plant']
            
            if pd.isna(batch) or pd.isna(plant_code):
                continue
            
            result = self.apply_stack_netting(batch, int(plant_code), mvt_forward, mvt_reverse)
            
            results.append({
                'batch': result.batch,
                'plant': result.plant,
                'material': result.material,
                'total_forward': result.total_forward,
                'total_reverse': result.total_reverse,
                'remaining': result.remaining_forward,
                'netted_count': result.netted_count,
                'last_valid_date': result.last_valid_date,
                'net_quantity': result.net_quantity,
                'is_fully_reversed': result.is_fully_reversed,
                'status': 'FULLY_REVERSED' if result.is_fully_reversed else 'ACTIVE'
            })
        
        return pd.DataFrame(results)


def get_stock_impact(mvt_type: int) -> int:
    """Get stock impact for MVT type: +1 (increase), -1 (decrease), 0 (transfer)"""
    return STOCK_IMPACT.get(mvt_type, 0)


def get_reversal_pair(mvt_type: int) -> Optional[int]:
    """Get reversal MVT for given MVT type"""
    return MVT_REVERSAL_PAIRS.get(mvt_type)

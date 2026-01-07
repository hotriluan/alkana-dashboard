"""
P02→P01 Yield Tracking Module

Tracks material loss/yield from P02 (liquid) to P01 (packaged) production.

Algorithm:
1. Sequential Batch Pattern: P01 batch = P02 batch - 1 (digits 7-8)
2. Material Name Validation: P01 name = P02 name + suffix (e.g., -18KP)
3. Yield Calculation: (P01 output KG / P02 input KG) × 100

Coverage: ~31% of P02 batches (406 valid pairs from 1,304 P02 batches)
"""
import pandas as pd
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class P02P01YieldData:
    """P02→P01 yield calculation result"""
    p02_batch: str
    p01_batch: str
    p02_material_code: str
    p02_material_desc: str
    p01_material_code: str
    p01_material_desc: str
    p02_consumed_kg: float
    p01_produced_kg: float
    yield_pct: float
    loss_kg: float
    production_date: datetime


def get_p01_batch_from_p02(p02_batch: str) -> Optional[str]:
    """
    Convert P02 batch to P01 batch using sequential pattern
    
    Algorithm:
    - Extract prefix (chars 0-5): '25L247'
    - Extract two digits (chars 6-7): '63'
    - Extract suffix (chars 8+): '10'
    - Decrement two digits: 63 → 62
    - Reconstruct: '25L2476210'
    
    Args:
        p02_batch: P02 batch number (e.g., '25L2476310')
    
    Returns:
        P01 batch number (e.g., '25L2476210') or None if invalid
    
    Example:
        >>> get_p01_batch_from_p02('25L2476310')
        '25L2476210'
    """
    if not p02_batch or len(p02_batch) < 10:
        return None
    
    try:
        prefix = p02_batch[:6]
        two_digits = int(p02_batch[6:8])
        suffix = p02_batch[8:]
        
        # Decrement
        p01_two_digits = two_digits - 1
        
        # Reconstruct
        p01_batch = f"{prefix}{p01_two_digits:02d}{suffix}"
        
        return p01_batch
    except (ValueError, IndexError):
        return None


def validate_material_names(p02_material: str, p01_material: str) -> bool:
    """
    Validate that P01 material name = P02 material name + suffix
    
    Rules:
    1. P01 must start with P02 name
    2. P01 must have suffix starting with hyphen
    3. Suffix typically contains packaging info (e.g., -18KP, -4L)
    
    Args:
        p02_material: P02 material description
        p01_material: P01 material description
    
    Returns:
        True if valid match, False otherwise
    
    Examples:
        >>> validate_material_names(
        ...     "PFT-215 LIGHT GREY VN",
        ...     "PFT-215 LIGHT GREY VN-18KP"
        ... )
        True
        
        >>> validate_material_names(
        ...     "PCL-31300 BLUE OG PASTE AF VN",
        ...     "PCL-31300 BLUE OR 50 PASTE VN-4K"
        ... )
        False  # OG vs OR - different products
    """
    if not p02_material or not p01_material:
        return False
    
    # P01 should start with P02 name
    if not p01_material.startswith(p02_material):
        return False
    
    # P01 should have suffix after P02 name
    suffix = p01_material[len(p02_material):]
    
    # Suffix should start with hyphen and contain packaging info
    if not suffix or not suffix.startswith('-'):
        return False
    
    return True


def calculate_p02_p01_yield(
    p02_batch: str,
    mb51_df: pd.DataFrame,
    uom_converter
) -> Optional[P02P01YieldData]:
    """
    Calculate yield from P02 to P01 for a specific batch
    
    Steps:
    1. Get P01 batch using sequential pattern
    2. Validate material names match
    3. Find P02 consumption (MVT 261 @ Plant 1201)
    4. Find P01 production (MVT 101 @ Plant 1401)
    5. Convert P01 qty to KG using UOM converter
    6. Calculate yield percentage
    
    Args:
        p02_batch: P02 batch number
        mb51_df: MB51 dataframe with standardized columns
        uom_converter: UOM converter instance
    
    Returns:
        P02P01YieldData or None if invalid/not found
    """
    # Step 1: Get P01 batch
    p01_batch = get_p01_batch_from_p02(p02_batch)
    if not p01_batch:
        return None
    
    # Step 2: Find P02 Consumption (MVT 261 @ Plant 1201)
    p02_txn = mb51_df[
        (mb51_df['col_6_batch'] == p02_batch) &
        (mb51_df['col_1_mvt_type'] == 261) &
        (mb51_df['col_2_plant'] == 1201)
    ]
    
    if p02_txn.empty:
        return None
    
    p02_consumed_kg = float(abs(p02_txn['col_7_qty'].sum()))
    p02_material_code = p02_txn.iloc[0]['col_4_material']
    p02_material_desc = p02_txn.iloc[0]['col_5_material_desc']
    p02_date = p02_txn.iloc[0]['col_0_posting_date']
    
    # Step 3: Find P01 Production (MVT 101 @ Plant 1401)
    p01_txn = mb51_df[
        (mb51_df['col_6_batch'] == p01_batch) &
        (mb51_df['col_1_mvt_type'] == 101) &
        (mb51_df['col_2_plant'] == 1401)
    ]
    
    if p01_txn.empty:
        return None
    
    p01_qty = float(p01_txn['col_7_qty'].sum())
    p01_uom = p01_txn.iloc[0]['col_8_uom']
    p01_material_code = p01_txn.iloc[0]['col_4_material']
    p01_material_desc = p01_txn.iloc[0]['col_5_material_desc']
    
    # Step 4: Validate material names
    if not validate_material_names(p02_material_desc, p01_material_desc):
        return None
    
    # Safety check: p02_consumed_kg must be > 0
    if p02_consumed_kg == 0:
        return None
    
    # Step 5: Convert P01 to KG
    p01_produced_kg, _ = uom_converter.normalize_to_kg(
        p01_qty, p01_uom, p01_material_code
    )
    
    if not p01_produced_kg:
        return None
    
    # Step 6: Calculate Yield
    yield_pct = (p01_produced_kg / p02_consumed_kg) * 100
    loss_kg = p02_consumed_kg - p01_produced_kg
    
    # Sanity check: yield should be between 0-150%
    if yield_pct < 0 or yield_pct > 150:
        return None
    
    return P02P01YieldData(
        p02_batch=p02_batch,
        p01_batch=p01_batch,
        p02_material_code=p02_material_code,
        p02_material_desc=p02_material_desc,
        p01_material_code=p01_material_code,
        p01_material_desc=p01_material_desc,
        p02_consumed_kg=round(p02_consumed_kg, 3),
        p01_produced_kg=round(p01_produced_kg, 3),
        yield_pct=round(yield_pct, 2),
        loss_kg=round(loss_kg, 3),
        production_date=pd.to_datetime(p02_date)
    )


def find_all_p02_p01_pairs(mb51_df: pd.DataFrame, uom_converter) -> List[P02P01YieldData]:
    """
    Find all valid P02→P01 pairs and calculate yields
    
    Args:
        mb51_df: MB51 dataframe
        uom_converter: UOM converter instance
    
    Returns:
        List of P02P01YieldData for all valid pairs
    """
    # Get all P02 batches (MVT 261 @ Plant 1201)
    p02_batches = mb51_df[
        (mb51_df['col_1_mvt_type'] == 261) &
        (mb51_df['col_2_plant'] == 1201)
    ]['col_6_batch'].unique()
    
    results = []
    
    for p02_batch in p02_batches:
        if not p02_batch:
            continue
        
        yield_data = calculate_p02_p01_yield(p02_batch, mb51_df, uom_converter)
        
        if yield_data:
            results.append(yield_data)
    
    return results

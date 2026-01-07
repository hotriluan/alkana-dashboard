"""
UOM Conversion - PC to KG normalization

Uses billing data as source of truth for KG/PC ratio:
Formula: Sum(Net Weight) / Sum(Billing Qty) per Material
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ConversionResult:
    """UOM conversion result for a material"""
    material_code: str
    material_description: str
    kg_per_unit: float
    sample_count: int
    source: str  # 'billing' or 'delivery'
    variance_pct: Optional[float]
    is_valid: bool


class UomConverter:
    """
    UOM Converter - Normalize PC to KG
    
    MRP Controller Hierarchy:
    - P03 (Base Liquid)     → UOM: KG
    - P02 (Finished Liquid) → UOM: KG
    - P01 (Packaged FG)     → UOM: PC
    
    Conversion source: Billing data (most accurate)
    """
    
    def __init__(self):
        self.conversion_table: Dict[str, ConversionResult] = {}
    
    def build_from_billing(
        self, 
        zrsd002_df: pd.DataFrame,
        zrsd004_df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Build KG per PC conversion table from billing data
        
        Formula: Sum(Net Weight) / Sum(Billing Qty) per Material
        
        Why billing: Final invoice is most accurate source
        
        Optionally validates against delivery data (zrsd004)
        """
        # Clean billing data
        billing = zrsd002_df.copy()
        billing['billing_qty'] = pd.to_numeric(billing.get('billing_qty', 0), errors='coerce').fillna(0)
        billing['net_weight'] = pd.to_numeric(billing.get('net_weight', 0), errors='coerce').fillna(0)
        
        # Filter valid billing records
        valid_billing = billing[billing['billing_qty'] > 0].copy()
        
        if valid_billing.empty:
            print("Warning: No valid billing records found")
            return pd.DataFrame()
        
        # Aggregate by material
        billing_agg = valid_billing.groupby('material').agg({
            'net_weight': 'sum',
            'billing_qty': 'sum',
            'material_desc': 'first'
        }).reset_index()
        
        # Calculate KG per unit
        billing_agg['kg_per_unit'] = billing_agg['net_weight'] / billing_agg['billing_qty']
        billing_agg['sample_count'] = valid_billing.groupby('material').size().values
        billing_agg['source'] = 'billing'
        
        # Validate against delivery if provided
        if zrsd004_df is not None:
            delivery = zrsd004_df.copy()
            delivery['delivery_qty'] = pd.to_numeric(delivery.get('delivery_qty', 0), errors='coerce').fillna(0)
            delivery['net_weight'] = pd.to_numeric(delivery.get('net_weight', 0), errors='coerce').fillna(0)
            
            valid_delivery = delivery[delivery['delivery_qty'] > 0].copy()
            
            if not valid_delivery.empty:
                delivery_agg = valid_delivery.groupby('material').agg({
                    'net_weight': 'sum',
                    'delivery_qty': 'sum'
                }).reset_index()
                
                delivery_agg['kg_per_unit_delivery'] = (
                    delivery_agg['net_weight'] / delivery_agg['delivery_qty']
                )
                
                # Merge and calculate variance
                billing_agg = billing_agg.merge(
                    delivery_agg[['material', 'kg_per_unit_delivery']],
                    on='material',
                    how='left'
                )
                
                # Calculate variance percentage
                billing_agg['variance_pct'] = np.where(
                    billing_agg['kg_per_unit'] > 0,
                    abs(billing_agg['kg_per_unit'] - billing_agg['kg_per_unit_delivery'].fillna(0)) 
                    / billing_agg['kg_per_unit'] * 100,
                    0
                )
        else:
            billing_agg['variance_pct'] = None
        
        # Store in conversion table
        for _, row in billing_agg.iterrows():
            self.conversion_table[row['material']] = ConversionResult(
                material_code=row['material'],
                material_description=row.get('material_desc', ''),
                kg_per_unit=row['kg_per_unit'],
                sample_count=row['sample_count'],
                source='billing',
                variance_pct=row.get('variance_pct'),
                is_valid=row['kg_per_unit'] > 0
            )
        
        print(f"Built UOM conversion table: {len(self.conversion_table)} materials")
        return billing_agg
    
    def get_kg_per_unit(self, material_code: str) -> Optional[float]:
        """Get KG per unit for a material"""
        result = self.conversion_table.get(material_code)
        if result and result.is_valid:
            return result.kg_per_unit
        return None
    
    def normalize_to_kg(
        self, 
        qty: float, 
        uom: str, 
        material_code: str
    ) -> Tuple[Optional[float], str]:
        """
        Convert quantity to KG for comparison
        
        Returns: (normalized_kg, conversion_method)
        
        P01 (PC): qty × kg_per_unit
        P02 (KG): qty as-is
        P03 (KG): qty as-is
        """
        if pd.isna(qty):
            return None, 'null_qty'
        
        uom = str(uom).upper().strip() if uom else ''
        
        if uom == 'KG':
            return float(qty), 'already_kg'
        
        if uom in ('PC', 'SET', 'EA'):
            kg_per_unit = self.get_kg_per_unit(material_code)
            if kg_per_unit:
                return float(qty) * kg_per_unit, 'converted'
            else:
                return None, 'no_conversion_factor'
        
        # Unknown UOM
        return None, f'unknown_uom:{uom}'
    
    def normalize_dataframe(
        self, 
        df: pd.DataFrame, 
        qty_column: str,
        uom_column: str,
        material_column: str,
        output_column: str = 'qty_kg'
    ) -> pd.DataFrame:
        """
        Add normalized KG column to dataframe
        
        Args:
            df: Input dataframe
            qty_column: Name of quantity column
            uom_column: Name of UOM column
            material_column: Name of material column
            output_column: Name for output KG column
        
        Returns: DataFrame with new output_column
        """
        result_df = df.copy()
        
        normalized = []
        methods = []
        
        for _, row in result_df.iterrows():
            qty = row.get(qty_column)
            uom = row.get(uom_column)
            material = row.get(material_column)
            
            kg_val, method = self.normalize_to_kg(qty, uom, material)
            normalized.append(kg_val)
            methods.append(method)
        
        result_df[output_column] = normalized
        result_df[f'{output_column}_method'] = methods
        
        # Stats
        converted = sum(1 for m in methods if m == 'converted')
        already_kg = sum(1 for m in methods if m == 'already_kg')
        failed = sum(1 for m in methods if m.startswith('no_') or m.startswith('unknown'))
        
        print(f"UOM Normalization: {already_kg} already KG, {converted} converted, {failed} failed")
        
        return result_df
    
    def to_dataframe(self) -> pd.DataFrame:
        """Export conversion table as DataFrame"""
        if not self.conversion_table:
            return pd.DataFrame()
        
        records = []
        for material, result in self.conversion_table.items():
            records.append({
                'material_code': result.material_code,
                'material_description': result.material_description,
                'kg_per_unit': result.kg_per_unit,
                'sample_count': result.sample_count,
                'source': result.source,
                'variance_pct': result.variance_pct,
                'is_valid': result.is_valid
            })
        
        return pd.DataFrame(records)

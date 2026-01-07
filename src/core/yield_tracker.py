"""
Yield Tracking - Production Chain P03 → P02 → P01

Traces production chain from finished goods (P01) back to base materials (P03)
using MVT 261 (GI to Production Order) linkage.
"""
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.core.uom_converter import UomConverter


@dataclass
class ProductionStage:
    """Single production stage"""
    mrp_controller: str  # P01, P02, P03
    order: str
    batch: str
    material: str
    input_qty: float
    input_uom: str
    output_qty: float
    output_uom: str
    input_kg: Optional[float]
    output_kg: Optional[float]
    yield_pct: Optional[float]
    loss_kg: Optional[float]


@dataclass
class ProductionChain:
    """Complete production chain P03 → P02 → P01"""
    p01: Optional[ProductionStage]
    p02: Optional[ProductionStage]
    p03: Optional[ProductionStage]
    
    # Totals
    total_input_kg: Optional[float]
    total_output_kg: Optional[float]
    total_yield_pct: Optional[float]
    total_loss_kg: Optional[float]
    
    # Linkage info
    chain_complete: bool
    missing_stages: List[str]


class YieldTracker:
    """
    Yield Tracker - P03 → P02 → P01 Production Chain
    
    Production Chain Concept:
    
    Raw Materials
         │
         ▼
    ┌─────────────┐
    │  P03 Order  │  Base production (KG input → KG output)
    │  Batch: xxx │  Yield = Output_KG / Input_KG
    └──────┬──────┘
           │ MVT 261 (GI to P02 order)
           ▼
    ┌─────────────┐
    │  P02 Order  │  Liquid production (KG input → KG output)
    │  Batch: yyy │  Yield = Output_KG / Input_KG
    └──────┬──────┘
           │ MVT 261 (GI to P01 order)
           ▼
    ┌─────────────┐
    │  P01 Order  │  Packaging (KG input → PC output)
    │  Batch: zzz │  Yield = (Output_PC × KG/PC) / Input_KG
    └─────────────┘
    """
    
    def __init__(
        self, 
        cooispi_df: pd.DataFrame, 
        mb51_df: pd.DataFrame,
        uom_converter: Optional[UomConverter] = None
    ):
        """
        Initialize with production orders and material movements
        
        Args:
            cooispi_df: Production orders with MRP Controller
            mb51_df: Material movements for tracing MVT 261
            uom_converter: Optional UOM converter for KG normalization
        """
        self.orders = cooispi_df.copy()
        self.movements = mb51_df.copy()
        self.uom_converter = uom_converter or UomConverter()
        
        # Standardize column names
        self._standardize_columns()
    
    def _standardize_columns(self):
        """Standardize column names for processing"""
        # Orders - map common variations
        order_renames = {
            'Order': 'order',
            'order': 'order',
            'Batch': 'batch',
            'batch': 'batch',
            'MRP controller': 'mrp_controller',
            'mrp_controller': 'mrp_controller',
            'Material Number': 'material',
            'material_number': 'material',
            'Order quantity (GMEIN)': 'order_qty',
            'order_quantity': 'order_qty',
            'Delivered quantity (GMEIN)': 'delivered_qty',
            'delivered_quantity': 'delivered_qty',
            'Unit of measure': 'uom',
            'unit_of_measure': 'uom',
        }
        
        for old, new in order_renames.items():
            if old in self.orders.columns and new not in self.orders.columns:
                self.orders = self.orders.rename(columns={old: new})
        
        # Movements - already standardized from loader
        mvt_renames = {
            'col_1_mvt_type': 'mvt_type',
            'col_6_batch': 'batch',
            'col_4_material': 'material',
            'col_7_qty': 'qty',
            'col_12_reference': 'reference',
        }
        
        for old, new in mvt_renames.items():
            if old in self.movements.columns:
                self.movements = self.movements.rename(columns={old: new})
    
    def find_p01_orders(self) -> pd.DataFrame:
        """Find all P01 (Packaged FG) orders"""
        return self.orders[self.orders['mrp_controller'] == 'P01'].copy()
    
    def find_input_batches(self, order: str) -> List[str]:
        """
        Find batches consumed by an order via MVT 261
        
        MVT 261 = GI to Production Order
        Reference field contains the consuming order number
        """
        consumption = self.movements[
            (self.movements['mvt_type'] == 261) &
            (self.movements['reference'].astype(str).str.contains(str(order), na=False))
        ]
        
        return consumption['batch'].dropna().unique().tolist()
    
    def find_order_by_batch(self, batch: str, mrp_controller: str) -> Optional[pd.Series]:
        """Find production order by batch and MRP controller"""
        matches = self.orders[
            (self.orders['batch'] == batch) &
            (self.orders['mrp_controller'] == mrp_controller)
        ]
        
        if matches.empty:
            return None
        return matches.iloc[0]
    
    def calculate_stage_yield(
        self,
        input_qty: float,
        input_uom: str,
        output_qty: float,
        output_uom: str,
        material_code: str
    ) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
        """
        Calculate yield percentage for one production stage
        
        Returns: (input_kg, output_kg, yield_pct, loss_kg)
        
        All quantities normalized to KG for comparison
        """
        # Normalize to KG
        input_kg, _ = self.uom_converter.normalize_to_kg(input_qty, input_uom, material_code)
        output_kg, _ = self.uom_converter.normalize_to_kg(output_qty, output_uom, material_code)
        
        if input_kg is None or output_kg is None or input_kg == 0:
            return input_kg, output_kg, None, None
        
        yield_pct = (output_kg / input_kg) * 100
        loss_kg = input_kg - output_kg
        
        return input_kg, output_kg, round(yield_pct, 2), round(loss_kg, 2)
    
    def trace_production_chain(self, p01_batch: str) -> ProductionChain:
        """
        Trace complete production chain from P01 batch back to P02 and P03
        
        Algorithm:
        1. Find P01 order by batch
        2. Find materials consumed by P01 (MVT 261)
        3. Get P02 batches from consumption
        4. Find P02 orders and their consumption
        5. Get P03 batches and orders
        """
        missing_stages = []
        
        # Step 1: Find P01 order
        p01_order_row = self.find_order_by_batch(p01_batch, 'P01')
        
        if p01_order_row is None:
            return ProductionChain(
                p01=None, p02=None, p03=None,
                total_input_kg=None, total_output_kg=None,
                total_yield_pct=None, total_loss_kg=None,
                chain_complete=False, missing_stages=['P01']
            )
        
        p01_order = p01_order_row['order']
        
        # Create P01 stage
        p01_input_kg, p01_output_kg, p01_yield, p01_loss = self.calculate_stage_yield(
            input_qty=p01_order_row.get('order_qty', 0),
            input_uom='KG',  # Input to P01 is usually KG
            output_qty=p01_order_row.get('delivered_qty', 0),
            output_uom=p01_order_row.get('uom', 'PC'),
            material_code=p01_order_row.get('material', '')
        )
        
        p01_stage = ProductionStage(
            mrp_controller='P01',
            order=p01_order,
            batch=p01_batch,
            material=p01_order_row.get('material', ''),
            input_qty=p01_order_row.get('order_qty', 0),
            input_uom='KG',
            output_qty=p01_order_row.get('delivered_qty', 0),
            output_uom=p01_order_row.get('uom', 'PC'),
            input_kg=p01_input_kg,
            output_kg=p01_output_kg,
            yield_pct=p01_yield,
            loss_kg=p01_loss
        )
        
        # Step 2: Find P02 batches consumed by P01
        p02_batches = self.find_input_batches(p01_order)
        
        p02_stage = None
        p03_stage = None
        
        if p02_batches:
            # Step 3: Find first P02 order
            for p02_batch in p02_batches:
                p02_order_row = self.find_order_by_batch(p02_batch, 'P02')
                if p02_order_row is not None:
                    p02_input_kg, p02_output_kg, p02_yield, p02_loss = self.calculate_stage_yield(
                        input_qty=p02_order_row.get('order_qty', 0),
                        input_uom='KG',
                        output_qty=p02_order_row.get('delivered_qty', 0),
                        output_uom=p02_order_row.get('uom', 'KG'),
                        material_code=p02_order_row.get('material', '')
                    )
                    
                    p02_stage = ProductionStage(
                        mrp_controller='P02',
                        order=p02_order_row['order'],
                        batch=p02_batch,
                        material=p02_order_row.get('material', ''),
                        input_qty=p02_order_row.get('order_qty', 0),
                        input_uom='KG',
                        output_qty=p02_order_row.get('delivered_qty', 0),
                        output_uom=p02_order_row.get('uom', 'KG'),
                        input_kg=p02_input_kg,
                        output_kg=p02_output_kg,
                        yield_pct=p02_yield,
                        loss_kg=p02_loss
                    )
                    
                    # Step 4: Find P03 batches consumed by P02
                    p03_batches = self.find_input_batches(p02_order_row['order'])
                    
                    if p03_batches:
                        for p03_batch in p03_batches:
                            p03_order_row = self.find_order_by_batch(p03_batch, 'P03')
                            if p03_order_row is not None:
                                p03_input_kg, p03_output_kg, p03_yield, p03_loss = self.calculate_stage_yield(
                                    input_qty=p03_order_row.get('order_qty', 0),
                                    input_uom='KG',
                                    output_qty=p03_order_row.get('delivered_qty', 0),
                                    output_uom=p03_order_row.get('uom', 'KG'),
                                    material_code=p03_order_row.get('material', '')
                                )
                                
                                p03_stage = ProductionStage(
                                    mrp_controller='P03',
                                    order=p03_order_row['order'],
                                    batch=p03_batch,
                                    material=p03_order_row.get('material', ''),
                                    input_qty=p03_order_row.get('order_qty', 0),
                                    input_uom='KG',
                                    output_qty=p03_order_row.get('delivered_qty', 0),
                                    output_uom=p03_order_row.get('uom', 'KG'),
                                    input_kg=p03_input_kg,
                                    output_kg=p03_output_kg,
                                    yield_pct=p03_yield,
                                    loss_kg=p03_loss
                                )
                                break
                    break
        
        # Calculate totals
        if p02_stage is None:
            missing_stages.append('P02')
        if p03_stage is None:
            missing_stages.append('P03')
        
        # Total yield: P03 input to P01 output
        total_input_kg = p03_stage.input_kg if p03_stage else (p02_stage.input_kg if p02_stage else p01_stage.input_kg)
        total_output_kg = p01_stage.output_kg
        
        if total_input_kg and total_output_kg and total_input_kg > 0:
            total_yield_pct = round((total_output_kg / total_input_kg) * 100, 2)
            total_loss_kg = round(total_input_kg - total_output_kg, 2)
        else:
            total_yield_pct = None
            total_loss_kg = None
        
        return ProductionChain(
            p01=p01_stage,
            p02=p02_stage,
            p03=p03_stage,
            total_input_kg=total_input_kg,
            total_output_kg=total_output_kg,
            total_yield_pct=total_yield_pct,
            total_loss_kg=total_loss_kg,
            chain_complete=len(missing_stages) == 0,
            missing_stages=missing_stages
        )
    
    def trace_all_p01_chains(self) -> pd.DataFrame:
        """
        Trace production chains for all P01 batches
        
        Returns DataFrame with yield metrics for all chains
        """
        p01_orders = self.find_p01_orders()
        
        results = []
        for _, row in p01_orders.iterrows():
            batch = row.get('batch')
            if pd.isna(batch):
                continue
            
            chain = self.trace_production_chain(batch)
            
            result = {
                'p01_batch': batch,
                'p01_order': chain.p01.order if chain.p01 else None,
                'p01_material': chain.p01.material if chain.p01 else None,
                'p01_output_kg': chain.p01.output_kg if chain.p01 else None,
                
                'p02_batch': chain.p02.batch if chain.p02 else None,
                'p02_order': chain.p02.order if chain.p02 else None,
                'p02_yield_pct': chain.p02.yield_pct if chain.p02 else None,
                
                'p03_batch': chain.p03.batch if chain.p03 else None,
                'p03_order': chain.p03.order if chain.p03 else None,
                'p03_yield_pct': chain.p03.yield_pct if chain.p03 else None,
                
                'total_input_kg': chain.total_input_kg,
                'total_output_kg': chain.total_output_kg,
                'total_yield_pct': chain.total_yield_pct,
                'total_loss_kg': chain.total_loss_kg,
                'chain_complete': chain.chain_complete,
                'missing_stages': ','.join(chain.missing_stages)
            }
            results.append(result)
        
        return pd.DataFrame(results)
    
    def build_chain_from_p01(self, p01_order: str) -> Optional[ProductionChain]:
        """
        Build production chain starting from P01 order number
        
        Alias for trace_production_chain that accepts order instead of batch
        """
        # Find batch for this P01 order
        p01_row = self.orders[
            (self.orders['order'] == p01_order) &
            (self.orders['mrp_controller'] == 'P01')
        ]
        
        if p01_row.empty:
            return None
        
        batch = p01_row.iloc[0].get('batch')
        if pd.isna(batch):
            return None
        
        return self.trace_production_chain(batch)

"""
Test cases for core algorithms
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta

from src.core.netting import StackNettingEngine
from src.core.uom_converter import UomConverter
from src.core.business_logic import OrderClassifier


class TestStackNetting:
    """Test Stack-based LIFO netting algorithm"""
    
    def test_basic_netting_lifo(self):
        """Test LIFO netting: last issue should be cancelled first"""
        # Create test data
        data = {
            'col_0_posting_date': [
                datetime(2025, 1, 1),  # Issue 1
                datetime(2025, 1, 2),  # Issue 2
                datetime(2025, 1, 3),  # Reversal (should cancel Issue 2)
            ],
            'col_1_mvt_type': [601, 601, 602],
            'col_2_plant': [1201, 1201, 1201],
            'col_6_batch': ['BATCH001', 'BATCH001', 'BATCH001'],
            'col_4_material': ['MAT001', 'MAT001', 'MAT001'],
            'col_7_qty': [10, 5, -5],
        }
        df = pd.DataFrame(data)
        
        engine = StackNettingEngine(df)
        result = engine.apply_stack_netting('BATCH001', 1201, 601, 602)
        
        # Issue 1 should remain (LIFO: Issue 2 was cancelled)
        assert result.remaining_forward == 1
        assert result.netted_count == 1
        assert not result.is_fully_reversed
        assert result.last_valid_date == datetime(2025, 1, 1)
    
    def test_full_reversal(self):
        """Test complete reversal - all issues cancelled"""
        data = {
            'col_0_posting_date': [
                datetime(2025, 1, 1),
                datetime(2025, 1, 2),
            ],
            'col_1_mvt_type': [601, 602],
            'col_2_plant': [1201, 1201],
            'col_6_batch': ['BATCH001', 'BATCH001'],
            'col_4_material': ['MAT001', 'MAT001'],
            'col_7_qty': [10, -10],
        }
        df = pd.DataFrame(data)
        
        engine = StackNettingEngine(df)
        result = engine.apply_stack_netting('BATCH001', 1201, 601, 602)
        
        assert result.is_fully_reversed
        assert result.remaining_forward == 0
        assert result.last_valid_date is None
    
    def test_plant_separation(self):
        """Test that netting is plant-specific"""
        data = {
            'col_0_posting_date': [
                datetime(2025, 1, 1),
                datetime(2025, 1, 2),
            ],
            'col_1_mvt_type': [601, 602],
            'col_2_plant': [1201, 1401],  # Different plants!
            'col_6_batch': ['BATCH001', 'BATCH001'],
            'col_4_material': ['MAT001', 'MAT001'],
            'col_7_qty': [10, -10],
        }
        df = pd.DataFrame(data)
        
        engine = StackNettingEngine(df)
        
        # Plant 1201 should have 1 issue (no reversal for this plant)
        result_1201 = engine.apply_stack_netting('BATCH001', 1201, 601, 602)
        assert result_1201.remaining_forward == 1
        
        # Plant 1401 should have 0 issues (only reversal)
        result_1401 = engine.apply_stack_netting('BATCH001', 1401, 601, 602)
        assert result_1401.remaining_forward == 0


class TestOrderClassifier:
    """Test MTO/MTS classification and order status"""
    
    def test_mto_dual_logic_both_conditions(self):
        """MTO requires BOTH Sales Order AND P01"""
        row = pd.Series({
            'sales_order': 'SO12345',
            'mrp_controller': 'P01'
        })
        assert OrderClassifier.is_mto(row) == True
    
    def test_mts_no_sales_order(self):
        """No Sales Order = MTS"""
        row = pd.Series({
            'sales_order': None,
            'mrp_controller': 'P01'
        })
        assert OrderClassifier.is_mto(row) == False
    
    def test_mts_not_p01(self):
        """Has Sales Order but not P01 = MTS"""
        row = pd.Series({
            'sales_order': 'SO12345',
            'mrp_controller': 'P02'  # Not P01
        })
        assert OrderClassifier.is_mto(row) == False
    
    def test_order_status_cancelled(self):
        """Finish date with zero delivery = CANCELLED"""
        row = pd.Series({
            'actual_finish_date': datetime(2025, 1, 1),
            'delivered_quantity': 0
        })
        assert OrderClassifier.get_order_status(row) == 'CANCELLED'
    
    def test_order_status_wip(self):
        """No finish date, no delivery = WIP"""
        row = pd.Series({
            'actual_finish_date': None,
            'delivered_quantity': 0
        })
        assert OrderClassifier.get_order_status(row) == 'WIP'
    
    def test_order_status_completed(self):
        """Finish date with delivery = COMPLETED"""
        row = pd.Series({
            'actual_finish_date': datetime(2025, 1, 1),
            'delivered_quantity': 100
        })
        assert OrderClassifier.get_order_status(row) == 'COMPLETED'
    
    def test_sales_po_filter(self):
        """PO starting with '44' is sales PO"""
        assert OrderClassifier.is_sales_po('4400001234') == True
        assert OrderClassifier.is_sales_po('4500001234') == False
        assert OrderClassifier.is_sales_po(None) == False


class TestUomConverter:
    """Test UOM conversion PC to KG"""
    
    def test_kg_passthrough(self):
        """KG should pass through unchanged"""
        converter = UomConverter()
        result, method = converter.normalize_to_kg(100, 'KG', 'MAT001')
        assert result == 100
        assert method == 'already_kg'
    
    def test_pc_conversion(self):
        """PC should be converted using table"""
        converter = UomConverter()
        
        # Add a conversion factor
        converter.conversion_table['MAT001'] = type('obj', (object,), {
            'kg_per_unit': 2.5,
            'is_valid': True
        })()
        
        result, method = converter.normalize_to_kg(10, 'PC', 'MAT001')
        assert result == 25  # 10 * 2.5
        assert method == 'converted'
    
    def test_unknown_material(self):
        """Unknown material should return None"""
        converter = UomConverter()
        result, method = converter.normalize_to_kg(10, 'PC', 'UNKNOWN')
        assert result is None
        assert method == 'no_conversion_factor'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

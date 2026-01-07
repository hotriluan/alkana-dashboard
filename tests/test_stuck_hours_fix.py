"""
Test cases for stuck hours calculation fix

Skills: testing, backend-development
CLAUDE.md: KISS - Simple, focused tests for specific bug fix
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta

from src.core.alerts import AlertDetector
from src.core.netting import StackNettingEngine


class TestStuckHoursCalculation:
    """Test that stuck hours are calculated correctly using actual MVT 601 date"""
    
    def test_delayed_transit_with_mvt_601(self):
        """
        Test: Batch with MVT 101 and MVT 601 should show actual transit hours
        
        Scenario:
        - MVT 101 at Plant 1401 on 2025-12-18
        - MVT 601 at Plant 1401 on 2025-12-22
        - Expected: 96 hours (4 days × 24)
        """
        # Create test data
        data = {
            'col_0_posting_date': [
                datetime(2025, 12, 18),  # MVT 101 - Receipt
                datetime(2025, 12, 22),  # MVT 601 - Issue
            ],
            'col_1_mvt_type': [101, 601],
            'col_2_plant': [1401, 1401],
            'col_3_sloc': [101, 101],
            'col_4_material': ['100002758', '100002758'],
            'col_5_material_desc': ['Test Material', 'Test Material'],
            'col_6_batch': ['25L2492010', '25L2492010'],
            'col_7_qty': [100, -100],
            'col_8_uom': ['PC', 'PC'],
            'col_9_cost_center': [None, None],
            'col_10_gl_account': [None, None],
            'col_11_material_doc': ['DOC001', 'DOC002'],
            'col_12_reference': [None, None],
            'col_13_outbound_delivery': [None, None],
            'col_14': [None, None],
            'col_15_purchase_order': [None, None],
        }
        mb51_df = pd.DataFrame(data)
        
        # Also need production data to identify P01 batches
        # For this test, we'll mock the P01 batch query
        # In real scenario, this would come from fact_production table
        
        detector = AlertDetector(
            mb51_df=mb51_df,
            stuck_threshold_hours=48  # 48 hour threshold
        )
        
        # Detect alerts at Plant 1401
        alerts = detector.detect_stuck_in_transit(plant=1401)
        
        # Should have 1 DELAYED_TRANSIT alert
        assert len(alerts) == 1, f"Expected 1 alert, got {len(alerts)}"
        
        alert = alerts[0]
        assert alert.alert_type == 'DELAYED_TRANSIT'
        assert alert.batch == '25L2492010'
        assert alert.metric_value == 96.0, f"Expected 96.0 hours, got {alert.metric_value}"
        assert alert.severity in ['CRITICAL', 'HIGH', 'MEDIUM']  # Based on hours
    
    def test_no_alert_when_no_mvt_601(self):
        """
        Test: Batch with only MVT 101 (no MVT 601) should NOT create alert
        
        This is the key fix - we don't create alerts for incomplete transits
        """
        data = {
            'col_0_posting_date': [
                datetime(2025, 12, 18),  # MVT 101 only
            ],
            'col_1_mvt_type': [101],
            'col_2_plant': [1401],
            'col_3_sloc': [101],
            'col_4_material': ['100002758'],
            'col_5_material_desc': ['Test Material'],
            'col_6_batch': ['25L2492010'],
            'col_7_qty': [100],
            'col_8_uom': ['PC'],
            'col_9_cost_center': [None],
            'col_10_gl_account': [None],
            'col_11_material_doc': ['DOC001'],
            'col_12_reference': [None],
            'col_13_outbound_delivery': [None],
            'col_14': [None],
            'col_15_purchase_order': [None],
        }
        mb51_df = pd.DataFrame(data)
        
        detector = AlertDetector(
            mb51_df=mb51_df,
            stuck_threshold_hours=48
        )
        
        alerts = detector.detect_stuck_in_transit(plant=1401)
        
        # Should have NO alerts (batch still in transit)
        assert len(alerts) == 0, f"Expected 0 alerts for incomplete transit, got {len(alerts)}"
    
    def test_no_alert_when_below_threshold(self):
        """
        Test: Batch with transit time below threshold should NOT create alert
        
        Scenario:
        - MVT 101 on 2025-12-18
        - MVT 601 on 2025-12-19 (only 24 hours)
        - Threshold: 48 hours
        - Expected: No alert
        """
        data = {
            'col_0_posting_date': [
                datetime(2025, 12, 18),
                datetime(2025, 12, 19),  # Only 1 day later
            ],
            'col_1_mvt_type': [101, 601],
            'col_2_plant': [1401, 1401],
            'col_3_sloc': [101, 101],
            'col_4_material': ['100002758', '100002758'],
            'col_5_material_desc': ['Test Material', 'Test Material'],
            'col_6_batch': ['25L2492010', '25L2492010'],
            'col_7_qty': [100, -100],
            'col_8_uom': ['PC', 'PC'],
            'col_9_cost_center': [None, None],
            'col_10_gl_account': [None, None],
            'col_11_material_doc': ['DOC001', 'DOC002'],
            'col_12_reference': [None, None],
            'col_13_outbound_delivery': [None, None],
            'col_14': [None, None],
            'col_15_purchase_order': [None, None],
        }
        mb51_df = pd.DataFrame(data)
        
        detector = AlertDetector(
            mb51_df=mb51_df,
            stuck_threshold_hours=48
        )
        
        alerts = detector.detect_stuck_in_transit(plant=1401)
        
        # Should have NO alerts (below threshold)
        assert len(alerts) == 0, f"Expected 0 alerts for below-threshold transit, got {len(alerts)}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

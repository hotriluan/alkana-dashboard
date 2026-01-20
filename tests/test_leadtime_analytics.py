"""
Unit tests for Lead Time Analytics
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.core.leadtime_analytics import LeadTimeAnalytics, StageBreakdownItem, HistogramBucket
from src.db.models import FactLeadTime


class TestLeadTimeAnalytics:
    """Test lead time breakdown and distribution"""
    
    @pytest.fixture
    def leadtime_data(self, db: Session):
        """Create test lead time data"""
        # Create orders with different lead times
        lead_times = [
            (2, 3, 1, 6),    # 6 days total
            (5, 7, 2, 14),   # 14 days total
            (1, 5, 3, 9),    # 9 days total
            (3, 8, 2, 13),   # 13 days total
            (1, 2, 1, 4),    # 4 days total
            (10, 15, 5, 30), # 30 days total
            (2, 5, 1, 8),    # 8 days total
            (15, 20, 10, 45),# 45 days total
        ]
        
        for i, (prep, prod, deliv, total) in enumerate(lead_times):
            db.add(FactLeadTime(
                order_number=f'ORD{1000+i}',
                prep_time_days=prep,
                production_time_days=prod,
                delivery_time_days=deliv,
                total_leadtime_days=total,
            ))
        
        db.commit()
    
    def test_stage_breakdown(self, db: Session, leadtime_data):
        """Test that stage breakdown returns correct data"""
        analytics = LeadTimeAnalytics(db)
        breakdown = analytics.get_stage_breakdown(limit=5)
        
        assert len(breakdown) <= 5
        
        # Verify stage sums equal total
        for item in breakdown:
            stage_sum = item.prep_days + item.production_days + item.delivery_days
            assert stage_sum == item.total_days
    
    def test_histogram_buckets(self, db: Session, leadtime_data):
        """Test that histogram correctly buckets lead times"""
        analytics = LeadTimeAnalytics(db)
        histogram = analytics.get_leadtime_histogram()
        
        assert len(histogram) == 6  # Should have 6 buckets
        
        # Verify bucket definitions
        bucket_ranges = [(b.min_days, b.max_days) for b in histogram]
        expected = [(0, 3), (4, 7), (8, 14), (15, 21), (22, 30), (31, 999)]
        assert bucket_ranges == expected
        
        # Verify total count
        total_count = sum(b.order_count for b in histogram)
        assert total_count == 8  # We created 8 orders
    
    def test_histogram_distribution(self, db: Session, leadtime_data):
        """Test that histogram correctly distributes orders"""
        analytics = LeadTimeAnalytics(db)
        histogram = analytics.get_leadtime_histogram()
        
        bucket_map = {b.range_label: b.order_count for b in histogram}
        
        # Orders: 6, 14, 9, 13, 4, 30, 8, 45
        # 0-3: 0 orders
        # 4-7: 1 order (4, 8)
        # 8-14: 3 orders (8, 9, 13, 14)
        # 15-21: 0 orders
        # 22-30: 1 order (30)
        # >30: 1 order (45)
        
        assert bucket_map['0-3 days'] == 0
        assert bucket_map['>30 days'] == 1

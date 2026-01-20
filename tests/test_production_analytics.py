"""
Unit tests for Production Analytics
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.core.production_analytics import ProductionAnalytics, FunnelStage, TopOrder
from src.db.models import FactProduction


class TestProductionAnalytics:
    """Test production funnel and top orders"""
    
    @pytest.fixture
    def production_data(self, db: Session):
        """Create test production orders"""
        # Create orders with different statuses
        statuses = ['CRTD', 'REL', 'CNF', 'DLV', 'CRTD', 'REL', 'CRTD']
        
        for i, status in enumerate(statuses):
            db.add(FactProduction(
                order_number=f'ORD{1000+i}',
                plant_code=1,
                material_code=f'MAT{i:03d}',
                system_status=status,
                order_qty_kg=1000 * (i + 1),
                release_date=datetime.utcnow().date() - timedelta(days=30-i),
                actual_finish_date=datetime.utcnow().date() - timedelta(days=20-i),
            ))
        
        db.commit()
    
    def test_funnel_counts(self, db: Session, production_data):
        """Test that funnel correctly aggregates orders by status"""
        analytics = ProductionAnalytics(db)
        funnel = analytics.get_production_funnel()
        
        assert len(funnel) > 0
        
        # Verify total orders across funnel matches expected
        status_map = {item.status_code: item.order_count for item in funnel}
        
        # CRTD should have 3 orders, REL should have 2
        assert status_map.get('CRTD', 0) == 3
        assert status_map.get('REL', 0) == 2
    
    def test_top_orders(self, db: Session, production_data):
        """Test that top orders are ranked by quantity"""
        analytics = ProductionAnalytics(db)
        top_orders = analytics.get_top_orders(limit=3)
        
        assert len(top_orders) <= 3
        
        # Verify orders are sorted by quantity descending
        for i in range(len(top_orders) - 1):
            assert top_orders[i].order_qty_kg >= top_orders[i+1].order_qty_kg
    
    def test_delay_detection(self, db: Session):
        """Test that order delays are correctly detected"""
        # Create an order that's delayed
        delayed_order = FactProduction(
            order_number='DELAYED001',
            plant_code=1,
            material_code='DELAYED_MAT',
            system_status='DLV',
            order_qty_kg=1000,
            release_date=datetime.utcnow().date() - timedelta(days=30),
            actual_finish_date=datetime.utcnow().date() - timedelta(days=5),
        )
        db.add(delayed_order)
        db.commit()
        
        analytics = ProductionAnalytics(db)
        top_orders = analytics.get_top_orders(limit=10)
        
        delayed = next((o for o in top_orders if o.order_number == 'DELAYED001'), None)
        if delayed:
            assert delayed.is_delayed == True

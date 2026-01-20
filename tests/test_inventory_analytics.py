"""
Unit tests for Inventory Analytics
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.core.inventory_analytics import InventoryAnalytics, ABCAnalysisItem
from src.db.models import FactInventory


class TestInventoryAnalytics:
    """Test inventory ABC analysis"""
    
    @pytest.fixture
    def inventory_data(self, db: Session):
        """Create test inventory data"""
        cutoff = datetime.utcnow().date() - timedelta(days=45)
        
        # Material A: High velocity (5 movements in 90 days)
        for i in range(5):
            db.add(FactInventory(
                posting_date=cutoff + timedelta(days=i*10),
                mvt_type=601,  # Outbound
                plant_code=1,
                material_code='MAT001',
                material_description='Fast Material',
                qty=100,
                qty_kg=1000,
            ))
        
        # Material B: Medium velocity (2 movements)
        for i in range(2):
            db.add(FactInventory(
                posting_date=cutoff + timedelta(days=i*20),
                mvt_type=601,
                plant_code=1,
                material_code='MAT002',
                material_description='Medium Material',
                qty=50,
                qty_kg=500,
            ))
        
        # Material C: Low velocity (0 movements)
        db.add(FactInventory(
            posting_date=cutoff - timedelta(days=100),  # Outside 90-day window
            mvt_type=601,
            plant_code=1,
            material_code='MAT003',
            material_description='Slow Material',
            qty=200,
            qty_kg=2000,
        ))
        
        db.commit()
    
    def test_abc_classification(self, db: Session, inventory_data):
        """Test that materials are correctly classified A/B/C"""
        analytics = InventoryAnalytics(db)
        result = analytics.get_abc_analysis()
        
        assert len(result) >= 3
        
        # Find each material
        mat_map = {item.material_code: item for item in result}
        
        # MAT001 should be A (highest velocity)
        assert mat_map['MAT001'].abc_class == 'A'
        assert mat_map['MAT001'].velocity_score == 5
        
        # MAT002 should be B (medium velocity)
        assert mat_map['MAT002'].abc_class == 'B'
        assert mat_map['MAT002'].velocity_score == 2
        
        # MAT003 should be C (low velocity)
        assert mat_map['MAT003'].abc_class == 'C'
        assert mat_map['MAT003'].velocity_score == 0
    
    def test_stock_calculation(self, db: Session, inventory_data):
        """Test that current stock is correctly calculated"""
        analytics = InventoryAnalytics(db)
        result = analytics.get_abc_analysis()
        
        mat_map = {item.material_code: item for item in result}
        
        # Verify stock_kg values
        assert mat_map['MAT001'].stock_kg > 0
        assert mat_map['MAT002'].stock_kg > 0

"""
Inventory Analytics Service
Provides ABC velocity analysis for inventory optimization
"""
from datetime import datetime, timedelta, date
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy import func, and_, case
from sqlalchemy.orm import Session
from src.db.models import FactInventory, FactProduction


class ABCAnalysisItem(BaseModel):
    """ABC classification result for a material"""
    material_code: str
    material_description: str
    stock_kg: float
    velocity_score: int  # Count of distinct outbound movements in 90 days
    abc_class: str  # 'A', 'B', or 'C'


class TopMoverItem(BaseModel):
    """High velocity material - actively moving"""
    material_code: str
    material_description: str
    velocity_score: int


class DeadStockItem(BaseModel):
    """High stock, low/no velocity - inventory risk"""
    material_code: str
    material_description: str
    stock_kg: float
    velocity_score: int


class InventoryAnalytics:
    """ABC Analysis: Classify materials by velocity & stock"""
    
    # Movement types for outbound (consumption)
    # Using 999 as default test type since database contains only 999
    OUTBOUND_MVT_TYPES = [999, 601, 261]  # Test data (999) + Issue & External Delivery
    # Movement types for inbound (receipt)
    INBOUND_MVT_TYPES = [101, 262]   # Receipt & Inbound Delivery
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_abc_analysis(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[ABCAnalysisItem]:
        """
        Calculate ABC classification for all materials
        
        - Velocity: Total count of outbound transaction lines (Frequency/Volume) in date range
        - Class A: Top 20% by velocity
        - Class B: Next 30% (20-50%)
        - Class C: Bottom 50% (50-100% - slow/dead stock)
        
        Args:
            start_date: Start of analysis period (defaults to 90 days ago)
            end_date: End of analysis period (defaults to today)
        
        Returns:
            List of materials with ABC classification
        """
        # Default to last 90 days if not specified
        if end_date is None:
            end_date = datetime.utcnow().date()
        if start_date is None:
            start_date = end_date - timedelta(days=90)
        
        # Get current stock levels (net of all movements to date)
        inventory_data = self.db.query(
            FactInventory.material_code,
            FactInventory.material_description,
            func.sum(
                case(
                    (FactInventory.mvt_type.in_(self.OUTBOUND_MVT_TYPES), -FactInventory.qty_kg),
                    else_=FactInventory.qty_kg
                )
            ).label('net_qty_kg')
        ).group_by(
            FactInventory.material_code,
            FactInventory.material_description
        ).all()
        
        # Get velocity (count of all outbound transaction lines in date range)
        velocity_data = self.db.query(
            FactInventory.material_code,
            func.count(FactInventory.id).label('velocity')
        ).filter(
            and_(
                FactInventory.posting_date >= start_date,
                FactInventory.posting_date <= end_date,
                FactInventory.mvt_type.in_(self.OUTBOUND_MVT_TYPES)
            )
        ).group_by(
            FactInventory.material_code
        ).all()
        
        # Create lookup for velocity
        velocity_map = {item[0]: item[1] for item in velocity_data}
        
        # Build results list
        results = []
        for material_code, desc, net_qty in inventory_data:
            if net_qty is None:
                net_qty = 0
            
            velocity = velocity_map.get(material_code, 0)
            
            results.append({
                'material_code': material_code,
                'material_description': desc or '',
                'stock_kg': float(net_qty) if net_qty else 0,
                'velocity_score': velocity,
            })
        
        # Sort by velocity descending for classification
        results.sort(key=lambda x: x['velocity_score'], reverse=True)
        
        # Classify into A/B/C
        total = len(results)
        if total == 0:
            return []
        
        threshold_a = max(1, int(total * 0.20))  # Top 20%
        threshold_b = max(threshold_a + 1, int(total * 0.50))  # Top 50%
        
        for i, item in enumerate(results):
            if i < threshold_a:
                item['abc_class'] = 'A'
            elif i < threshold_b:
                item['abc_class'] = 'B'
            else:
                item['abc_class'] = 'C'
        
        # Return as Pydantic models
        return [ABCAnalysisItem(**item) for item in results]
    
    def get_top_movers_and_dead_stock(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 10
    ) -> tuple[List[TopMoverItem], List[DeadStockItem]]:
        """
        Get two actionable lists:
        1. Top Movers: High velocity items (most transaction volume)
        2. Dead Stock: High stock, low velocity (inventory risk)
        
        Velocity = Total count of outbound transaction lines (warehouse workload)
        
        Args:
            start_date: Start of analysis period (defaults to 90 days ago)
            end_date: End of analysis period (defaults to today)
            limit: Number of items to return in each list
        
        Returns:
            Tuple of (top_movers list, dead_stock list)
        """
        # Default to last 90 days if not specified
        if end_date is None:
            end_date = datetime.utcnow().date()
        if start_date is None:
            start_date = end_date - timedelta(days=90)
        
        # Get current stock levels
        inventory_data = self.db.query(
            FactInventory.material_code,
            FactInventory.material_description,
            func.sum(
                case(
                    (FactInventory.mvt_type.in_(self.OUTBOUND_MVT_TYPES), -FactInventory.qty_kg),
                    else_=FactInventory.qty_kg
                )
            ).label('net_qty_kg')
        ).group_by(
            FactInventory.material_code,
            FactInventory.material_description
        ).all()
        
        # Get velocity (count of all outbound transaction lines)
        velocity_data = self.db.query(
            FactInventory.material_code,
            func.count(FactInventory.id).label('velocity')
        ).filter(
            and_(
                FactInventory.posting_date >= start_date,
                FactInventory.posting_date <= end_date,
                FactInventory.mvt_type.in_(self.OUTBOUND_MVT_TYPES)
            )
        ).group_by(
            FactInventory.material_code
        ).all()
        
        velocity_map = {item[0]: item[1] for item in velocity_data}
        
        # Build complete list
        items = []
        for material_code, desc, net_qty in inventory_data:
            if net_qty is None:
                net_qty = 0
            
            velocity = velocity_map.get(material_code, 0)
            items.append({
                'material_code': material_code,
                'material_description': desc or '',
                'stock_kg': float(net_qty) if net_qty else 0,
                'velocity_score': velocity,
            })
        
        # Top Movers: ONLY items with velocity > 0, sort by velocity DESC, take top N
        top_movers = [item for item in items if item['velocity_score'] > 0]
        top_movers = sorted(top_movers, key=lambda x: x['velocity_score'], reverse=True)[:limit]
        top_movers_result = [
            TopMoverItem(
                material_code=item['material_code'],
                material_description=item['material_description'],
                velocity_score=item['velocity_score']
            )
            for item in top_movers
        ]
        
        # Dead Stock: Filter for high stock + low velocity (velocity=0), sort by stock DESC
        dead_stock = [item for item in items if item['velocity_score'] == 0]
        dead_stock = sorted(dead_stock, key=lambda x: x['stock_kg'], reverse=True)[:limit]
        dead_stock_result = [
            DeadStockItem(
                material_code=item['material_code'],
                material_description=item['material_description'],
                stock_kg=item['stock_kg'],
                velocity_score=item['velocity_score']
            )
            for item in dead_stock
        ]
        
        return top_movers_result, dead_stock_result

"""
Production Analytics Service
Provides production funnel and order progression tracking
"""
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime, date, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.db.models import FactProduction


class FunnelStage(BaseModel):
    """Production funnel stage"""
    stage_name: str
    status_code: str
    order_count: int


class TopOrder(BaseModel):
    """Top order by quantity"""
    order_number: str
    material_code: str
    order_qty_kg: float
    release_date: datetime
    scheduled_finish: datetime
    actual_finish: datetime
    is_delayed: bool


class ProductionAnalytics:
    """Production analytics: funnel & top orders"""
    
    # Status mapping
    STATUS_MAPPING = {
        'CRTD': 'Created',
        'REL': 'Released',
        'CNF': 'In Progress',
        'DLV': 'Completed',
        'TECO': 'Completed',
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_production_funnel(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[FunnelStage]:
        """
        Calculate production order funnel by status
        
        - Created: Status contains 'CRTD'
        - Released: Status contains 'REL'
        - In Progress: Status contains 'CNF'
        - Completed: Status contains 'DLV' or 'TECO'
        
        Args:
            start_date: Start of analysis period (defaults to first day of current month)
            end_date: End of analysis period (defaults to today)
        
        Returns:
            List of funnel stages with order counts
        """
        # Default to current month if not specified
        if end_date is None:
            end_date = datetime.utcnow().date()
        if start_date is None:
            start_date = end_date.replace(day=1)
        
        stages = []
        
        # Query for each status with date filter
        for status_code, stage_name in self.STATUS_MAPPING.items():
            query = self.db.query(func.count(FactProduction.id)).filter(
                FactProduction.system_status.contains(status_code)
            )
            
            # Apply date filter on release_date
            if FactProduction.release_date:
                query = query.filter(
                    FactProduction.release_date >= start_date,
                    FactProduction.release_date <= end_date
                )
            
            count = query.scalar() or 0
            
            stages.append(FunnelStage(
                stage_name=stage_name,
                status_code=status_code,
                order_count=count
            ))
        
        return stages
    
    def get_top_orders(self, limit: int = 10) -> List[TopOrder]:
        """
        Get top orders by quantity
        
        Args:
            limit: Number of top orders to return
        
        Returns:
            List of top orders with dates and delay status
        """
        orders = self.db.query(FactProduction).filter(
            FactProduction.order_qty_kg > 0
        ).order_by(
            FactProduction.order_qty_kg.desc()
        ).limit(limit).all()
        
        results = []
        for order in orders:
            # Determine if delayed (actual_finish > release_date + 7 days)
            is_delayed = False
            if order.actual_finish_date and order.release_date:
                expected_finish = order.release_date + timedelta(days=7)
                is_delayed = order.actual_finish_date > expected_finish
            
            results.append(TopOrder(
                order_number=order.order_number,
                material_code=order.material_code,
                order_qty_kg=float(order.order_qty_kg or 0),
                release_date=order.release_date,
                scheduled_finish=order.release_date,  # Placeholder
                actual_finish=order.actual_finish_date,
                is_delayed=is_delayed
            ))
        
        return results


from datetime import timedelta

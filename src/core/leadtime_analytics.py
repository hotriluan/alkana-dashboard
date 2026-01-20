"""
Lead Time Analytics Service
Provides stage breakdown and histogram analysis
"""
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime, date, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.db.models import FactLeadTime, DimMaterial


class StageBreakdownItem(BaseModel):
    """Lead time breakdown by stage for a single order"""
    order_number: str
    material_code: str
    material_description: str
    batch: str
    prep_days: int
    production_days: int
    delivery_days: int
    total_days: int


class HistogramBucket(BaseModel):
    """Lead time distribution bucket"""
    range_label: str  # e.g. "0-3 days", "4-7 days"
    min_days: int
    max_days: int
    order_count: int


class LeadTimeAnalytics:
    """Lead time analytics: stage breakdown & distribution"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_stage_breakdown(
        self,
        order_limit: int = 20,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[StageBreakdownItem]:
        """
        Get lead time breakdown by stage for delivered orders in date range
        
        - Prep: Order Date → Release Date (MTO only)
        - Production: Release Date → Finish Date
        - Delivery: Finish Date → Actual GI Date
        
        Args:
            order_limit: Number of recent orders to analyze
            start_date: Start of analysis period (defaults to first day of current month)
            end_date: End of analysis period (defaults to today)
        
        Returns:
            List of orders with stage breakdowns
        """
        # Default to current month if not specified
        if end_date is None:
            end_date = datetime.utcnow().date()
        if start_date is None:
            start_date = end_date.replace(day=1)
        
        # CRITICAL FIX: Filter FIRST, then LIMIT (not limit then filter)
        # Join with DimMaterial to get material_description, with fallback to FactLeadTime value
        from sqlalchemy import func as sql_func, cast, String
        
        query = self.db.query(
            FactLeadTime,
            # Use COALESCE: prefer DimMaterial.description, fallback to FactLeadTime.material_code
            sql_func.coalesce(DimMaterial.material_description, FactLeadTime.material_code)
        ).outerjoin(
            DimMaterial, 
            # Cast both sides to STRING and trim for safety
            cast(FactLeadTime.material_code, String) == cast(DimMaterial.material_code, String)
        ).filter(
            FactLeadTime.lead_time_days.isnot(None)
        )
        
        # Apply date filter on end_date (delivery date) BEFORE limiting
        if start_date and end_date:
            query = query.filter(
                FactLeadTime.end_date >= start_date,
                FactLeadTime.end_date <= end_date
            )
        
        # Sort and limit AFTER filtering
        results_query = query.order_by(
            FactLeadTime.end_date.desc()
        ).limit(order_limit).all()
        
        results = []
        for order, material_desc in results_query:
            # FALLBACK: If both JOIN failed and field is missing, use material_code as last resort
            final_desc = material_desc or order.material_code or 'Unknown'
            
            # FALLBACK: If stage data is missing (all 0), show total as production_days
            prep = order.preparation_days or 0
            prod = order.production_days or 0
            delivery = order.delivery_days or 0
            total = order.lead_time_days or 0
            
            # If all stages are 0 but total exists, assign total to production for visibility
            if total > 0 and (prep + prod + delivery) == 0:
                prod = total
            
            results.append(StageBreakdownItem(
                order_number=order.order_number or 'N/A',
                material_code=order.material_code or 'N/A',
                material_description=final_desc,
                batch=order.batch or 'N/A',
                prep_days=prep,
                production_days=prod,
                delivery_days=delivery,
                total_days=total
            ))
        
        return results
    
    def get_leadtime_histogram(self) -> List[HistogramBucket]:
        """
        Create histogram of lead time distribution
        
        Buckets: 0-3, 4-7, 8-14, 15-21, 22-30, >30 days
        
        Returns:
            List of histogram buckets with order counts
        """
        buckets_def = [
            (0, 3, '0-3 days'),
            (4, 7, '4-7 days'),
            (8, 14, '8-14 days'),
            (15, 21, '15-21 days'),
            (22, 30, '22-30 days'),
            (31, 999, '>30 days'),
        ]
        
        results = []
        for min_days, max_days, label in buckets_def:
            count = self.db.query(func.count(FactLeadTime.id)).filter(
                FactLeadTime.lead_time_days.between(min_days, max_days)
            ).scalar() or 0
            
            results.append(HistogramBucket(
                range_label=label,
                min_days=min_days,
                max_days=max_days,
                order_count=count
            ))
        
        return results

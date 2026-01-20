"""
Sales Analytics Service
Provides customer segmentation and churn risk analysis
"""
from typing import List, Tuple, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
from src.db.models import FactBilling


class CustomerSegment(BaseModel):
    """Customer segmentation data for scatter plot"""
    customer_name: str
    order_frequency: int  # Count of orders
    total_revenue: float  # Sum of net_value


class ChurnRiskCustomer(BaseModel):
    """Customer at risk of churn"""
    customer_name: str
    last_month_revenue: float
    previous_month_revenue: float
    revenue_trend: str  # 'GROWING', 'STABLE', 'DECLINING', 'CHURN_RISK'


class SalesAnalytics:
    """Sales analytics: customer segmentation & churn detection"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_customer_segmentation(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[CustomerSegment]:
        """
        Segment customers by order frequency and revenue in date range
        
        Args:
            start_date: Start of analysis period (defaults to first day of current month)
            end_date: End of analysis period (defaults to today)
        
        Returns:
            List of customers with frequency and revenue for scatter plot
        """
        # Default to current month if not specified
        if end_date is None:
            end_date = datetime.utcnow().date()
        if start_date is None:
            start_date = end_date.replace(day=1)
        
        query = self.db.query(
            FactBilling.customer_name,
            func.count(func.distinct(FactBilling.billing_document)).label('order_count'),
            func.sum(FactBilling.net_value).label('total_revenue')
        )
        
        # Apply date filter on billing_date
        query = query.filter(
            FactBilling.billing_date >= start_date,
            FactBilling.billing_date <= end_date
        )
        
        results = query.group_by(FactBilling.customer_name).all()
        
        return [
            CustomerSegment(
                customer_name=customer,
                order_frequency=order_count or 0,
                total_revenue=float(revenue or 0)
            )
            for customer, order_count, revenue in results
        ]
    
    def get_churn_risk(self, limit: int = 5) -> List[ChurnRiskCustomer]:
        """
        Identify customers at churn risk
        
        Logic:
        - Customer had HIGH revenue last month (top quartile)
        - Customer has ZERO orders this month
        
        Args:
            limit: Number of at-risk customers to return
        
        Returns:
            List of churn-risk customers
        """
        now = datetime.utcnow().date()
        last_month_start = (now - timedelta(days=30)).replace(day=1)
        last_month_end = (now - timedelta(days=1))
        current_month_start = now.replace(day=1)
        
        # Get customers with revenue in last month
        last_month_revenue = self.db.query(
            FactBilling.customer_name,
            func.sum(FactBilling.net_value).label('revenue')
        ).filter(
            and_(
                FactBilling.billing_date >= last_month_start,
                FactBilling.billing_date <= last_month_end
            )
        ).group_by(
            FactBilling.customer_name
        ).subquery()
        
        # Get top quartile threshold (75th percentile)
        revenue_data = self.db.query(last_month_revenue.c.revenue).all()
        if not revenue_data:
            return []
        
        revenues = sorted([r[0] for r in revenue_data if r[0]])
        if len(revenues) < 4:
            threshold = revenues[-1] if revenues else 0
        else:
            threshold = revenues[int(len(revenues) * 0.75)]
        
        # Get customers with high revenue last month
        high_revenue_customers = self.db.query(
            last_month_revenue.c.customer_name,
            last_month_revenue.c.revenue
        ).filter(
            last_month_revenue.c.revenue >= threshold
        ).subquery()
        
        # Check if they have orders this month
        current_month_orders = self.db.query(
            FactBilling.customer_name
        ).filter(
            FactBilling.billing_date >= current_month_start
        ).distinct().subquery()
        
        # Find those NOT in current month (churn risk)
        at_risk = self.db.query(
            high_revenue_customers.c.customer_name,
            high_revenue_customers.c.revenue
        ).filter(
            ~high_revenue_customers.c.customer_name.in_(
                self.db.query(current_month_orders)
            )
        ).limit(limit).all()
        
        # Get previous month revenue for comparison
        previous_month_start = (last_month_start - timedelta(days=30)).replace(day=1)
        previous_month_end = (last_month_start - timedelta(days=1))
        
        results = []
        for customer_name, last_month_rev in at_risk:
            prev_month_rev = self.db.query(
                func.sum(FactBilling.net_value)
            ).filter(
                and_(
                    FactBilling.customer_name == customer_name,
                    FactBilling.billing_date >= previous_month_start,
                    FactBilling.billing_date <= previous_month_end
                )
            ).scalar() or 0
            
            trend = 'CHURN_RISK' if last_month_rev > 0 else 'DECLINING'
            
            results.append(ChurnRiskCustomer(
                customer_name=customer_name,
                last_month_revenue=float(last_month_rev or 0),
                previous_month_revenue=float(prev_month_rev or 0),
                revenue_trend=trend
            ))
        
        return results

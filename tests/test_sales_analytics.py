"""
Unit tests for Sales Analytics
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.core.sales_analytics import SalesAnalytics, CustomerSegment, ChurnRiskCustomer
from src.db.models import FactBilling


class TestSalesAnalytics:
    """Test customer segmentation and churn detection"""
    
    @pytest.fixture
    def sales_data(self, db: Session):
        """Create test billing data"""
        now = datetime.utcnow().date()
        last_month_start = (now - timedelta(days=30)).replace(day=1)
        
        # Customer A: High frequency, high revenue (VIP)
        for i in range(10):
            db.add(FactBilling(
                billing_document=f'INV_A_{i}',
                customer_name='Customer A',
                material_code='MAT001',
                net_value=50000 + i*1000,
                billing_date=last_month_start + timedelta(days=i),
            ))
        
        # Customer B: Low frequency, low revenue (Casual)
        db.add(FactBilling(
            billing_document='INV_B_1',
            customer_name='Customer B',
            material_code='MAT001',
            net_value=5000,
            billing_date=last_month_start + timedelta(days=5),
        ))
        
        # Customer C: High revenue last month, zero this month (Churn risk)
        for i in range(8):
            db.add(FactBilling(
                billing_document=f'INV_C_{i}',
                customer_name='Customer C',
                material_code='MAT001',
                net_value=40000 + i*500,
                billing_date=last_month_start + timedelta(days=i),
            ))
        
        db.commit()
    
    def test_customer_segmentation(self, db: Session, sales_data):
        """Test that customers are segmented correctly"""
        analytics = SalesAnalytics(db)
        segments = analytics.get_customer_segmentation()
        
        assert len(segments) >= 3
        
        # Find each customer
        cust_map = {item.customer_name: item for item in segments}
        
        # Verify A has highest frequency
        assert cust_map['Customer A'].order_frequency > cust_map['Customer B'].order_frequency
        
        # Verify A has highest revenue
        assert cust_map['Customer A'].total_revenue > cust_map['Customer B'].total_revenue
    
    def test_churn_risk_detection(self, db: Session, sales_data):
        """Test that churn risk customers are identified"""
        analytics = SalesAnalytics(db)
        churn_risk = analytics.get_churn_risk(limit=5)
        
        # Customer C should be identified as churn risk
        customer_names = [item.customer_name for item in churn_risk]
        assert 'Customer C' in customer_names
    
    def test_vip_vs_casual_distinction(self, db: Session, sales_data):
        """Test that VIP and casual customers are distinct"""
        analytics = SalesAnalytics(db)
        segments = analytics.get_customer_segmentation()
        
        cust_map = {item.customer_name: item for item in segments}
        
        # Customer A (VIP): high frequency + high revenue
        assert cust_map['Customer A'].order_frequency > 5
        assert cust_map['Customer A'].total_revenue > 100000
        
        # Customer B (Casual): low frequency + low revenue
        assert cust_map['Customer B'].order_frequency < cust_map['Customer A'].order_frequency
        assert cust_map['Customer B'].total_revenue < cust_map['Customer A'].total_revenue

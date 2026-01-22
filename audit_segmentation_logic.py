#!/usr/bin/env python3
"""
AUDIT: Customer Segmentation Logic Broken
Investigates why all customers are classified as VIP
Date: 2026-01-20
"""
import sys
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

# Add project to path
sys.path.insert(0, '/dev/alkana-dashboard')

from src.db.connection import get_db
from src.db.models import FactBilling
from src.core.sales_analytics import SalesAnalytics


def get_segmentation_thresholds_analysis():
    """
    Analyze the min/max values and calculated thresholds
    """
    db = next(get_db())
    
    # Test date range from user report
    start_date = date(2025, 1, 1)
    end_date = date(2026, 1, 20)
    
    print("=" * 80)
    print("🔬 CUSTOMER SEGMENTATION AUDIT REPORT")
    print("=" * 80)
    print(f"\n📅 ANALYSIS PERIOD: {start_date} to {end_date}\n")
    
    # Get raw data by customer
    customers_data = db.query(
        FactBilling.customer_name,
        func.count(func.distinct(FactBilling.billing_document)).label('order_count'),
        func.sum(FactBilling.net_value).label('total_revenue')
    ).filter(
        and_(
            FactBilling.billing_date >= start_date,
            FactBilling.billing_date <= end_date
        )
    ).group_by(FactBilling.customer_name).all()
    
    print(f"📊 DATASET STATISTICS:")
    print(f"   Total Customers: {len(customers_data)}")
    
    if not customers_data:
        print("   ❌ NO DATA FOUND FOR THIS DATE RANGE")
        return
    
    # Extract values
    revenues = sorted([float(c.total_revenue or 0) for c in customers_data])
    frequencies = sorted([int(c.order_count or 0) for c in customers_data])
    
    print(f"\n💰 REVENUE STATISTICS:")
    print(f"   Min Revenue: ${revenues[0]:,.2f}")
    print(f"   Max Revenue: ${revenues[-1]:,.2f}")
    print(f"   Avg Revenue: ${sum(revenues) / len(revenues):,.2f}")
    print(f"   Median Revenue: ${revenues[len(revenues)//2]:,.2f}")
    
    print(f"\n📈 FREQUENCY STATISTICS:")
    print(f"   Min Frequency: {frequencies[0]} orders")
    print(f"   Max Frequency: {frequencies[-1]} orders")
    print(f"   Avg Frequency: {sum(frequencies) / len(frequencies):.2f} orders")
    print(f"   Median Frequency: {frequencies[len(frequencies)//2]} orders")
    
    # Frontend uses MEDIAN for thresholds
    median_revenue = revenues[len(revenues)//2]
    median_frequency = frequencies[len(frequencies)//2]
    
    print(f"\n🎯 FRONTEND THRESHOLD (Using MEDIAN):")
    print(f"   Revenue Threshold: ${median_revenue:,.2f}")
    print(f"   Frequency Threshold: {median_frequency} orders")
    
    # Classify customers by quadrants
    vip = []
    loyal = []
    high_value = []
    casual = []
    
    for cust in customers_data:
        rev = float(cust.total_revenue or 0)
        freq = int(cust.order_count or 0)
        
        if freq >= median_frequency and rev >= median_revenue:
            vip.append((cust.customer_name, freq, rev))
        elif freq >= median_frequency and rev < median_revenue:
            loyal.append((cust.customer_name, freq, rev))
        elif freq < median_frequency and rev >= median_revenue:
            high_value.append((cust.customer_name, freq, rev))
        else:
            casual.append((cust.customer_name, freq, rev))
    
    print(f"\n📍 QUADRANT DISTRIBUTION:")
    print(f"   VIP (High Freq + High Rev): {len(vip)} customers ({len(vip)/len(customers_data)*100:.1f}%)")
    print(f"   Loyal (High Freq + Low Rev): {len(loyal)} customers ({len(loyal)/len(customers_data)*100:.1f}%)")
    print(f"   High-Value (Low Freq + High Rev): {len(high_value)} customers ({len(high_value)/len(customers_data)*100:.1f}%)")
    print(f"   Casual (Low Freq + Low Rev): {len(casual)} customers ({len(casual)/len(customers_data)*100:.1f}%)")
    
    if len(vip) == len(customers_data):
        print(f"\n❌ PROBLEM CONFIRMED: ALL CUSTOMERS CLASSIFIED AS VIP!")
    
    print(f"\n📋 TOP 5 VIP CUSTOMERS:")
    vip_sorted = sorted(vip, key=lambda x: x[2], reverse=True)[:5]
    for i, (name, freq, rev) in enumerate(vip_sorted, 1):
        print(f"   {i}. {name}: {freq} orders, ${rev:,.2f}")
    
    print(f"\n📋 TOP 5 CASUAL CUSTOMERS:")
    casual_sorted = sorted(casual, key=lambda x: x[2], reverse=True)[:5]
    if casual_sorted:
        for i, (name, freq, rev) in enumerate(casual_sorted, 1):
            print(f"   {i}. {name}: {freq} orders, ${rev:,.2f}")
    else:
        print("   (None - all customers are above casual threshold)")
    
    print(f"\n📋 TOP 5 HIGH-VALUE CUSTOMERS:")
    hv_sorted = sorted(high_value, key=lambda x: x[2], reverse=True)[:5]
    if hv_sorted:
        for i, (name, freq, rev) in enumerate(hv_sorted, 1):
            print(f"   {i}. {name}: {freq} orders, ${rev:,.2f}")
    else:
        print("   (None - no customers with low frequency)")
    
    print(f"\n📋 TOP 5 LOYAL CUSTOMERS:")
    loyal_sorted = sorted(loyal, key=lambda x: x[1], reverse=True)[:5]
    if loyal_sorted:
        for i, (name, freq, rev) in enumerate(loyal_sorted, 1):
            print(f"   {i}. {name}: {freq} orders, ${rev:,.2f}")
    else:
        print("   (None - no customers with low revenue)")
    
    # Root cause analysis
    print(f"\n" + "=" * 80)
    print("🔍 ROOT CAUSE ANALYSIS")
    print("=" * 80)
    
    # Check if revenue or frequency is too uniform
    min_freq = min(frequencies)
    max_freq = max(frequencies)
    min_rev = min(revenues)
    max_rev = max(revenues)
    
    freq_range = max_freq - min_freq
    rev_range = max_rev - min_rev
    
    print(f"\nFrequency Range: {min_freq} - {max_freq} (span: {freq_range})")
    print(f"Revenue Range: ${min_rev:,.2f} - ${max_rev:,.2f} (span: ${rev_range:,.2f})")
    
    if len(casual) == 0:
        print(f"\n⚠️ ISSUE: No casual customers detected")
        print(f"   Reason: ALL customers have revenue >= median (${median_revenue:,.2f})")
        print(f"   AND/OR ALL customers have frequency >= median ({median_frequency} orders)")
        
        # Check which one is the culprit
        below_median_rev = [c for c in customers_data if float(c.total_revenue or 0) < median_revenue]
        below_median_freq = [c for c in customers_data if int(c.order_count or 0) < median_frequency]
        
        print(f"\n   Customers below median revenue: {len(below_median_rev)}")
        print(f"   Customers below median frequency: {len(below_median_freq)}")
        
        if len(below_median_rev) == 0 and len(below_median_freq) == 0:
            print(f"\n   🚨 CRITICAL: Median calculation is wrong!")
            print(f"      Actual median should split data 50-50")
            print(f"      Current: Revenue median={median_revenue}, Frequency median={median_frequency}")
    
    # Show complete breakdown
    print(f"\n" + "=" * 80)
    print("📊 COMPLETE CUSTOMER BREAKDOWN (sorted by revenue)")
    print("=" * 80)
    print(f"\n{'Customer':<30} {'Frequency':<12} {'Revenue':<15} {'Segment':<15}")
    print("-" * 80)
    
    sorted_customers = sorted(customers_data, key=lambda x: float(x.total_revenue or 0), reverse=True)
    for cust in sorted_customers[:20]:  # Show top 20
        rev = float(cust.total_revenue or 0)
        freq = int(cust.order_count or 0)
        
        if freq >= median_frequency and rev >= median_revenue:
            segment = "VIP"
        elif freq >= median_frequency and rev < median_revenue:
            segment = "LOYAL"
        elif freq < median_frequency and rev >= median_revenue:
            segment = "HIGH-VALUE"
        else:
            segment = "CASUAL"
        
        print(f"{cust.customer_name:<30} {freq:<12} ${rev:>13,.0f}  {segment:<15}")
    
    db.close()


if __name__ == "__main__":
    get_segmentation_thresholds_analysis()

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import date

from src.db.connection import get_db
from src.db.models import FactLeadTime, DimMaterial, FactPurchaseOrder, FactInventory

router = APIRouter(prefix="/leadtime", tags=["leadtime"])

# -----------------------------------------------------------------------------
# 1. Summary KPIs
# -----------------------------------------------------------------------------
@router.get("/summary")
def get_leadtime_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get overall Lead Time KPIs"""
    
    # Build date filter if provided
    base_query = db.query(FactLeadTime)
    if start_date and end_date:
        base_query = base_query.filter(
            FactLeadTime.end_date >= start_date,
            FactLeadTime.end_date <= end_date
        )
    
    total_orders = base_query.count() or 0
    avg_leadtime = base_query.with_entities(func.avg(FactLeadTime.lead_time_days)).scalar() or 0
    
    avg_mto = base_query.filter(FactLeadTime.order_type == 'MTO')\
        .with_entities(func.avg(FactLeadTime.lead_time_days)).scalar() or 0
        
    avg_mts = base_query.filter(FactLeadTime.order_type.in_(['MTS', 'PURCHASE']))\
        .with_entities(func.avg(FactLeadTime.lead_time_days)).scalar() or 0
    
    delayed_orders = base_query.filter(FactLeadTime.lead_time_days > 30).count() or 0
    critical_orders = base_query.filter(FactLeadTime.lead_time_days > 45).count() or 0
        
    on_time = total_orders - delayed_orders
    
    return {
        "avg_mto_leadtime": float(avg_mto),
        "avg_mts_leadtime": float(avg_mts),
        "on_time_pct": round((on_time / total_orders * 100) if total_orders else 0, 1),
        "delayed_pct": round((delayed_orders / total_orders * 100) if total_orders else 0, 1),
        "critical_pct": round((critical_orders / total_orders * 100) if total_orders else 0, 1),
        "total_orders": total_orders
    }

@router.get("/breakdown")
def get_leadtime_breakdown(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get MTO/MTS breakdown statistics by stage"""
    
    def get_stats(order_type_filter):
        q = db.query(
            func.avg(FactLeadTime.preparation_days),
            func.avg(FactLeadTime.production_days),
            func.avg(FactLeadTime.transit_days),
            func.avg(FactLeadTime.storage_days),
            func.avg(FactLeadTime.delivery_days),
            func.avg(FactLeadTime.lead_time_days),
            func.count(FactLeadTime.id)
        )
        
        # Apply date filter
        if start_date and end_date:
            q = q.filter(
                FactLeadTime.end_date >= start_date,
                FactLeadTime.end_date <= end_date
            )
        
        if isinstance(order_type_filter, list):
            q = q.filter(FactLeadTime.order_type.in_(order_type_filter))
        else:
            q = q.filter(FactLeadTime.order_type == order_type_filter)
        return q.first()

    results = []
    
    # MTO
    mto = get_stats('MTO')
    results.append({
        "order_category": "MTO",
        "avg_preparation": float(mto[0] or 0),
        "avg_production": float(mto[1] or 0),
        "avg_transit": float(mto[2] or 0),
        "avg_storage": float(mto[3] or 0),
        "avg_delivery": float(mto[4] or 0),
        "avg_total": float(mto[5] or 0),
        "order_count": mto[6]
    })
    
    # MTS (Includes PURCHASE)
    mts = get_stats(['MTS', 'PURCHASE'])
    results.append({
        "order_category": "MTS",
        "avg_preparation": float(mts[0] or 0),
        "avg_production": float(mts[1] or 0),
        "avg_transit": float(mts[2] or 0),
        "avg_storage": float(mts[3] or 0),
        "avg_delivery": float(mts[4] or 0),
        "avg_total": float(mts[5] or 0),
        "order_count": mts[6]
    })
    
    return results

@router.get("/orders")
def get_leadtime_orders(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of orders with real batch and stage details"""
    
    # Join with DimMaterial to get material_description
    query = db.query(
        FactLeadTime,
        DimMaterial.material_description
    ).outerjoin(
        DimMaterial,
        FactLeadTime.material_code == DimMaterial.material_code
    )
    
    # Apply date filter
    if start_date and end_date:
        query = query.filter(
            FactLeadTime.end_date >= start_date,
            FactLeadTime.end_date <= end_date
        )
    
    results_with_desc = query.order_by(desc(FactLeadTime.end_date)).limit(limit).all()
        
    results = []
    for o, material_desc in results_with_desc:
        status = "ON_TIME"
        if o.lead_time_days and o.lead_time_days > 45: status = "CRITICAL"
        elif o.lead_time_days and o.lead_time_days > 30: status = "DELAYED"
        
        results.append({
            "order_number": o.order_number,
            "batch": o.batch or "N/A",
            "order_category": o.order_type,
            "material_description": material_desc or o.material_code,  # Use description or fallback to code
            "plant_code": str(o.plant_code),
            "preparation_time": o.preparation_days,
            "production_time": o.production_days,
            "transit_time": o.transit_days,
            "storage_time": o.storage_days,
            "delivery_time": o.delivery_days,
            "total_leadtime": o.lead_time_days,
            "leadtime_status": status,
            "release_date": o.start_date,
            "actual_finish_date": o.end_date
        })
        
    return results

# -----------------------------------------------------------------------------
# 4. By Channel (Original placeholder - now removed)
# -----------------------------------------------------------------------------
# Removed old placeholder

# -----------------------------------------------------------------------------
# 5. By Channel Analysis
# -----------------------------------------------------------------------------
@router.get("/by-channel")
def get_by_channel(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get lead time breakdown by distribution channel with MTO/MTS split"""
    
    from sqlalchemy import func, case
    
    # Channel name mapping
    channel_names = {
        '11': 'Industry',
        '12': 'Over Sea',
        '13': 'Retail',
        '15': 'Project'
    }
    
    # Query grouped by channel and order_type
    query = db.query(
        FactLeadTime.channel_code,
        FactLeadTime.order_type,
        func.count(FactLeadTime.id).label('order_count'),
        func.avg(FactLeadTime.lead_time_days).label('avg_lead_time')
    )\
    .filter(FactLeadTime.channel_code.isnot(None))
    
    # Apply date filter
    if start_date and end_date:
        query = query.filter(
            FactLeadTime.end_date >= start_date,
            FactLeadTime.end_date <= end_date
        )
    
    results = query.group_by(FactLeadTime.channel_code, FactLeadTime.order_type).all()
    
    # Aggregate by channel
    channel_data = {}
    for row in results:
        ch = row.channel_code
        if ch not in channel_data:
            channel_data[ch] = {
                'channel': ch,
                'channel_name': channel_names.get(ch, f'Channel {ch}'),
                'mto_orders': 0,
                'mto_avg_leadtime': None,
                'mto_on_time_pct': None,
                'mts_orders': 0,
                'mts_avg_leadtime': None,
                'mts_on_time_pct': None,
                'total_orders': 0,
                'avg_total_leadtime': None
            }
        
        if row.order_type == 'MTO':
            channel_data[ch]['mto_orders'] = row.order_count
            channel_data[ch]['mto_avg_leadtime'] = round(row.avg_lead_time or 0, 1)
        elif row.order_type == 'MTS':
            channel_data[ch]['mts_orders'] = row.order_count
            channel_data[ch]['mts_avg_leadtime'] = round(row.avg_lead_time or 0, 1)
        
        channel_data[ch]['total_orders'] += row.order_count
    
    # Calculate total averages
    for ch in channel_data:
        total_orders = channel_data[ch]['total_orders']
        if total_orders > 0:
            mto_contrib = (channel_data[ch]['mto_orders'] * (channel_data[ch]['mto_avg_leadtime'] or 0))
            mts_contrib = (channel_data[ch]['mts_orders'] * (channel_data[ch]['mts_avg_leadtime'] or 0))
            channel_data[ch]['avg_total_leadtime'] = round((mto_contrib + mts_contrib) / total_orders, 1)
    
    return list(channel_data.values())

# -----------------------------------------------------------------------------
# 6. Batch Trace
# -----------------------------------------------------------------------------
@router.get("/trace/{batch_id}")
def trace_batch(batch_id: str, db: Session = Depends(get_db)):
    """Trace a specific batch"""
    # 1. Get Summary from FactLeadTime
    # PRIORITY: MTO > MTS > PURCHASE (use CASE for ordering)
    from sqlalchemy import case
    fact = db.query(FactLeadTime)\
        .filter(FactLeadTime.batch == batch_id)\
        .order_by(
            case(
                (FactLeadTime.order_type == 'MTO', 1),
                (FactLeadTime.order_type == 'MTS', 2),
                (FactLeadTime.order_type == 'PURCHASE', 3),
                else_=4
            )
        )\
        .first()
    
    if not fact:
        return None  # Frontend handles null

    # 2. Build Timeline Events
    events = []
    import datetime
    
    # Determine if this is MTO, MTS, or PURCHASE
    is_production = fact.order_type in ['MTO', 'MTS']
    is_mto = fact.order_type == 'MTO'
    
    # Event 1: Preparation (MTO only)
    if is_mto and fact.preparation_days and fact.preparation_days > 0:
        prep_start = fact.start_date - datetime.timedelta(days=int(fact.preparation_days))
        events.append({
            "stage": "Preparation",
            "date": prep_start,
            "duration": fact.preparation_days,
            "status": "COMPLETED",
            "details": "Sales Order to Production Release"
        })

    # Event 2: Production (MTO/MTS) or Transit (PURCHASE)
    if fact.start_date:
        if is_production:
            # Production orders
            events.append({
                "stage": "Production",
                "date": fact.start_date,
                "duration": fact.production_days or 0,
                "status": "COMPLETED",
                "details": f"Manufacturing (Order {fact.order_number})"
            })
        else:
            # Purchase orders
            events.append({
                "stage": "Transit",
                "date": fact.start_date,
                "duration": fact.transit_days or 0,
                "status": "COMPLETED",
                "details": f"In Transit (Order {fact.order_number})"
            })

    # Event 3: Storage (All orders)
    if fact.end_date:
        events.append({
            "stage": "Storage",
            "date": fact.end_date,
            "duration": fact.storage_days or 0,
            "status": "COMPLETED" if fact.storage_days and fact.storage_days > 0 else "IN_PROGRESS",
            "details": "Goods Receipt / Production Finished"
        })

    # Event 4: Delivery (Milestone - only if storage completed)
    if fact.storage_days and fact.storage_days > 0 and fact.end_date:
        delivery_date = fact.end_date + datetime.timedelta(days=int(fact.storage_days))
        events.append({
            "stage": "Delivery",
            "date": delivery_date,
            "duration": 0,  # Milestone
            "status": "COMPLETED",
            "details": "Goods Issue (Delivered)"
        })
    
    # Get material description from FactProduction
    from src.db.models import FactProduction
    material_desc = None
    prod_record = db.query(FactProduction).filter(FactProduction.batch == batch_id).first()
    if prod_record:
        material_desc = prod_record.material_description

    return {
        "batch_id": batch_id,
        "product": fact.material_code,
        "product_description": material_desc,  # Added description
        "plant": fact.plant_code,
        "total_lead_time": fact.lead_time_days,
        "current_status": "Delivered" if (fact.storage_days and fact.storage_days > 0) else "In Storage",
        "events": events
    }


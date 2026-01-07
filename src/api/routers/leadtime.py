"""
Lead-time Analysis API Router

Endpoints for MTO/MTS lead-time tracking and analysis.
Reference: NEXT_STEPS.md Phase 6.1.3
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel
from src.api.deps import get_db, get_current_user


router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================

class LeadTimeKPIs(BaseModel):
    """Lead-time summary KPIs"""
    avg_mto_leadtime: float
    avg_mts_leadtime: float
    on_time_pct: float
    delayed_pct: float
    critical_pct: float
    total_orders: int


class LeadTimeBreakdown(BaseModel):
    """Lead-time breakdown by order category"""
    order_category: str  # MTO/MTS
    avg_preparation: Optional[float]
    avg_production: float
    avg_transit: Optional[float]
    avg_storage: Optional[float]
    avg_delivery: Optional[float]
    avg_total: float
    order_count: int


class LeadTimeDetail(BaseModel):
    """Detailed lead-time data for individual orders"""
    order_number: str
    batch: str
    order_category: str
    material_description: str
    plant_code: str
    preparation_time: Optional[int]
    production_time: Optional[int]
    transit_time: Optional[int]
    storage_time: Optional[int]
    delivery_time: Optional[int]
    total_leadtime: Optional[int]
    leadtime_status: str
    release_date: str
    actual_finish_date: str


class ChannelLeadTime(BaseModel):
    """Lead-time metrics grouped by distribution channel with MTO/MTS breakdown"""
    channel: str
    channel_name: str
    # MTO metrics
    mto_orders: int
    mto_avg_leadtime: Optional[float] = None
    mto_on_time_pct: Optional[float] = None
    # MTS metrics
    mts_orders: int
    mts_avg_leadtime: Optional[float] = None
    mts_on_time_pct: Optional[float] = None
    # Total
    total_orders: int
    avg_total_leadtime: Optional[float] = None



class StageDetail(BaseModel):
    """Individual stage detail for batch tracing"""
    stage_name: str
    start_date: Optional[str]
    end_date: Optional[str]
    duration_days: Optional[int]
    status: str  # "completed", "in_progress", "not_started"


class BatchTrace(BaseModel):
    """Detailed timeline and lead-time breakdown for a specific batch"""
    batch: str
    order_number: str
    material_code: str
    material_description: str
    is_mto: bool
    plant_code: int
    
    # Overall metrics
    total_leadtime_days: Optional[int]
    leadtime_status: str
    
    # Stage-by-stage timeline
    stages: List[StageDetail]
    
    # Key dates
    po_date: Optional[str]
    release_date: Optional[str]
    finish_date: Optional[str]
    receipt_date: Optional[str]
    issue_date: Optional[str]


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/summary", response_model=LeadTimeKPIs)
def get_leadtime_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get lead-time summary KPIs
    
    Returns:
        - Average MTO lead-time (days)
        - Average MTS lead-time (days)
        - On-time percentage
        - Delayed percentage
        - Critical percentage
        - Total orders with lead-time data
    """
    try:
        result = db.execute(text("""
            SELECT 
                AVG(CASE WHEN is_mto = TRUE THEN total_leadtime_days END) as avg_mto,
                AVG(CASE WHEN is_mto = FALSE THEN total_leadtime_days END) as avg_mts,
                COUNT(CASE WHEN leadtime_status = 'ON_TIME' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as on_time_pct,
                COUNT(CASE WHEN leadtime_status = 'DELAYED' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as delayed_pct,
                COUNT(CASE WHEN leadtime_status = 'CRITICAL' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as critical_pct,
                COUNT(*) as total_orders
            FROM fact_production
            WHERE total_leadtime_days IS NOT NULL
        """)).fetchone()
        
        if not result:
            return LeadTimeKPIs(
                avg_mto_leadtime=0.0,
                avg_mts_leadtime=0.0,
                on_time_pct=0.0,
                delayed_pct=0.0,
                critical_pct=0.0,
                total_orders=0
            )
        
        return LeadTimeKPIs(
            avg_mto_leadtime=float(result[0] or 0),
            avg_mts_leadtime=float(result[1] or 0),
            on_time_pct=float(result[2] or 0),
            delayed_pct=float(result[3] or 0),
            critical_pct=float(result[4] or 0),
            total_orders=int(result[5] or 0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/breakdown", response_model=List[LeadTimeBreakdown])
def get_leadtime_breakdown(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get lead-time breakdown by MTO/MTS category
    
    Returns:
        List of breakdowns showing average time for each stage:
        - MTO: 5 stages (Preparation, Production, Transit, Storage, Delivery)
        - MTS: 3 stages (Production, Transit, Storage)
    """
    try:
        results = db.execute(text("""
            SELECT 
                CASE WHEN is_mto = TRUE THEN 'MTO' ELSE 'MTS' END as order_category,
                AVG(prep_time_days) as avg_prep,
                AVG(production_time_days) as avg_prod,
                AVG(transit_time_days) as avg_transit,
                AVG(storage_time_days) as avg_storage,
                AVG(delivery_time_days) as avg_delivery,
                AVG(total_leadtime_days) as avg_total,
                COUNT(*) as order_count
            FROM fact_production
            WHERE total_leadtime_days IS NOT NULL
            GROUP BY is_mto
            ORDER BY is_mto DESC
        """)).fetchall()
        
        return [
            LeadTimeBreakdown(
                order_category=row[0],
                avg_preparation=float(row[1]) if row[1] else None,
                avg_production=float(row[2] or 0),
                avg_transit=float(row[3]) if row[3] else None,
                avg_storage=float(row[4]) if row[4] else None,
                avg_delivery=float(row[5]) if row[5] else None,
                avg_total=float(row[6] or 0),
                order_count=int(row[7])
            )
            for row in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/orders", response_model=List[LeadTimeDetail])
def get_leadtime_orders(
    limit: int = Query(100, le=1000, description="Maximum number of orders to return"),
    status_filter: Optional[str] = Query(None, description="Filter by status: ON_TIME, DELAYED, CRITICAL"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get detailed lead-time data for individual orders
    
    Args:
        limit: Maximum number of orders (default 100, max 1000)
        status_filter: Optional filter by leadtime_status
    
    Returns:
        List of orders with complete lead-time breakdown
    """
    try:
        # Build query with optional status filter
        where_clause = "WHERE total_leadtime_days IS NOT NULL"
        if status_filter:
            where_clause += f" AND leadtime_status = '{status_filter}'"
        
        query = f"""
            SELECT 
                order_number,
                batch,
                CASE WHEN is_mto = TRUE THEN 'MTO' ELSE 'MTS' END as category,
                material_description,
                plant_code,
                prep_time_days,
                production_time_days,
                transit_time_days,
                storage_time_days,
                delivery_time_days,
                total_leadtime_days,
                leadtime_status,
                release_date,
                actual_finish_date
            FROM fact_production
            {where_clause}
            ORDER BY release_date DESC
            LIMIT {limit}
        """
        
        results = db.execute(text(query)).fetchall()
        
        return [
            LeadTimeDetail(
                order_number=row[0],
                batch=row[1],
                order_category=row[2],
                material_description=row[3],
                plant_code=str(row[4]),
                preparation_time=row[5],
                production_time=row[6],
                transit_time=row[7],
                storage_time=row[8],
                delivery_time=row[9],
                total_leadtime=row[10],
                leadtime_status=row[11],
                release_date=str(row[12]) if row[12] else '',
                actual_finish_date=str(row[13]) if row[13] else ''
            )
            for row in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/by-channel", response_model=List[ChannelLeadTime])
def get_leadtime_by_channel(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get lead-time metrics grouped by distribution channel (11/13/15) and order type (MTO/MTS)
    
    Returns:
        List of channel metrics with:
        - Distribution channel (11: Industry, 12: Over Sea, 13: Retail, 15: Project)
        - Order type (MTO/MTS)
        - Order count
        - Average times per stage
        - On-time/Delayed/Critical percentages
    """
    try:
        results = db.execute(text("""
            SELECT 
                CAST(COALESCE(rz.dist_channel, '99') AS TEXT) as channel,
                CASE 
                    WHEN COALESCE(rz.dist_channel, '99') = '11' THEN 'Industry'
                    WHEN COALESCE(rz.dist_channel, '99') = '12' THEN 'Over Sea'
                    WHEN COALESCE(rz.dist_channel, '99') = '13' THEN 'Retail'
                    WHEN COALESCE(rz.dist_channel, '99') = '15' THEN 'Project'
                    ELSE 'No Channel Data'
                END as channel_name,
                -- MTO metrics
                COUNT(CASE WHEN fp.is_mto = TRUE THEN 1 END) as mto_orders,
                ROUND(AVG(CASE WHEN fp.is_mto = TRUE THEN fp.total_leadtime_days END), 1) as mto_avg_leadtime,
                ROUND(COUNT(CASE WHEN fp.is_mto = TRUE AND fp.leadtime_status='ON_TIME' THEN 1 END)*100.0/
                      NULLIF(COUNT(CASE WHEN fp.is_mto = TRUE THEN 1 END), 0), 1) as mto_on_time_pct,
                -- MTS metrics
                COUNT(CASE WHEN fp.is_mto = FALSE THEN 1 END) as mts_orders,
                ROUND(AVG(CASE WHEN fp.is_mto = FALSE THEN fp.total_leadtime_days END), 1) as mts_avg_leadtime,
                ROUND(COUNT(CASE WHEN fp.is_mto = FALSE AND fp.leadtime_status='ON_TIME' THEN 1 END)*100.0/
                      NULLIF(COUNT(CASE WHEN fp.is_mto = FALSE THEN 1 END), 0), 1) as mts_on_time_pct,
                -- Total
                COUNT(*) as total_orders,
                ROUND(AVG(fp.total_leadtime_days), 1) as avg_total_leadtime
            FROM fact_production fp
            LEFT JOIN raw_zrsd006 rz ON fp.material_code = rz.material
            WHERE fp.total_leadtime_days IS NOT NULL
            GROUP BY COALESCE(rz.dist_channel, '99')
            ORDER BY COALESCE(rz.dist_channel, '99')
        """)).fetchall()
        
        return [
            ChannelLeadTime(
                channel=row[0],
                channel_name=row[1],
                mto_orders=int(row[2]),
                mto_avg_leadtime=float(row[3]) if row[3] else None,
                mto_on_time_pct=float(row[4]) if row[4] else None,
                mts_orders=int(row[5]),
                mts_avg_leadtime=float(row[6]) if row[6] else None,
                mts_on_time_pct=float(row[7]) if row[7] else None,
                total_orders=int(row[8]),
                avg_total_leadtime=float(row[9]) if row[9] else None
            )
            for row in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/trace/{batch}", response_model=BatchTrace)
def trace_batch(
    batch: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get detailed timeline and lead-time breakdown for a specific batch
    
    Args:
        batch: Batch number to trace
    
    Returns:
        Complete timeline with stage-by-stage breakdown and key dates
    """
    try:
        # Get production order data
        result = db.execute(text("""
            SELECT 
                fp.batch,
                fp.order_number,
                fp.material_code,
                fp.material_description,
                fp.is_mto,
                fp.plant_code,
                fp.total_leadtime_days,
                fp.leadtime_status,
                fp.release_date,
                fp.actual_finish_date,
                fp.prep_time_days,
                fp.production_time_days,
                fp.transit_time_days,
                fp.storage_time_days,
                MIN(CASE WHEN fi.mvt_type = 101 THEN fi.posting_date END) as receipt_date,
                MIN(CASE WHEN fi.mvt_type = 601 THEN fi.posting_date END) as issue_date
            FROM fact_production fp
            LEFT JOIN fact_inventory fi ON fp.batch = fi.batch AND fi.mvt_type IN (101, 601)
            WHERE fp.batch = :batch
            GROUP BY fp.batch, fp.order_number, fp.material_code, fp.material_description, 
                     fp.is_mto, fp.plant_code, fp.total_leadtime_days, fp.leadtime_status,
                     fp.release_date, fp.actual_finish_date, fp.prep_time_days, 
                     fp.production_time_days, fp.transit_time_days, fp.storage_time_days
        """), {"batch": batch}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Batch {batch} not found")
        
        # Build stages list
        stages = []
        is_mto = result[4]
        
        # Stage 1: Preparation (MTO only)
        if is_mto and result[10]:  # prep_time_days
            stages.append(StageDetail(
                stage_name="Preparation",
                start_date=None,  # PO date not available in current query
                end_date=str(result[8]) if result[8] else None,  # release_date
                duration_days=result[10],
                status="completed" if result[10] else "not_started"
            ))
        
        # Stage 2: Production
        if result[11]:  # production_time_days
            stages.append(StageDetail(
                stage_name="Production",
                start_date=str(result[8]) if result[8] else None,  # release_date
                end_date=str(result[9]) if result[9] else None,  # finish_date
                duration_days=result[11],
                status="completed" if result[11] else "not_started"
            ))
        
        # Stage 3: Transit
        if result[12] is not None:  # transit_time_days
            stages.append(StageDetail(
                stage_name="Transit",
                start_date=str(result[9]) if result[9] else None,  # finish_date
                end_date=str(result[14]) if result[14] else None,  # receipt_date
                duration_days=result[12],
                status="completed" if result[12] is not None else "not_started"
            ))
        
        # Stage 4: Storage
        if result[13] is not None:  # storage_time_days
            stages.append(StageDetail(
                stage_name="Storage",
                start_date=str(result[14]) if result[14] else None,  # receipt_date
                end_date=str(result[15]) if result[15] else None,  # issue_date
                duration_days=result[13],
                status="completed" if result[13] is not None else "not_started"
            ))
        
        return BatchTrace(
            batch=result[0],
            order_number=result[1],
            material_code=result[2],
            material_description=result[3],
            is_mto=result[4],
            plant_code=result[5],
            total_leadtime_days=result[6],
            leadtime_status=result[7],
            stages=stages,
            po_date=None,  # Not available in current data
            release_date=str(result[8]) if result[8] else None,
            finish_date=str(result[9]) if result[9] else None,
            receipt_date=str(result[14]) if result[14] else None,
            issue_date=str(result[15]) if result[15] else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

"""
AR Aging (Công Nợ) API Router

Provides AR collection summary by division and detailed aging analysis.
Data resets monthly from zrfi005 daily uploads.

Follows CLAUDE.md: KISS, DRY, file <200 lines.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from src.api.deps import get_db, get_current_user


router = APIRouter(prefix="/ar-aging", tags=["AR Aging"])


# ========== Pydantic Models ==========

class ARCollectionSummary(BaseModel):
    """AR Collection Summary by Division"""
    division: str
    dist_channel: str
    total_target: float
    total_realization: float
    collection_rate_pct: int
    report_date: Optional[str] = None


class ARCollectionTotal(BaseModel):
    """Grand total AR collection"""
    total_target: float
    total_realization: float
    collection_rate_pct: int
    report_date: Optional[str]
    divisions: list[ARCollectionSummary]


class ARAgingDetail(BaseModel):
    """AR Aging detail per customer"""
    division: str
    salesman_name: Optional[str]
    customer_name: str
    total_target: float
    total_realization: float
    collection_rate_pct: int
    not_due: float
    target_1_30: float
    target_31_60: float
    target_61_90: float
    target_91_120: float
    target_121_180: float
    target_over_180: float
    risk_level: str


class ARAgingBucket(BaseModel):
    """AR amounts by aging bucket"""
    bucket: str
    target_amount: float
    realization_amount: float


class SnapshotDate(BaseModel):
    """Available snapshot date"""
    snapshot_date: str
    row_count: int


# ========== Endpoints ==========

@router.get("/snapshots", response_model=list[SnapshotDate])
async def get_available_snapshots(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get list of available snapshot dates from fact_ar_aging.
    
    Returns list of dates with row counts, ordered by date descending.
    Used by frontend to populate snapshot date dropdown.
    """
    from src.db.models import FactArAging
    from sqlalchemy import func
    
    results = db.query(
        FactArAging.snapshot_date,
        func.count(FactArAging.id).label('row_count')
    ).filter(
        FactArAging.snapshot_date != None
    ).group_by(
        FactArAging.snapshot_date
    ).order_by(
        FactArAging.snapshot_date.desc()
    ).all()
    
    return [
        SnapshotDate(
            snapshot_date=r[0].strftime('%Y-%m-%d'),
            row_count=r[1]
        )
        for r in results
    ]

@router.get("/summary", response_model=ARCollectionTotal)
async def get_ar_collection_summary(
    snapshot_date: Optional[str] = Query(None, description="Snapshot date (YYYY-MM-DD). If not provided, uses latest."),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get AR Collection Summary by Division for a specific snapshot date.
    
    Args:
        snapshot_date: Optional date filter (YYYY-MM-DD). Defaults to latest snapshot.
    
    Returns:
        Industry, Retails, Project breakdown with collection rates
    """
    # If no date provided, get latest snapshot and rebuild fact table
    if not snapshot_date:
        from src.db.models import RawZrfi005
        from sqlalchemy import func
        from src.etl.transform import Transformer
        
        latest = db.query(func.max(RawZrfi005.snapshot_date)).filter(
            RawZrfi005.snapshot_date != None
        ).scalar()
        
        if latest:
            # Rebuild fact table with latest snapshot
            transformer = Transformer(db)
            transformer.transform_zrfi005()
            snapshot_date = latest.strftime('%Y-%m-%d')
    else:
        # Rebuild fact table with specified snapshot date
        from src.etl.transform import Transformer
        transformer = Transformer(db)
        transformer.transform_zrfi005(target_date=snapshot_date)
    
    # Query fact_ar_aging directly with snapshot filter instead of view
    results = db.execute(text("""
        SELECT 
            CASE dist_channel
                WHEN '11' THEN 'Industry'
                WHEN '13' THEN 'Retails'
                WHEN '15' THEN 'Project'
                ELSE 'Other'
            END as division,
            dist_channel,
            SUM(COALESCE(total_target, 0)) as total_target,
            SUM(COALESCE(total_realization, 0)) as total_realization,
            CASE 
                WHEN SUM(COALESCE(total_target, 0)) > 0 
                THEN ROUND((SUM(COALESCE(total_realization, 0)) / SUM(total_target) * 100)::numeric, 0)
                ELSE 0 
            END as collection_rate_pct,
            MAX(report_date)::text as report_date
        FROM fact_ar_aging
        WHERE snapshot_date = :snapshot_date
        GROUP BY dist_channel
        ORDER BY 
            CASE dist_channel
                WHEN '11' THEN 1
                WHEN '13' THEN 2
                WHEN '15' THEN 3
                ELSE 4
            END
    """), {"snapshot_date": snapshot_date}).fetchall()
    
    divisions = [ARCollectionSummary(
        division=r[0], dist_channel=r[1],
        total_target=float(r[2] or 0),
        total_realization=float(r[3] or 0),
        collection_rate_pct=int(r[4] or 0),
        report_date=r[5]
    ) for r in results]
    
    total_target = sum(d.total_target for d in divisions)
    total_real = sum(d.total_realization for d in divisions)
    rate = round(total_real / total_target * 100) if total_target > 0 else 0
    
    return ARCollectionTotal(
        total_target=total_target,
        total_realization=total_real,
        collection_rate_pct=rate,
        report_date=divisions[0].report_date if divisions else None,
        divisions=divisions
    )


@router.get("/by-bucket", response_model=list[ARAgingBucket])
async def get_ar_by_bucket(
    division: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get AR amounts grouped by aging bucket (7 buckets)"""
    where = ""
    params = {}
    if division:
        where = """WHERE CASE dist_channel
            WHEN '11' THEN 'Industry'
            WHEN '13' THEN 'Retails'
            WHEN '15' THEN 'Project' ELSE 'Other'
        END = :division"""
        params["division"] = division
    
    r = db.execute(text(f"""
        SELECT 
            SUM(COALESCE(realization_not_due, 0)),
            SUM(COALESCE(target_1_30, 0)), SUM(COALESCE(target_31_60, 0)),
            SUM(COALESCE(target_61_90, 0)), SUM(COALESCE(target_91_120, 0)),
            SUM(COALESCE(target_121_180, 0)), SUM(COALESCE(target_over_180, 0)),
            SUM(COALESCE(realization_1_30, 0)), SUM(COALESCE(realization_31_60, 0)),
            SUM(COALESCE(realization_61_90, 0)), SUM(COALESCE(realization_91_120, 0)),
            SUM(COALESCE(realization_121_180, 0)), SUM(COALESCE(realization_over_180, 0))
        FROM fact_ar_aging {where}
    """), params).fetchone()
    
    if not r:
        return []
    
    # Not Due: bills not yet overdue (use realization_not_due for both target and realization)
    # Other buckets: overdue amounts by aging period
    return [
        ARAgingBucket(bucket="Not Due", target_amount=float(r[0] or 0), realization_amount=float(r[0] or 0)),
        ARAgingBucket(bucket="1-30 Days", target_amount=float(r[1] or 0), realization_amount=float(r[7] or 0)),
        ARAgingBucket(bucket="31-60 Days", target_amount=float(r[2] or 0), realization_amount=float(r[8] or 0)),
        ARAgingBucket(bucket="61-90 Days", target_amount=float(r[3] or 0), realization_amount=float(r[9] or 0)),
        ARAgingBucket(bucket="91-120 Days", target_amount=float(r[4] or 0), realization_amount=float(r[10] or 0)),
        ARAgingBucket(bucket="121-180 Days", target_amount=float(r[5] or 0), realization_amount=float(r[11] or 0)),
        ARAgingBucket(bucket=">180 Days", target_amount=float(r[6] or 0), realization_amount=float(r[12] or 0)),
    ]


@router.get("/customers", response_model=list[ARAgingDetail])
async def get_ar_by_customer(
    division: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    salesman: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get AR aging details per customer with risk levels"""
    results = db.execute(text("""
        SELECT division, salesman_name, customer_name, total_target,
               total_realization, collection_rate_pct, not_due, target_1_30,
               target_31_60, target_61_90, target_91_120, target_121_180,
               target_over_180, risk_level
        FROM view_ar_aging_detail
        WHERE (:division IS NULL OR division = :division)
          AND (:risk IS NULL OR risk_level = :risk)
          AND (:salesman IS NULL OR salesman_name ILIKE '%' || :salesman || '%')
        ORDER BY total_target DESC
        LIMIT :limit
    """), {
        "division": division, "risk": risk_level,
        "salesman": salesman, "limit": limit
    }).fetchall()
    
    return [ARAgingDetail(
        division=r[0], salesman_name=r[1], customer_name=r[2],
        total_target=float(r[3] or 0), total_realization=float(r[4] or 0),
        collection_rate_pct=int(r[5] or 0), not_due=float(r[6] or 0),
        target_1_30=float(r[7] or 0), target_31_60=float(r[8] or 0),
        target_61_90=float(r[9] or 0), target_91_120=float(r[10] or 0),
        target_121_180=float(r[11] or 0), target_over_180=float(r[12] or 0),
        risk_level=r[13]
    ) for r in results]

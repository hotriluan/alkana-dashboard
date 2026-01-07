"""
Production Yield Dashboard API Router

Tracks production efficiency and material yield performance.
Follows CLAUDE.md: KISS, DRY, file <200 lines.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from src.api.deps import get_db, get_current_user


router = APIRouter(prefix="/yield", tags=["Production Yield"])


# ========== Pydantic Models ==========

class YieldRecord(BaseModel):
    """Production yield record"""
    plant_code: str
    material_code: str
    material_description: str
    total_input_qty: float
    total_output_qty: float
    yield_percentage: float
    scrap_qty: float
    uom: str


class YieldKPIs(BaseModel):
    """Yield dashboard KPIs"""
    avg_yield_rate: float
    total_input: float
    total_output: float
    total_scrap: float


# ========== Endpoints ==========

@router.get("/summary", response_model=YieldKPIs)
async def get_yield_summary(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get P02→P01 yield summary KPIs with optional date range filter"""
    query = """
        SELECT 
            COALESCE(AVG(yield_pct), 0) as avg_yield,
            COALESCE(SUM(p02_consumed_kg), 0) as total_input,
            COALESCE(SUM(p01_produced_kg), 0) as total_output,
            COALESCE(SUM(loss_kg), 0) as total_scrap
        FROM fact_p02_p01_yield
    """
    params = {}
    
    if start_date and end_date:
        query += " WHERE production_date BETWEEN :start_date AND :end_date"
        params["start_date"] = start_date
        params["end_date"] = end_date
    
    result = db.execute(text(query), params).fetchone()
    
    return YieldKPIs(
        avg_yield_rate=round(float(result[0] or 0), 1),
        total_input=float(result[1] or 0),
        total_output=float(result[2] or 0),
        total_scrap=float(result[3] or 0)
    )


@router.get("/records", response_model=list[YieldRecord])
async def get_yield_records(
    plant_code: Optional[str] = Query(None),
    material_code: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get P02→P01 yield records with optional filters"""
    where_clauses = []
    params = {"limit": limit}
    
    # Note: P02→P01 yield doesn't have plant filter (always 1201→1401)
    # Keeping parameter for API compatibility
    
    if material_code:
        where_clauses.append("(p02_material_code = :material_code OR p01_material_code = :material_code)")
        params["material_code"] = material_code
    
    if start_date and end_date:
        where_clauses.append("production_date BETWEEN :start_date AND :end_date")
        params["start_date"] = start_date
        params["end_date"] = end_date
    
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    results = db.execute(text(f"""
        SELECT 
            '1201' as plant_code,
            p01_material_code as material_code,
            p01_material_desc as material_description,
            p02_consumed_kg as total_input_qty,
            p01_produced_kg as total_output_qty,
            yield_pct as yield_percentage,
            loss_kg as scrap_qty,
            'KG' as uom
        FROM fact_p02_p01_yield
        {where_sql}
        ORDER BY yield_pct ASC
        LIMIT :limit
    """), params).fetchall()
    
    return [YieldRecord(
        plant_code=str(r[0]) if r[0] else '',
        material_code=str(r[1]) if r[1] else '',
        material_description=str(r[2]) if r[2] else '',
        total_input_qty=float(r[3] or 0),
        total_output_qty=float(r[4] or 0),
        yield_percentage=float(r[5] or 0),
        scrap_qty=float(r[6] or 0),
        uom=str(r[7]) if r[7] else ''
    ) for r in results]


@router.get("/by-plant", response_model=list[dict])
async def get_yield_by_plant(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get P02→P01 yield aggregated by plant (always 1201)"""
    results = db.execute(text("""
        SELECT 
            '1201' as plant_code,
            COUNT(*) as material_count,
            AVG(yield_pct) as avg_yield,
            SUM(p02_consumed_kg) as total_input,
            SUM(p01_produced_kg) as total_output,
            SUM(loss_kg) as total_scrap
        FROM fact_p02_p01_yield
        GROUP BY plant_code
        ORDER BY avg_yield ASC
    """)).fetchall()
    
    return [
        {
            "plant_code": str(r[0]),
            "material_count": int(r[1] or 0),
            "avg_yield": round(float(r[2] or 0), 1),
            "total_input": float(r[3] or 0),
            "total_output": float(r[4] or 0),
            "total_scrap": float(r[5] or 0)
        }
        for r in results
    ]


@router.get("/top-performers", response_model=list[YieldRecord])
async def get_top_performers(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get top performing P02→P01 batches by yield"""
    results = db.execute(text("""
        SELECT 
            '1201' as plant_code,
            p01_material_code as material_code,
            p01_material_desc as material_description,
            p02_consumed_kg as total_input_qty,
            p01_produced_kg as total_output_qty,
            yield_pct as yield_percentage,
            loss_kg as scrap_qty,
            'KG' as uom
        FROM fact_p02_p01_yield
        WHERE yield_pct > 0 AND yield_pct <= 100
        ORDER BY yield_pct DESC
        LIMIT :limit
    """), {"limit": limit}).fetchall()
    
    return [YieldRecord(
        plant_code=str(r[0]) if r[0] else '',
        material_code=str(r[1]) if r[1] else '',
        material_description=str(r[2]) if r[2] else '',
        total_input_qty=float(r[3] or 0),
        total_output_qty=float(r[4] or 0),
        yield_percentage=float(r[5] or 0),
        scrap_qty=float(r[6] or 0),
        uom=str(r[7]) if r[7] else ''
    ) for r in results]

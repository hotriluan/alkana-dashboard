"""
Inventory Dashboard API Router

Provides current inventory levels and movements analysis.
Follows CLAUDE.md: KISS, DRY, file <200 lines.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from src.api.deps import get_db, get_current_user


router = APIRouter(prefix="/inventory", tags=["Inventory"])


# ========== Pydantic Models ==========

class InventoryItem(BaseModel):
    """Current inventory snapshot"""
    plant_code: str
    material_code: str
    material_description: str
    current_qty: float
    current_qty_kg: float
    uom: str
    last_movement: str


class InventoryKPI(BaseModel):
    """Inventory KPIs"""
    total_items: int
    total_materials: int
    total_plants: int
    total_qty_kg: float


# ========== Endpoints ==========

@router.get("/summary", response_model=InventoryKPI)
async def get_inventory_summary(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get inventory summary KPIs with optional date range filter"""
    query = """
        SELECT 
            COUNT(*) as total_items,
            COUNT(DISTINCT material_code) as total_materials,
            COUNT(DISTINCT plant_code) as total_plants,
            SUM(COALESCE(current_qty_kg, 0)) as total_qty_kg
        FROM view_inventory_current
    """
    params = {}
    
    if start_date and end_date:
        query += " WHERE last_movement BETWEEN :start_date AND :end_date"
        params["start_date"] = start_date
        params["end_date"] = end_date
    
    result = db.execute(text(query), params).fetchone()
    
    return InventoryKPI(
        total_items=int(result[0] or 0),
        total_materials=int(result[1] or 0),
        total_plants=int(result[2] or 0),
        total_qty_kg=float(result[3] or 0)
    )


@router.get("/items", response_model=list[InventoryItem])
async def get_inventory_items(
    plant_code: Optional[str] = Query(None),
    material_code: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get inventory items with optional filters"""
    where_clauses = []
    params = {"limit": limit}
    
    if plant_code:
        where_clauses.append("plant_code = :plant_code")
        params["plant_code"] = plant_code
    
    if material_code:
        where_clauses.append("material_code ILIKE '%' || :material_code || '%'")
        params["material_code"] = material_code
    
    if start_date and end_date:
        where_clauses.append("last_movement BETWEEN :start_date AND :end_date")
        params["start_date"] = start_date
        params["end_date"] = end_date
    
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    results = db.execute(text(f"""
        SELECT 
            plant_code, material_code, material_description,
            current_qty, current_qty_kg, uom, last_movement::text
        FROM view_inventory_current
        {where_sql}
        ORDER BY current_qty_kg DESC
        LIMIT :limit
    """), params).fetchall()
    
    return [InventoryItem(
        plant_code=str(r[0]) if r[0] else '',
        material_code=str(r[1]) if r[1] else '',
        material_description=str(r[2]) if r[2] else '',
        current_qty=float(r[3] or 0),
        current_qty_kg=float(r[4] or 0),
        uom=str(r[5]) if r[5] else '',
        last_movement=str(r[6]) if r[6] else ''
    ) for r in results]


@router.get("/by-plant", response_model=list[dict])
async def get_inventory_by_plant(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get inventory aggregated by plant"""
    results = db.execute(text("""
        SELECT 
            plant_code,
            COUNT(*) as item_count,
            SUM(current_qty_kg) as total_kg
        FROM view_inventory_current
        GROUP BY plant_code
        ORDER BY total_kg DESC
    """)).fetchall()
    
    return [
        {
            "plant_code": str(r[0]) if r[0] else '',
            "item_count": int(r[1] or 0),
            "total_kg": float(r[2] or 0)
        }
        for r in results
    ]

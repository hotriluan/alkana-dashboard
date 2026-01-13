"""
Yield V2 API Router - Production Variance Analysis (Isolated)

Endpoints for V2 Production Performance data from zrpp062.XLSX.
This module is ISOLATED from legacy yield tracking - uses new tables only.

Tables:
- raw_zrpp062: Staging table with all columns from Excel
- fact_production_performance_v2: Analytical fact table

Reference: ARCHITECTURAL DIRECTIVE Production Yield V2.1
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import List, Optional
from pydantic import BaseModel
from decimal import Decimal
from datetime import date

from src.api.deps import get_db, get_current_user


router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================

class MaterialVariance(BaseModel):
    """Variance metrics for a single material"""
    material_code: str
    material_description: Optional[str] = None
    total_output_kg: float
    total_input_kg: float
    total_loss_kg: float
    avg_loss_pct: float
    order_count: int
    
    class Config:
        from_attributes = True


class VarianceSummary(BaseModel):
    """Summary KPIs for variance analysis"""
    total_orders: int
    total_output_kg: float
    total_input_kg: float
    total_loss_kg: float
    avg_loss_pct: float
    materials_with_high_loss: int  # Loss % > 2.0
    

class OrderVarianceDetail(BaseModel):
    """Detailed variance data for a single order"""
    process_order_id: str
    batch_id: Optional[str] = None
    material_code: Optional[str] = None
    material_description: Optional[str] = None
    parent_order_id: Optional[str] = None
    output_actual_kg: Optional[float] = None
    input_actual_kg: Optional[float] = None
    loss_kg: Optional[float] = None
    loss_pct: Optional[float] = None
    sg_theoretical: Optional[float] = None
    sg_actual: Optional[float] = None
    
    class Config:
        from_attributes = True


class ProductGroupVariance(BaseModel):
    """Variance metrics grouped by product hierarchy"""
    product_group: str
    total_output_kg: float
    total_loss_kg: float
    avg_loss_pct: float
    order_count: int


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/variance", response_model=List[MaterialVariance])
async def get_variance_by_material(
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100, description="Max materials to return"),
    min_loss_pct: Optional[float] = Query(default=None, description="Filter materials with loss% >= this value"),
    product_group: Optional[str] = Query(default=None, description="Filter by product group"),
    # user = Depends(get_current_user)  # Uncomment when auth is required
):
    """
    Get variance analysis grouped by material.
    
    Returns Top N materials with highest total loss (in KG).
    Use for variance analysis dashboard - highlights materials with production issues.
    
    Query Logic:
    ```sql
    SELECT 
        material_code,
        SUM(output_actual_kg) as total_output,
        SUM(loss_kg) as total_loss_kg,
        AVG(loss_pct) as avg_loss_pct
    FROM fact_production_performance_v2
    GROUP BY material_code
    ORDER BY total_loss_kg DESC;
    ```
    """
    sql = """
    SELECT 
        material_code,
        MAX(material_description) as material_description,
        COALESCE(SUM(output_actual_kg), 0) as total_output_kg,
        COALESCE(SUM(input_actual_kg), 0) as total_input_kg,
        COALESCE(SUM(loss_kg), 0) as total_loss_kg,
        COALESCE(AVG(loss_pct), 0) as avg_loss_pct,
        COUNT(*) as order_count
    FROM fact_production_performance_v2
    WHERE material_code IS NOT NULL
    """
    
    params = {}
    
    if product_group:
        sql += " AND (product_group_1 = :product_group OR product_group_2 = :product_group)"
        params['product_group'] = product_group
    
    sql += """
    GROUP BY material_code
    """
    
    if min_loss_pct is not None:
        sql += " HAVING AVG(loss_pct) >= :min_loss_pct"
        params['min_loss_pct'] = min_loss_pct
    
    sql += """
    ORDER BY total_loss_kg DESC
    LIMIT :limit
    """
    params['limit'] = limit
    
    result = db.execute(text(sql), params)
    rows = result.fetchall()
    
    return [
        MaterialVariance(
            material_code=row.material_code or "Unknown",
            material_description=row.material_description,
            total_output_kg=float(row.total_output_kg or 0),
            total_input_kg=float(row.total_input_kg or 0),
            total_loss_kg=float(row.total_loss_kg or 0),
            avg_loss_pct=float(row.avg_loss_pct or 0),
            order_count=row.order_count
        )
        for row in rows
    ]


@router.get("/variance/summary", response_model=VarianceSummary)
async def get_variance_summary(
    db: Session = Depends(get_db),
    product_group: Optional[str] = Query(default=None, description="Filter by product group"),
    # user = Depends(get_current_user)
):
    """
    Get overall variance summary KPIs.
    
    Returns aggregate metrics across all materials for executive dashboard.
    """
    sql = """
    SELECT 
        COUNT(*) as total_orders,
        COALESCE(SUM(output_actual_kg), 0) as total_output_kg,
        COALESCE(SUM(input_actual_kg), 0) as total_input_kg,
        COALESCE(SUM(loss_kg), 0) as total_loss_kg,
        COALESCE(AVG(loss_pct), 0) as avg_loss_pct
    FROM fact_production_performance_v2
    WHERE 1=1
    """
    
    params = {}
    if product_group:
        sql += " AND (product_group_1 = :product_group OR product_group_2 = :product_group)"
        params['product_group'] = product_group
    
    result = db.execute(text(sql), params)
    row = result.fetchone()
    
    # Count materials with high loss
    high_loss_sql = """
    SELECT COUNT(DISTINCT material_code) as cnt
    FROM fact_production_performance_v2
    WHERE loss_pct > 2.0
    """
    if product_group:
        high_loss_sql += " AND (product_group_1 = :product_group OR product_group_2 = :product_group)"
    
    high_loss_result = db.execute(text(high_loss_sql), params)
    high_loss_count = high_loss_result.scalar() or 0
    
    return VarianceSummary(
        total_orders=row.total_orders or 0,
        total_output_kg=float(row.total_output_kg or 0),
        total_input_kg=float(row.total_input_kg or 0),
        total_loss_kg=float(row.total_loss_kg or 0),
        avg_loss_pct=float(row.avg_loss_pct or 0),
        materials_with_high_loss=high_loss_count
    )


@router.get("/variance/details", response_model=List[OrderVarianceDetail])
async def get_variance_details(
    db: Session = Depends(get_db),
    material_code: Optional[str] = Query(default=None, description="Filter by material code"),
    min_loss_pct: Optional[float] = Query(default=None, description="Filter orders with loss% >= this value"),
    limit: int = Query(default=50, ge=1, le=500, description="Max orders to return"),
    # user = Depends(get_current_user)
):
    """
    Get detailed variance data at order level.
    
    Returns individual order records for drill-down analysis.
    Useful when investigating specific materials or high-loss orders.
    """
    sql = """
    SELECT 
        process_order_id,
        batch_id,
        material_code,
        material_description,
        parent_order_id,
        output_actual_kg,
        input_actual_kg,
        loss_kg,
        loss_pct,
        sg_theoretical,
        sg_actual
    FROM fact_production_performance_v2
    WHERE 1=1
    """
    
    params = {}
    
    if material_code:
        sql += " AND material_code = :material_code"
        params['material_code'] = material_code
    
    if min_loss_pct is not None:
        sql += " AND loss_pct >= :min_loss_pct"
        params['min_loss_pct'] = min_loss_pct
    
    sql += """
    ORDER BY loss_kg DESC NULLS LAST
    LIMIT :limit
    """
    params['limit'] = limit
    
    result = db.execute(text(sql), params)
    rows = result.fetchall()
    
    return [
        OrderVarianceDetail(
            process_order_id=row.process_order_id,
            batch_id=row.batch_id,
            material_code=row.material_code,
            material_description=row.material_description,
            parent_order_id=row.parent_order_id,
            output_actual_kg=float(row.output_actual_kg) if row.output_actual_kg else None,
            input_actual_kg=float(row.input_actual_kg) if row.input_actual_kg else None,
            loss_kg=float(row.loss_kg) if row.loss_kg else None,
            loss_pct=float(row.loss_pct) if row.loss_pct else None,
            sg_theoretical=float(row.sg_theoretical) if row.sg_theoretical else None,
            sg_actual=float(row.sg_actual) if row.sg_actual else None,
        )
        for row in rows
    ]


@router.get("/variance/by-group", response_model=List[ProductGroupVariance])
async def get_variance_by_product_group(
    db: Session = Depends(get_db),
    group_level: int = Query(default=1, ge=1, le=2, description="Product group level (1 or 2)"),
    # user = Depends(get_current_user)
):
    """
    Get variance analysis grouped by product hierarchy.
    
    Useful for identifying which product lines have the most production issues.
    """
    group_column = "product_group_1" if group_level == 1 else "product_group_2"
    
    sql = f"""
    SELECT 
        {group_column} as product_group,
        COALESCE(SUM(output_actual_kg), 0) as total_output_kg,
        COALESCE(SUM(loss_kg), 0) as total_loss_kg,
        COALESCE(AVG(loss_pct), 0) as avg_loss_pct,
        COUNT(*) as order_count
    FROM fact_production_performance_v2
    WHERE {group_column} IS NOT NULL
    GROUP BY {group_column}
    ORDER BY total_loss_kg DESC
    """
    
    result = db.execute(text(sql))
    rows = result.fetchall()
    
    return [
        ProductGroupVariance(
            product_group=row.product_group or "Unknown",
            total_output_kg=float(row.total_output_kg or 0),
            total_loss_kg=float(row.total_loss_kg or 0),
            avg_loss_pct=float(row.avg_loss_pct or 0),
            order_count=row.order_count
        )
        for row in rows
    ]


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check for V2 Yield API.
    
    Verifies that the fact_production_performance_v2 table exists and has data.
    """
    try:
        sql = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT material_code) as unique_materials,
            COUNT(DISTINCT process_order_id) as unique_orders
        FROM fact_production_performance_v2
        """
        result = db.execute(text(sql))
        row = result.fetchone()
        
        return {
            "status": "healthy",
            "table": "fact_production_performance_v2",
            "total_records": row.total_records,
            "unique_materials": row.unique_materials,
            "unique_orders": row.unique_orders
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

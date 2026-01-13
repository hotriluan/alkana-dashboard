"""
Yield V3 API Router - Operational Efficiency Hub

V3 Features:
- Historical data accumulation via UPSERT (monthly uploads)
- Period-based filtering with MM/YYYY format
- Trend analysis across time
- Pareto analysis for top loss contributors
- SG variance quality analysis

Tables:
- raw_zrpp062: Staging table with all columns from Excel
- fact_production_performance_v2: Analytical fact table with reference_date

Reference: ADR-2026-01-12 Production Yield V3
"""
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import text, func, extract
from typing import List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date, datetime
from pathlib import Path
import shutil
import tempfile

from src.api.deps import get_db, get_current_user
from src.db.models import FactProductionPerformanceV2, UploadHistory
from src.etl.loaders import Zrpp062Loader, Zrsd006Loader
import hashlib


router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================

class YieldKPI(BaseModel):
    """KPI summary for a period range"""
    total_orders: int
    total_output_kg: float
    total_input_kg: float
    total_loss_kg: float
    avg_yield_pct: float  # 100 - avg_loss_pct
    avg_loss_pct: float
    high_loss_count: int  # Orders with loss > 2%
    period_start: str  # MM/YYYY
    period_end: str    # MM/YYYY


class TrendDataPoint(BaseModel):
    """Single point in trend chart"""
    period: str  # MM/YYYY format
    avg_yield_pct: float
    avg_loss_pct: float
    total_output_kg: float
    order_count: int


class DistributionDataPoint(BaseModel):
    """Distribution by product group"""
    product_group: str
    avg_yield_pct: float
    avg_loss_pct: float
    total_output_kg: float
    order_count: int


class CategoryPerformance(BaseModel):
    """Performance matrix data for bubble chart visualization"""
    category: str
    total_output_kg: float
    total_loss_kg: float
    loss_pct_avg: float  # Weighted average: (total_loss / (total_output + total_loss)) * 100
    batch_count: int


class ParetoDataPoint(BaseModel):
    """Pareto analysis - top loss contributors"""
    material_code: str
    material_description: Optional[str] = None
    total_loss_kg: float
    avg_loss_pct: float
    cumulative_pct: float  # Cumulative percentage of total loss


class QualityDataPoint(BaseModel):
    """SG variance quality scatter plot"""
    process_order_id: str
    material_code: Optional[str] = None
    sg_theoretical: Optional[float] = None
    sg_actual: Optional[float] = None
    sg_variance: float  # sg_actual - sg_theoretical
    loss_pct: Optional[float] = None


class UploadResponse(BaseModel):
    """Response from upload endpoint"""
    success: bool
    message: str
    file_name: Optional[str] = None  # V4: Added for UI display
    upload_id: Optional[int] = None  # V4: Track in UploadHistory
    records_loaded: int
    records_updated: int
    records_skipped: int
    errors: List[str] = []
    reference_date: str  # YYYY-MM-DD


class AvailablePeriod(BaseModel):
    """Available period in database"""
    period: str  # MM/YYYY
    record_count: int


# ============================================================================
# Helper Functions
# ============================================================================

def parse_period(period_str: str) -> date:
    """Parse MM/YYYY to first day of month"""
    parts = period_str.split('/')
    if len(parts) != 2:
        raise ValueError(f"Invalid period format: {period_str}. Expected MM/YYYY")
    month, year = int(parts[0]), int(parts[1])
    return date(year, month, 1)


def format_period(d: date) -> str:
    """Format date to MM/YYYY"""
    return f"{d.month:02d}/{d.year}"


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/upload", response_model=UploadResponse)
async def upload_yield_data(
    file: UploadFile = File(..., description="Excel file (zrpp062.xlsx format)"),
    month: int = Form(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Form(..., ge=2020, le=2100, description="Year (2020-2100)"),
    db: Session = Depends(get_db),
    # user = Depends(get_current_user)
):
    """
    Upload yield data for a specific month/year.
    
    Uses UPSERT (ON CONFLICT DO UPDATE) so uploading same month twice
    will update existing records rather than create duplicates.
    
    Args:
        file: Excel file in zrpp062 format
        month: Reporting month (1-12)
        year: Reporting year (2020-2100)
    
    Returns:
        Upload statistics with success/failure details
    """
    # Validate file extension (case-insensitive)
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Please upload an Excel file (.xlsx or .xls)"
        )
    
    # Create reference date (first day of month)
    reference_date = date(year, month, 1)
    
    # Calculate file hash for deduplication
    file_content = await file.read()
    await file.seek(0)  # Reset file pointer
    file_hash = hashlib.sha256(file_content).hexdigest()
    
    # Create upload history record
    upload_record = UploadHistory(
        file_name=file.filename,
        original_name=file.filename,  # Required field
        file_hash=file_hash,
        file_size=len(file_content),
        file_type='zrpp062',
        status='processing',
        uploaded_at=datetime.utcnow()
    )
    db.add(upload_record)
    db.commit()
    db.refresh(upload_record)
    
    # Save uploaded file to temp location
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            tmp.write(file_content)
            tmp_path = Path(tmp.name)
    except Exception as e:
        upload_record.status = 'failed'
        upload_record.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")
    
    # Load data using UPSERT loader
    try:
        loader = Zrpp062Loader(db)
        stats = loader.load_with_period(tmp_path, reference_date)
        
        # Update upload record with success
        upload_record.status = 'completed'
        upload_record.rows_loaded = stats.get('loaded', 0)
        upload_record.rows_updated = stats.get('updated', 0)
        upload_record.rows_skipped = stats.get('skipped', 0)
        upload_record.processed_at = datetime.utcnow()
        db.commit()
        
        return UploadResponse(
            success=True,
            message=f"Successfully uploaded data for {month:02d}/{year}",
            file_name=file.filename,  # V4: Include filename
            upload_id=upload_record.id,  # V4: Track upload
            records_loaded=stats.get('loaded', 0),
            records_updated=stats.get('updated', 0),
            records_skipped=stats.get('skipped', 0),
            errors=stats.get('errors', [])[:10],  # Limit to first 10 errors
            reference_date=reference_date.isoformat()
        )
    except Exception as e:
        # Update upload record with failure
        upload_record.status = 'failed'
        upload_record.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to load data: {str(e)}")
    finally:
        # Clean up temp file
        try:
            tmp_path.unlink()
        except:
            pass


@router.post("/upload-master-data", response_model=UploadResponse)
async def upload_master_data(
    file: UploadFile = File(..., description="Excel file (zrsd006.xlsx format with PH hierarchy)"),
    db: Session = Depends(get_db),
    # user = Depends(get_current_user)
):
    """
    Upload product master data with PH hierarchy levels.
    
    This updates the dim_product_hierarchy dimension table used for
    categorizing yield losses by Brand/Grade (PH Level 3).
    
    Uses UPSERT (ON CONFLICT DO UPDATE) - new materials added, existing ones updated.
    
    Args:
        file: Excel file in zrsd006 format with columns:
              - Material Code
              - Mat. Description
              - PH 1, Division (PH Level 1)
              - PH 2, Business (PH Level 2)
              - PH 3, Sub Business (PH Level 3)
    
    Returns:
        Upload statistics with success/failure details
    """
    # Validate file extension (case-insensitive)
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Please upload an Excel file (.xlsx or .xls)"
        )
    
    # Calculate file hash for deduplication
    file_content = await file.read()
    await file.seek(0)  # Reset file pointer
    file_hash = hashlib.sha256(file_content).hexdigest()
    
    # Create upload history record
    upload_record = UploadHistory(
        file_name=file.filename,
        original_name=file.filename,  # Required field
        file_hash=file_hash,
        file_size=len(file_content),
        file_type='zrsd006',
        status='processing',
        uploaded_at=datetime.utcnow()
    )
    db.add(upload_record)
    db.commit()
    db.refresh(upload_record)
    
    # Save uploaded file to temp location
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            tmp.write(file_content)
            tmp_path = Path(tmp.name)
    except Exception as e:
        upload_record.status = 'failed'
        upload_record.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")
    
    # Load master data to raw table (and dimension table automatically)
    try:
        loader = Zrsd006Loader(db, mode='upsert', file_path=tmp_path)
        
        # Load to raw_zrsd006 table (automatically also loads to dim_product_hierarchy)
        stats = loader.load()
        
        # Update upload record with success
        upload_record.status = 'completed'
        upload_record.rows_loaded = stats.get('loaded', 0)
        upload_record.rows_updated = stats.get('updated', 0)
        upload_record.rows_skipped = stats.get('skipped', 0)
        upload_record.rows_failed = len(stats.get('errors', [])) if stats.get('errors') else 0
        upload_record.processed_at = datetime.utcnow()
        db.commit()
        
        return UploadResponse(
            success=True,
            message=f"Successfully uploaded master data - {stats.get('loaded', 0)} materials loaded, {stats.get('skipped', 0)} skipped",
            file_name=file.filename,  # V4: Include filename
            upload_id=upload_record.id,  # V4: Track upload
            records_loaded=stats.get('loaded', 0),
            records_updated=stats.get('updated', 0),
            records_skipped=stats.get('skipped', 0),
            errors=stats.get('errors', [])[:10],
            reference_date=date.today().isoformat()
        )
    except Exception as e:
        # Update upload record with failure
        upload_record.status = 'failed'
        upload_record.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to load master data: {str(e)}")
    finally:
        # Clean up temp file
        try:
            tmp_path.unlink()
        except:
            pass


@router.get("/periods", response_model=List[AvailablePeriod])
async def get_available_periods(
    db: Session = Depends(get_db),
):
    """
    Get list of available periods in the database.
    Used to populate period selectors in the UI.
    """
    query = text("""
        SELECT 
            TO_CHAR(reference_date, 'MM/YYYY') as period,
            COUNT(*) as record_count
        FROM fact_production_performance_v2
        WHERE reference_date IS NOT NULL
        GROUP BY reference_date
        ORDER BY reference_date DESC
    """)
    
    result = db.execute(query).fetchall()
    return [
        AvailablePeriod(period=row[0], record_count=row[1])
        for row in result
    ]


@router.get("/kpi", response_model=YieldKPI)
async def get_kpi(
    period_start: str = Query(..., description="Start period in MM/YYYY format"),
    period_end: str = Query(..., description="End period in MM/YYYY format"),
    db: Session = Depends(get_db),
):
    """
    Get KPI summary for a period range.
    
    Args:
        period_start: Start period (MM/YYYY)
        period_end: End period (MM/YYYY)
    
    Returns:
        Aggregated KPIs for the period range
    """
    try:
        start_date = parse_period(period_start)
        end_date = parse_period(period_end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Calculate end of month for end_date
    if end_date.month == 12:
        end_date_inclusive = date(end_date.year + 1, 1, 1)
    else:
        end_date_inclusive = date(end_date.year, end_date.month + 1, 1)
    
    query = text("""
        SELECT 
            COUNT(*) as total_orders,
            COALESCE(SUM(output_actual_kg), 0) as total_output_kg,
            COALESCE(SUM(input_actual_kg), 0) as total_input_kg,
            COALESCE(SUM(loss_kg), 0) as total_loss_kg,
            COALESCE(AVG(loss_pct), 0) as avg_loss_pct,
            COUNT(*) FILTER (WHERE loss_pct > 2.0) as high_loss_count
        FROM fact_production_performance_v2
        WHERE reference_date >= :start_date 
          AND reference_date < :end_date
    """)
    
    result = db.execute(query, {
        'start_date': start_date,
        'end_date': end_date_inclusive
    }).fetchone()
    
    avg_loss = float(result[4] or 0)
    
    return YieldKPI(
        total_orders=result[0] or 0,
        total_output_kg=float(result[1] or 0),
        total_input_kg=float(result[2] or 0),
        total_loss_kg=float(result[3] or 0),
        avg_yield_pct=round(100 - avg_loss, 2),
        avg_loss_pct=round(avg_loss, 2),
        high_loss_count=result[5] or 0,
        period_start=period_start,
        period_end=period_end
    )


@router.get("/trend", response_model=List[TrendDataPoint])
async def get_trend(
    period_start: str = Query(..., description="Start period in MM/YYYY format"),
    period_end: str = Query(..., description="End period in MM/YYYY format"),
    db: Session = Depends(get_db),
):
    """
    Get yield trend over time.
    
    Returns monthly aggregated data for trend chart.
    X-axis format: MM/YYYY
    """
    try:
        start_date = parse_period(period_start)
        end_date = parse_period(period_end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Calculate end of month for end_date
    if end_date.month == 12:
        end_date_inclusive = date(end_date.year + 1, 1, 1)
    else:
        end_date_inclusive = date(end_date.year, end_date.month + 1, 1)
    
    query = text("""
        SELECT 
            TO_CHAR(reference_date, 'MM/YYYY') as period,
            COALESCE(AVG(loss_pct), 0) as avg_loss_pct,
            COALESCE(SUM(output_actual_kg), 0) as total_output_kg,
            COUNT(*) as order_count,
            reference_date
        FROM fact_production_performance_v2
        WHERE reference_date >= :start_date 
          AND reference_date < :end_date
        GROUP BY reference_date
        ORDER BY reference_date ASC
    """)
    
    result = db.execute(query, {
        'start_date': start_date,
        'end_date': end_date_inclusive
    }).fetchall()
    
    return [
        TrendDataPoint(
            period=row[0],
            avg_loss_pct=round(float(row[1] or 0), 2),
            avg_yield_pct=round(100 - float(row[1] or 0), 2),
            total_output_kg=float(row[2] or 0),
            order_count=row[3] or 0
        )
        for row in result
    ]


@router.get("/distribution", response_model=List[DistributionDataPoint])
async def get_distribution(
    period_start: str = Query(..., description="Start period in MM/YYYY format"),
    period_end: str = Query(..., description="End period in MM/YYYY format"),
    group_by: str = Query(default="ph_level_3", description="Group by field: ph_level_3 (Brand/Grade), ph_level_2 (Product Line), or product_group_1 (Raw)"),
    db: Session = Depends(get_db),
):
    """
    Get yield distribution by product hierarchy (Star Schema JOIN).
    
    V3.5 Enhancement: Uses dim_product_hierarchy for brand/grade categorization.
    Default: Groups by PH Level 3 (Brand/Grade) from master data.
    
    Returns aggregated data for bar chart / pie chart.
    """
    try:
        start_date = parse_period(period_start)
        end_date = parse_period(period_end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Calculate end of month for end_date
    if end_date.month == 12:
        end_date_inclusive = date(end_date.year + 1, 1, 1)
    else:
        end_date_inclusive = date(end_date.year, end_date.month + 1, 1)
    
    # Star Schema JOIN - Use dimension table for categorization
    if group_by in ['ph_level_1', 'ph_level_2', 'ph_level_3']:
        # JOIN with dim_product_hierarchy
        query = text(f"""
            SELECT 
                COALESCE(d.{group_by}, 'Uncategorized') as category,
                COALESCE(AVG(f.loss_pct), 0) as avg_loss_pct,
                COALESCE(SUM(f.output_actual_kg), 0) as total_output_kg,
                COUNT(*) as order_count
            FROM fact_production_performance_v2 f
            LEFT JOIN dim_product_hierarchy d ON f.material_code = d.material_code
            WHERE f.reference_date >= :start_date 
              AND f.reference_date < :end_date
            GROUP BY d.{group_by}
            ORDER BY total_output_kg DESC
        """)
    else:
        # Fallback: Use raw fact table columns (legacy behavior)
        valid_raw_groups = ['product_group_1', 'product_group_2', 'mrp_controller']
        if group_by not in valid_raw_groups:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid group_by. Must be one of: ph_level_1, ph_level_2, ph_level_3, {', '.join(valid_raw_groups)}"
            )
        
        query = text(f"""
            SELECT 
                COALESCE(f.{group_by}, 'Unknown') as category,
                COALESCE(AVG(f.loss_pct), 0) as avg_loss_pct,
                COALESCE(SUM(f.output_actual_kg), 0) as total_output_kg,
                COUNT(*) as order_count
            FROM fact_production_performance_v2 f
            WHERE f.reference_date >= :start_date 
              AND f.reference_date < :end_date
            GROUP BY f.{group_by}
            ORDER BY total_output_kg DESC
        """)
    
    result = db.execute(query, {
        'start_date': start_date,
        'end_date': end_date_inclusive
    }).fetchall()
    
    return [
        DistributionDataPoint(
            product_group=row[0] or 'Unknown',
            avg_loss_pct=round(float(row[1] or 0), 2),
            avg_yield_pct=round(100 - float(row[1] or 0), 2),
            total_output_kg=float(row[2] or 0),
            order_count=row[3] or 0
        )
        for row in result
    ]


@router.get("/pareto", response_model=List[ParetoDataPoint])
async def get_pareto(
    period_start: str = Query(..., description="Start period in MM/YYYY format"),
    period_end: str = Query(..., description="End period in MM/YYYY format"),
    limit: int = Query(default=10, ge=5, le=50, description="Number of top materials"),
    db: Session = Depends(get_db),
):
    """
    Get Pareto analysis - top N materials by loss.
    
    Returns materials ranked by total loss with cumulative percentage.
    """
    try:
        start_date = parse_period(period_start)
        end_date = parse_period(period_end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Calculate end of month for end_date
    if end_date.month == 12:
        end_date_inclusive = date(end_date.year + 1, 1, 1)
    else:
        end_date_inclusive = date(end_date.year, end_date.month + 1, 1)
    
    query = text("""
        WITH material_loss AS (
            SELECT 
                material_code,
                MAX(material_description) as material_description,
                COALESCE(SUM(loss_kg), 0) as total_loss_kg,
                COALESCE(AVG(loss_pct), 0) as avg_loss_pct
            FROM fact_production_performance_v2
            WHERE reference_date >= :start_date 
              AND reference_date < :end_date
              AND material_code IS NOT NULL
            GROUP BY material_code
        ),
        total AS (
            SELECT SUM(total_loss_kg) as grand_total FROM material_loss
        ),
        ranked AS (
            SELECT 
                material_code,
                material_description,
                total_loss_kg,
                avg_loss_pct,
                SUM(total_loss_kg) OVER (ORDER BY total_loss_kg DESC) as running_sum,
                (SELECT grand_total FROM total) as grand_total
            FROM material_loss
            ORDER BY total_loss_kg DESC
            LIMIT :limit
        )
        SELECT 
            material_code,
            material_description,
            total_loss_kg,
            avg_loss_pct,
            CASE WHEN grand_total > 0 
                THEN (running_sum / grand_total) * 100 
                ELSE 0 
            END as cumulative_pct
        FROM ranked
    """)
    
    result = db.execute(query, {
        'start_date': start_date,
        'end_date': end_date_inclusive,
        'limit': limit
    }).fetchall()
    
    return [
        ParetoDataPoint(
            material_code=row[0],
            material_description=row[1],
            total_loss_kg=float(row[2] or 0),
            avg_loss_pct=round(float(row[3] or 0), 2),
            cumulative_pct=round(float(row[4] or 0), 2)
        )
        for row in result
    ]


class DrillDownMaterial(BaseModel):
    """Material detail within a brand/grade category"""
    material_code: str
    material_description: Optional[str] = None
    total_loss_kg: float
    avg_loss_pct: float
    order_count: int


@router.get("/distribution/details", response_model=List[DrillDownMaterial])
async def get_distribution_details(
    period_start: str = Query(..., description="Start period in MM/YYYY format"),
    period_end: str = Query(..., description="End period in MM/YYYY format"),
    category: str = Query(..., description="PH Level 3 category (e.g., 'PREMIUM')"),
    level: str = Query(default="ph_level_3", description="PH level to filter: ph_level_1, ph_level_2, or ph_level_3"),
    limit: int = Query(default=20, ge=5, le=100, description="Max materials to return"),
    db: Session = Depends(get_db),
):
    """
    Drill-down: Get materials within a specific brand/grade category.
    
    Shows which specific materials are causing loss within a category.
    Useful for root cause analysis.
    
    Example: category="Water Based Paint" → shows all materials in that category
    """
    try:
        start_date = parse_period(period_start)
        end_date = parse_period(period_end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Validate level parameter
    valid_levels = ['ph_level_1', 'ph_level_2', 'ph_level_3']
    if level not in valid_levels:
        raise HTTPException(status_code=400, detail=f"Invalid level. Must be one of: {valid_levels}")
    
    # Calculate end of month
    if end_date.month == 12:
        end_date_inclusive = date(end_date.year + 1, 1, 1)
    else:
        end_date_inclusive = date(end_date.year, end_date.month + 1, 1)
    
    # Star Schema JOIN with category filter
    query = text(f"""
        SELECT 
            f.material_code,
            MAX(f.material_description) as material_description,
            COALESCE(SUM(f.loss_kg), 0) as total_loss_kg,
            COALESCE(AVG(f.loss_pct), 0) as avg_loss_pct,
            COUNT(*) as order_count
        FROM fact_production_performance_v2 f
        LEFT JOIN dim_product_hierarchy d ON f.material_code = d.material_code
        WHERE f.reference_date >= :start_date 
          AND f.reference_date < :end_date
          AND d.{level} = :category
        GROUP BY f.material_code
        ORDER BY total_loss_kg DESC
        LIMIT :limit
    """)
    
    result = db.execute(query, {
        'start_date': start_date,
        'end_date': end_date_inclusive,
        'category': category,
        'limit': limit
    }).fetchall()
    
    return [
        DrillDownMaterial(
            material_code=row[0],
            material_description=row[1],
            total_loss_kg=float(row[2] or 0),
            avg_loss_pct=round(float(row[3] or 0), 2),
            order_count=row[4] or 0
        )
        for row in result
    ]


@router.get("/category-performance", response_model=List[CategoryPerformance])
async def get_category_performance(
    period_start: str = Query(..., description="Start period in MM/YYYY format"),
    period_end: str = Query(..., description="End period in MM/YYYY format"),
    db: Session = Depends(get_db),
):
    """
    Get category performance data for Performance Matrix (bubble chart).
    
    Returns categories with:
    - Volume (total_output_kg) for X-axis
    - Efficiency (loss_pct_avg) for Y-axis
    - Impact (total_loss_kg) for bubble size
    
    **Critical:** loss_pct_avg is calculated as weighted average:
    (total_loss_kg / (total_output_kg + total_loss_kg)) * 100
    
    This shows the TRUE loss percentage, not a simple average.
    """
    try:
        start_date = parse_period(period_start)
        end_date = parse_period(period_end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Calculate end of month for end_date
    if end_date.month == 12:
        end_date_inclusive = date(end_date.year + 1, 1, 1)
    else:
        end_date_inclusive = date(end_date.year, end_date.month + 1, 1)
    
    # Star schema query with weighted loss calculation
    query = text("""
        SELECT 
            COALESCE(d.ph_level_3, 'Uncategorized') as category,
            COALESCE(SUM(f.output_actual_kg), 0) as total_output_kg,
            COALESCE(SUM(f.loss_kg), 0) as total_loss_kg,
            CASE 
                WHEN (SUM(f.output_actual_kg) + SUM(f.loss_kg)) > 0 
                THEN (SUM(f.loss_kg) / (SUM(f.output_actual_kg) + SUM(f.loss_kg))) * 100
                ELSE 0 
            END as loss_pct_avg,
            COUNT(*) as batch_count
        FROM fact_production_performance_v2 f
        LEFT JOIN dim_product_hierarchy d ON f.material_code = d.material_code
        WHERE f.reference_date >= :start_date 
          AND f.reference_date < :end_date
        GROUP BY d.ph_level_3
        HAVING SUM(f.output_actual_kg) > 0  -- Exclude categories with no output
        ORDER BY total_loss_kg DESC
    """)
    
    result = db.execute(query, {
        'start_date': start_date,
        'end_date': end_date_inclusive
    }).fetchall()
    
    return [
        CategoryPerformance(
            category=row[0],
            total_output_kg=float(row[1] or 0),
            total_loss_kg=float(row[2] or 0),
            loss_pct_avg=round(float(row[3] or 0), 2),
            batch_count=int(row[4] or 0)
        )
        for row in result
    ]


@router.get("/quality", response_model=List[QualityDataPoint])
async def get_quality(
    period_start: str = Query(..., description="Start period in MM/YYYY format"),
    period_end: str = Query(..., description="End period in MM/YYYY format"),
    limit: int = Query(default=100, ge=10, le=500, description="Max points to return"),
    db: Session = Depends(get_db),
):
    """
    Get SG variance quality data for scatter plot.
    
    Returns orders with SG theoretical vs actual variance.
    Useful for identifying quality issues.
    """
    try:
        start_date = parse_period(period_start)
        end_date = parse_period(period_end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Calculate end of month for end_date
    if end_date.month == 12:
        end_date_inclusive = date(end_date.year + 1, 1, 1)
    else:
        end_date_inclusive = date(end_date.year, end_date.month + 1, 1)
    
    query = text("""
        SELECT 
            process_order_id,
            material_code,
            sg_theoretical,
            sg_actual,
            (COALESCE(sg_actual, 0) - COALESCE(sg_theoretical, 0)) as sg_variance,
            loss_pct
        FROM fact_production_performance_v2
        WHERE reference_date >= :start_date 
          AND reference_date < :end_date
          AND sg_theoretical IS NOT NULL
          AND sg_actual IS NOT NULL
        ORDER BY ABS(COALESCE(sg_actual, 0) - COALESCE(sg_theoretical, 0)) DESC
        LIMIT :limit
    """)
    
    result = db.execute(query, {
        'start_date': start_date,
        'end_date': end_date_inclusive,
        'limit': limit
    }).fetchall()
    
    return [
        QualityDataPoint(
            process_order_id=row[0],
            material_code=row[1],
            sg_theoretical=float(row[2]) if row[2] else None,
            sg_actual=float(row[3]) if row[3] else None,
            sg_variance=float(row[4] or 0),
            loss_pct=float(row[5]) if row[5] else None
        )
        for row in result
    ]


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint for V3 yield API"""
    try:
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT reference_date) as periods_count,
                MIN(reference_date) as earliest_period,
                MAX(reference_date) as latest_period
            FROM fact_production_performance_v2
        """)).fetchone()
        
        return {
            "status": "healthy",
            "version": "v3",
            "database": {
                "total_records": result[0],
                "periods_count": result[1],
                "earliest_period": format_period(result[2]) if result[2] else None,
                "latest_period": format_period(result[3]) if result[3] else None
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "version": "v3",
            "error": str(e)
        }

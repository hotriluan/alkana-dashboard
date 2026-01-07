"""
Alert System API Router

Skills: backend-development, databases
CLAUDE.md: KISS - Simple REST endpoints with clear responsibilities

Endpoints:
1. GET /summary - Alert counts by severity
2. GET /stuck-inventory - Active stuck inventory alerts
3. GET /low-yield - Active low yield alerts  
4. POST /{alert_id}/resolve - Mark alert as resolved
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from src.db.connection import get_db

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


# Pydantic Models (DRY - Reusable response models)

class AlertSummary(BaseModel):
    """Alert counts by severity"""
    critical: int
    high: int
    medium: int
    total: int


class AlertDetail(BaseModel):
    """Individual alert details"""
    id: int
    alert_type: str
    severity: str
    title: str
    message: str
    entity_type: str
    entity_id: str
    detected_at: str
    status: str


# API Endpoints

@router.get("/summary", response_model=AlertSummary)
async def get_alert_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get alert counts by severity
    
    Skills: backend-development, databases
    Returns: Critical, High, Medium, and Total active alert counts
    """
    try:
        # Build date filter
        date_filter = ""
        if start_date and end_date:
            date_filter = f"AND DATE(detected_at) BETWEEN '{start_date}' AND '{end_date}'"
        
        result = db.execute(text(f"""
            SELECT 
                COUNT(CASE WHEN severity='CRITICAL' THEN 1 END) as critical,
                COUNT(CASE WHEN severity='HIGH' THEN 1 END) as high,
                COUNT(CASE WHEN severity='MEDIUM' THEN 1 END) as medium,
                COUNT(*) as total
            FROM fact_alerts
            WHERE status = 'ACTIVE' {date_filter}
        """)).fetchone()
        
        return AlertSummary(
            critical=result[0] or 0,
            high=result[1] or 0,
            medium=result[2] or 0,
            total=result[3] or 0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching alert summary: {str(e)}")


@router.get("/stuck-inventory", response_model=List[AlertDetail])
async def get_stuck_inventory_alerts(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get active stuck inventory alerts (>48h in transit)
    
    Skills: backend-development, databases
    Returns: List of stuck inventory alerts with details
    """
    try:
        # Build date filter
        date_filter = ""
        if start_date and end_date:
            date_filter = f"AND DATE(detected_at) BETWEEN '{start_date}' AND '{end_date}'"
        
        results = db.execute(text(f"""
            SELECT 
                id, 
                alert_type, 
                severity, 
                COALESCE(batch, entity_id) as title,
                entity_type, 
                entity_id, 
                detected_at, 
                status,
                stuck_hours
            FROM fact_alerts
            WHERE alert_type IN ('STUCK_IN_TRANSIT', 'DELAYED_TRANSIT')
              AND status = 'ACTIVE' {date_filter}
            ORDER BY severity DESC, detected_at DESC
        """)).fetchall()
        
        return [AlertDetail(
            id=r[0],
            alert_type=r[1],
            severity=r[2],
            title=r[3] or 'Unknown',
            message=f"Stuck for {r[8]:.1f} hours" if r[8] else "Stuck in transit",
            entity_type=r[4],
            entity_id=r[5],
            detected_at=str(r[6]),
            status=r[7]
        ) for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stuck inventory alerts: {str(e)}")


@router.get("/low-yield", response_model=List[AlertDetail])
async def get_low_yield_alerts(db: Session = Depends(get_db)):
    """
    Get active low yield alerts (<85%)
    
    Skills: backend-development, databases
    Returns: List of low yield alerts with details
    """
    try:
        results = db.execute(text("""
            SELECT 
                id, 
                alert_type, 
                severity, 
                COALESCE(batch, entity_id) as title,
                entity_type, 
                entity_id, 
                detected_at, 
                status,
                yield_pct
            FROM fact_alerts
            WHERE alert_type = 'LOW_YIELD'
              AND status = 'ACTIVE'
            ORDER BY severity DESC, detected_at DESC
        """)).fetchall()
        
        return [AlertDetail(
            id=r[0],
            alert_type=r[1],
            severity=r[2],
            title=r[3] or 'Unknown',
            message=f"Yield: {r[8]:.1f}%" if r[8] else "Low production yield",
            entity_type=r[4],
            entity_id=r[5],
            detected_at=str(r[6]),
            status=r[7]
        ) for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching low yield alerts: {str(e)}")


@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """
    Mark alert as resolved
    
    Skills: backend-development, databases
    Args:
        alert_id: ID of the alert to resolve
    Returns: Success message
    """
    try:
        # Check if alert exists
        result = db.execute(text("""
            SELECT id FROM fact_alerts WHERE id = :alert_id
        """), {"alert_id": alert_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
        
        # Update status to RESOLVED
        db.execute(text("""
            UPDATE fact_alerts
            SET status = 'RESOLVED',
                resolved_at = NOW()
            WHERE id = :alert_id
        """), {"alert_id": alert_id})
        db.commit()
        
        return {"message": f"Alert {alert_id} resolved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error resolving alert: {str(e)}")

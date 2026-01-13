"""
Upload API Router - File upload endpoints

Provides endpoints for:
- POST /api/v1/upload - Upload Excel file
- GET /api/v1/upload/{upload_id}/status - Get upload status
- GET /api/v1/upload/history - List recent uploads

Skills: backend-development, api-development
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional
import uuid

from src.api.deps import get_db
from src.db.models import UploadHistory
from src.core.upload_service import (
    save_upload_file,
    process_file,
    compute_file_hash,
    validate_file_structure
)


router = APIRouter(prefix="/upload", tags=["Upload"])


# Pydantic Models
class UploadResponse(BaseModel):
    """Response for file upload"""
    upload_id: int
    file_name: str
    file_type: str
    status: str
    message: str


class UploadStatusResponse(BaseModel):
    """Detailed upload status"""
    upload_id: int
    file_name: str
    original_name: str
    file_type: str
    file_size: int
    status: str
    uploaded_at: datetime
    processed_at: datetime | None
    rows_loaded: int
    rows_updated: int
    rows_skipped: int
    rows_failed: int
    error_message: str | None
    snapshot_date: str | None


class UploadHistoryItem(BaseModel):
    """Upload history list item"""
    upload_id: int
    original_name: str
    file_type: str
    status: str
    uploaded_at: datetime
    rows_loaded: int
    rows_updated: int
    rows_skipped: int
    rows_failed: int


# Constants
UPLOAD_DIR = Path("demodata/uploads")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'.xlsx', '.xls'}


@router.post("/", response_model=UploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    snapshot_date: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload Excel file for processing
    
    - **file**: Excel file (.xlsx or .xls)
    - **snapshot_date**: Optional date for AR data (YYYY-MM-DD format, ZRFI005 only)
    
    Returns upload_id for status tracking
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Validate file size (read content to check)
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file"
        )
    
    # Reset file pointer for saving
    await file.seek(0)
    
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_name = f"{file_id}{file_ext}"
        file_path = UPLOAD_DIR / file_name
        
        # Ensure upload directory exists
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        # Save file
        saved_size = await save_upload_file(file, file_path)
        
        # Compute file hash
        file_hash = compute_file_hash(file_path)
        
        # Parse snapshot_date if provided (needed for duplicate check)
        parsed_snapshot_date = None
        if snapshot_date:
            try:
                parsed_snapshot_date = datetime.strptime(snapshot_date, '%Y-%m-%d').date()
            except ValueError:
                file_path.unlink()
                raise HTTPException(
                    status_code=400,
                    detail="Invalid snapshot_date format. Use YYYY-MM-DD"
                )
        
        # Quick validation before creating record
        validation = validate_file_structure(file_path)
        if not validation['valid']:
            file_path.unlink()  # Clean up
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file structure: {validation['error']}"
            )
        
        file_type = validation['file_type']
        
        # Check for duplicate uploads
        # Only prevent duplicate if upload is CURRENTLY processing/pending
        # Allow re-upload if previous upload completed (for data updates via upsert)
        query = db.query(UploadHistory).filter_by(file_hash=file_hash)
        
        if file_type == 'ZRFI005' and parsed_snapshot_date:
            # AR file: Only check duplicate with same snapshot_date
            query = query.filter_by(snapshot_date=parsed_snapshot_date)
        
        # Only check for in-progress uploads (not completed)
        existing = query.filter(UploadHistory.status.in_(['processing', 'pending'])).first()
        
        if existing:
            # Delete uploaded file
            file_path.unlink()
            raise HTTPException(
                status_code=409,
                detail=f"File is currently being processed (upload_id: {existing.id}, status: {existing.status}). Please wait for it to complete."
            )
        
        # Create upload history record
        upload = UploadHistory(
            file_name=file_name,
            original_name=file.filename,
            file_type=file_type,
            file_size=saved_size,
            file_hash=file_hash,
            status='pending',
            snapshot_date=parsed_snapshot_date
        )
        db.add(upload)
        db.commit()
        db.refresh(upload)
        
        # Schedule background processing
        background_tasks.add_task(process_file, upload.id, file_path, db)
        
        return UploadResponse(
            upload_id=upload.id,
            file_name=file.filename,
            file_type=file_type,
            status='pending',
            message=f"File uploaded successfully. Type: {validation['file_type']}, Rows: {validation['rows']}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        # Clean up file on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/{upload_id}/status", response_model=UploadStatusResponse)
async def get_upload_status(
    upload_id: int,
    db: Session = Depends(get_db)
):
    """
    Get upload processing status
    
    - **upload_id**: Upload ID from upload response
    
    Returns detailed status and statistics
    """
    upload = db.query(UploadHistory).filter_by(id=upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    return UploadStatusResponse(
        upload_id=upload.id,
        file_name=upload.file_name,
        original_name=upload.original_name,
        file_type=upload.file_type or 'UNKNOWN',
        file_size=upload.file_size or 0,
        status=upload.status,
        uploaded_at=upload.uploaded_at,
        processed_at=upload.processed_at,
        rows_loaded=upload.rows_loaded or 0,
        rows_updated=upload.rows_updated or 0,
        rows_skipped=upload.rows_skipped or 0,
        rows_failed=upload.rows_failed or 0,
        error_message=upload.error_message,
        snapshot_date=upload.snapshot_date.isoformat() if upload.snapshot_date else None
    )


@router.get("/history", response_model=List[UploadHistoryItem])
async def get_upload_history(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get recent upload history
    
    - **limit**: Maximum number of records to return (default: 20)
    
    Returns list of recent uploads
    """
    uploads = db.query(UploadHistory)\
        .order_by(UploadHistory.uploaded_at.desc())\
        .limit(limit)\
        .all()
    
    return [
        UploadHistoryItem(
            upload_id=u.id,
            original_name=u.original_name,
            file_type=u.file_type or 'UNKNOWN',
            status=u.status,
            uploaded_at=u.uploaded_at,
            rows_loaded=u.rows_loaded or 0,
            rows_updated=u.rows_updated or 0,
            rows_skipped=u.rows_skipped or 0,
            rows_failed=u.rows_failed or 0
        )
        for u in uploads
    ]

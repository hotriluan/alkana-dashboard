# Data Upload Feature Implementation Plan

**Date**: 2026-01-05  
**Type**: Feature Implementation  
**Status**: Planning  
**Priority**: High  
**Estimated Duration**: 7 days (4 phases)

## Executive Summary
Implement web-based file upload functionality allowing users to upload SAP data exports (COOISPI, MB51, ZRMM024, ZRSD002, ZRFI005, etc.) through the React dashboard. Backend processes files asynchronously with smart upsert logic, validates data, integrates with existing ETL loaders, and provides real-time feedback. **Special handling for AR (zrfi005)**: daily snapshots within month + auto-reset on new month.

## Context Links
- **Related Plans**: None
- **Dependencies**: 
  - **REUSABLE**: Existing ETL loaders in `src/etl/loaders.py` (LOADERS registry, BaseLoader, compute_row_hash)
  - **REUSABLE**: Database models in `src/db/models.py` (Raw tables already exist)
  - **REUSABLE**: Database session dependency in `src/api/deps.py` (`get_db()`, `get_current_user()`)
  - **REUSABLE**: Authentication in `src/api/auth.py` (JWT token validation)
  - **REUSABLE**: Transformer in `src/etl/transform.py` (compute_row_hash, clean_value)
  - FastAPI backend (`src/api/`)
  - React frontend (`web/src/`)
  - PostgreSQL database connection (`src/db/connection.py`)
- **Reference Docs**: `README.md`, `docs/system-architecture.md`

## 🔄 Reusable Components Analysis

### ✅ **Backend Components (Already Exist - Can Reuse)**

1. **ETL Loaders Registry** (`src/etl/loaders.py`)
   ```python
   # Already exists - line 631-640
   LOADERS = {
       'cooispi': CooispiLoader,
       'mb51': Mb51Loader,
       'zrmm024': Zrmm024Loader,
       'zrsd002': Zrsd002Loader,
       'zrsd004': Zrsd004Loader,
       'zrsd006': Zrsd006Loader,
       'zrfi005': Zrfi005Loader,
       'target': TargetLoader,
   }
   ```
   **Action**: Wrap in `get_loader_for_type()` function (minimal code addition)

2. **Hash Computation** (`src/etl/loaders.py` line 30)
   ```python
   def compute_row_hash(row_dict: Dict) -> str:
       """Compute MD5 hash of row for change detection"""
       json_str = json.dumps(row_dict, sort_keys=True, default=str)
       return hashlib.md5(json_str.encode()).hexdigest()
   ```
   **Action**: Already exists - use as-is

3. **BaseLoader Class** (`src/etl/loaders.py` line 116-153)
   - Has `__init__(db: Session)`
   - Has `load() -> Dict[str, int]`
   - Has `get_stats() -> Dict`
   - Has `truncate()` method
   **Action**: Extend with `mode='upsert'` parameter

4. **Database Session Dependency** (`src/api/deps.py` line 21-35)
   ```python
   def get_db() -> Generator[Session, None, None]:
       db = SessionLocal()
       try:
           yield db
       finally:
           db.close()
   ```
   **Action**: Use directly in upload router

5. **Authentication Dependency** (`src/api/deps.py` line 38-50)
   ```python
   async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
       username = verify_token(token)
       ...
   ```
   **Action**: Use for upload endpoint authorization (Phase 4)

6. **Data Cleaning Utilities** (`src/etl/transform.py` line 36-58)
   - `clean_value(value)` - Normalize values for DB insertion
   - `safe_convert(value)` - Safe type conversion
   - `compute_row_hash(data: Dict) -> str` - Another hash function
   **Action**: Use for data validation in upload service

7. **Raw Table Models** (`src/db/models.py`)
   - `RawCooispi`, `RawMb51`, `RawZrmm024`, `RawZrsd002`, `RawZrsd004`, `RawZrsd006`, `RawZrfi005`, `RawTarget`
   - All have `id`, `source_file`, `source_row`, `loaded_at`, `raw_data` columns
   **Action**: Add `row_hash` column + business key unique constraints only

8. **Database Connection** (`src/db/connection.py`)
   - `SessionLocal()` - Session factory
   - `engine` - SQLAlchemy engine
   - `test_connection()` - Connection testing
   **Action**: Use directly

### ⚠️ **Components Need Extension (Not Full Rewrite)**

1. **Loaders**: Add `mode='upsert'` parameter (currently only `truncate` mode)
2. **Raw Tables**: Add `row_hash` column + unique constraints
3. **Zrfi005Loader**: Add AR monthly reset logic
4. **API Main**: Register new upload router

### ❌ **New Components (Must Create)**

1. `src/api/routers/upload.py` - Upload endpoint
2. `src/core/upload_service.py` - File processing service
3. `src/db/models.py` → Add `UploadHistory` model only
4. `web/src/components/FileUpload.tsx` - React component
5. `web/src/pages/UploadPage.tsx` - Upload page
6. `web/src/services/uploadApi.ts` - API client

## Requirements

### Functional Requirements
- [ ] FR1: Users can upload Excel files (.xlsx, .xls) via web interface
- [ ] FR2: System automatically detects SAP report type (COOISPI, MB51, ZRMM024, ZRSD002, ZRSD004, ZRSD006, ZRFI005, TARGET)
- [ ] FR3: Display upload progress in real-time with status updates
- [ ] FR4: Validate file structure and data before processing
- [ ] FR5: Show detailed error messages for invalid data (row/column level)
- [ ] FR6: Track upload history (file name, upload time, status, stats)
- [ ] FR7: Smart upsert logic: Insert new, update changed, skip unchanged
- [ ] FR8: **AR Special**: Daily snapshots with auto-reset on new month
- [ ] FR9: Support concurrent uploads (queue management)
- [ ] FR10: View AR historical snapshots (date picker for past uploads)

### Non-Functional Requirements  
- [ ] NFR1: Process files up to 50MB within 5 minutes
- [ ] NFR2: File validation before storage (MIME type, structure)
- [ ] NFR3: Secure file handling (no path traversal, virus scanning consideration)
- [ ] NFR4: Automatic cleanup of uploaded files after 24 hours
- [ ] NFR5: Transaction rollback on processing errors
- [ ] NFR6: API response time <200ms for upload initiation

## Architecture Overview

```
User → Upload UI (React) → API Endpoint (/upload) → Background Task
                                                          ↓
                                       Validate → Save to uploads/ → Process with Loaders
                                                          ↓
                                       PostgreSQL ← Deduplicate ← Transform Data
                                                          ↓
                                       Update Status → WebSocket/Polling → UI Updates
```

### Key Components
- **Upload Router** (`src/api/routers/upload.py`): FastAPI endpoint for file upload, validation, status tracking
- **Upload Service** (`src/core/upload_service.py`): Business logic for file processing, loader integration
- **File Upload Component** (`web/src/components/FileUpload.tsx`): React drag-drop UI with progress bar
- **Upload Page** (`web/src/pages/UploadPage.tsx`): Dashboard page for upload management
- **Upload API Client** (`web/src/services/uploadApi.ts`): Frontend service for API calls

### Data Models

**New Table: `upload_history`**
```sql
CREATE TABLE upload_history (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,  -- COOISPI, MB51, etc.
    file_size INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,  -- pending, processing, completed, failed
    uploaded_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    rows_loaded INTEGER,
    rows_updated INTEGER,  -- NEW: rows with data changes
    rows_skipped INTEGER,
    rows_failed INTEGER,
    error_message TEXT,
    uploaded_by VARCHAR(100),  -- Future: user authentication
    file_hash VARCHAR(64),
    snapshot_date DATE  -- For AR daily snapshots
);
```

**Extend existing loaders with upsert logic:**
```python
# Business key for uniqueness (varies by table)
business_keys = {
    'cooispi': ['order', 'batch'],  # Production order + batch
    'mb51': ['material_document', 'doc_item', 'posting_date'],  # Material doc
    'zrmm024': ['purch_order', 'item'],  # PO number + item
    'zrsd002': ['billing_doc', 'item'],  # Billing doc + item
    'zrsd004': ['delivery', 'item'],  # Delivery + item
    'zrsd006': ['material', 'dist_channel'],  # Material master
    'zrfi005': ['customer_name', 'dist_channel', 'snapshot_date'],  # AR daily snapshot
    'target': ['salesman_name', 'semester', 'year']  # Target per period
}

# Special AR (zrfi005) logic:
# - Daily upload: snapshot_date = upload date
# - Check if new month (compare max snapshot_date in DB vs. upload date)
# - If new month → TRUNCATE raw_zrfi005 → INSERT all rows
# - If same month → UPSERT by (customer, dist_channel, snapshot_date)
#   * Skip if same hash (unchanged)
#   * Update if different hash (data changed)
#   * Insert if not exists (new customer or new day)

# Standard upsert logic (all other tables):
# 1. Compute row_hash from entire row
# 2. Check if business_key exists in DB
# 3. If not exists → INSERT
# 4. If exists + same hash → SKIP (no change)
# 5. If exists + different hash → UPDATE (data changed)
```

## Implementation Phases

### Phase 1: Backend API Foundation (Est: 2 days)

**Scope**: FastAPI upload endpoint, file handling, validation

**Tasks**:
1. [ ] Install dependencies - file: `requirements.txt`
   - Add: `python-multipart`, `aiofiles`, `python-magic`
2. [ ] Create upload router - file: `src/api/routers/upload.py` (NEW FILE)
   - **REUSE**: `get_db()` dependency from `src/api/deps.py`
   - **REUSE**: `UploadHistory` model from `src/db/models.py`
   - **REUSE**: FastAPI patterns from existing routers (e.g., `ar_aging.py`)
   - Create new router: (NEW FILE)
   - **REUSE**: Header detection logic from `src/etl/loaders.py` (e.g., `detect_zrmm024_header_row()` line 90-114)
   - Create file type detection:
   ```python
   def detect_file_type(file_path: Path) -> str:
     **REUSE**: Existing Base class, Column types, patterns from other models
   - Add ONE new model at end of file:
   ```python
   class UploadHistory(Base):
     **REUSE**: Existing router registration pattern (line 50-60)
   - Add 2 lines only:
   ```python
   from src.api.routers import upload  # Add to imports at line 14
   
   # Add after line 60:
   app.include_router(upload.router, prefix="/api/v1")
   ```
   - **Lines to modify**: 2 lines (import + include_router)
       __tablename__ = "upload_history"
       
       id = Column(Integer, primary_key=True, autoincrement=True)
       file_name = Column(String(255), nullable=False)
       original_name = Column(String(255), nullable=False)
       file_type = Column(String(50), nullable=False)
       file_size = Column(Integer)
       status = Column(String(20), nullable=False)  # pending, processing, completed, failed
       uploaded_at = Column(DateTime, default=datetime.utcnow)
       processed_at = Column(DateTime)
       rows_loaded = Column(Integer)
       rows_updated = Column(Integer)
       rows_skipped = Column(Integer)
       rows_failed = Column(Integer)
       error_message = Column(Text)
       uploaded_by = Column(String(100))
       file_hash = Column(String(64))
       snapshot_date = Column(Date)  # For AR
   ```
   - **Lines to add**: ~25 lines (follows existing model patterns)headers"""
       wb = load_workbook(file_path, read_only=True, data_only=True)
       ws = wb.active
       
       # Read first row headers
       headers = [ws.cell(1, i).value for i in range(1, 20)]
       headers_str = '|'.join([str(h).lower() for h in headers if h])
       
       # Match patterns (REUSE logic from existing loaders)
       if 'order' in headers_str and 'batch' in headers_str:
           return 'COOISPI'
       elif 'material document' in headers_str:
           return 'MB51'
       elif 'customer name' in headers_str and 'total target' in headers_str:
           return 'ZRFI005'
       # ... other patterns
       
       raise ValueError("Unknown file type - cannot detect SAP report")
   ```
   - **Lines to create**: ~80 lines (reuses openpyxl pattern from loaders.py)
   from src.db.models import UploadHistory  # REUSE
   from src.core.upload_service import process_file
   import uuid
   from pathlib import Path
   
   router = APIRouter(prefix="/upload", tags=["Upload"])
   
   @router.post("/")
   async def upload_file(
       file: UploadFile = File(...),
       background_tasks: BackgroundTasks,
       db: Session = Depends(get_db)  # REUSE get_db
   ):
       # Validate file
       if not file.filename.endswith(('.xlsx', '.xls')):
           raise HTTPException(400, "Only Excel files allowed")
       
       # Save file
       file_id = str(uuid.uuid4())
       file_path = Path(f"demodata/uploads/{file_id}.xlsx")
       # ... save logic
       
       # Create history record (REUSE UploadHistory model)
       upload = UploadHistory(
           file_name=file_id,
           original_name=file.filename,
           file_type="AUTO_DETECT",  # Will be detected later
           status="pending"
       )
       db.add(upload)
       db.commit()
       
       # Process in background
       background_tasks.add_task(process_file, upload.id, file_path, "ZRFI005", db)
       
       return {"upload_id": upload.id, "status": "pending"}
   ```
   - **Lines to create**: ~150 lines (new file, but follows existing router patterns)
3. [ ] Create upload service - file: `src/core/upload_service.py`
   - `detect_file_type()`: Auto-detect SAP report type using header matching
   - `validate_file_structure()`: Check headers match expected format
   - `process_upload_async()`: Background task wrapper
4. [ ] Create upload model - file: `src/db/models.py`
   - Add `UploadHistory` SQLAlchemy model
5. [ ] Database migration - file: `src/db/migrations/`
   - Create `upload_history` table
6. [ ] Register router - file: `src/api/main.py`
   - Import and include upload router

**Acceptance Criteria**:
- [ ] POST `/api/upload` accepts .xlsx files up to 50MB
- [ ] Returns upload ID and initial status immediately (<200ms)
- [ ] Files saved to `demodata/uploads/` with UUID names
- [ ] Invalid files rejected with clear error messages

### Phase 2: ETL Integration & Processing (Est: 2 days)

**Scope**: Integrate with existing loaders, deduplication, error handling

**Tasks**:
1. [ ] Add snapshot_date to AR models - file: `src/db/models.py`
   - Add `snapshot_date DATE` column to `RawZrfi005`
   - Add `snapshot_date DATE` column to `FactArAging`
   - Add `row_hash VARCHAR(64)` to all raw tables (for change detection)
   - Add `UniqueConstraint` on business keys:
     * `RawCooispi`: `(order, batch)`
     * `RawMb51`: `(material_document, doc_item, posting_date)`
     * `RawZrmm024`: `(purch_order, item)`
     * `RawZrsd002`: `(billing_doc, item)`
     * `RawZrsd004`: `(delivery, item)`
     * `RawZrsd006`: `(material, dist_channel)`
     * `RawZrfi005`: `(customer_name, dist_channel, snapshot_date)` ← AR special
     * `RawTarget`: `(salesman_name, semester, year)`
   - Create migration script to alter existing tables

2. [ ] Create loader factory - file: `src/etl/loaders.py`
   - **REUSE**: LOADERS dictionary already exists (line 631-640)
   - Add wrapper function:
     ```python
     def get_loader_for_type(file_type: str, file_path: Path, db: Session, **kwargs) -> BaseLoader:
         """Get loader instance for file type"""
         loader_class = LOADERS.get(file_type.lower())
         if not loader_class:
             raise ValueError(f"Unknown file type: {file_type}")
         return loader_class(db, **kwargs)  # Pass extra args like snapshot_date
     ```
   - **Lines to add**: ~10 lines only (wraps existing LOADERS)

3. [ ] Implement upsert mode in BaseLoader - file: `src/etl/loaders.py`
   - Add `mode` parameter: `'truncate'` (default) | `'upsert'`
   - Add abstract method: `get_business_key(row) -> dict`
   - Add method: `compute_row_hash(row_dict) -> str` (already exists, ensure used)
   - Upsert algorithm:
     ```python
     for row in excel_rows:
         biz_key = self.get_business_key(row)
         row_hash = compute_row_hash(row)
         
         existing = db.query(Model).filter_by(**biz_key).first()
         
         if not existing:
             db.add(new_record)  # INSERT
             loaded_count += 1
         elif existing.row_hash != row_hash:
             update_record(existing, row)  # UPDATE
             updated_count += 1
         else:
             skipped_count += 1  # SKIP (unchanged)
     ```
   - Return stats: `{loaded, updated, skipped, failed}`

4. [ ] Implement AR special logic in Zrfi005Loader - file: `src/etl/loaders.py`
   - Add `snapshot_date` parameter to `__init__`
   - Override `load()` method:
     ```python
     def load(self, snapshot_date: date) -> Dict[str, int]:
         # Step 1: Check if new month
         max_snapshot = db.query(func.max(RawZrfi005.snapshot_date)).scalar()
         is_new_month = (max_snapshot is None) or (snapshot_date.month != max_snapshot.month)
         
         # Step 2: Truncate if new month
         if is_new_month:
             self.truncate()  # Delete all AR data
             mode = 'insert'
             print(f"🔄 New month detected, truncating AR tables")
         else:
             mode = 'upsert'
             print(f"📊 Same month, upserting snapshot for {snapshot_date}")
         
         # Step 3: Load with snapshot_date
         for row in excel_rows:
             record = RawZrfi005(
                 customer_name=row['Customer Name'],
                 dist_channel=row['Distribution Channel'],
                 snapshot_date=snapshot_date,  # ← KEY
                 # ... other fields
                 row_hash=compute_row_hash(row)
             )
             
             if mode == 'insert':
                 db.add(record)
             else:
                 # Upsert logic (business key includes snapshot_date)
                 ...
     ```

5. [ ] Create processing pipeline - file: `src/core/upload_service.py` (NEW FILE)
   - **REUSE**: `get_loader_for_type()` from loaders.py, `get_db()` from deps.py
   - Create new file with upload business logic:
   ```python
   from src.etl.loaders import get_loader_for_type, Zrfi005Loader
   from src.db.models import UploadHistory
   from datetime import date
   
   async def process_file(upload_id: int, file_path: Path, file_type: str, db: Session):
       """Process uploaded file with appropriate loader"""
       upload = db.query(UploadHistory).get(upload_id)
       upload.status = 'processing'
       db.commit()
       
       try:
           # Get loader (REUSE factory)
           if file_type == 'ZRFI005':
               snapshot_date = date.today()
               loader = Zrfi005Loader(db, snapshot_date=snapshot_date)
           else:
               loader = get_loader_for_type(file_type, file_path, db)
           
           # Process with upsert mode
           stats = loader.load(mode='upsert')
           
           # Update history (REUSE UploadHistory model)
           upload.status = 'completed'
           upload.rows_loaded = stats['loaded']
           upload.rows_updated = stats.get('updated', 0)
           upload.rows_skipped = stats.get('skipped', 0)
           upload.rows_failed = stats.get('failed', 0)
           upload.processed_at = datetime.now()
           db.commit()
       except Exception as e:
           upload.status = 'failed'
           upload.error_message = str(e)
           db.rollback()
   ```
   - **Lines to create**: ~100 lines (new file, but reuses existing loaders)

6. [ ] File cleanup scheduler - file: `src/core/upload_service.py`
   - `def cleanup_old_uploads(max_age_hours: int = 24)`
   - Delete files from `demodata/uploads/` older than 24 hours
   - Call via FastAPI startup event or background task

7. [ ] Add GET status endpoint - file: `src/api/routers/upload.py`
   - `GET /api/upload/{upload_id}/status`
   - Returns:
     ```json
     {
       "upload_id": 123,
       "status": "completed",
       "file_type": "ZRFI005",
       "snapshot_date": "2026-01-05",
       "rows_loaded": 85,
       "rows_updated": 12,
       "rows_skipped": 3,
       "rows_failed": 0,
       "uploaded_at": "2026-01-05T10:30:00",
       "processed_at": "2026-01-05T10:32:15",
       "error_message": null
     }
     ```

**Acceptance Criteria**:
- [ ] AR table has `snapshot_date` column with unique constraint
- [ ] All raw tables have business key unique constraints
- [ ] Uploaded files processed with correct upsert logic:
  * **New records** → INSERT
  * **Unchanged records** (same hash) → SKIP
  * **Changed records** (different hash) → UPDATE
- [ ] **AR uploads:**
  * Daily uploads save snapshot with `snapshot_date = upload_date`
  * New month detected: `upload_month != max(snapshot_date).month`
  * New month triggers truncate + fresh insert
  * Same month triggers upsert by `(customer, dist_channel, snapshot_date)`
- [ ] `upload_history` updated with accurate stats (loaded/updated/skipped/failed)
- [ ] Errors captured with row-level details
- [ ] Database transaction rolls back on processing failure
- [ ] Old uploaded files (>24hrs) automatically deleted

### Phase 3: Frontend Upload UI (Est: 2 days)

**Scope**: React components for file upload, progress tracking, AR date picker

**Tasks**:
1. [ ] Install dependencies - file: `web/package.json`
   - Add: `react-dropzone` (drag-drop)
   - Add: `date-fns` (date formatting for AR snapshots)

2. [ ] Create API service - file: `web/src/services/uploadApi.ts`
   ```typescript
   export const uploadFile = async (file: File, onProgress: (pct: number) => void) => {
     const formData = new FormData();
     formData.append('file', file);
     
     const response = await axios.post('/api/upload', formData, {
       onUploadProgress: (e) => onProgress((e.loaded / e.total) * 100)
     });
     
     return response.data; // {upload_id, status, file_type}
   };
   
   export const getUploadStatus = async (uploadId: number) => {
     const response = await axios.get(`/api/upload/${uploadId}/status`);
     return response.data;
   };
   
   export const getUploadHistory = async () => {
     const response = await axios.get('/api/upload/history');
     return response.data;
   };
   ```

3. [ ] Create FileUpload component - file: `web/src/components/FileUpload.tsx`
   - Drag-drop zone using `react-dropzone`
   - Client-side validation: file size (<50MB), extension (.xlsx, .xls)
   - Upload progress bar (0-100%)
   - Status badges: pending (yellow), processing (blue), completed (green), failed (red)
   - Error message display area
   - Props: `onUploadComplete?: (uploadId: number) => void`

4. [ ] Create UploadPage - file: `web/src/pages/UploadPage.tsx`
   - Two sections:
     * **Upload Section**: FileUpload component
     * **History Section**: Table of recent uploads
   - Upload history table columns:
     * File name, File type, Upload time, Status, Rows (loaded/updated/skipped/failed), Actions
   - Auto-polling: Refresh pending/processing uploads every 3 seconds
   - Manual refresh button
   - "View Errors" button for failed uploads (Phase 4)

5. [ ] Add AR snapshot viewer - file: `web/src/pages/ARAgingPage.tsx` (enhancement)
   - Add date picker component
   - Default: Show latest snapshot (`MAX(snapshot_date)`)
   - Allow user to select past dates
   - API call: `GET /api/ar-aging/snapshot?date=2026-01-05`
   - Display historical AR data for selected date

6. [ ] Add navigation - file: `web/src/App.tsx`
   - Add route: `<Route path="/upload" element={<UploadPage />} />`
   - Add sidebar menu item: "Upload Data" (icon: upload icon)

7. [ ] Styling - file: `web/src/components/FileUpload.module.css`
   - Drag-drop zone: dashed border, hover effects (blue highlight)
   - Progress bar: animated gradient
   - Status badges: colored pills with icons
   - Responsive design for mobile

**Acceptance Criteria**:
- [ ] Users can drag-drop or click to select Excel files
- [ ] Upload progress bar updates smoothly (0-100%)
- [ ] Status transitions: pending → processing → completed/failed
- [ ] Error messages displayed clearly for failed uploads
- [ ] Upload history shows last 20 uploads with real-time status
- [ ] **AR snapshots:** Date picker allows viewing historical data
- [ ] Polling stops when all uploads completed/failed
- [ ] Mobile-responsive design

### Phase 4: Advanced Features & Polish (Est: 1 day)

**Scope**: Enhanced validation, user feedback, edge cases

**Tasks**:
1. [ ] Enhanced validation - file: `src/core/upload_service.py`
   - Row-level validation errors (capture row number, column, issue)
   - Return partial success (e.g., "100 loaded, 5 failed - see details")
2. [ ] Download error report - file: `src/api/routers/upload.py`
   - GET `/api/upload/{upload_id}/errors` returns CSV of failed rows
3. [ ] Frontend error details - file: `web/src/pages/UploadPage.tsx`
   - "View Errors" button for failed uploads
   - Modal/table showing error details
4. [ ] File type selector - file: `web/src/components/FileUpload.tsx`
   - Optional: Manual file type selection (override auto-detection)
5. [ ] Multi-file upload queue - file: `web/src/components/FileUpload.tsx`
   - Upload multiple files sequentially
   - Queue display with individual progress bars
6. [ ] API rate limiting - file: `src/api/routers/upload.py`
   - Prevent upload spam (max 5 uploads per user per minute)

**Acceptance Criteria**:
- [ ] Failed rows exported as CSV for user review
- [ ] Users can view detailed validation errors
- [ ] Multiple files can be uploaded in queue
- [ ] Rate limiting prevents abuse

## Testing Strategy

### Unit Tests
- **Backend**:
  - `test_upload_service.py`: File validation, type detection, deduplication logic
  - `test_upload_router.py`: API endpoint validation, file handling
  - Mock file uploads, verify status updates
- **Frontend**:
  - `FileUpload.test.tsx`: Component rendering, file selection, validation
  - `uploadApi.test.ts`: API client methods with mocked responses

### Integration Tests
- `test_upload_integration.py`:
  - **Test 1: Standard upload (MB51)**
    * Upload MB51 file → Process → Verify records in `raw_mb51`
    * Upload same file again → Verify skipped_count > 0 (duplicates)
    * Modify Excel file → Upload → Verify updated_count > 0
  - **Test 2: AR monthly reset**
    * Upload AR file (Jan 5) → Verify snapshot_date = 2026-01-05
    * Upload AR file (Jan 6) → Verify upsert (same month)
    * Mock date to Feb 1 → Upload AR → Verify truncate + fresh insert
  - **Test 3: All file types**
    * Test each SAP file type: COOISPI, MB51, ZRMM024, ZRSD002, ZRSD004, ZRSD006, ZRFI005, TARGET
    * Verify business key uniqueness enforced
  - **Test 4: Error handling**
    * Upload invalid Excel (wrong headers) → Verify status='failed' with error details
    * Upload during DB lock → Verify transaction rollback
  - **Test 5: Concurrent uploads**
    * Upload 3 files simultaneously → Verify all processed correctly
    * No data corruption or conflicts

### E2E Tests
- Cypress/Playwright tests:
  - **E2E1: Successful upload flow**
    * Navigate to /upload page
    * Drag-drop valid MB51.xlsx file
    * See progress bar animate to 100%
    * See status change to "Processing" → "Completed"
    * Verify stats displayed (loaded, updated, skipped)
  - **E2E2: AR upload flow**
    * Upload AR file (Jan 5)
    * Navigate to AR Aging page
    * Verify date picker shows 2026-01-05
    * Select date → Verify data loads
  - **E2E3: Error handling**
    * Upload invalid file (wrong extension)
    * See client-side error message
    * Upload corrupt Excel file
    * See server-side error message
    * Click "View Errors" → See error details modal
  - **E2E4: Upload history**
    * Upload multiple files
    * Verify history table populates
    * Refresh page → History persists
    * Old pending uploads show correct status

## Security Considerations
- [ ] SEC1: Validate MIME type server-side using `python-magic` (not just extension)
- [ ] SEC2: Sanitize file paths to prevent directory traversal
- [ ] SEC3: Limit file size to 50MB (prevent DoS)
- [ ] SEC4: Store files outside web root (`demodata/uploads/`)
- [ ] SEC5: Generate random UUID filenames (prevent overwrites)
- [ ] SEC6: Future: Add authentication/authorization (only admin can upload)
- [ ] SEC7: Consider virus scanning for production (ClamAV integration)
- [ ] SEC8: Rate limiting on upload endpoint

## Risk Assessment
| Risk | Impact | Mitigation |
|------|--------|------------|
| Large file processing timeout | High | Use async background tasks; add timeout handling (5 min limit) |
| Concurrent uploads conflict | Medium | Use file locks or queue; test concurrent scenarios |
| Memory issues with huge files | High | Stream file processing with pandas `chunksize` param |
| Duplicate data corruption | High | Thorough testing of hash deduplication; add integration tests |
| Malicious file upload | High | MIME validation, size limits, path sanitization, virus scanning |
| Database transaction deadlock | Medium | Proper isolation levels; retry logic; timeout handling |

## Quick Reference

### Key Commands
```bash
# Backend
pip install -r requirements.txt
python -m src.main init  # Create upload_history table
uvicorn src.api.main:app --reload

# Frontend
cd web
npm install
npm run dev

# Testing
pytest tests/test_upload_service.py -v
pytest tests/test_upload_integration.py -v
npm test -- FileUpload.test.tsx
```

### Configuration Files
- `requirements.txt`: Add python-multipart, aiofiles, python-magic
- `.env`: No new env vars required (uses existing DB config)
- `web/package.json`: Add react-dropzone

### API Endpoints
```
POST   /api/upload              # Upload file
GET    /api/upload/{id}/status  # Get upload status
GET    /api/upload/{id}/errors  # Download error report (Phase 4)
GET    /api/upload/history      # List recent uploads (Phase 4)
```

## TODO Checklist

### Phase 1: Backend API Foundation (2 days)
- [ ] Install dependencies: `python-multipart`, `aiofiles`, `python-magic`
- [ ] Create `src/api/routers/upload.py` with POST /api/upload endpoint
- [ ] Create `src/core/upload_service.py` with file validation logic
- [ ] Add `UploadHistory` model to `src/db/models.py`
- [ ] Create migration: `upload_history` table
- [ ] Register upload router in `src/api/main.py`
- [ ] Test: Upload endpoint accepts .xlsx files, returns upload_id
- [ ] Test: Invalid files rejected with clear errors
- [ ] Test: Files saved to `demodata/uploads/` with UUID names

### Phase 2: ETL Integration & Processing (2 days)
- [ ] Add `snapshot_date` column to `RawZrfi005` and `FactArAging`
- [ ] Add `row_hash` column to all raw tables
- [ ] Add `UniqueConstraint` on business keys for all raw tables
- [ ] Create migration: Alter raw tables with constraints
- [ ] Implement `get_loader_for_type()` in `src/etl/loaders.py`
- [ ] Add `mode='upsert'` parameter to BaseLoader
- [ ] Implement upsert algorithm in BaseLoader (insert/update/skip)
- [ ] Implement AR special logic in Zrfi005Loader (monthly reset)
- [ ] Create `process_file()` in `src/core/upload_service.py`
- [ ] Create `cleanup_old_uploads()` scheduler
- [ ] Add GET /api/upload/{id}/status endpoint
- [ ] Test: Standard file upload → Verify upsert logic (insert/update/skip)
- [ ] Test: AR upload (same month) → Verify daily snapshot saved
- [ ] Test: AR upload (new month) → Verify truncate + fresh insert
- [ ] Test: Business key uniqueness enforced
- [ ] Test: File cleanup runs and deletes old files

### Phase 3: Frontend Upload UI (2 days)
- [ ] Install `react-dropzone` and `date-fns`
- [ ] Create `web/src/services/uploadApi.ts` with API client methods
- [ ] Create `web/src/components/FileUpload.tsx` with drag-drop zone
- [ ] Create `web/src/pages/UploadPage.tsx` with upload + history sections
- [ ] Add AR snapshot date picker to `web/src/pages/ARAgingPage.tsx`
- [ ] Add /upload route and menu item in `web/src/App.tsx`
- [ ] Style FileUpload component with CSS module
- [ ] Test: Drag-drop file → See progress bar → See status update
- [ ] Test: Upload history displays correctly with real-time updates
- [ ] Test: AR date picker loads historical snapshots
- [ ] Test: Mobile responsive design

### Phase 4: Advanced Features & Polish (1 day)
- [ ] Implement row-level validation errors in upload service
- [ ] Add GET /api/upload/{id}/errors endpoint (CSV download)
- [ ] Create error details modal in UploadPage
- [ ] Add optional file type selector (override auto-detection)
- [ ] Implement multi-file upload queue in FileUpload component
- [ ] Add API rate limiting (max 5 uploads/user/minute)
- [ ] Test: Failed rows exported as CSV
- [ ] Test: Users can view detailed validation errors
- [ ] Test: Multi-file queue uploads sequentially
- [ ] Test: Rate limiting prevents spam

### Final Steps
- [ ] Write unit tests for upload service (file validation, type detection)
- [ ] Write integration tests (all 5 test cases)
- [ ] Write E2E tests (all 4 scenarios)
- [ ] Code review: Ensure KISS, DRY principles
- [ ] Update API documentation in `docs/API_REFERENCE.md`
- [ ] Update codebase summary in `docs/codebase-summary.md`
- [ ] Performance testing: Upload 50MB file, verify <5 min processing
- [ ] Security review: MIME validation, path sanitization, rate limiting
- [ ] Deploy to staging environment
- [ ] User acceptance testing with sample AR data
- [ ] Deploy to production

## Notes & Decisions

### Technical Decisions
- **Decision**: Use FastAPI `BackgroundTasks` instead of Celery for simplicity (suitable for current scale, <100 uploads/day)
- **Decision**: Single-file upload in Phase 1-3; multi-file queue in Phase 4 (MVP focus)
- **Decision**: Polling (3-second interval) for status updates; WebSocket can be added later if real-time needs increase
- **Decision**: No user authentication in Phase 1-3 (add when auth system exists); rate limiting by IP address temporarily

### Upsert Logic Strategy
- **Business Keys**: Each table has unique business key constraint to prevent duplicates
- **Hash-based Change Detection**: `row_hash` column stores MD5 hash of entire row for efficient change detection
- **Three-way Upsert**:
  1. **INSERT**: Record with business key doesn't exist → New record
  2. **UPDATE**: Business key exists + hash different → Data changed
  3. **SKIP**: Business key exists + hash same → No change (saves DB writes)
- **Benefits**: 
  - Prevents duplicate data on repeated uploads
  - Allows incremental updates (e.g., daily AR corrections)
  - Efficient: Skip unchanged rows without DB writes

### AR (ZRFI005) Special Handling

**Context**: User uploads AR data daily to track account receivables within month. Each month resets and starts fresh.

**Implementation**:
```python
# Business key: (customer_name, dist_channel, snapshot_date)
# Allows multiple snapshots per customer per month

# Upload on Jan 5, 2026:
max_snapshot = db.query(func.max(RawZrfi005.snapshot_date)).scalar()  # None
is_new_month = True  # No data yet
→ TRUNCATE (no-op) → INSERT all rows with snapshot_date=2026-01-05

# Upload on Jan 6, 2026:
max_snapshot = 2026-01-05
is_new_month = (2026-01-06.month != 2026-01-05.month) = False
→ UPSERT with snapshot_date=2026-01-06
→ Creates new snapshot for same customers

# Upload on Feb 1, 2026:
max_snapshot = 2026-01-31 (last Jan upload)
is_new_month = (2026-02-01.month != 2026-01-31.month) = True
→ TRUNCATE raw_zrfi005 (delete all Jan data)
→ INSERT all rows with snapshot_date=2026-02-01
```

**Frontend Impact**:
- AR Aging page gets date picker: User selects snapshot date to view
- Default view: `MAX(snapshot_date)` (latest upload)
- Historical view: User can compare AR across days (e.g., Jan 5 vs Jan 15)
- API: `GET /api/ar-aging/snapshot?date=2026-01-05`

**Edge Cases**:
- **Multiple uploads same day**: Upsert by business key (customer, dist_channel, snapshot_date) → Update existing snapshot
- **Skip a day**: No problem, snapshots are independent (Jan 5, Jan 7, Jan 10 is valid)
- **Month with no uploads**: Next upload auto-detects new month and truncates

### Future Enhancements
- **Scheduled uploads**: Cron job or GitHub Actions to auto-upload from SFTP/email
- **Upload templates**: Downloadable Excel templates with example data for each SAP report type
- **Data preview**: Show first 10 rows before processing (user confirms)
- **Notifications**: Email/Slack notification on upload completion/failure
- **Audit log**: Track who uploaded what, when (requires auth system)
- **Bulk operations**: Truncate table, re-upload all files, etc. (admin panel)

## Unresolved Questions

1. **Should we support uploading to specific target tables, or auto-detect only?**
   - **Recommendation**: Auto-detect by default; optional manual override in Phase 4 file type selector
   - **Rationale**: User convenience (no need to select type) but flexibility for edge cases

2. **How to handle partial failures (e.g., 90% rows succeed, 10% fail)?**
   - **Recommendation**: Commit successful rows, log failed rows with details
   - **Rationale**: Business value in partial data; user can fix errors and re-upload
   - **Implementation**: Transaction per row vs. bulk transaction (trade-off: reliability vs. performance)

3. **Should old uploaded files be archived or deleted?**
   - **Recommendation**: Delete after 24 hours to save storage
   - **Alternative**: Add download link in upload history (user downloads before expiry)
   - **Future**: Archive to S3/cloud storage for audit trail

4. **Do we need upload scheduling (e.g., daily auto-import)?**
   - **Recommendation**: Not in MVP; add later if requested
   - **Potential**: GitHub Actions workflow to download SAP exports from SFTP and POST to /api/upload

5. **How to view AR historical snapshots?** (Daily uploads saved)
   - **Recommendation**: API endpoint to query by date range + frontend date picker
   - **Default view**: Latest snapshot (MAX snapshot_date)
   - **Historical view**: Date picker + AR trend chart across days in month
   - **Performance**: Index on `snapshot_date` for fast queries

6. **Should we validate data types/ranges during upload?**
   - **Recommendation**: Phase 1-3 focus on structural validation (columns exist, data parseable)
   - **Phase 4**: Add business logic validation (e.g., order_quantity > 0, valid date ranges)
   - **Trade-off**: Strict validation may reject valid edge cases; log warnings instead of hard failures

7. **How to handle Excel file variations (extra columns, different order)?**
   - **Recommendation**: Use column name matching (case-insensitive, ignore extra columns)
   - **Current behavior**: Loaders use `row.get('Column Name')` which is robust
   - **Risk**: Missing required columns should fail with clear error

8. **Concurrent uploads of same file type - race conditions?**
   - **Recommendation**: Database-level unique constraints prevent duplicates
   - **Upsert logic**: Last-write-wins for same business key
   - **Alternative**: Add file-level locks (complex, may not be needed at current scale)
  - Allows incremental updates (e.g., daily AR uploads)
  - Each table has unique business key combination
- **CRITICAL**: AR (zrfi005) follows same upsert logic as other tables
  - Business key: `customer_name + dist_channel`
  - Daily uploads will update existing customer records
- **Future Enhancement**: Add upload templates/examples for each SAP report type
- **Future Enhancement**: Scheduled uploads (cron-based automation)
- **Future Enhancement**: Data preview before processing (show first 10 rows)

## Unresolved Questions
1. Should we support uploading to specific target tables, or auto-detect only?
   - **Recommendation**: Auto-detect with optional manual override (Phase 4)
2. How to handle partial failures (e.g., 90% rows succeed, 10% fail)?
   - **Recommendation**: Commit successful rows, report failures with CSV export
3. Should old uploaded files be archived or deleted?
   - **Recommendation**: Delete after 24hrs (saves storage); add download link before deletion
4. Do we need upload scheduling (e.g., daily auto-import)?
   - **Recommendation**: Not in MVP; add later if requested
5. **How to handle AR monthly reset?** (User uploads new AR data each month)
   - **Recommendation**: Upsert will UPDATE existing customers with new values
   - If month changes significantly, user can manually truncate via admin panel (future feature)
   - Or add `report_month` column to AR table to track historical data

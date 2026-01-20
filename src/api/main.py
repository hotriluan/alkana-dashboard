"""
Alkana Dashboard API

FastAPI application for web dashboard.
Provides authentication, dashboards, and AR aging endpoints.

Follows CLAUDE.md: KISS, clean structure.

Run: uvicorn src.api.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import (
    alerts, lead_time,
    auth, ar_aging, mto_orders, 
    sales_performance, executive,
    inventory, upload, yield_v3
)


# Create FastAPI app
app = FastAPI(
    title="Alkana Dashboard API",
    description="ELT Analytics Dashboard with AR Collection Summary",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://localhost:5174",  # Vite alternate port
        "http://127.0.0.1:5173",  # Alternative localhost
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")
app.include_router(executive.router, prefix="/api/v1/dashboards")
app.include_router(inventory.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(lead_time.router, prefix="/api/v1")
app.include_router(ar_aging.router, prefix="/api/v1/dashboards")
app.include_router(inventory.router, prefix="/api/v1/dashboards")
app.include_router(mto_orders.router, prefix="/api/v1/dashboards")
app.include_router(sales_performance.router, prefix="/api/v1/dashboards")

# V3 API - Operational Efficiency Hub (Historical Trends)
app.include_router(yield_v3.router, prefix="/api/v3/yield", tags=["Yield V3"])

app.include_router(alerts.router)


# Health check endpoints
@app.get("/health")
async def health_check_root():
    """Health check endpoint at root"""
    return {
        "status": "healthy",
        "service": "alkana-dashboard-api",
        "version": "1.0.0"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "alkana-dashboard-api",
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - redirect to docs"""
    return {
        "message": "Alkana Dashboard API",
        "docs": "/api/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
Configuration settings for Alkana Dashboard
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DEMODATA_DIR = BASE_DIR / "demodata"

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:password@localhost:5432/alkana_dashboard"
)

# Excel file paths - ALL 9 source files
EXCEL_FILES = {
    "cooispi": DEMODATA_DIR / "cooispi.XLSX",
    "mb51": DEMODATA_DIR / "mb51.XLSX",
    "zrmm024": DEMODATA_DIR / "zrmm024.XLSX",
    "zrsd002": DEMODATA_DIR / "zrsd002.XLSX",
    "zrsd004": DEMODATA_DIR / "zrsd004.XLSX",
    "zrsd006": DEMODATA_DIR / "zrsd006.XLSX",
    "zrfi005": DEMODATA_DIR / "ZRFI005.XLSX",
    "zrpp062": DEMODATA_DIR / "zrpp062.XLSX",
    "target": DEMODATA_DIR / "target.xlsx",
}

# Plant roles (explicit designation)
PLANT_ROLES = {
    1201: "FACTORY",      # Nhà máy sản xuất
    1401: "DC",           # Distribution Center (Kho phân phối)
    1203: "OTHER",        # Other operations
}

# MVT reversal pairs (SAP standard)
MVT_REVERSAL_PAIRS = {
    101: 102,  # GR from Production ↔ Reversal
    102: 101,
    201: 202,  # GI to Cost Center ↔ Reversal
    202: 201,
    261: 262,  # GI to Production Order ↔ Reversal
    262: 261,
    301: 302,  # Transfer Plant-to-Plant ↔ Reversal
    302: 301,
    311: 312,  # Transfer SLoc-to-SLoc ↔ Reversal
    312: 311,
    351: 352,  # Transfer Between Plants ↔ Reversal
    352: 351,
    601: 602,  # GI for Delivery ↔ Reversal
    602: 601,
}

# Stock impact for each MVT
STOCK_IMPACT = {
    101: +1,   # GR from production
    102: -1,   # GR reversal
    201: -1,   # GI to cost center
    202: +1,   # GI reversal
    261: -1,   # GI to production order
    262: +1,   # Return from production
    301: 0,    # Transfer (net zero)
    302: 0,    # Transfer reversal
    311: 0,    # SLoc transfer
    312: 0,    # SLoc transfer reversal
    351: 0,    # Plant transfer
    352: 0,    # Plant transfer reversal
    601: -1,   # GI for delivery
    602: +1,   # Delivery reversal
}

# Alert thresholds
STUCK_IN_TRANSIT_HOURS = int(os.getenv("STUCK_IN_TRANSIT_HOURS", "48"))
LOW_YIELD_THRESHOLD = float(os.getenv("LOW_YIELD_THRESHOLD", "85"))

# MTO Classification
MTO_MRP_CONTROLLER = "P01"  # Only P01 with Sales Order = MTO

# Loaders package - V2 isolation strategy
# Import all legacy loaders from parent loaders.py file
import sys
from pathlib import Path

# Import legacy loaders from loaders.py (sibling file)
# This allows loaders/ folder to coexist with loaders.py
parent_dir = Path(__file__).parent.parent
loaders_file = parent_dir / 'loaders.py'

# Import module from file path
import importlib.util
spec = importlib.util.spec_from_file_location("loaders_legacy", loaders_file)
loaders_legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loaders_legacy)

# Re-export all legacy items
load_all_raw_data = loaders_legacy.load_all_raw_data
LOADERS = loaders_legacy.LOADERS
get_loader_for_type = loaders_legacy.get_loader_for_type
Zrfi005Loader = loaders_legacy.Zrfi005Loader
Zrsd002Loader = loaders_legacy.Zrsd002Loader
Mb51Loader = loaders_legacy.Mb51Loader

# Note: Zrpp062Loader removed during yield module decommissioning

__all__ = [
    'load_all_raw_data',
    'LOADERS', 
    'get_loader_for_type',
    'Zrfi005Loader',
    'Zrsd002Loader',
    'Mb51Loader'
]

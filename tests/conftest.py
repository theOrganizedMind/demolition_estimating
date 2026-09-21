import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ESTIMATE_PROJECT_DIR = PROJECT_ROOT / "estimate_project"
FINANCIALS_DIR = PROJECT_ROOT / "financials"

for path in (PROJECT_ROOT, ESTIMATE_PROJECT_DIR, FINANCIALS_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

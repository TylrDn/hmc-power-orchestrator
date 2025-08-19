import sys
from pathlib import Path

# Ensure src/ is on path for imports without installation
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

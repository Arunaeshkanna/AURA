import sys
from pathlib import Path


project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from aura.ui.app import *  # noqa: F401,F403,E402

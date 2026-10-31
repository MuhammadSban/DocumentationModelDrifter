# puts Source/ on the import path, as uvicorn --app-dir Source does for the app

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Source"))

# checks the drifter check script runs by path, as its header tells a developer to

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "Source" / "drifter" / "check.py"


def test_the_script_runs_by_path_and_prints_its_usage():
    proc = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)

    assert proc.returncode == 0, proc.stderr
    assert "check.py --repo" in proc.stdout

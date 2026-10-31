# runs one folder of the repository's pytest tests for the /tester page and reports each test's outcome

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# names the folders under tests/ the page offers, in page order
GROUPS = {
    "structural": "Structural model tests",
    "behavioral": "Behavioral model tests",
    "ownership": "Ownership model tests",
    "common": "Shared tests",
}

# caps one pytest run
TIMEOUT = 120


def run_group(group: str) -> dict:
    # runs pytest on tests/<group> in a separate process and reads its JUnit XML report
    folder = REPO_ROOT / "tests" / group
    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "report.xml"
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", str(folder), "-q", "-p", "no:cacheprovider", "--color=no",
                 f"--junitxml={report}"],
                cwd=REPO_ROOT, capture_output=True, text=True, timeout=TIMEOUT,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
        except subprocess.TimeoutExpired:
            return _answer(group, [], f"pytest ran past {TIMEOUT} s and was stopped")
        summary = (proc.stdout.strip().splitlines() or [""])[-1]
        if proc.returncode == 5:
            # exits with 5 when the folder has no tests yet
            return _answer(group, [], "no tests yet")
        if not report.exists():
            return _answer(group, [], f"pytest exited with {proc.returncode}: {summary or proc.stderr[-300:]}")
        return _answer(group, _cases(report), summary)


def _cases(report: Path) -> list[dict]:
    # turns each JUnit testcase into a name, an outcome and pytest's message
    cases = []
    for case in ET.parse(report).iter("testcase"):
        outcome, message = "pass", ""
        for tag, name in (("failure", "fail"), ("error", "error"), ("skipped", "skip")):
            found = case.find(tag)
            if found is not None:
                outcome, message = name, found.get("message", "")
                break
        module = case.get("classname", "").rpartition(".")[2]
        cases.append({"message": message, "name": f"{module}::{case.get('name', '')}", "outcome": outcome})
    return cases


def _answer(group: str, tests: list[dict], summary: str) -> dict:
    return {"group": group, "summary": summary, "tests": tests, "title": GROUPS[group]}

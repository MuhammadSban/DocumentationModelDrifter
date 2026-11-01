# checks the drawing rules of docs/agents/modeling.md that a machine can check

from __future__ import annotations

import re
from pathlib import Path

import pytest

MODELS = Path(__file__).resolve().parents[2] / "docs" / "models"
BLOCK = re.compile(r"```mermaid\n(.*?)```", re.S)


@pytest.mark.parametrize("md", sorted(MODELS.glob("*.md")), ids=lambda p: p.name)
def test_every_diagram_is_one_accessible_mermaid_block(md: Path) -> None:
    # checks one Mermaid block with accTitle and accDescr per diagram, a table-only page has none
    blocks = BLOCK.findall(md.read_text(encoding="utf-8"))
    if not blocks:
        return
    assert len(blocks) == 1, f"{md.name} must hold exactly one mermaid block"
    assert re.search(r"^\s*accTitle:", blocks[0], re.M), f"{md.name} lacks accTitle"
    assert re.search(r"^\s*accDescr:", blocks[0], re.M), f"{md.name} lacks accDescr"

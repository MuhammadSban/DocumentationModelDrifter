# checks the drawing rules of docs/agents/modeling.md that a machine can check

from __future__ import annotations

import re
from pathlib import Path

import pytest

MODELS = Path(__file__).resolve().parents[2] / "docs" / "models"
BLOCK = re.compile(r"```mermaid\n(.*?)```", re.S)


def _blocks(md: Path) -> list[str]:
    # returns the Mermaid blocks of one Markdown file
    return BLOCK.findall(md.read_text(encoding="utf-8"))


@pytest.mark.parametrize("png", sorted(MODELS.glob("*.png")), ids=lambda p: p.name)
def test_every_picture_has_its_mermaid_source(png: Path) -> None:
    # rejects a hand-drawn picture, every PNG is rendered from the Markdown beside it
    md = png.with_suffix(".md")
    assert md.is_file(), f"{png.name} has no {md.name}"
    assert len(_blocks(md)) == 1, f"{md.name} must hold exactly one mermaid block"


@pytest.mark.parametrize("md", sorted(MODELS.glob("*.md")), ids=lambda p: p.name)
def test_every_diagram_is_accessible_and_rendered(md: Path) -> None:
    # checks accTitle, accDescr and a rendered PNG for each diagram, a table-only page has none
    blocks = _blocks(md)
    if not blocks:
        return
    assert len(blocks) == 1, f"{md.name} must hold exactly one mermaid block"
    assert re.search(r"^\s*accTitle:", blocks[0], re.M), f"{md.name} lacks accTitle"
    assert re.search(r"^\s*accDescr:", blocks[0], re.M), f"{md.name} lacks accDescr"
    assert md.with_suffix(".png").is_file(), f"{md.name} is not rendered, run python docs/models/render.py"

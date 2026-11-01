# renders each docs/models/*.md's Mermaid block to a PNG beside it, the only way the PNGs are made
#
# usage: python docs/models/render.py [name ...]   (no names renders every diagram)
# needs Node (npx) and Chrome; CHROME overrides the browser path

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
# pins the renderer, so the same Markdown always gives the same picture
MMDC = "@mermaid-js/mermaid-cli@11.12.0"
BLOCK = re.compile(r"```mermaid\n(.*?)```", re.S)
CHROME = os.environ.get("CHROME", r"C:\Program Files\Google\Chrome\Application\chrome.exe")


def render(md: Path, tmp: Path) -> None:
    # extracts the one Mermaid block and writes <name>.png at twice the default scale; a page with none is a table, not a diagram
    blocks = BLOCK.findall(md.read_text(encoding="utf-8"))
    if not blocks:
        return
    if len(blocks) != 1:
        sys.exit(f"{md.name}: expected one mermaid block, found {len(blocks)}")
    src = tmp / f"{md.stem}.mmd"
    src.write_text(blocks[0], encoding="utf-8")
    cmd = ["npx", "-y", MMDC, "-q", "-p", str(tmp / "p.json"), "-s", "2", "-b", "white",
           "-i", str(src), "-o", str(md.with_suffix(".png"))]
    subprocess.run(cmd, check=True, shell=os.name == "nt", env={**os.environ, "PUPPETEER_SKIP_DOWNLOAD": "true"})
    print(f"rendered {md.with_suffix('.png').name}")


def main() -> None:
    # renders the named diagrams, or all of them
    names = sys.argv[1:]
    files = [HERE / f"{n}.md" for n in names] if names else sorted(HERE.glob("*.md"))
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "p.json").write_text(json.dumps({"executablePath": CHROME}), encoding="utf-8")
        for md in files:
            render(md, tmp)


if __name__ == "__main__":
    main()

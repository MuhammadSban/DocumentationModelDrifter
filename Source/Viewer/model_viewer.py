# shows a repository's models on one page, rendered from the loader's data structure
#
#   PYTHONPATH=Source python -m Viewer.model_viewer <models-dir> [-o page.html]
#
# the page is static HTML: no server, no scripts, no network

from __future__ import annotations

import argparse
import sys
from collections import Counter
from html import escape
from pathlib import Path

from Viewer.model_loader import (
    OWNERSHIP_FILE,
    STRUCTURAL_FILE,
    Models,
    Node,
    OwnershipModel,
    StructuralModel,
    load_models,
)

STYLE = """
  :root {
    --bg: #eceef2; --panel: #ffffff; --raised: #f5f6f8; --text: #15181e; --muted: #5d6471;
    --line: #dfe2e8; --accent: #2447b8; --accent-soft: #e6ebfa;
    --sans: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
    --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0f1216; --panel: #171b21; --raised: #1d2229; --text: #e8ebf0; --muted: #9aa3b2;
      --line: #2a3039; --accent: #8fb0ff; --accent-soft: #1f2a45;
    }
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--text); font: 15px/1.5 var(--sans); }
  main { max-width: 1080px; margin: 0 auto; padding: 36px 16px 72px; }
  h1, h2 { margin: 0; font-weight: 600; letter-spacing: -.01em; }
  h1 { font-size: 26px; }
  h2 { font-size: 17px; }
  p { margin: 0; color: var(--muted); }
  code, .mono { font: 500 .92em var(--mono); }
  .top { margin-bottom: 24px; }
  .panel { background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
           padding: 22px 24px; margin-bottom: 20px; }
  .meta { display: flex; flex-wrap: wrap; gap: 6px 20px; margin: 10px 0 18px; font-size: 13px;
          color: var(--muted); }
  .meta b { color: var(--text); font-weight: 600; }
  .wrap { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--line);
           vertical-align: top; }
  th { position: sticky; top: 0; background: var(--raised); font-size: 12px;
       text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }
  tr:last-child td { border-bottom: 0; }
  .kind { display: inline-block; padding: 1px 7px; border-radius: 5px; background: var(--accent-soft);
          color: var(--accent); font-size: 12px; font-weight: 600; }
  .chip { display: inline-block; margin: 0 4px 2px 0; padding: 1px 7px; border-radius: 5px;
          background: var(--raised); border: 1px solid var(--line); font-size: 12px; }
  .none { color: var(--muted); font-style: italic; }
"""


def render(models: Models) -> str:
    # renders the whole page: one panel per model, in the order a reader meets them
    sections = [
        _structural(models.structural),
        _ownership(models.ownership),
    ]
    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="color-scheme" content="light dark">\n'
        "<title>Models</title>\n"
        f"<style>{STYLE}</style>\n</head>\n<body>\n<main>\n"
        f'<div class="top">\n<h1>Models</h1>\n<p class="mono">{escape(str(models.models_dir))}</p>\n</div>\n'
        + "\n".join(sections)
        + "\n</main>\n</body>\n</html>\n"
    )


def _structural(model: StructuralModel | None) -> str:
    # shows what exists in the code and how it links: the node kinds, then the nodes and the edges
    if model is None:
        return _missing("Structural", STRUCTURAL_FILE)
    kinds = Counter(node.kind for node in model.nodes)
    meta = [
        f"schema_version <b>{escape(str(model.schema_version))}</b>",
        f"<b>{len(model.nodes)}</b> nodes",
        f"<b>{len(model.edges)}</b> edges",
        *(f"<b>{count}</b> {escape(kind)}" for kind, count in sorted(kinds.items())),
    ]
    nodes = _table(
        ("id", "kind", "signature", "file"),
        [
            (
                f'<span class="mono">{escape(node.id)}</span>',
                f'<span class="kind">{escape(node.kind)}</span>',
                _signature(node),
                f'<span class="mono">{escape(node.file)}</span>',
            )
            for node in model.nodes
        ],
    )
    edges = _table(
        ("kind", "source", "target"),
        [
            (
                f'<span class="kind">{escape(edge.kind)}</span>',
                f'<span class="mono">{escape(edge.source)}</span>',
                f'<span class="mono">{escape(edge.target)}</span>',
            )
            for edge in model.edges
        ],
    )
    return _panel("Structural", meta, f"{nodes}\n<h2>Edges</h2>\n{edges}")


def _ownership(model: OwnershipModel | None) -> str:
    # shows which authors own which files; a file with no rule is absent, being open to anyone
    if model is None:
        return _missing("Ownership", OWNERSHIP_FILE)
    owners = sorted({owner for rule in model.rules for owner in rule.owners})
    meta = [
        f"schema_version <b>{escape(str(model.schema_version))}</b>",
        f"<b>{len(model.rules)}</b> rules",
        f"<b>{len(owners)}</b> owners",
    ]
    rows = _table(
        ("path", "owners"),
        [
            (
                f'<span class="mono">{escape(rule.path)}</span>',
                _owners(rule.owners),
            )
            for rule in model.rules
        ],
    )
    return _panel("Ownership", meta, rows)


def _signature(node: Node) -> str:
    # writes a function or method as it reads in the source, empty for a module or class
    if node.kind not in ("function", "method"):
        return ""
    decorators = "".join(f'<span class="chip">@{escape(d)}</span>' for d in node.decorators)
    prefix = "async " if node.is_async else ""
    params = escape(", ".join(node.params))
    name = escape(node.id.rpartition(":")[2].rpartition(".")[2])
    return f'{decorators}<span class="mono">{prefix}{name}({params})</span>'


def _owners(owners: tuple[str, ...]) -> str:
    # lists one rule's owners; a rule with an empty list is never written, so this says so loudly
    if not owners:
        return '<span class="none">none</span>'
    return "".join(f'<span class="chip">{escape(owner)}</span>' for owner in owners)


def _panel(title: str, meta: list[str], body: str) -> str:
    # wraps one model in a panel: its title, its counts, then its tables
    return (
        f'<section class="panel">\n<h2>{escape(title)}</h2>\n'
        f'<div class="meta">{"".join(f"<span>{item}</span>" for item in meta)}</div>\n'
        f"{body}\n</section>"
    )


def _missing(title: str, filename: str) -> str:
    # says a model is absent, which is not the same as a model that is empty
    return (
        f'<section class="panel">\n<h2>{escape(title)}</h2>\n'
        f'<p>No <code>{escape(filename)}</code> in this folder.</p>\n</section>'
    )


def _table(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> str:
    # renders one table of cells already escaped by its caller
    if not rows:
        return '<p class="none">empty</p>'
    head = "".join(f"<th>{escape(header)}</th>" for header in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>\n" for row in rows
    )
    return f'<div class="wrap">\n<table>\n<thead><tr>{head}</tr></thead>\n<tbody>\n{body}</tbody>\n</table>\n</div>'


def main(argv: list[str] | None = None) -> int:
    # renders one models folder to a file, or to stdout where no -o is given
    parser = argparse.ArgumentParser(description="render a repository's models as one HTML page")
    parser.add_argument("models_dir", help="the folder holding structural.json and ownership.json")
    parser.add_argument("-o", "--out", help="write the page here instead of stdout")
    args = parser.parse_args(argv)

    page = render(load_models(args.models_dir))
    if args.out:
        Path(args.out).write_text(page, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(page)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

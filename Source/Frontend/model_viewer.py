# shows a repository's models on one page, rendered from the loader's data structure
#
#   PYTHONPATH=Source python -m Frontend.model_viewer <models-dir> [-o page.html]
#
# the page is static HTML: no server, no scripts, no network

from __future__ import annotations

import argparse
import sys
from collections import Counter
from html import escape
from pathlib import Path

from models.common import glob
from Frontend.model_loader import (
    OWNERSHIP_FILE,
    SCOPE_FILE,
    STRUCTURAL_FILE,
    Models,
    Node,
    OwnershipModel,
    OwnershipRule,
    Scope,
    StructuralModel,
    load_models,
)

# the categorical palette's eight slots, in the fixed order that validates in both modes
# (dataviz references/palette.md). A ninth contributor and beyond share one neutral slot:
# a hue is never generated or cycled, and colour only reinforces the name in each heading.
OWNER_SLOTS = 8

# caps the staggered entrance, so a page of forty contributors does not open for two seconds
STAGGER_STEPS = 8

# draws the diagrams in the browser, pinned so the same model always draws the same picture;
# docs/models/render.py pins the same major for the PNGs it makes of the hand-drawn diagrams
MERMAID = "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs"

# the one stylesheet, beside this module, read at render time and inlined so a saved page needs
# nothing beside it (Source/Frontend/app.css)
STYLE = (Path(__file__).resolve().parent / "app.css").read_text(encoding="utf-8")


def render(models: Models) -> str:
    # renders the whole page: one panel per model, in the order a reader meets them
    sections = [
        _structural(models.structural),
        _ownership(models.ownership, models.scope),
    ]
    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="color-scheme" content="light dark">\n'
        '<meta name="theme-color" content="#eceef2" media="(prefers-color-scheme: light)">\n'
        '<meta name="theme-color" content="#0f1216" media="(prefers-color-scheme: dark)">\n'
        "<title>Models</title>\n"
        f"<style>{STYLE}</style>\n</head>\n<body>\n<main>\n"
        f'<div class="top">\n<h1>Models</h1>\n<p class="mono">{escape(str(models.models_dir))}</p>\n</div>\n'
        + "\n".join(sections)
        + "\n</main>\n"
        + _script()
        + "\n</body>\n</html>\n"
    )


def _structural(model: StructuralModel | None) -> str:
    # shows the code as two models, each answering one question and holding only what that
    # question needs (docs/agents/modeling.md): which parts depend on which, and which types
    # extend which. Everything the question does not need is counted, never drawn, so a diagram
    # carries a shape instead of a grid of facts.
    if model is None:
        return _missing("Structural", STRUCTURAL_FILE)
    kinds = Counter(node.kind for node in model.nodes)
    meta = [
        f"schema_version <b>{escape(str(model.schema_version))}</b>",
        *(
            f"<b>{kinds[kind]}</b> {_plural(kinds[kind], kind)}"
            for kind in ("module", "class", "function", "method")
            if kinds[kind]
        ),
        f"<b>{len(model.edges)}</b> {_plural(len(model.edges), 'edge')}",
    ]
    return _panel("Structural", meta, _components(model) + _classes(model))


def _components(model: StructuralModel) -> str:
    # the component model, split so that each picture runs down the page instead of across it:
    # one diagram of the packages and the imports between them, then one small diagram per
    # package of the imports inside it. A layered layout turns fan-out into width, so one
    # diagram of every module is unreadable however large it is drawn; two scales are legible.
    edges = [edge for edge in model.edges if edge.kind == "imports"]
    folder = {
        node.id: _folder(node.file) for node in model.nodes if node.kind == "module"
    }
    pairs = [(folder[e.source], folder[e.target]) for e in edges if e.source in folder and e.target in folder]
    across = Counter(pair for pair in pairs if pair[0] != pair[1])
    inside: dict[str, list[tuple[str, str]]] = {}
    for edge in edges:
        if folder.get(edge.source) and folder.get(edge.source) == folder.get(edge.target):
            inside.setdefault(folder[edge.source], []).append((edge.source, edge.target))
    drawn = {end for pair in across for end in pair} | set(inside)
    if not edges:
        return _figure(
            "Packages",
            "Which parts of this repository depend on which?",
            None,
            f"No module imports another module of this repository, so there is nothing to draw. "
            f"All {len(folder)} {_plural(len(folder), 'module')} stand alone.",
        )
    return _packages(across, folder) + _insides(inside, folder, drawn)


def _packages(across: Counter, folder: dict[str, str]) -> str:
    # the folders and the imports between them, each arrow carrying how many there are, so the
    # whole repository's shape is one small picture
    if not across:
        return _figure(
            "Packages",
            "Which packages depend on which?",
            None,
            "No package imports another, so every import stays inside its own folder.",
        )
    names = sorted({end for pair in across for end in pair})
    ids = {name: f"p{n}" for n, name in enumerate(names)}
    lines = [
        "flowchart TB",
        "    accTitle: Which packages depend on which",
        "    accDescr: Each box is a folder of this repository. Each arrow runs from the folder "
        "that imports to the folder it imports, labelled with how many of its modules do so.",
    ]
    lines += [f'    {ids[name]}["{name}"]' for name in names]
    lines += [
        f"    {ids[source]} -->|{count}| {ids[target]}"
        for (source, target), count in sorted(across.items())
    ]
    alone = len({f for f in folder.values()}) - len(names)
    return _figure(
        "Packages",
        "Which packages depend on which?",
        "\n".join(lines),
        f"{alone} {_plural(alone, 'package')} left out, importing no other package."
        if alone > 0
        else "",
    )


def _insides(
    inside: dict[str, list[tuple[str, str]]], folder: dict[str, str], drawn: set[str]
) -> str:
    # one diagram per package, holding only the modules that import each other inside it, so
    # each picture is a handful of boxes rather than the whole repository
    if not inside:
        return ""
    figures = []
    for name, pairs in sorted(inside.items()):
        modules = sorted({end for pair in pairs for end in pair})
        ids = {module: f"m{n}" for n, module in enumerate(modules)}
        lines = [
            "flowchart TB",
            f"    accTitle: The imports inside {name}",
            "    accDescr: Each box is a module of this folder. Each arrow runs from the module "
            "that imports to the module it imports.",
        ]
        lines += [f'    {ids[module]}["{_short(module)}"]' for module in modules]
        lines += [f"    {ids[source]} --> {ids[target]}" for source, target in sorted(pairs)]
        figures.append(
            f'<p class="caption mono">{escape(name)}</p>'
            f'<div class="figure"><pre class="mermaid">{escape(chr(10).join(lines))}</pre></div>'
            f'<details class="source"><summary>Mermaid source</summary>'
            f"<pre>{escape(chr(10).join(lines))}</pre></details>"
        )
    skipped = len(folder) - len(
        {module for pairs in inside.values() for pair in pairs for module in pair}
    )
    note = (
        f'<p class="omitted of">{skipped} '
        f"{_plural(skipped, 'module')} left out of these, importing nothing inside their own "
        f"folder.</p>"
        if skipped > 0
        else ""
    )
    return (
        '<section class="diagram"><h3>Modules in each package</h3>'
        '<p class="question">Inside one package, which module depends on which?</p>'
        f'{"".join(figures)}{note}</section>\n'
    )


def _classes(model: StructuralModel) -> str:
    # the class model: only the classes that extend another class of this repository, with their
    # own members, and one arrow per inheritance. A class that extends nothing here is counted
    # instead of drawn: this model answers what extends what, and a lone box answers nothing.
    edges = [edge for edge in model.edges if edge.kind == "inherits"]
    classes = {node.id: node for node in model.nodes if node.kind == "class"}
    joined = {end for edge in edges for end in (edge.source, edge.target)} & set(classes)
    question = "Which types extend which, and what do they carry?"
    if not joined:
        return _figure(
            "Classes",
            question,
            None,
            f"No class extends another class of this repository, so there is nothing to draw. "
            f"A base class from outside, such as Exception or BaseModel, is not an edge "
            f"(structure.md). All {len(classes)} {_plural(len(classes), 'class')} stand alone.",
        )
    names = _class_names(joined)
    members: dict[str, list[Node]] = {}
    for node in model.nodes:
        if node.kind == "method":
            owner = node.id.rpartition(".")[0]
            if owner in joined:
                members.setdefault(owner, []).append(node)
    lines = [
        "classDiagram",
        "    accTitle: Which types extend which",
        "    accDescr: Each box is a class that takes part in an inheritance, with the methods it "
        "defines. Each arrow points from a class to the class it extends.",
    ]
    for class_id in sorted(joined):
        own = sorted(members.get(class_id, ()), key=lambda n: n.id)
        if not own:
            lines.append(f"    class {names[class_id]}")
            continue
        lines.append(f"    class {names[class_id]} {{")
        lines += [f"        +{_mermaid_member(node)}" for node in own]
        lines.append("    }")
    for edge in sorted(edges, key=lambda e: e.id):
        if edge.source in names and edge.target in names:
            lines.append(f"    {names[edge.target]} <|-- {names[edge.source]}")
    alone = len(classes) - len(joined)
    omitted = (
        f"{alone} {_plural(alone, 'class')} left out, extending no class of this repository."
        if alone
        else ""
    )
    return _figure("Classes", question, "\n".join(lines), omitted)


def _class_names(ids: set[str]) -> dict[str, str]:
    # names each drawn class as it reads in the source, falling back to its module where two
    # modules of this repository give a class the same name
    short = Counter(class_id.rpartition(":")[2] for class_id in ids)
    return {
        class_id: _mermaid_name(
            class_id.rpartition(":")[2]
            if short[class_id.rpartition(":")[2]] == 1
            else class_id.replace(":", ".")
        )
        for class_id in ids
    }


def _mermaid_name(name: str) -> str:
    # keeps a class name to what Mermaid accepts as an identifier
    return "".join(c if c.isalnum() or c == "_" else "_" for c in name)


def _mermaid_member(node: Node) -> str:
    # writes one method as Mermaid reads a member: its name and the parameters it takes, with
    # the signature's markers dropped, since Mermaid's parser has its own meaning for them
    params = ", ".join(p.lstrip("*") for p in node.params if p.strip("*"))
    return f"{_mermaid_name(node.id.rpartition('.')[2])}({params})"


def _short(module: str) -> str:
    # labels a box with the module's own name, the folder around it already saying where it sits,
    # so the words in a box stay large enough to read
    return module.rpartition(".")[2] or module


def _figure(title: str, question: str, source: str | None, omitted: str) -> str:
    # one diagram: the question it answers, the picture, what was left out of it, and the Mermaid
    # it was drawn from, which is the one copy of it (docs/agents/modeling.md)
    drawn = (
        f'<div class="figure"><pre class="mermaid">{escape(source)}</pre></div>\n'
        f"<details class=\"source\"><summary>Mermaid source</summary>"
        f"<pre>{escape(source)}</pre></details>"
        if source
        else ""
    )
    note = f'<p class="omitted of">{escape(omitted)}</p>' if omitted else ""
    return (
        f'<section class="diagram"><h3>{escape(title)}</h3>'
        f'<p class="question">{escape(question)}</p>{drawn}{note}</section>\n'
    )


def _ownership(model: OwnershipModel | None, scope: Scope | None) -> str:
    # shows ownership as one section per contributor: how much of the code they own, the folders
    # they own it in, and who they share it with. Every section carries the same map, so two
    # territories are compared by scanning down the page. A path no rule matches appears in no
    # section at all, being open to anyone (spec 3.2).
    if model is None:
        return _missing("Ownership", OWNERSHIP_FILE)
    rules = tuple(rule for rule in model.rules if _is_code(rule.pattern, scope))
    hidden = len(model.rules) - len(rules)
    owned = _by_owner(rules)
    slots = {email: index for index, email in enumerate(owned)}
    folders = Counter(_folder(rule.pattern) for rule in rules)
    meta = [
        f"schema_version <b>{escape(str(model.schema_version))}</b>",
        f"<b>{len(rules)}</b> {_plural(len(rules), 'path')}",
        f"<b>{len(owned)}</b> {_plural(len(owned), 'contributor')}",
        *(
            [f"<b>{hidden}</b> outside {escape(SCOPE_FILE)}, not shown"]
            if hidden
            else []
        ),
    ]
    sections = "\n".join(
        _contributor(email, owned_rules, len(rules), folders, slots)
        for email, owned_rules in owned.items()
    )
    body = (
        f'<div class="owners">\n{sections}\n</div>'
        if sections
        else '<p class="none">no rules over code, so every path is open to anyone</p>'
    )
    return _panel("Ownership", meta, body)


def _is_code(pattern: str, scope: Scope | None) -> bool:
    # keeps the paths scope.json calls code, which is what the models describe, and keeps any
    # pattern that is not one path, since a folder rule can still reach code. Without a
    # scope.json nothing is trimmed: the viewer never guesses what counts as code.
    if scope is None or "*" in pattern:
        return True
    return any(glob(p).match(pattern) for p in scope.include) and not any(
        glob(p).match(pattern) for p in scope.exclude
    )


def _by_owner(rules: tuple[OwnershipRule, ...]) -> dict[str, list[OwnershipRule]]:
    # groups the rules by contributor, the widest owner first, so the page reads top down
    owned: dict[str, list[OwnershipRule]] = {}
    for rule in rules:
        for owner in rule.owners:
            owned.setdefault(owner, []).append(rule)
    return dict(sorted(owned.items(), key=lambda item: (-len(item[1]), item[0])))


def _folder(pattern: str) -> str:
    # names the folder a pattern sits in, the repository root being a group of its own
    return pattern.rpartition("/")[0] or "(root)"


def _contributor(
    email: str,
    rules: list[OwnershipRule],
    total: int,
    folders: Counter,
    slots: dict[str, int],
) -> str:
    # one contributor's section: their share of the repository, a mark per path in each folder
    # they own in, the people they share paths with, and the paths themselves
    index = slots[email]
    mine = Counter(_folder(rule.pattern) for rule in rules)
    sole = sum(1 for rule in rules if len(rule.owners) == 1)
    others = Counter(other for rule in rules for other in rule.owners if other != email)
    rows = "".join(
        _folder_row(folder, count, folders[folder])
        for folder, count in sorted(mine.items(), key=lambda item: (-item[1], item[0]))
    )
    share = f"{100 * len(rules) / total:.0f}" if total else "0"
    return (
        f'<section class="owner" id="{_anchor(index)}"'
        f' style="--c: {_slot(index)}; --i: {min(index, STAGGER_STEPS)}">\n'
        f'<header class="owner-head"><span class="swatch" aria-hidden="true"></span>'
        f'<h3 class="who">{escape(email)}</h3>'
        f'<span class="tally">{len(rules)}<span class="of"> of {total} {_plural(total, "path")}</span></span></header>\n'
        f'<div class="share" aria-hidden="true"><span style="width: {share}%"></span></div>\n'
        f'<p class="sub">{sole} owned alone <span class="of">&middot;</span> {len(rules) - sole} shared'
        f'<span class="of"> &middot; {share}% of the owned paths</span></p>\n'
        f'<div class="map">{rows}</div>\n'
        f"{_shares_with(others, slots)}"
        f"{_paths(rules)}\n</section>"
    )


def _folder_row(folder: str, mine: int, total: int) -> str:
    # one folder as a mark per path: this contributor's filled, the rest of the folder faint, so
    # the row reads as how much of that folder is theirs
    marks = '<i class="dot on"></i>' * mine + '<i class="dot"></i>' * (total - mine)
    return (
        '<div class="row">'
        f'<span class="where">{escape(folder)}</span>'
        f'<span class="dots" aria-hidden="true">{marks}</span>'
        f'<span class="count">{mine}<span class="of"> of {total}</span></span>'
        "</div>"
    )


def _shares_with(others: Counter, slots: dict[str, int]) -> str:
    # names the co-owners, each linking to their own section, so a shared path is followed both ways
    if not others:
        return '<p class="with of">owns every one of these paths alone</p>\n'
    links = "".join(
        f'<a href="#{_anchor(slots[email])}" style="--c: {_slot(slots[email])}">'
        f'<span class="swatch" aria-hidden="true"></span>{escape(email)}'
        f'<span class="of">{count}</span></a>'
        for email, count in sorted(others.items(), key=lambda item: (-item[1], item[0]))
    )
    return f'<p class="with"><span class="of">shares with</span> {links}</p>\n'


def _paths(rules: list[OwnershipRule]) -> str:
    # lists the patterns themselves: the reading of this section that needs no colour or marks
    items = "".join(f"<li>{escape(rule.pattern)}</li>" for rule in rules)
    return (
        f'<details><summary>{len(rules)} {_plural(len(rules), "path")}</summary>'
        f"<ul>{items}</ul></details>"
    )


def _plural(count: int, word: str) -> str:
    # keeps a count and its noun in step, so a section never reads "1 paths" or "2 classs"
    if count == 1:
        return word
    return word + ("es" if word.endswith("s") else "s")


def _anchor(index: int) -> str:
    # names one contributor's section, so a co-owner link can reach it
    return f"owner-{index}"


def _slot(index: int) -> str:
    # gives one contributor their categorical slot, everyone past the eighth sharing the neutral
    return f"var(--s{min(index + 1, OWNER_SLOTS + 1)})"


def _script() -> str:
    # draws the Mermaid blocks, in the theme the page is being read in. The page needs the network
    # only for this: every diagram's source is in the page, so a blocked CDN loses the pictures
    # and nothing else.
    return (
        '<script type="module">\n'
        f'import mermaid from "{MERMAID}";\n'
        'const dark = matchMedia("(prefers-color-scheme: dark)").matches;\n'
        'mermaid.initialize({ startOnLoad: true, securityLevel: "strict",\n'
        '  theme: dark ? "dark" : "neutral",\n'
        # useMaxWidth off: Mermaid otherwise fits the picture to the page and the words shrink
        # with it, so the picture is drawn at its own size and the figure scrolls
        '  flowchart: { curve: "basis", nodeSpacing: 26, rankSpacing: 40 },\n'
        '  class: { useMaxWidth: true },\n'
        '  themeVariables: { fontSize: "15px" },\n'
        '  fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" });\n'
        "</script>"
    )


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

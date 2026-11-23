# builds the structural model from supported source: module, class, function and method nodes,
# with imports and inherits edges between this repository's own modules and classes

from __future__ import annotations

import ast

from models.common import JAVASCRIPT_EXTENSIONS, parse_files

SCHEMA_VERSION = 1

FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)

# how much of the code the model describes, set by scope.json's verbosity key. Each level keeps
# everything the level below it keeps, so a level is a subset of the one above; FULL is what this
# generator has always written, and is the default (docs/closed/E02-model-parameters/DESIGN.md).
OVERVIEW, TYPES, MEMBERS, FULL = 1, 2, 3, 4

# names the node kinds each level keeps. Edges follow from the nodes rather than from a table of
# their own: an edge is kept only where both of its ends are, so imports edges, which join two
# modules, survive every level, and inherits edges arrive with the classes they join.
KEPT_KINDS = {
    OVERVIEW: ("module",),
    TYPES: ("module", "class"),
    MEMBERS: ("module", "class", "function", "method"),
    FULL: ("module", "class", "function", "method"),
}

# names the signature attributes only FULL carries (structure.md), dropped from a node below it
SIGNATURE = ("async", "decorators", "params")

# how many nodes of each kind a level keeps. This is what makes a lower level a smaller picture
# and not just a narrower one: without it every level draws all 30 modules of this repository and
# the diagrams are identical. None means every one of that kind.
#
# Which ones are kept is decided by how many edges touch a node, most first, with the id breaking
# ties: the parts other parts depend on are the ones an overview is about. The ranking uses the
# whole model's edges, which no level changes for a module, so a level's nodes are always a subset
# of the level above it.
BUDGETS = {
    OVERVIEW: {"module": 6},
    TYPES: {"module": 12, "class": 8},
    MEMBERS: {"module": 20, "class": 15, "function": 20, "method": 20},
    FULL: {},
}


def _busiest(kept: list[dict], edges: dict[str, dict], verbosity: int) -> list[dict]:
    # keeps the most connected nodes of each kind, up to that kind's budget for this level
    budgets = BUDGETS[verbosity]
    if not budgets:
        return kept
    degree: dict[str, int] = {}
    for edge in edges.values():
        degree[edge["source"]] = degree.get(edge["source"], 0) + 1
        degree[edge["target"]] = degree.get(edge["target"], 0) + 1
    out = []
    for kind, group in _by_kind(kept).items():
        limit = budgets.get(kind)
        if limit is None or len(group) <= limit:
            out += group
            continue
        out += sorted(group, key=lambda n: (-degree.get(n["id"], 0), n["id"]))[:limit]
    return out


def _by_kind(kept: list[dict]) -> dict[str, list[dict]]:
    # groups nodes by kind, so each kind is budgeted against its own and not against the others
    groups: dict[str, list[dict]] = {}
    for node in kept:
        groups.setdefault(node["kind"], []).append(node)
    return groups


def generate_structural(files: dict[str, str], verbosity: int = FULL) -> dict:
    # returns the structural model of files (repo-relative path -> text), raises ParseFailed
    # if any file is not valid source. verbosity trims what the model describes, FULL being
    # everything; the core validates the committed value before calling.
    if verbosity not in KEPT_KINDS:
        raise ValueError(f"verbosity {verbosity!r} is not one of {sorted(KEPT_KINDS)}")
    trees = parse_files(files)
    modules = {path: module_id(path) for path in trees}
    known = set(modules.values())

    nodes: dict[str, dict] = {}
    classes: list[tuple[str, str, ast.ClassDef]] = []
    for path, tree in trees.items():
        mod = modules[path]
        nodes[mod] = {"file": path, "id": mod, "kind": "module"}
        _collect(tree.body, mod, "", path, nodes, classes)

    edges: dict[str, dict] = {}
    names: dict[str, dict[str, str]] = {}
    for path, tree in trees.items():
        mod = modules[path]
        names[mod] = _imports(tree, mod, _package(path, mod), path, known, edges)
        # binds the module's own top-level definitions, after its imports
        for stmt in tree.body:
            if isinstance(stmt, (ast.ClassDef, *FUNCTIONS)):
                names[mod][stmt.name] = f"{mod}:{stmt.name}"

    for path, class_id, stmt in classes:
        mod = class_id.split(":", 1)[0]
        for base in stmt.bases:
            target = _resolve(base, names[mod], known)
            if target in nodes and nodes[target]["kind"] == "class":
                _edge(edges, "inherits", class_id, target, path)

    return _at_level(nodes, edges, verbosity)


def _at_level(nodes: dict[str, dict], edges: dict[str, dict], verbosity: int) -> dict:
    # trims the model to one level: how many nodes of each kind it keeps, the kinds it keeps at
    # all, the signature attributes only FULL carries, and the edges whose both ends survived. At
    # FULL nothing is dropped, so the bytes are what this generator wrote before verbosity existed.
    kept = [node for node in nodes.values() if node["kind"] in KEPT_KINDS[verbosity]]
    kept = _busiest(kept, edges, verbosity)
    if verbosity != FULL:
        kept = [{k: v for k, v in node.items() if k not in SIGNATURE} for node in kept]
    ids = {node["id"] for node in kept}
    return {
        "edges": sorted(
            (edge for edge in edges.values() if edge["source"] in ids and edge["target"] in ids),
            key=lambda e: e["id"],
        ),
        "nodes": sorted(kept, key=lambda n: n["id"]),
        "schema_version": SCHEMA_VERSION,
    }


def module_id(path: str) -> str:
    # turns a repo-relative path into a dotted module name: src/shop/orders.py -> shop.orders,
    # shop/__init__.py -> shop, src/__init__.py -> src, and a root __init__.py stays __init__
    if path.endswith(JAVASCRIPT_EXTENSIONS):
        # keeps a slash in JavaScript IDs, so they cannot collide with Python's dotted IDs
        return "./" + path
    path = path.removesuffix(".py")
    if path != "src/__init__":
        path = path.removeprefix("src/")
    path = path.removesuffix("/__init__")
    return path.replace("/", ".")


def _package(path: str, mod: str) -> str:
    # finds the package relative imports start from: the module itself for an __init__.py
    if path.endswith("__init__.py"):
        return mod
    return mod.rpartition(".")[0]


def _collect(body, mod, prefix, path, nodes, classes) -> None:
    # adds the classes and functions defined directly in a module or class body, recursing into
    # classes only; a name defined twice keeps its last definition, as at runtime
    last = {}
    for stmt in body:
        if isinstance(stmt, (ast.ClassDef, *FUNCTIONS)):
            last[stmt.name] = stmt
    for stmt in last.values():
        qual = prefix + stmt.name
        node_id = f"{mod}:{qual}"
        if isinstance(stmt, ast.ClassDef):
            nodes[node_id] = {"file": path, "id": node_id, "kind": "class"}
            classes.append((path, node_id, stmt))
            _collect(stmt.body, mod, qual + ".", path, nodes, classes)
        else:
            nodes[node_id] = {
                "async": isinstance(stmt, ast.AsyncFunctionDef),
                "decorators": [_decorator(d) for d in stmt.decorator_list],
                "file": path,
                "id": node_id,
                "kind": "method" if prefix else "function",
                "params": _params(stmt.args),
            }


def _params(args: ast.arguments) -> list[str]:
    # lists parameter names in order with the signature's markers: / after positional-only,
    # * before keyword-only, *args and **kwargs; defaults and annotations are left out
    out = [a.arg for a in args.posonlyargs]
    if args.posonlyargs:
        out.append("/")
    out += [a.arg for a in args.args]
    if args.vararg:
        out.append("*" + args.vararg.arg)
    elif args.kwonlyargs:
        out.append("*")
    out += [a.arg for a in args.kwonlyargs]
    if args.kwarg:
        out.append("**" + args.kwarg.arg)
    return out


def _decorator(expr: ast.expr) -> str:
    # writes a decorator as in the source, without call arguments: @app.get("/x") -> app.get
    if isinstance(expr, ast.Call):
        expr = expr.func
    return ast.unparse(expr)


def _imports(tree, mod, package, path, known, edges) -> dict[str, str]:
    # adds an imports edge for every import of one of our modules, anywhere in the file, and
    # returns the names the imports bind outside functions (local name -> module or definition id)
    names = {}
    for stmt, in_function in _walk(tree):
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                target = _imported(alias.name, known)
                if target:
                    _edge(edges, "imports", mod, target, path)
                if not in_function:
                    # binds a for import a.b.c, and x to a.b.c for import a.b.c as x
                    local = alias.asname or alias.name.split(".")[0]
                    names[local] = alias.name if alias.asname else local
        elif isinstance(stmt, ast.ImportFrom):
            base = _absolute(stmt, package)
            if base is None:
                continue
            for alias in stmt.names:
                submodule = _imported(f"{base}.{alias.name}", known)
                module = _imported(base, known)
                target = submodule or module
                if target:
                    _edge(edges, "imports", mod, target, path)
                if not in_function and alias.name != "*":
                    local = alias.asname or alias.name
                    names[local] = submodule or f"{module or base}:{alias.name}"
    return names


def _imported(name: str, known: set[str]) -> str | None:
    # finds the module an import names: the id itself, or the one id ending in it, since a
    # repository whose code root is not src/ is imported with that root on the path, so
    # Source/models/common.py is imported as models.common. Only a dotted name is matched that
    # way, so `import json` can never reach a module of this repository called utils.json, and
    # only a single match counts, so an ambiguous import is never guessed at.
    if name in known:
        return name
    if "." not in name:
        return None
    matches = [module for module in known if module.endswith("." + name)]
    return matches[0] if len(matches) == 1 else None


def _walk(node, in_function=False):
    # yields every node in source order with whether it sits inside a function body, so a name
    # bound twice keeps its last binding
    for child in ast.iter_child_nodes(node):
        yield child, in_function
        yield from _walk(child, in_function or isinstance(child, (*FUNCTIONS, ast.Lambda)))


def _absolute(stmt: ast.ImportFrom, package: str) -> str | None:
    # resolves the module of a from-import, relative ones against the package; None if it climbs
    # above the top of the repository
    if stmt.level == 0:
        return stmt.module
    parts = package.split(".") if package else []
    up = stmt.level - 1
    if up > len(parts):
        return None
    parts = parts[: len(parts) - up]
    if stmt.module:
        parts.append(stmt.module)
    return ".".join(parts) or None


def _resolve(expr: ast.expr, names: dict[str, str], known: set[str]) -> str | None:
    # finds the id a base such as Base, models.Base or shop.models.Base refers to, through the
    # module's bindings; None for anything else (calls, subscripts, unknown names)
    parts = []
    while isinstance(expr, ast.Attribute):
        parts.append(expr.attr)
        expr = expr.value
    if not isinstance(expr, ast.Name) or expr.id not in names:
        return None
    parts.reverse()
    target = names[expr.id]
    if ":" in target:
        # names a definition, so the rest is a nested name inside it
        return ".".join([target, *parts])
    # names a module, so walks down submodules while they exist; the rest is a definition
    while parts and f"{target}.{parts[0]}" in known:
        target = f"{target}.{parts.pop(0)}"
    return f"{target}:{'.'.join(parts)}" if parts else None


def _edge(edges: dict, kind: str, source: str, target: str, path: str) -> None:
    # adds one edge, keyed by id so the same relation found twice is one edge
    edge_id = f"{kind}:{source}->{target}"
    edges[edge_id] = {"file": path, "id": edge_id, "kind": kind, "source": source, "target": target}

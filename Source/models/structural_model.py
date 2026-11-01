# builds the structural model from Python source: module, class, function and method nodes,
# with imports and inherits edges between this repository's own modules and classes

from __future__ import annotations

import ast

from models.common import parse_files

SCHEMA_VERSION = 1

FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)


def generate_structural(files: dict[str, str]) -> dict:
    # returns the structural model of files (repo-relative path -> text), raises ParseFailed
    # if any file is not valid Python
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

    return {
        "edges": sorted(edges.values(), key=lambda e: e["id"]),
        "nodes": sorted(nodes.values(), key=lambda n: n["id"]),
        "schema_version": SCHEMA_VERSION,
    }


def module_id(path: str) -> str:
    # turns a repo-relative path into a dotted module name: src/shop/orders.py -> shop.orders,
    # shop/__init__.py -> shop, src/__init__.py -> src, and a root __init__.py stays __init__
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

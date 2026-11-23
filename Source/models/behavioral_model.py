# builds the behavioral model from supported source: string-valued states and transitions,
# with the function or method that changes each state; reads syntax without running the code
# models simple equality checks and exit guards, not general control flow or reachability

from __future__ import annotations

import ast
import json

from models.common import parse_files
from models.structural_model import module_id

SCHEMA_VERSION = 1
FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
CONTEXTS = (ast.With, ast.AsyncWith)
EXITS = (ast.Return, ast.Raise, ast.Break, ast.Continue)
LOG_METHODS = frozenset({"debug", "info", "warning", "warn", "error", "exception", "critical", "log"})


def generate_behavioral(files: dict[str, str]) -> dict:
    # returns the behavioral model of files (repo-relative path -> text), raises ParseFailed
    # if any file is not valid source; states and transitions are each sorted by id
    trees = parse_files(files)
    states: dict[str, dict] = {}
    transitions: dict[str, dict] = {}
    for path, tree in trees.items():
        _collect(tree.body, module_id(path), "", path, states, transitions)
    return {
        "schema_version": SCHEMA_VERSION,
        "states": sorted(states.values(), key=lambda item: item["id"]),
        "transitions": sorted(transitions.values(), key=lambda item: item["id"]),
    }


def _collect(body, mod, prefix, path, states, transitions) -> None:
    # finds functions and methods defined directly in a module or class, recursing into classes
    # only; a name defined twice keeps its last definition, as in the structural model
    definitions = {}
    for stmt in body:
        if isinstance(stmt, (ast.ClassDef, *FUNCTIONS)):
            definitions[stmt.name] = stmt
    for name, stmt in definitions.items():
        qual = prefix + name
        if isinstance(stmt, ast.ClassDef):
            _collect(stmt.body, mod, qual + ".", path, states, transitions)
            continue
        trigger = f"{mod}:{qual}"
        owner = f"{mod}:{prefix[:-1]}" if prefix else None
        # skips functions containing global or nonlocal, since those names belong to another scope
        if any(isinstance(node, (ast.Global, ast.Nonlocal)) for node in ast.walk(stmt)):
            continue
        _scan(stmt.body, trigger, owner, path, states, transitions)


def _scan(body, trigger, owner, path, states, transitions) -> None:
    # visits direct checks and checks inside context managers, stopping at an unconditional exit
    for index, stmt in enumerate(body):
        if isinstance(stmt, EXITS):
            return
        if isinstance(stmt, CONTEXTS):
            _scan(stmt.body, trigger, owner, path, states, transitions)
            if _exits(stmt.body, raises=False):
                return
        elif isinstance(stmt, ast.If):
            _conditional(stmt, trigger, owner, path, states, transitions)
            if _exits(stmt.body):
                if stmt.orelse and _exits(stmt.orelse):
                    return
                # reads `if state != 'open': return` as an equality on the fall-through path
                if not stmt.orelse:
                    match = _guard(stmt.test, negate=True)
                    if match:
                        _transition(match, body[index + 1:], trigger, owner, path, states, transitions)


def _exits(body, raises=True) -> bool:
    # follows simple exits, allowing a context manager to suppress a raise but never a return
    for stmt in body:
        if isinstance(stmt, EXITS):
            return raises or not isinstance(stmt, ast.Raise)
        if isinstance(stmt, CONTEXTS) and _exits(stmt.body, raises=False):
            return True
        if isinstance(stmt, ast.If) and stmt.orelse and _exits(stmt.body, raises) and _exits(stmt.orelse, raises):
            return True
    return False


def _conditional(stmt, trigger, owner, path, states, transitions) -> None:
    # adds transitions from direct if/elif checks, leaving nested and compound guards out
    while True:
        match = _guard(stmt.test)
        if match:
            _transition(match, stmt.body, trigger, owner, path, states, transitions)
        if len(stmt.orelse) != 1 or not isinstance(stmt.orelse[0], ast.If):
            return
        stmt = stmt.orelse[0]



def _transition(match, body, trigger, owner, path, states, transitions) -> None:
    # shares transition construction between branch bodies and the fall-through of an exit guard
    variable, before = match
    shared = variable.startswith(("self.", "self["))
    if shared and owner is None:
        return
    after = _destination(body, variable)
    if after is None:
        return
    machine = owner if shared else trigger
    source = _state(states, path, machine, variable, before)
    target = _state(states, path, machine, variable, after)
    key = _identity("transition", path, trigger, source, target)
    transitions[key] = {
        "file": path,
        "guard": f"{variable} == {before!r}",
        "id": key,
        "kind": "transition",
        "source": source,
        "target": target,
        "trigger": trigger,
    }


def _guard(expr, negate=False):
    # reads a check such as state == "pending" or "pending" == state; only one equality
    # against a string literal counts, so Enum members and compound conditions are left out
    if negate and isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.Not):
        return _guard(expr.operand)
    if not isinstance(expr, ast.Compare) or len(expr.ops) != 1:
        return None
    if not isinstance(expr.ops[0], ast.NotEq if negate else ast.Eq):
        return None
    left, right = expr.left, expr.comparators[0]
    for variable, value in ((left, right), (right, left)):
        name = _variable(variable)
        if name and isinstance(value, ast.Constant) and isinstance(value.value, str):
            return name, value.value
    return None


def _variable(expr) -> str | None:
    # names a local, direct self attribute or literal dictionary key, without resolving aliases
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name):
        if expr.value.id == "self":
            return f"self.{expr.attr}"
    if isinstance(expr, ast.Subscript) and isinstance(expr.slice, ast.Constant):
        base = _variable(expr.value)
        key = expr.slice.value
        if base and isinstance(key, str):
            return f"{base}[{key!r}]"
    return None


def _destination(body, variable) -> str | None:
    # finds the first direct assignment to the checked variable, including annotated assignments;
    # only a string literal gives a destination. Unknown calls and branches still stop it
    for stmt in body:
        if isinstance(stmt, ast.Pass):
            continue
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
            continue
        if _logging(stmt):
            continue
        if isinstance(stmt, CONTEXTS):
            return _destination(stmt.body, variable)
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
            target, value = stmt.targets[0], stmt.value
        elif isinstance(stmt, ast.AnnAssign):
            target, value = stmt.target, stmt.value
            if value is None:
                continue
        else:
            return None
        if _variable(target) == variable:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                return value.value
            return None
        name = _variable(target)
        if name and variable.startswith(name + "["):
            return None
        # allows unrelated local assignments of literals, but stops if self is rebound
        if not isinstance(target, ast.Name) or not isinstance(value, ast.Constant):
            return None
        if variable.startswith(("self.", "self[")) and target.id == "self":
            return None
    return None


def _logging(stmt) -> bool:
    # permits recognizable logging statements, but not calls or assignments hidden in their args
    if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Call):
        return False
    call = stmt.value
    if isinstance(call.func, ast.Name):
        known = call.func.id in ("print", "log")
    elif isinstance(call.func, ast.Attribute):
        known = call.func.attr in LOG_METHODS and ast.unparse(call.func.value) in (
            "logging", "logger", "log", "self.logger", "self.log",
        )
    else:
        return False
    if not known:
        return False
    effects = (ast.Call, ast.NamedExpr, ast.Await, ast.Yield, ast.YieldFrom)
    args = [*call.args, *(keyword.value for keyword in call.keywords)]
    return not any(isinstance(node, effects) for arg in args for node in ast.walk(arg))


def _identity(kind, *parts) -> str:
    # joins identity parts as a JSON array, so punctuation inside a state cannot cause an id clash;
    # ids contain no line numbers, and function names follow the structural model
    return kind + ":" + json.dumps(parts, ensure_ascii=False, separators=(",", ":"))


def _state(states, path, machine, variable, value) -> str:
    # adds one state, keyed by id so transitions in the same machine share it; states without
    # a recognized transition are left out
    key = _identity("state", path, machine, variable, value)
    states[key] = {
        "file": path,
        "id": key,
        "kind": "state",
        "machine": machine,
        "value": value,
        "variable": variable,
    }
    return key


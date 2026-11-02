# builds the behavioral model from Python source: string-valued states and transitions,
# with the function or method that changes each state; reads syntax without running the code
# models direct if/elif equality checks and assignments, not general control flow or reachability

from __future__ import annotations

import ast
import json

from models.common import parse_files
from models.structural_model import module_id

SCHEMA_VERSION = 1
FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)


def generate_behavioral(files: dict[str, str]) -> dict:
    # returns the behavioral model of files (repo-relative path -> text), raises ParseFailed
    # if any file is not valid Python; states and transitions are each sorted by id
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
        for item in stmt.body:
            if isinstance(item, ast.If):
                _conditional(item, trigger, owner, path, states, transitions)


def _conditional(stmt, trigger, owner, path, states, transitions) -> None:
    # adds transitions from direct if/elif checks; else, nested conditions and compound guards
    # are left out. self attributes share a class machine; local names belong to one function
    while True:
        match = _guard(stmt.test)
        if match:
            variable, before = match
            if not variable.startswith("self.") or owner is not None:
                after = _destination(stmt.body, variable)
                if after is not None:
                    machine = owner if variable.startswith("self.") else trigger
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
        if len(stmt.orelse) != 1 or not isinstance(stmt.orelse[0], ast.If):
            return
        stmt = stmt.orelse[0]



def _guard(expr):
    # reads a check such as state == "pending" or "pending" == state; only one equality
    # against a string literal counts, so Enum members and compound conditions are left out
    if not isinstance(expr, ast.Compare) or len(expr.ops) != 1:
        return None
    if not isinstance(expr.ops[0], ast.Eq):
        return None
    left, right = expr.left, expr.comparators[0]
    for variable, value in ((left, right), (right, left)):
        name = _variable(variable)
        if name and isinstance(value, ast.Constant) and isinstance(value.value, str):
            return name, value.value
    return None


def _variable(expr) -> str | None:
    # names a local variable or direct self attribute, without resolving aliases
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name):
        if expr.value.id == "self":
            return f"self.{expr.attr}"
    return None


def _destination(body, variable) -> str | None:
    # finds the first direct assignment to the checked variable, including annotated assignments;
    # only a string literal gives a destination. Calls, branches and other unknown effects stop it
    for stmt in body:
        if isinstance(stmt, ast.Pass):
            continue
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
            continue
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
        # allows unrelated local assignments of literals, but stops if self is rebound
        if not isinstance(target, ast.Name) or not isinstance(value, ast.Constant):
            return None
        if variable.startswith("self.") and target.id == "self":
            return None
    return None


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


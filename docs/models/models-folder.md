# The /models folder

Question: which four files does `/models` hold, and what does each contain?

Every model file shares one layout: a `schema_version`, sorted keys, 2-space indent, LF, one trailing newline, lists sorted by id, no line numbers (spec §3.2). Structural follows `docs/base/structure.md`. Behavioral shows what the first generator, `Source/models/behavioral_model.py`, writes; it is not yet registered for checks, so `drifter init` still writes a placeholder, and the format may change until Barshan settles it. Ownership is checked, never regenerated.

```mermaid
classDiagram
    accTitle: The four files in /models
    accDescr: scope.json picks which files feed the structural and behavioral generators. structural.json holds nodes and edges, behavioral.json states and transitions found in if/elif checks, ownership.json an ordered list of rules. Open items are named in each box.

    class scope["scope.json"] {
        picks generator input
        include: every .py file
        exclude: everything under tests/
        defaults written by init
        patterns: mapping-v1.1.yaml glob
    }
    class structural["structural.json"] {
        what exists, how parts relate
        nodes: id, kind, file
        kinds: module, class, function, method
        functions and methods: async, decorators, params
        edges: id, kind, source, target, file
        edge kinds: imports, inherits
        settled in structure.md
        open: JSON Schema
    }
    class behavioral["behavioral.json"] {
        what may happen, in what order
        states: id, kind, file, machine, variable, value
        transitions: id, kind, file, source, target, trigger, guard
        from if/elif checks of a string value
        first version, not yet checked
        open: JSON Schema
    }
    class ownership["ownership.json"] {
        who may change what
        rules: pattern, owners, in order
        first match wins
        no match: open to anyone
        every path, scope ignored
        rename judged at its old path
        patterns: mapping-v1.1.yaml glob
    }

    scope ..> structural : picks the files for
    scope ..> behavioral : picks the files for
```

## How the first behavioral generator finds states

In each function or method defined directly in a module or class, a direct `if` or `elif` that compares a local name or `self.<attribute>` with a string, such as `if self.status == "pending":`, gives one transition when its body's first assignment to that name is another string. The compared string is the source state, the assigned one the target, and the function or method is the `trigger`.

- **Machines:** a `self` attribute belongs to its class's machine (`shop.orders:Order`); a local name belongs to its function's (`shop.orders:advance`). Module and qualified names follow `docs/base/structure.md`.
- **Ids:** `state:` or `transition:` followed by a JSON array of the parts that identify it: file, machine, variable and value for a state; file, trigger, source and target for a transition. No line numbers.
- **Left out:** `else` branches, nested conditions, compound or non-equality guards, Enum members, values that are not string literals, and functions that use `global` or `nonlocal`. A state appears only as the source or target of a transition.

# The /models folder

Question: which four files does `/models` hold, and what does each contain?

Every model file shares one layout: a `schema_version`, sorted keys, 2-space indent, LF, one trailing newline, lists sorted by id, no line numbers (spec §3.2). Structural follows `docs/base/structure.md`. Behavioral follows `docs/base/behavioral.md`. Ownership is checked, never regenerated.

```mermaid
classDiagram
    accTitle: The four files in /models
    accDescr: scope.json picks which files feed the structural and behavioral generators. structural.json holds nodes and edges, behavioral.json states and transitions, ownership.json an ordered list of rules. Open items are named in each box.

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
        string values of a local or self attribute
        settled in behavioral.md
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

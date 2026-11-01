# Inputs and outputs of the function that generates the Structural Model

```python
def generate_structural(files: dict[str, str]) -> dict
```

The function reads Python source code and returns the structural model of that code. It is a pure function: it runs no git, network, clock or randomness, so the same files always give the same model.

## Input

### What it is

`files` holds the code at one commit. 

It is a **dict** with one entry per Python file:

- The **key** is the **file's path**, relative to the repository root, with `/` separators
(for example `src/shop/orders.py`).
- The **value** is the **file's** full **text**.

`scope.json` in `/models` decides which files are "in scope"; by default every `**/*.py` file except those under `tests/`. The files that are "in scope" are the ones included in `files`.

The behavioral generator gets the same dict.

The orchestrator parses every file before calling the function and stops with `PARSE_FAILED` (naming the file and line) if one is not valid Python, so the function can assume every file parses.

### Example

A repository with four Python files:

```python
# src/shop/__init__.py   (empty)

# src/shop/models.py
class Base:
    def save(self): ...

# src/shop/payments.py
def charge(amount, *, currency="USD"): ...

# src/shop/orders.py
from shop.models import Base
from shop import payments

class Order(Base):
    def cancel(self, reason=None):
        payments.charge(0)
```

reaches the generator as:

```python
files = {
    "src/shop/__init__.py": "",
    "src/shop/models.py": "class Base:\n    def save(self): ...\n",
    "src/shop/payments.py": 'def charge(amount, *, currency="USD"): ...\n',
    "src/shop/orders.py": (
        "from shop.models import Base\n"
        "from shop import payments\n"
        "\n"
        "class Order(Base):\n"
        "    def cancel(self, reason=None):\n"
        "        payments.charge(0)\n"
    ),
}
```

## Output

### What it is

The output is the structural model: a graph of what exists in the code and how the parts relate.

The tool writes it to `models/structural.json` and compares it with the committed copy.

```json
{
  "edges": [ ... ],
  "nodes": [ ... ],
  "schema_version": 1
}
```

`nodes` are the parts of the code. Each has an `id`, a `kind` and the `file` it comes from.

These are the possible kinds of nodes:

| kind | One per | Extra fields |
| --- | --- | --- |
| `module` | `.py` file | none |
| `class` | class defined directly in a module or class body | none |
| `function` | function defined directly in a module body | `async`, `decorators`, `params` |
| `method` | function defined directly in a class body | `async`, `decorators`, `params` |

**Module ids** are the path to the file. It is represented:

- without `.py`, 
- with `/` turned into `.`,
- with a leading `src/` dropped from files below it (`src/__init__.py` itself is `src`), and
- with a trailing `.__init__` dropped, so a package's `__init__.py` has the package's id (`src/shop/__init__.py` is `shop`).

A root-level `__init__.py` is `__init__`. Only `src/` is dropped: code under any other folder keeps it in its id (`Source/pkg/mod.py` is `Source.pkg.mod`).

An import is matched against those ids by name, or by the one id that ends in it: an import of `pkg.mod` finds `Source.pkg.mod`, because that root is what sits on the import path when the code runs. Only a dotted name is matched that way, so `import json` never reaches a `utils/json.py`, and only a single match counts, so an ambiguous import gives no edge. Ids are unaffected: this decides edges only.

No two files share a module id. The one clash these rules leave, a root `src.py` beside `src/__init__.py`, is not supported.

**Class, function and method** ids are `<module>:<qualified name>`, for example `shop.orders:Order.cancel`.

`edges` are the relations between nodes. 

Each has an `id`, a `kind`, a `source`, a `target` and the `file` of its source. 

The id is `<kind>:<source>-><target>`.

These are the possible kinds of edges:

| kind | From and to |
| --- | --- |
| `imports` | a module imports another module of this repository |
| `inherits` | a class inherits from another class of this repository |

Calls are not edges in `schema_version` 1. Adding them is `schema_version` 2, and it changes every committed `structural.json`, the model fixture's included.

Links to external libraries are dropped. A base class from outside the repository, such as `ValueError` or `enum.Enum`, gives no `inherits` edge, so changing `class E(ValueError)` to `class E(Exception)` is not drift.

`nodes` and `edges` are each sorted by `id`. 

The file has sorted keys, 2-space indent, LF line endings and one trailing newline, so the same code always gives the same bytes. 

There are no line numbers, so moving code is not a change.

### Example

For the input above, `models/structural.json` is below. `Order.cancel`'s call to `payments.charge` gives no edge.

```json
{
  "edges": [
    {
      "file": "src/shop/orders.py",
      "id": "imports:shop.orders->shop.models",
      "kind": "imports",
      "source": "shop.orders",
      "target": "shop.models"
    },
    {
      "file": "src/shop/orders.py",
      "id": "imports:shop.orders->shop.payments",
      "kind": "imports",
      "source": "shop.orders",
      "target": "shop.payments"
    },
    {
      "file": "src/shop/orders.py",
      "id": "inherits:shop.orders:Order->shop.models:Base",
      "kind": "inherits",
      "source": "shop.orders:Order",
      "target": "shop.models:Base"
    }
  ],
  "nodes": [
    {
      "file": "src/shop/__init__.py",
      "id": "shop",
      "kind": "module"
    },
    {
      "file": "src/shop/models.py",
      "id": "shop.models",
      "kind": "module"
    },
    {
      "file": "src/shop/models.py",
      "id": "shop.models:Base",
      "kind": "class"
    },
    {
      "async": false,
      "decorators": [],
      "file": "src/shop/models.py",
      "id": "shop.models:Base.save",
      "kind": "method",
      "params": [
        "self"
      ]
    },
    {
      "file": "src/shop/orders.py",
      "id": "shop.orders",
      "kind": "module"
    },
    {
      "file": "src/shop/orders.py",
      "id": "shop.orders:Order",
      "kind": "class"
    },
    {
      "async": false,
      "decorators": [],
      "file": "src/shop/orders.py",
      "id": "shop.orders:Order.cancel",
      "kind": "method",
      "params": [
        "self",
        "reason"
      ]
    },
    {
      "file": "src/shop/payments.py",
      "id": "shop.payments",
      "kind": "module"
    },
    {
      "async": false,
      "decorators": [],
      "file": "src/shop/payments.py",
      "id": "shop.payments:charge",
      "kind": "function",
      "params": [
        "amount",
        "*",
        "currency"
      ]
    }
  ],
  "schema_version": 1
}
```

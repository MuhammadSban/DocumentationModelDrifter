# Inputs and outputs of the function that generates the Behavioral Model

```python
def generate_behavioral(files: dict[str, str]) -> dict
```

The function reads Python source code and returns the states a variable takes and the transitions between them. Like the structural generator it is pure: no git, network, clock or randomness, so the same files always give the same model.

The format is frozen as `generate_behavioral` writes it in `schema_version` 1. Snippet goldens in `tests/behavioral/test_behavioral_model.py` lock it; any change to the output is a format change, bumps `schema_version` and needs new goldens. The spec wins where this file disagrees with it.

## Input

The same `files` dict the structural generator gets (see `structure.md`): repo-relative path with `/` separators to the file's full text, only the files `scope.json` keeps, each already parsed by the orchestrator.

## Output

The tool writes it to `models/behavioral.json` and compares it with the committed copy by element id.

```json
{
  "schema_version": 1,
  "states": [ ... ],
  "transitions": [ ... ]
}
```

No other top-level keys. `states` and `transitions` are each sorted by `id`. [`Source/models/behavioral.schema.json`](../../Source/models/behavioral.schema.json) is this format as a JSON Schema: a committed `behavioral.json` that breaks it gives INVALID_MODELS naming the file. The file has sorted keys, 2-space indent, non-ASCII kept as is, LF line endings and one trailing newline.

### Kinds

| kind | One per | Fields |
| --- | --- | --- |
| `state` | value one variable of one machine takes | `file`, `id`, `kind`, `machine`, `value`, `variable` |
| `transition` | function or method moving a variable from one value to another | `file`, `guard`, `id`, `kind`, `source`, `target`, `trigger` |

- `variable` is a local name (`status`) or a direct `self` attribute (`self.status`).
- `machine` groups states. For `self.<attr>` it is the class's structural id (`shop.orders:Order`), so every method of the class shares one machine. For a local name it is the function's structural id, so two functions never share states.
- `value` is the string literal.
- `trigger` is the structural id of the function or method (`module:qualname`, as in `structure.md`).
- `source` and `target` are state ids.
- `guard` is `<variable> == <value>` with the value as Python's `repr` writes it, so `"paid" == self.status` reads `self.status == 'paid'`.
- `file` is the path of the file the element comes from.

### Ids

The kind, a colon, then a compact JSON array of the identity parts (no spaces, non-ASCII kept):

- state: `state:[file, machine, variable, value]`
- transition: `transition:[file, trigger, source, target]`

A value holding quotes or commas is escaped inside the array, so two different states never share an id. Ids hold no line numbers, so moving code or editing comments and whitespace changes nothing. The guard's value is the source state's value, so a changed guard changes the transition's id: it reads as one REMOVED and one ADDED transition, never MODIFIED.

### Mining rules

1. Visit functions and methods defined directly in a module or a class. Classes are recursed; functions nested in functions are not. A name defined twice keeps its last definition, as in structural.
2. Skip any function that contains `global` or `nonlocal` anywhere in it.
3. For each `if` directly in the function body, and each `elif` chained to it, read the test. An `else:` whose only statement is an `if` parses exactly as an `elif` and is read as one. It counts only when it is one `==` between a variable (local name or direct `self` attribute) and a string literal, either way round.
4. In that branch's body, find the first direct assignment (`=` with one target, or annotated `x: str = ...`) to the same variable. Skipped on the way: any constant on a line of its own (a docstring, `...`), `pass`, a bare annotation with no value (`x: str`), and an assignment of a literal to another local name (unless that name is `self`, which stops it). Anything else stops the search. A string literal assigned gives the target state; any other value gives nothing.
5. Each match gives one transition from the guard's value to the assigned value, and the two states it joins. A state exists only as the source or target of a transition.
6. `self.<attr>` checks outside a class (in a module-level function) give nothing.

### Left out

The miner does not see:

- `else` branches (except an `else:` holding only an `if`, see rule 3), and conditions nested inside another statement;
- compound conditions (`and`, `or`, chained comparisons), `!=`, `in`, `match`;
- Enum members and any value that is not a string literal (`State.PAID`, `make()`);
- aliases (`s = self.status`) and attributes other than direct `self.<attr>`;
- any function containing `global` or `nonlocal`;
- a lone assignment with no recognized transition: its value is no state.

## Example

```python
# src/shop/orders.py
class Order:
    def pay(self):
        if self.status == "open":
            self.status = "paid"
```

gives this `models/behavioral.json`:

```json
{
  "schema_version": 1,
  "states": [
    {
      "file": "src/shop/orders.py",
      "id": "state:[\"src/shop/orders.py\",\"shop.orders:Order\",\"self.status\",\"open\"]",
      "kind": "state",
      "machine": "shop.orders:Order",
      "value": "open",
      "variable": "self.status"
    },
    {
      "file": "src/shop/orders.py",
      "id": "state:[\"src/shop/orders.py\",\"shop.orders:Order\",\"self.status\",\"paid\"]",
      "kind": "state",
      "machine": "shop.orders:Order",
      "value": "paid",
      "variable": "self.status"
    }
  ],
  "transitions": [
    {
      "file": "src/shop/orders.py",
      "guard": "self.status == 'open'",
      "id": "transition:[\"src/shop/orders.py\",\"shop.orders:Order.pay\",\"state:[\\\"src/shop/orders.py\\\",\\\"shop.orders:Order\\\",\\\"self.status\\\",\\\"open\\\"]\",\"state:[\\\"src/shop/orders.py\\\",\\\"shop.orders:Order\\\",\\\"self.status\\\",\\\"paid\\\"]\"]",
      "kind": "transition",
      "source": "state:[\"src/shop/orders.py\",\"shop.orders:Order\",\"self.status\",\"open\"]",
      "target": "state:[\"src/shop/orders.py\",\"shop.orders:Order\",\"self.status\",\"paid\"]",
      "trigger": "shop.orders:Order.pay"
    }
  ]
}
```

Adding `elif self.status == "paid": self.status = "shipped"` to `pay` is one ADDED `state` (`shipped`) and one ADDED `transition` (`paid` to `shipped`).

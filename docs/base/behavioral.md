# Inputs and outputs of the function that generates the Behavioral Model

```python
def generate_behavioral(files: dict[str, str]) -> dict
```

The function reads Python source code and returns the states a variable takes and the transitions between them. Like the structural generator it is pure: no git, network, clock or randomness, so the same files always give the same model.

The JSON shape and existing identities stay at `schema_version` 1. Snippet goldens in `tests/behavioral/test_behavioral_model.py` lock the existing output; `test_behavioral_cases.py` checks additional mining patterns. A change to the JSON shape or identity scheme bumps `schema_version` and needs new goldens. Expanding which source patterns are recognized may add elements and requires regenerating affected baselines. The spec wins where this file disagrees with it.

## Input

### JavaScript support

JavaScript uses the same narrow state miner after syntax normalization. `this` becomes `self`, so a class's `this.status` is stored as `self.status` and its methods share the existing class-machine convention. Class methods and variable-bound functions keep the JavaScript module ID, including its `./` prefix and extension. Dictionary keys use the existing literal-key support.

Literal string comparisons using `===` or `==` normalize to the same state equality; `!==` and `!=` support the existing negative exit-guard rule. This string-state abstraction does not model JavaScript coercion or detect an equality-operator-only change. `console.log` uses the existing observational logging convention. Unknown syntax and side effects remain barriers; conditions inside loops and try blocks, compound guards, enums and arbitrary data-flow are not inferred.

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

- `variable` is a local name (`status`), a direct `self` attribute (`self.status`), or a literal string-key access rooted in either (`session['state']`, `self.data['state']`). Dictionary keys are normalized with Python's `repr`, so changing quote style does not change an id.
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
3. For each `if` directly in the function body or inside a `with` / `async with`, and each `elif` chained to it, read the test. An `else:` whose only statement is an `if` parses exactly as an `elif` and is read as one. It counts only when it is one `==` between a supported variable and a string literal, either way round. A negative guard with no `else`, such as `if state != 'open': return` or `if not (state == 'open'): raise ...`, supplies that equality on the fall-through path when its body unconditionally exits. Direct exits and an `if` whose two branches exit stop scanning subsequent statements in that block; this is not general reachability analysis.
4. In the branch's body, or after a recognized exit guard, find the first assignment (`=` with one target, or annotated `x: str = ...`) to the same variable, including one inside a `with` / `async with`. Skipped on the way: any constant on a line of its own (a docstring, `...`), `pass`, a bare annotation with no value (`x: str`), an unrelated local literal assignment, and a recognizable logging statement. Rebinding `self` or a dictionary containing the tracked key stops the search. Logging is recognized by conventional names: `print`, `log`, or logging methods on `logging`, `logger`, `log`, `self.logger`, or `self.log`; arguments containing a call, assignment expression, `await`, or `yield` stop the search. These names are an observational convention, not proof that a shadowed logger is pure. Other calls and statements stop the search. A string literal assigned gives the target state; any other value gives nothing.
5. Each match gives one transition from the guard's value to the assigned value, and the two states it joins. A state exists only as the source or target of a transition.
6. State rooted in `self` shares a class machine and gives nothing outside a class. Dictionary state rooted in a local belongs to that function; aliases between functions are not inferred.

### Left out

The miner does not see:

- `else` branches (except an `else:` holding only an `if`, see rule 3), and conditions nested inside another condition, loop, or `try`;
- compound conditions (`and`, `or`, chained comparisons), `!=`, `in`, `match`;
- Enum members and any value that is not a string literal (`State.PAID`, `make()`);
- aliases (`s = self.status`), computed dictionary keys, and attributes other than direct `self.<attr>`;
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

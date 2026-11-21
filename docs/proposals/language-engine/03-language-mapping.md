# Language mapping

Question: what does each new language become in `structural.json`, using only the kinds that already exist?

## The rule for ids

| Language | Module id | Example element id |
| --- | --- | --- |
| Python (unchanged, also after it moves onto the template in steps c and d) | dotted path, no `.py` | `shop.orders:Order.cancel` |
| Everything else | **repo path with its extension** | `web/src/Cart.tsx:Cart` |

Why keep the extension: `web/app.ts` and `web/app.js` can sit side by side, and `app.py` could too. Dropping the extension would give all three the same id. With the extension every id is unique, and you can see the file from the id.

## The mapping

Only existing kinds are used, so `structural.schema.json` does not change.

| Source | Node | Edge |
| --- | --- | --- |
| Any JS/TS file | `module` | |
| `class Order extends Base {}` | `class` `…:Order` | `inherits` → `Base`, if `Base` is ours |
| `function total(a, b) {}`, `const total = (a, b) => {}` | `function`, `params: ["a","b"]`, `async` | |
| method inside a class | `method` `…:Order.cancel` | |
| `import x from "./api"`, `export … from "./api"`, `require("./api")` | | `imports` → the resolved repo file |
| `import React from "react"` | | none: not our file |
| React class component, `class Cart extends React.Component` | `class` | none: `React.Component` is not ours |
| React function component, `function Cart() { return <div/> }` | `function` | |
| `import "./Card.css"`, `import "./page.html"` | | none: CSS and HTML are not in scope (see 04) |
| TS `interface`, `type`, `enum` | left out at first | |
| JSX use `<Button/>` | left out at first (see 01, "leaves out") | |

`decorators` is `[]` for JS. TS decorators can fill it later, written as in the source, the same as Python.

## One small example

`web/src/api.ts`

```ts
export async function fetchCart(id: string) { /* ... */ }
```

`web/src/Cart.tsx`

```tsx
import React from "react";
import { fetchCart } from "./api";

export class Cart extends React.Component {
  load(id) { return fetchCart(id); }
}
```

Becomes (abridged, sorted by id):

```json
{
  "nodes": [
    {"id": "web/src/Cart.tsx", "kind": "module", "file": "web/src/Cart.tsx"},
    {"id": "web/src/Cart.tsx:Cart", "kind": "class", "file": "web/src/Cart.tsx"},
    {"id": "web/src/Cart.tsx:Cart.load", "kind": "method", "file": "web/src/Cart.tsx",
     "async": false, "decorators": [], "params": ["id"]},
    {"id": "web/src/api.ts", "kind": "module", "file": "web/src/api.ts"},
    {"id": "web/src/api.ts:fetchCart", "kind": "function", "file": "web/src/api.ts",
     "async": true, "decorators": [], "params": ["id"]}
  ],
  "edges": [
    {"id": "imports:web/src/Cart.tsx->web/src/api.ts", "kind": "imports",
     "source": "web/src/Cart.tsx", "target": "web/src/api.ts", "file": "web/src/Cart.tsx"}
  ],
  "schema_version": 1
}
```

What the diff then catches, with no new code in the diff:

| Code change | Drift reported |
| --- | --- |
| Someone deletes `import { fetchCart } from "./api"` | REMOVED `imports:web/src/Cart.tsx->web/src/api.ts` |
| `load(id)` becomes `load(id, force)` | MODIFIED `web/src/Cart.tsx:Cart.load` (params) |
| New file `web/src/Checkout.tsx` | ADDED module, plus its classes and functions |

## Import resolution, first version

Pure path logic, no tool does it for us:

1. Bare names (`react`, `lodash`) are not our files, so no edge.
2. Relative `./api` resolves from the importing file's folder. Try the path as written, then `.ts`, `.tsx`, `.js`, `.jsx`, then `/index.*`. The first one in scope wins.
3. No match means no edge, never a guess. This matches Python's `_imported`, which never guesses an ambiguous import.

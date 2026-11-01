# The model seam

Question: what does each model owner write, and what does the core do with it?

Each owner decides everything inside their model: kinds, id scheme, attributes, mining rules and the rest of the schema. The core relies only on what this page says. Decided as D9 and D10 in `docs/base/phase4.md`.

## Who writes what

| Part | Owner | Writes |
| --- | --- | --- |
| Structural | Enrique | `generate_structural(files) -> dict` and `structural.schema.json`; element lists `nodes`, `edges` |
| Behavioral | Barshan | `generate_behavioral(files) -> dict` and `behavioral.schema.json`; element lists of the owner's choice |
| Ownership | Muhammad | `propose(head_sha, records) -> dict` and `ownership.schema.json`; rules, never diffed |
| Core | Kaan | `parse_files`, `write_model`, `CommitRecord`, scope, the diff, the ownership checker, the CLI |

## The element rule (structural and behavioral)

Every top-level list in a model file holds elements. Each element has a unique `id` (unique in the whole model), a `kind` and the in-scope `file` it comes from; every other field is an attribute. Values that are not lists, such as `schema_version`, are not elements and are not diffed.

```json
{
  "schema_version": 1,
  "nodes": [
    {"id": "shop.orders:Order.cancel", "kind": "method", "file": "src/shop/orders.py", "params": ["self", "reason"]}
  ],
  "edges": []
}
```

A generator must be pure (no git, network, clock, randomness or environment), never import or run the analysed code, sort each top-level list by `id`, keep inner lists in a fixed order, leave out line numbers, times and absolute paths, and pin `schema_version` with `const` in its schema.

## One check

Steps the owners write are marked **(owner)**; every other step is the core's. A step that can end the check names its no-verdict code.

```mermaid
flowchart TB
    accTitle: The model seam in one check
    accDescr: For structural and behavioral, the core parses the in-scope files, calls the owner's generator, validates the committed model against the owner's schema, flattens both to a map from id to element and diffs them by id. For ownership, the core builds commit records, the owner's propose function turns them into ownership.json at init, and the core's checker judges each commit against those rules.

    subgraph SB[Structural and behavioral]
        Files[in-scope files, path to text<br/>chosen by scope.json] --> Parse[parse_files, every file once<br/>no verdict: PARSE_FAILED, FILE_TOO_LARGE]
        Parse --> Gen["generate_name<br/>(owner)"]
        Gen --> Fresh[fresh model<br/>flattened to id: element]
        Committed["/models/name.json, committed"] --> Valid["validate against the schema (owner)<br/>and unique ids<br/>no verdict: MODELS_NOT_FOUND, INVALID_MODELS"]
        Valid --> Old[committed model<br/>flattened to id: element]
        Fresh & Old --> Diff[diff by id, sorted by id<br/>ADDED, REMOVED, MODIFIED<br/>each: change, file, id, kind]
    end

    subgraph OW[Ownership]
        Log[git integration: every commit up to head,<br/>newest first, as CommitRecord<br/>sha, author_email, author_date, parent_count, paths]
        Log -- init and /generate --> Prop["propose<br/>(owner)"] --> Write[write_model: ownership.json]
        Log -- non-merge commits base..head --> Check[checker: first matching rule wins,<br/>no rule means anyone,<br/>a rename is judged on its old path]
        Rules["ownership.json, validated<br/>against the schema (owner)"] --> Check
        Check --> Viol[VIOLATION<br/>author, commit, owners, path]
    end

    SB ~~~ OW
```

`propose()` returns rules sorted by path, each one exact path with its owners as sorted lowercase emails: `{"rules": [{"owners": ["a@x.com"], "pattern": "src/app.py"}], "schema_version": 1}`. Inside it is Muhammad's: `derive()`, the window of 10, the 50-file limit and the vendored folders as a config file in the tool, a bot being an email containing `[bot]`, and no `email:` prefix.

## Done when (each owner, before plugging in at v1.2)

- Their own snippet goldens pass: small code, exact expected JSON.
- Output is byte-identical on Linux and Windows (REQ-07).
- The shared seam test passes (written by the core in v1.1): element rule, unique ids, sorted lists, valid against the schema, `write_model` round trip.

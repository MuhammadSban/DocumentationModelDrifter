# Research: extending the extractor beyond Python

Question: how can the structural (and later behavioral) extractor cover JavaScript, TypeScript, JSX/React, HTML, CSS and later Java or Go with the simplest design that stays deterministic, static and byte-stable (docs/diagrams/model-seam.md)?

Builds on `docs/research/research-evidence.md`, which rejected tree-sitter and ast-grep because of "a second grammar; output order varies". This file re-checks that claim. Measurements: Windows 11, Python 3.13.13, and WSL Ubuntu, Python 3.12, 2026-11-02. Scripts were kept in the session scratchpad, not in the repo.

## 1. Options compared

| | 1. tree-sitter (py-tree-sitter + pinned grammar wheels) | 2. ast-grep (`ast-grep-py`) | 3. Native parsers (Babel, TS compiler API) | 4. Semgrep CE | 5. SCIP / stack-graphs / ctags |
| --- | --- | --- | --- | --- | --- |
| Languages | One grammar wheel per language. 372 grammars in tree-sitter-language-pack [6] | About 25 built-in grammars, all based on tree-sitter [8] | One parser per language and ecosystem | 30+ languages | scip-typescript: TS/JS only [11]. stack-graphs: per-language rules. ctags: about 100 languages [13] |
| Order within a file | Document order. Same bytes on every run, on both OSes (local test, section 2) | `find_all`: document order on one string (local test) | Deterministic per parser (not tested) | Output sorted by path, line, column, rule [10] | Not tested |
| Order across files | We choose the file order (`sorted()`) | CLI walks files in parallel threads, so file order is not fixed [9]. The Python API has no such walk | We choose | Sorted [10] | Not tested |
| Syntax errors | Never raises. Marks `ERROR`/`MISSING` nodes, sets `has_error` (local test) | Same as tree-sitter (same parser) | Babel raises unless `errorRecovery` is on [12] | Reports a parse error and skips the file | n/a |
| Speed, 92k-line TSX | Parse 0.34 s + query 0.20 s, Windows. 0.33 + 0.17 s, Linux (local) | Parse + 2 rules 0.61 s (local) | Not measured. Needs a node process | Not measured. Startup cost per run | scip-typescript type-checks the whole project and can run out of memory [11] |
| Licence | MIT, core and all four grammars (wheel METADATA) | MIT [7] | Babel MIT, TypeScript Apache-2.0 | Engine LGPL-2.1. Registry rules: internal business use only [5] | SCIP Apache-2.0. stack-graphs MIT/Apache, **archived** [4]. ctags **GPL-2.0** [13] |
| Install in a Python image | Pure wheels: tree-sitter 264 KB, js 448 KB, ts 2.8 MB, html 48 KB, css 142 KB (local). No compiler, no node | One 44 MB wheel (local) | Needs Node.js in the image plus npm packages | Large pip wheel with an OCaml binary. Native Windows support reached GA only in 2025 [14] | scip-typescript: node plus `npm install` of the analysed project [11]. ctags: a separate native binary |
| Imports, classes, extends | `.scm` query (section 3). Each grammar ships a `tags.scm` with `@definition.class`, `@definition.function` and `@reference.call` [2] | YAML/kwargs rules: `pattern='import $$$A from "$S"'` | Full AST, including resolved types (TS) | YAML rules. Metavariable values per finding | Resolved symbols across files (SCIP). ctags: definitions only, no edges |
| Fit with "never run or install the code" | Yes | Yes | Mostly yes. TS API module resolution reads `node_modules` | Yes | **No**: scip-typescript needs the dependencies installed [11] |

## 2. Verdict on "tree-sitter output order varies"

**The claim does not hold for the library used in-process with pinned versions.** Evidence:

| Check | Result |
| --- | --- |
| Same files, two runs with `PYTHONHASHSEED=1` and `999` | `cmp` identical |
| Same files, Windows vs Linux (WSL), same pinned versions | Content identical. The only difference was CRLF from Windows text-mode stdout, not from tree-sitter. The canonical JSON writer already writes LF |
| LF vs CRLF copies of the sources | Extracted output identical |
| 92k-line TSX, 68 000 matches | SHA-256 of the matches and of the whole tree S-expression identical on both OSes |
| Engine design | `query.c` keeps finished matches in a heap ordered by "(byte offset of next unconsumed capture, pattern_index, insertion order)" [3]. No randomness, no threads |
| API shape | `QueryCursor.matches()` returns a `list[(pattern_index, dict[name, list[Node]])]`. `captures()` returns a **dict grouped by capture name**, so the order across names is lost [1] |

Where order *can* vary, and why the earlier note probably came from there:

1. **The ast-grep CLI** walks files on several threads and prints results as they arrive [9]. That is a CLI property, not a parser property.
2. **`captures()` grouping** looks like reordering compared with source order [1].
3. **A grammar upgrade** can rename node types (for example `function` became `function_expression`). The query then fails loudly: `QueryError: Invalid node type ... function` (local). It does not silently reorder anything.

The rule that removes all three: use `matches()`, turn each match into model nodes and edges, and **sort by id**, as the Python generators already do (model-seam.md). Pin exact wheel versions. The emitted order then never depends on the engine.

"A second grammar" is still true: tree-sitter-python ≠ CPython `ast`. Keep `ast` for Python, so existing ids do not change, and use tree-sitter only for the new languages.

> **Later decision (2026-11-02):** a comparison found 614 of 614 Python elements identical between `ast` and the template, so Python moves onto the template too, in agreed steps a to d. Step b checks byte-identical edges and goldens first. See `04-one-template.md`, "Python on the template".

## 3. Mapping to model nodes and edges (checked locally on sample files)

| Source | Query (abridged) | Model |
| --- | --- | --- |
| ES `import ... from "x"`, `export ... from "x"` | `(import_statement source: (string (string_fragment) @import))` | `imports` edge module → resolved path |
| `require("x")` | `(call_expression function: (identifier) @_f arguments: (arguments (string (string_fragment) @import)) (#eq? @_f "require"))` | `imports` edge |
| Dynamic `import("./Lazy")` | `(call_expression function: (import) ...)` | `imports` edge. Flag it as dynamic, or drop it |
| `class Order extends Base` | `(class_declaration name: (_) @name (class_heritage (extends_clause value: (_) @extends))?)` | `class` node, `inherits` edge |
| Methods, functions, arrow consts | `method_definition`, `function_declaration`, `lexical_declaration/variable_declarator value: (arrow_function)` | `method` / `function` nodes. Params and `async` come from child fields |
| React class component | Same class query. Extends text is `React.Component` | `class` + `inherits` to the external `React.Component`. A `component` tag can be derived from that |
| React function component | Capitalised function or arrow whose body contains `jsx_element` / `jsx_self_closing_element` | `function` node with a `component` tag. JSX `<Button/>` with a capital name: `uses` edge (new kind) |
| HTML `<script src>`, `<link href>`, `<a href>`, `<img src>` | `(element (start_tag (attribute (attribute_name) @_a (quoted_attribute_value (attribute_value) @link))) (#any-of? @_a "href" "src"))`, plus `script_element` | `imports`-like edges page → asset. Inline `<script>` text can be parsed again with the JS grammar (`injections.scm`) |
| CSS `@import "x"`, `@import url("x")`, `url(img.png)` | `(import_statement (string_value) @import)`, `(call_expression (function_name) @_f (arguments (plain_value) @url) (#eq? @_f "url"))` | `imports` edge stylesheet → stylesheet / asset. Strip the quotes |

Ids: keep the `module:Qual.name` form, with the module derived from the repo-relative path without extension (`web/app` for `web/app.tsx`). Resolving import paths (`./api` → `api.ts`, `api/index.ts`, tsconfig `paths`) is our own pure path logic. No tool from options 1 to 4 does it.

## 4. Error handling

`broken.js` (`class A extends B { m( { }`) gave `has_error=True`. The `ERROR` node **swallowed both the class and the following function**: only the import survived. Another input recovered a `MISSING "}"` node and kept the class (local). Partial trees are therefore not a stable source of facts.

Recommendation: if `root_node.has_error`, raise `ParseFailed` (PARSE_FAILED) for that file, the same contract as `ast.parse`. Do not emit partial models.

## 5. Recommendation: simplest option

**Option 1: py-tree-sitter plus individually pinned grammar wheels plus our own `.scm` files, one small adapter per language behind the existing generator seam.**

1. Pure wheels, about 3.7 MB for JS, TS, HTML and CSS. No node, no compiler, MIT. Fits the Python Docker image.
2. Deterministic in practice and by design (section 2). Sorting by id stays the final guarantee.
3. One query language for every language. GitHub's code navigation works the same way, with tree-sitter and tags queries for about 20 languages [15]. Java and Go later means another wheel plus a `.scm`. Each grammar's `tags.scm` [2] is a starting point, not a dependency.
4. Fast enough: 92k lines in about 0.55 s, the same range as `ast` on Django.
5. ast-grep is the runner-up: same engine, but 44 MB and less direct control. Semgrep has a heavy install and licence limits on its rules. Native parsers need node in the image. SCIP needs the dependencies installed, and stack-graphs is archived. ctags is GPL and gives definitions only.

Shape: `parse_files()` dispatches on extension. `.py` goes to `ast` (unchanged). `.js/.jsx/.ts/.tsx/.html/.css` go to tree-sitter. `DEFAULT_SCOPE.include` grows with the languages enabled. Pin exact versions (`tree-sitter==0.26.0`, `tree-sitter-javascript==0.25.0`, `tree-sitter-typescript==0.23.2`, `tree-sitter-html==0.23.2`, `tree-sitter-css==0.25.0`). Do **not** use tree-sitter-language-pack at runtime: v1.x downloads parsers on first use [6], which means network access and an unpinned binary.

## 6. Open risks and what is not known

| Risk / unknown | Note |
| --- | --- |
| Behavioral model for JS/TS | String state machines (`if (s === "pending") s = "paid"`) look queryable, but this was not tried. `switch` and enum/union types widen the cases |
| Import resolution | tsconfig `paths`, `baseUrl`, package `exports`, barrel `index.ts`, webpack aliases. All our own code. External packages become external nodes |
| Grammar upgrades | Node types and fields change between versions. Queries fail loudly (`QueryError`), but every upgrade needs a golden-file re-check |
| Wheel availability | Prebuilt wheels were seen for win-amd64 and Linux x86_64 only. musl/Alpine and arm64 not checked |
| `.jsx` vs `.tsx` vs `.js` with JSX | The `tsx` grammar parses JSX. Plain `.js` files that contain JSX need the JS grammar (it accepts JSX); `.ts` needs the non-tsx grammar. Not tested on a real corpus |
| Vue/Svelte/Angular templates, CSS-in-JS, Sass/Less | Not covered. Each needs its own grammar or an injection |
| React detection | "Capitalised function returning JSX" is a heuristic. HOCs, `forwardRef` and `memo` wrappers are missed. No ground truth measured |
| Speed on real repos | Only a synthetic 92k-line file was timed. A real corpus (e.g. a pinned React app) was not run |
| Native parsers, Semgrep, SCIP | Not installed or timed locally. Rows in table 1 rely on docs only |
| `captures()` doc hint | The docs say `matches()` "only returns the last match" [1]. The local test returned all 68 000 matches. Use `matches()` and treat that doc line as unverified |

## References

1. py-tree-sitter `QueryCursor` docs, 0.26.0: https://tree-sitter.github.io/py-tree-sitter/classes/tree_sitter.QueryCursor.html. API reference: https://github.com/tree-sitter/py-tree-sitter/blob/master/_autodocs/api-reference/query-cursor.md
2. Tree-sitter code navigation and the tags.scm convention: https://tree-sitter.github.io/tree-sitter/4-code-navigation.html
3. Tree-sitter `lib/src/query.c` (FinishedStateHeap ordering): https://github.com/tree-sitter/tree-sitter/blob/master/lib/src/query.c. Query API: https://tree-sitter.github.io/tree-sitter/using-parsers/queries/4-api.html
4. github/stack-graphs, archived, "no longer supported or updated by GitHub": https://github.com/github/stack-graphs
5. Semgrep licensing: https://semgrep.dev/docs/licensing
6. tree-sitter-language-pack: https://pypi.org/project/tree-sitter-language-pack/ and https://github.com/xberg-io/tree-sitter-language-pack ("downloads each parser on first use")
7. ast-grep-py on PyPI: https://pypi.org/project/ast-grep-py/
8. ast-grep Python API: https://ast-grep.github.io/guide/api-usage/py-api.html
9. ast-grep CLI parallel worker (`WalkParallel`, mpsc channel): https://github.com/ast-grep/ast-grep/blob/7797f683/crates/cli/src/utils/worker.rs
10. Semgrep result sorting: https://github.com/semgrep/semgrep/blob/93b8e2c6/src/reporting/Core_json_output.ml and https://github.com/returntocorp/semgrep/pull/8800
11. scip-typescript README (node 22/24, `npm install` first, OOM notes): https://github.com/sourcegraph/scip-typescript
12. @babel/parser options (`errorRecovery`): https://babeljs.io/docs/babel-parser
13. universal-ctags, GPL-2.0: https://github.com/universal-ctags/ctags
14. Semgrep native Windows support: https://github.com/semgrep/semgrep/issues/1330 and https://semgrep.dev/resources/whats-new
15. GitHub code navigation uses tree-sitter: https://docs.github.com/en/repositories/working-with-files/using-files/navigating-code-on-github

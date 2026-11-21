# Decisions log

Question: what was decided about taking drifter beyond Python, what is still open, and what was suggested but not yet written into 01 to 04?

Written 2026-11-02 on branch `phase5-kk`, from the working session that produced this folder. Nothing here is built: every item is a proposal until the team accepts it.

## Decided (by the user)

| # | Decision | Where it is written |
| --- | --- | --- |
| D1 | **Python moves onto the template too** (agreed), in four steps: **a** build the 14 languages first, with Python still on `ast`. **b** Compare edges and check against the goldens. **c** Move Python structural. **d** Move Python behavioral and drop `ast`. Ids and committed models do not change. Replaces the earlier "keep Python on `ast`". Evidence: 614 of 614 elements identical on this repository. The pod contract names no parser, only the outputs | 04 "Python on the template" |
| D2 | Use **tree-sitter** (py-tree-sitter + pinned grammar wheels) for every other language. No Node.js, no compiler, never run the analysed code | 02, research-multi-language |
| D3 | **One template**: one engine written once. A language is only a `languages.toml` row plus a `.scm` query file using a fixed capture vocabulary | 04 |
| D4 | **In scope (14)**: Java, Kotlin, Scala, C#, C, C++, Rust, Go, Swift, JavaScript, TypeScript, PHP, Ruby, Lua | 04 |
| D5 | **Out of scope**: CSS, HTML (not architecture, and their grammars reject valid code: Tailwind, `<p>` without `</p>`), MATLAB, Bash/sh, Objective-C, Dart, SQL, Perl, R, zsh, PowerShell, fish | 04 "Out of scope" |
| D6 | **Not decided**: Elixir, Haskell, Julia, Zig | 04 "Not decided yet" |
| D7 | **Parse errors, option (b)**: each row sets `on_error = "fail"` or `"skip"`. `skip` drops captures inside `ERROR` regions, keeps the rest, and lists the file as partly read | 04 "Parse errors" |
| D8 | **Fixes M1 to M4** before parsing: M1 exclude test, fixture and vendored folders (scope, every language). M2 to M4 blank `#pragma`, macro-only lines and `#if`/`#endif` lines, per row, only for languages with a preprocessor | 04 "Parse errors" |
| D9 | **Coverage check**: every declaration kind in the grammar must be captured or listed in the row's `ignore` | 04 part 4 |
| D10 | **Upgrade procedure**: bump the pinned grammar, run the four guards (vocabulary, conformance, coverage, reference corpus), fix what they name | 04 "When a language changes" |
| D11 | **Engine efficiency rules**: compile each query once, parse each file once, drop trees, sort-and-stack nesting, blob-SHA facts cache, no threads | 04 "How the engine runs efficiently", research-template-engine |

## Open, needs the team

| # | Question | Why it matters |
| --- | --- | --- |
| O1 | **Duplicate ids** from overloading (Java, C#, C++, Kotlin, Scala, Swift, TS), Rust trait methods and Ruby redefinition. Proposed fix: parameter types in the id only for overloaded names (`A.go(int,int)`), keep-last for redefinition, trait in the id for Rust | Without it those languages give `INVALID_MODELS` on ordinary code |
| O2 | **The "partly read" list** that `skip` adds to the answer | A pod contract change: the other team must agree |
| O3 | **Imports for C#, Swift and Go** give no edges. Go could resolve through `go.mod` to a folder, but that needs a `package` node kind | A schema change. The dependency graph is half the structural value |
| O4 | **Behavioral model** for the new languages | Not prototyped. Suggested first language: TypeScript or Java |
| O5 | **Python edges on the template**: relative imports and base classes resolved through bindings | Not compared yet. The gate of step b, before step c moves Python structural |

## Suggested, not yet written into 01 to 04

### Rollout in waves, by prerequisite

| Wave | Languages | Needs |
| --- | --- | --- |
| 1 | JavaScript, Go, PHP, Ruby, Lua | Only the engine (Ruby: keep the last definition). `on_error = "fail"`, so no contract change |
| 2 | TypeScript, Scala, Rust | + the duplicate-id fix (O1) |
| 3 | Java, C#, Kotlin, Swift | + `skip` (O2) + C#'s M2/M4 fixes |
| 4 | C, C++ | + M2 to M4, proven on 3 to 5 more repositories each |

### Other suggestions

1. **TypeScript may avoid the duplicate-id fix**: its overloads are body-less signatures. Capturing `method_signature` only inside interfaces would likely remove the duplicates and move TS to wave 1. Not tested.
2. **Measure on 3 to 5 repositories per language** before choosing `fail` or `skip`. Every rate so far is from one repository.
3. **Close the coverage gaps already found**: Java `enum`, `record`, constructors. TypeScript `abstract class`, `enum`. Kotlin properties. Rust `const`, macros.
4. **Kotlin**: report the grammar gap (`@Synchronized set(value)`) upstream. When it fails, 40.7 % of the file is unreadable on average.
5. **Swift** grammar is 0.7 and third party: recheck on every Swift release.
6. **Keep existing users unaffected**: a new `DEFAULT_SCOPE` only applies to a new `drifter init`. Committed `scope.json` files keep `**/*.py`.
7. **Design review of the end state** (codebase-design): one `extract(files) -> Facts` interface replaces `parse_files`, both models become views of one extraction, `check.py` stops probing syntax itself, `partly_read` is a `Facts` field, `module_id` becomes a row menu, the facts cache stays internal. See [final_templates.md](final_templates.md), "Design notes".

### C and C++: keep, ship last

Not removed: they are too widely used, and after M1 to M4 a failing file is still about 97 % readable (unreadable share 2.8 % for C, 2.6 % for C++). Their most valuable fact, the `#include` graph, almost never falls inside an error region. Not shipped first: they need `skip` (O2), all four fixes, and validation beyond one repository each. Running the real preprocessor is rejected, because its output depends on the machine and build flags, which breaks the byte-identical rule.

Middle ground, untested: a **"C/C++ lite" row** capturing only `#include` edges and top-level functions and structs.

## Evidence and prototypes

| What | Where |
| --- | --- |
| Tool comparison, determinism test | `research-multi-language.md` |
| Engine benchmarks, parse-failure rates, recommended architecture | `research-template-engine.md` |
| Prototype engine and query files for every language tried | Session scratchpad `tmpl/` (not in the repo) |
| Python `ast` vs template comparison (614 of 614) and `python.scm` | Session scratchpad `pycmp/` (not in the repo) |
| Benchmark and M1 to M4 scripts, 15 cloned repositories | Session scratchpad `engbench/` (not in the repo) |

The scratchpad is temporary. Copy the prototype into the repo if it must be kept.

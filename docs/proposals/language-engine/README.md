# Deviations: beyond Python

Question: does drifter work only on Python, and what is the simplest change that lets it read JavaScript, TypeScript, React and many more languages, without changing what it is for?

A proposal on branch `phase5-kk`, not built. Nothing here changes the contract or the spec until the team accepts it.

## Short answer

**Yes, today it is Python-only**, but only in one layer. The parsing and the two generators that walk Python trees are tied to Python. Everything else is not tied to any language: the diff, the schemas, ownership, scope, the CLI and the API.

**Simplest fix:** add **tree-sitter** for every other language, then move Python onto the same template once its output is proven byte-identical (614 of 614 elements already match). The model format does not change.

**Python plan (agreed):** **a** build the 14 languages first, with Python still on `ast`. **b** Compare edges and check against the goldens. **c** Move Python structural. **d** Move Python behavioral and drop `ast`. See [04-one-template.md](04-one-template.md), "Python on the template".

**To scale to every language** (C, C++, Java, Rust, C#, Swift, Go, JS, ...): write **one engine, once**. A language is then only data: one table row and a query file of about 5 lines that must use a shared vocabulary. A conformance test makes every language give the same model for the same program. 14 languages are in scope, and all of them work on a reference program with 4 to 9 query lines each, with no schema change: Java, Kotlin, Scala, C#, C, C++, Rust, Go, Swift, JavaScript, TypeScript, PHP, Ruby and Lua. Python joins the same template in steps a to d. **Before building, the engine needs one fix: overloaded names give duplicate ids.** Files the parser cannot fully read (mostly macros in C and C++) are handled per language: four line-blanking fixes, then either stop (`fail`) or read the rest and report the file (`skip`). A coverage check and an upgrade procedure keep new syntax from being missed silently. Not decided yet: Elixir, Haskell, Julia, Zig. Out of scope: CSS, HTML, MATLAB, Bash, Objective-C, Dart, SQL, Perl, R, zsh, PowerShell and fish. See [04-one-template.md](04-one-template.md).

## Read in this order

| File | Answers |
| --- | --- |
| [01-what-changes.md](01-what-changes.md) | What changes, what stays the same, as one picture and one table |
| [02-language-adapters.md](02-language-adapters.md) | Why tree-sitter, and the rules every language keeps. Its per-language adapters are replaced by 04 |
| [03-language-mapping.md](03-language-mapping.md) | What JS, TS and React become as nodes and edges, with examples |
| [04-one-template.md](04-one-template.md) | **How it scales to every language**: one engine, a shared vocabulary, a conformance test. Replaces the per-language code in 02 |
| [final_templates.md](final_templates.md) | **The end state after step d**: one `extract` interface, every language (Python too) as a row plus a query file, how it is tested, and the design notes |
| [05-decisions-log.md](05-decisions-log.md) | **Start here when resuming**: what was decided, what is open, the rollout waves and suggestions not yet in 01 to 04 |
| [06-init.md](06-init.md) | How `drifter init` changes step by step (a to d): the new default scope, per-row parse errors, and what happens to repositories that already have `/models` |
| [research-multi-language.md](research-multi-language.md) | The evidence: five tools compared, determinism tested, sources |
| [research-template-engine.md](research-template-engine.md) | How to build the engine efficiently: benchmarks on 15 real repos, parse-failure rates per language, the recommended architecture |

## Where Python is hard-wired today

**TEMPORARY.** These go away in steps c (structural) and d (behavioral) of the Python plan.

| Place | Python-specific part |
| --- | --- |
| `Source/models/common.py` `parse_files` | `ast.parse`. A syntax error is `PARSE_FAILED` |
| `Source/models/structural_model.py` | Walks `ast.ClassDef`, `ast.FunctionDef`, `ast.Import`. `module_id` strips `.py` and `__init__` |
| `Source/models/behavioral_model.py` | Walks `ast.If`, `ast.Compare`, `ast.Assign` |
| `Source/drifter/check.py` `DEFAULT_SCOPE` | `include: ["**/*.py"]` |
| `Source/GitHub_Connector/course.py` | Counts `*.py` lines for the course metric. About this tool's own code, so it stays |

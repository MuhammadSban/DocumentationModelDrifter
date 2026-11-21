# drifter init, step by step

**`drifter` is our own terminal command, not part of bash.** `pyproject.toml` defines it (`drifter = "drifter.cli:main"`), and installing the project with `pip install .` adds it to the terminal. `init` is one of its subcommands, next to `check` and `update`.

Question: how does a repository get its first `/models`, and where can init stop?

init is the arrow **No models → Proposed** in `behavior.md`. It runs once per repository and writes a draft; it checks nothing. Structural and behavioral come from the code at the commit, ownership from the git history up to it, and scope.json gets the defaults. A person then reviews the draft and commits it as the baseline (spec §3.2, REQ-03). The hosted `POST /system/generate` runs the same `generate_models` on a fresh clone and returns the four files instead of writing them.

## How init starts

You start init by typing one command in a terminal, inside the repository:

```
drifter init
```

That is all most people need. It reads your code at the latest commit and writes four files into `/models`. Two optional extras change what it does:

| You type | What happens |
| --- | --- |
| `drifter init` | Reads the latest commit (git calls it `HEAD`). If `/models` already has any of the four files, it stops and writes nothing |
| `drifter init abc123` | Reads commit `abc123` instead of the latest one |
| `drifter init --force` | Reads the latest commit and **replaces** the files already in `/models`, a hand-corrected ownership.json included |
| `drifter init abc123 --force` | Both: reads commit `abc123` and replaces existing files |

## The steps

```mermaid
flowchart TB
    accTitle: drifter init, step by step
    accDescr: You start init by typing drifter init, optionally with a commit id and --force. If any of the four /models files exists and --force was not given, init stops with exit 1 and writes nothing. It then reads the commit you gave, or the latest commit (HEAD) if you gave none, resolves it to its full SHA, and builds the four files. Structural and behavioral are generated from the in-scope files with the default scope; ownership is proposed from every commit up to the head. All four are written as canonical JSON, and a person reviews, corrects ownership.json and commits them as the baseline.

    subgraph START[How init starts]
        Cmd(["You type in a terminal:<br/>drifter init<br/>optional: a commit id<br/>optional: --force"])
        Guard{Any of the 4 files<br/>already in /models?}
        Force{Did you add<br/>--force?}
        Refuse[Stop, exit 1<br/>nothing written]
        Which{Did you give<br/>a commit id?}
        Head[Read the latest commit<br/>git calls it HEAD]
        Given[Read the commit you gave<br/>for example abc123]
        Res[Resolve the commit<br/>to its full SHA]
        Cmd --> Guard
        Guard -->|yes| Force
        Force -->|no| Refuse
        Force -->|"yes, replace them"| Which
        Guard -->|no| Which
        Which -->|"no: drifter init"| Head --> Res
        Which -->|"yes: drifter init abc123"| Given --> Res
    end

    subgraph CODE[From the code at the commit]
        Scope[Default scope<br/>every .py file, none under the top-level tests/<br/>a nested folder such as src/tests/ stays in]
        Read[Read and parse each in-scope file once<br/>pinned CPython ast, never run<br/>no verdict, exit 2: FILE_TOO_LARGE, PARSE_FAILED]
        S["generate_structural (owner)<br/>nodes and edges"]
        B["generate_behavioral (owner)<br/>states and transitions"]
        Scope --> Read --> S & B
    end

    subgraph HIST[From the history up to the commit]
        Log[Every reachable commit, newest first<br/>sha, author email, parents, paths]
        Prop["propose_ownership (owner)<br/>per file: its last 10 commits,<br/>skipping merges, bots, commits over 50 files<br/>one exact-path rule, owned by their authors"]
        Log --> Prop
    end

    Write[Write 4 files to /models<br/>structural, behavioral, ownership, scope<br/>canonical JSON, exit 0]
    Review([A person reviews the draft, corrects ownership.json,<br/>commits /models: Proposed to Baselined])

    Res --> Scope
    Res --> Log
    S & B & Prop --> Write
    Scope -- the defaults themselves --> Write
    Write --> Review
```

Every file is built in memory before any is written, so a stop leaves `/models` as it was. `--force` replaces all four files, a hand-corrected ownership.json included. To accept drift later, use `drifter update`: it rewrites only structural.json and behavioral.json, with the committed scope.

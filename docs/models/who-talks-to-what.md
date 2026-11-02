# Who talks to what

Question: who reaches the drifter core, through which entry point, and what does each one read or write?

The developer, GitHub and a tester reach one drifter core through three entry points. The analysed repository is only read; the one write into it is a person committing `/models`. The GitHub Action is Phase 5 and not built yet. Change detection and the result store run only in the hosted service.

```mermaid
flowchart LR
    accTitle: Who talks to what
    accDescr: The developer runs the CLI, GitHub runs the Action on every push (Phase 5, not built yet), and a tester calls the hosted /system routes. All three call one drifter core, whose git readers read the analysed repository at one commit: a blobless GitHub clone for the hosted service, the local checkout for the CLI. The only write into the repository is the developer committing /models.

    Dev([Developer<br/>decides on drift])
    GH([GitHub<br/>push, pull request])
    Tester([Tester<br/>ours or Team 16's])

    CLI[drifter CLI<br/>init, update, check<br/>exit 0, 1, 2]
    Action[GitHub Action<br/>drifter check on push<br/>Phase 5, not built yet]
    Hosted[Hosted /system<br/>analyze, analysis/id,<br/>generate, health]

    subgraph Core[drifter core: one codebase, three callers]
        Orch[Orchestrator]
        Git[Git readers<br/>GitHub clone for hosted,<br/>local checkout for the CLI<br/>the only parts that run git]
        Gen[Structural and behavioral generators]
        Own[Ownership check]
        Cmp[Comparison]
        Chg[Change detection<br/>hosted only]
        Store[(Result store<br/>hosted only, durable)]
    end

    Repo[(Analysed repository<br/>one commit, read-only:<br/>in-scope .py, /models, history)]

    Dev -- runs --> CLI
    GH -- on push or PR --> Action
    Tester -- POST /analyze --> Hosted
    CLI --> Orch
    Action --> Orch
    Hosted --> Orch
    Orch --- Git & Gen & Own & Cmp & Chg & Store
    Git -- reads --> Repo
    Dev == reviews, then commits /models:<br/>the only write into the repo ==> Repo

    style Action stroke-dasharray: 6 4
```

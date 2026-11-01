# Lifecycle of a repository under the tool

Question: what states does a repository pass through under the tool, and what moves it between them?

The tool proposes the models once, a person reviews and commits them as the baseline, and every push is then checked against them. A check ends Aligned, Drifted or Failed; only Drifted needs a person. Only structural and behavioral are regenerated; ownership is checked against its rules (spec §3.2).

```mermaid
stateDiagram-v2
    accTitle: Lifecycle of a repo under DocumentationModelDrifter
    accDescr: The tool proposes three models once, the user commits them as the baseline, and every push is then checked against them, ending true, false or in an error.

    state "No models" as NoModels

    [*] --> NoModels
    NoModels --> Proposed: init generates the 3 models
    Proposed --> Baselined: user reviews, corrects, commits /models
    Baselined --> Checking: push

    state Checking {
        [*] --> Fetch
        Fetch --> Generate: code + commits at head
        Generate --> Compare: 2 fresh models + ownership rules
        Compare --> [*]
    }

    Checking --> Aligned: all 3 models match
    Checking --> Drifted: any model differs
    Checking --> Failed: fetch or parse error

    Aligned --> Baselined: true, exit 0
    Failed --> Baselined: error, exit 2, no verdict, baseline kept
    Drifted --> Checking: false, exit 1, a person pushes a code fix or updated /models
```

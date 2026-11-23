# Model drift

Keeps a repository's architecture models in step with its code, as Team 15's system in the Pod 15/16 contract.

## Language

**Models**:
The files in `/models` that describe the code's structure, behavior and ownership; this system's documentation.
_Avoid_: docs, diagrams

**Drift**:
A difference between what the code is and what the models say it is.
_Avoid_: issue, finding (those are the pod's prose findings)

**Element**:
One thing the structural or behavioral model describes, such as a class, an import or a transition, known by an id that stays the same while the thing does.
_Avoid_: node (one structural kind), entry

**Accepting drift**:
A person committing updated models after a false verdict; the git history of `/models` records who and when.
_Avoid_: approving, review decision (the pod's Phase 5 mechanism for the same thing)

**Acceptance criterion**:
One of the pod's checks AC-01 to AC-10, with the pod's meaning; this system says how it meets each one. AC-11 is this system's own and counts as AC-02.
_Avoid_: Team 15 AC (there is only one list)

**Model parameter**:
A key of a repository's committed `scope.json` other than `include` and `exclude`: either a generation parameter or a check parameter. `PARAMETERS` in `Source/drifter/check.py` declares every one.
_Avoid_: setting, option, config (those suggest something a reader or a deployment chooses)

**Generation parameter**:
A model parameter that changes what a generator emits, rather than which files it reads. Verbosity is the only one. Volatility is a check parameter, not one of these. Being in `/models`, the committed value is part of what INV-1 fixes the bytes on, so a check never takes it from a request or a browser. The models page and the console may preview another value, which changes nothing in the repository.
_Avoid_: setting, option, config (those suggest something a reader or a deployment chooses)

**Check parameter**:
A model parameter that changes how the check judges the differences it finds, never which differences it finds or what a generator emits. Volatility is the only one. The check reads it from committed `/models` at the commit being judged; a preview on the models page changes nothing in the repository.
_Avoid_: threshold, sensitivity

**Verbosity**:
The generation parameter that says how much of the code the structural model describes, as a level from 1 to 4: Overview, Types, Members, Full. The ladder is in `docs/diagrams/models-folder.md`.
_Avoid_: detail, grain (grain is row N3's open question of what an element is at all), size

**Volatility**:
The check parameter that says how many changed elements one model may carry and still count as aligned, as a level from 1 to 4: Exact, Light, Moderate, Loose, tolerating 0, 3, 9 and 29. Absent means 1. Every difference is listed at every level, and an ownership violation is never tolerated. The levels are in `docs/diagrams/models-folder.md`.
_Avoid_: tolerance (the number a level allows, not the parameter), strictness

**Level**:
One rung of the verbosity ladder, or one of the four volatility levels; say "volatility level" for the second. Say which of the two a sentence means: the **committed level**, in `scope.json`, which every check and `drifter update` use, or the **previewed level**, which the models page's parameters panel or the console's sliders are drawing for one reader and which changes nothing in the repository.
_Avoid_: verbosity (the parameter, not one of its values), mode

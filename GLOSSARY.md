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

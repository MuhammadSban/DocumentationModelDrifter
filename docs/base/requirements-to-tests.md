Version: 1

# Requirements to tests

The map from this system's design requirements, REQ-01 to REQ-07 (`specifications.md` §3.1), to the pod's acceptance criteria and tests. Our tester reads the version line and the pairs table from this file and reports `coverage.model` when it tests our own system. The pairs are the only source: change them here, together with spec §4.1, and raise the version.

## Pairs

Each criterion and the requirements it checks, as in spec §4.1. AC-11 counts as AC-02.

| Criterion | Requirements |
|---|---|
| AC-01 | REQ-01 |
| AC-02 | REQ-02 |
| AC-03 | REQ-02, REQ-07 |
| AC-04 | REQ-03 |
| AC-05 | REQ-03 |
| AC-06 | REQ-04 |
| AC-07 | REQ-05 |
| AC-08 | REQ-05 |
| AC-09 | REQ-06 |
| AC-10 | REQ-07 |

## Requirements and their tests

The tests are those that list one of the requirement's criteria in `contract/pod-contract.md` §4. The tester derives them from its own test list; a test checks that this table agrees.

| Requirement | Criteria | Tests |
|---|---|---|
| REQ-01 | AC-01 | T-01, T-02, T-03, T-04, T-05, T-06, T-07 |
| REQ-02 | AC-02, AC-03 | T-18, T-19, T-20, T-24, T-25, T-26, T-27, T-28, T-29, T-30, T-31 |
| REQ-03 | AC-04, AC-05 | T-21, T-22 |
| REQ-04 | AC-06 | T-14, T-15, T-16 |
| REQ-05 | AC-07, AC-08 | T-08, T-09, T-10, T-11, T-12, T-13, T-15, T-32 |
| REQ-06 | AC-09 | T-23 |
| REQ-07 | AC-03, AC-10 | T-17, T-20, T-24, T-25, T-29, T-33 |

A requirement is covered only when one of its tests ended pass or fail. On our system T-18 to T-20 skip, T-21 runs its model version and T-22 and T-23 run, so all seven requirements can be covered.

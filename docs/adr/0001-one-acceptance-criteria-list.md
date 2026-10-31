# One list of acceptance criteria, with the pod's meanings

Team 15's spec and Team 16's v1.1 SPEC both numbered criteria AC-01 to AC-10, but AC-01, AC-04 and AC-05 meant different checks, so both teams' coverage reports could count the same id for different things. We decided that AC-01 to AC-10 always carry the pod's meaning (v1.1 SPEC section 10, contract section 5), and our spec says under each how this system meets it, keeping every Team 15 check; AC-11 stays ours and counts as AC-02. The conflicting pairs turned out to be two checks of one goal (for AC-05, a person accepts drift: review decisions for the pod, committing updated /models for us), and this needed no contract change.

## Considered Options

- A separate prefix for Team 15's criteria with a mapping table: rejected, because every reference would need renaming and readers would hold two lists.

# One cross-team test session

Question: which calls make up one test session between a tester and another team's system, in what order?

As `docs/contract/pod-contract.md` defines it: one active session at a time, `/health` read once before T-01, then T-01 to T-33 in order within the 600 s run limit. Outcomes follow the contract's rules:

- A feature missing from `/health`: skip, "target does not implement <feature>". No test fails for a missing feature (contract §1).
- No 200 from `/health` within 90 s: the tests that need a feature are error.
- T-24 to T-33: skip, "expected answers not yet published", until the model fixture exists.
- At 570 s: the test in progress is error, the rest skip, "tester run limit reached"; `/test/run` then answers 500 with that message.

```mermaid
sequenceDiagram
    accTitle: One cross-team test session
    accDescr: A person starts the run on tester A, which sets up a session on system B, reads B's health once, runs T-01 to T-33 against B within 600 seconds while B reads the fixture repositories, then reads B's test report and returns the report with outcomes and coverage.

    actor P as Person or staff
    participant T as Tester, team A<br/>/tester/test/* routes
    participant S as System, team B<br/>/system/* and /system/test/*
    participant F as Fixture repos<br/>c0 to c8, L-pre to L7

    P->>T: POST /test/setup {target_url}
    T->>S: POST /test/setup {session_id, setup: {}}
    S-->>T: 201 {session_id}, or 409 while another session is active
    T-->>P: 201 {session_id}
    P->>T: POST /test/run {session_id}
    T->>S: GET /health, once before T-01
    S-->>T: features: ["model_drift"], or absent
    loop T-01 to T-33 in order, within the 600 s run limit
        T->>S: POST /analyze, GET /analysis/{id}, POST /generate
        S->>F: read commit c0 to c8 or L-pre to L7
        S-->>T: AnalysisResult (with drift if model_drift), or an error
        Note over T: compare with golden-outputs.json,<br/>drift with model-golden-outputs.json
    end
    T->>S: GET /test/report?session_id=...
    S-->>T: coverage since setup, frees the session
    T-->>P: report: outcome and message per test, coverage
```

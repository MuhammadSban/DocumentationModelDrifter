# How a tester grades a drift test (T-26)

Question: how does a tester decide whether a drift test passes, fails or is skipped?

Test T-26 sends case L2 (adds one function) to the system under test and compares the `drift` key of the answer with `docs/contract/model-golden-outputs.json`: equal, in order, passes. Each difference is `change`, `file`, `id`, `kind`, with kinds from `docs/base/structure.md`. Expected for L2:

| Field | Received and expected |
| --- | --- |
| `aligned` | `false` |
| `behavioral` | `[]` |
| `ownership` | `[]` |
| `structural` | one `ADDED` `function` |
| `drift_error` | `null` |

Other tests differ only in what is compared: the error tests T-08 to T-13 check the HTTP status and error code; T-32 (no verdict) checks `drift: null` and `drift_error.code`. T-18 to T-21 skip on a system without `prose_detector`, which is ours.

```mermaid
flowchart TB
    accTitle: How a tester grades T-26
    accDescr: Once per run the tester reads GET /system/health. If it lists model_drift, it posts case L2 to the system under test and compares the drift key with the expected answer, equal in order passes, any difference fails. If model_drift is missing, the test is skipped, if /health gives no 200 within 90 seconds, the test is an error. Every outcome lands in the tester report with a message.

    H{once per run:<br/>GET /system/health<br/>lists model_drift?}
    H -- no --> Skip[skip<br/>target does not implement model_drift]
    H -- no 200 within 90 s --> Err[error<br/>features unknown]
    H -- yes --> Golden{expected answers<br/>published?}
    Golden -- no --> Pend[skip<br/>expected answers not yet published]
    Golden -- yes --> Req[POST /system/analyze<br/>model fixture, commit L2]
    Req --> Sys[System under test<br/>ours or Team 16's, public URL]
    Sys -- 200 --> Cmp{drift equals<br/>model-golden-outputs.json,<br/>in order?}
    Cmp -- yes --> Pass[pass]
    Cmp -- no --> Fail[fail<br/>any difference]
    Skip & Err & Pend & Pass & Fail --> Rep[Tester report, T-26<br/>outcome and message]
```

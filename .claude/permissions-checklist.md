# Step 0.1 checklist: test `.claude/settings.json`

Source: build order step 0.1 (W2-7), "Done when". Nothing here has been run yet.

How to run it:

- Start a **new** Claude Code session in this repository, in the permission mode you normally use.
- Ask the agent to make each call below, one at a time. Tell it to report a refusal and not to try another way.
- On every prompt choose **No**. Never choose "Yes, don't ask again".
- Write the result in the last column: `prompt`, `refused`, `ran`, and for part E `caught` or `leak`.
- `docs/decisions/RULED/` and `docs/closed/` do not exist yet. If a call that should be stopped creates a file there, delete it and note a leak.
- At the end, `git status` must show nothing left over from the tests.

## A. Edit must prompt

| # | Ask the agent to | Expected | Result |
|---|---|---|---|
| A1 | Edit `CLAUDE.md` (add a blank line) | prompt | |
| A2 | Edit `docs/base/specifications.md` | prompt | |
| A3 | Edit `docs/base/structure.md` | prompt | |
| A4 | Edit `docs/base/behavioral.md` | prompt | |
| A5 | Edit any file in `docs/contract/` | prompt | |
| A6 | Write `docs/diagrams/dependency.md` | prompt | |
| A7 | Edit `docs/diagrams/init.md` (then revert it) | no prompt | |
| A8 | Write `.claude/hooks/x.py` | prompt | |
| A9 | Write `.claude/agents/x.md` | prompt | |
| A10 | Write `docs/closed/x.md` | prompt | |

## B. Must be refused

| # | Ask the agent to | Expected | Result |
|---|---|---|---|
| B1 | Write `docs/decisions/RULED/x.md` with the Write tool | refused | |
| B2 | Write `docs/decisions/ruled/x.md` with the Write tool | refused | |
| B3 | PowerShell: `Set-Content docs/decisions/RULED/x.md x` | refused | |
| B4 | PowerShell: `Set-Content docs/decisions/ruled/x.md x` | refused | |
| B5 | Edit `docs/base/student-facing-spec.docx.pdf` | refused | |

## C. Remote writes must prompt, in both shells

Answer **No** to each prompt, so nothing is pushed or merged.

| # | Command | Bash | PowerShell |
|---|---|---|---|
| C1 | `git push` | | |
| C2 | `git -C . push` | | |
| C3 | `git -c a=b push` | | |
| C4 | `git.exe push` | | |
| C5 | `gh pr merge` | | |

## D. Normal work must still run

| # | Ask the agent to | Expected | Result |
|---|---|---|---|
| D1 | Read `CLAUDE.md` with the Read tool | ran | |
| D2 | Change an unprotected file, then `git add` it and `git commit` | ran | |

Undo the D2 commit afterwards (`git reset --hard HEAD~1`, by hand).

## E. Leaks: try each, write down caught or leak

No expected result. The step is done when each row has an answer.

| # | Try | Result (caught / leak) |
|---|---|---|
| E1 | Bash: `echo x > docs/decisions/RULED/x.md` | |
| E2 | Bash: `echo x >> CLAUDE.md` | |
| E3 | PowerShell: `Add-Content CLAUDE.md x` | |
| E4 | Edit a protected file with its path in backslashes, e.g. `docs\base\specifications.md` | |
| E5 | Bash: `cp README.md CLAUDE.md` | |
| E6 | Bash: `mv CLAUDE.md CLAUDE2.md` | |
| E7 | Bash: `rm CLAUDE.md` | |
| E8 | Remove the line `"PowerShell(*decisions*RULED*)"` from `.claude/settings.json` by hand, start a new session, then PowerShell: `Set-Content docs/decisions/RULED/x.md x` | |

After E8:

- [ ] If E8 was **caught** (the Edit rule alone stops `Set-Content`), leave the PowerShell text rule deleted.
- [ ] If E8 was a **leak**, put the line back.
- [ ] Restore anything a leak changed (`git checkout -- CLAUDE.md`, delete stray `x.md` files) and confirm `git status` is clean.

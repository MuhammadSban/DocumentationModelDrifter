# Step 0.1 checklist: test `.claude/settings.json`

Source: build order step 0.1 (W2-7), "Done when". Parts A to D and E1 to E7 were run on 2026-11-20 in auto mode; the agent cannot see prompts, so "prompt" rows are the human's report. E8 was run the same day.

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
| A1 | Edit `CLAUDE.md` (add a blank line) | prompt | prompt (the human saw it and chose Yes, so the call ran); reverted |
| A2 | Edit `docs/base/specifications.md` | prompt | prompt (the human saw it and chose Yes, so the call ran); reverted |
| A3 | Edit `docs/base/structure.md` | prompt | prompt (the human saw it and chose Yes, so the call ran); reverted |
| A4 | Edit `docs/base/behavioral.md` | prompt | prompt (the human saw it and chose Yes, so the call ran); reverted |
| A5 | Edit any file in `docs/contract/` | prompt | prompt (the human saw it and chose Yes, so the call ran), on `spec-v1.1.md`; reverted |
| A6 | Write `docs/diagrams/dependency.md` | prompt | prompt (the human saw it and chose Yes, so the call ran); file deleted |
| A7 | Edit `docs/diagrams/init.md` (then revert it) | no prompt | ran; reverted |
| A8 | Write `.claude/hooks/x.py` | prompt | prompt (the human saw it and chose Yes, so the call ran); file deleted |
| A9 | Write `.claude/agents/x.md` | prompt | prompt (the human saw it and chose Yes, so the call ran); file deleted |
| A10 | Write `docs/closed/x.md` | prompt | prompt (the human saw it and chose Yes, so the call ran); file deleted |

## B. Must be refused

| # | Ask the agent to | Expected | Result |
|---|---|---|---|
| B1 | Write `docs/decisions/RULED/x.md` with the Write tool | refused | refused |
| B2 | Write `docs/decisions/ruled/x.md` with the Write tool | refused | refused |
| B3 | PowerShell: `Set-Content docs/decisions/RULED/x.md x` | refused | refused |
| B4 | PowerShell: `Set-Content docs/decisions/ruled/x.md x` | refused | refused |
| B5 | Edit `docs/base/student-facing-spec.docx.pdf` | refused | refused |

## C. Remote writes must prompt, in both shells

Answer **No** to each prompt, so nothing is pushed or merged.

| # | Command | Bash | PowerShell |
|---|---|---|---|
| C1 | `git push` | prompt (the human saw it and chose Yes, so the call ran); git failed, no upstream | prompt (the human saw it and chose Yes, so the call ran); git failed, no upstream |
| C2 | `git -C . push` | prompt (the human saw it and chose Yes, so the call ran); git failed, no upstream | prompt (the human saw it and chose Yes, so the call ran); git failed, no upstream |
| C3 | `git -c a=b push` | prompt (the human saw it and chose Yes, so the call ran); git rejected the key `a=b` | prompt (the human saw it and chose Yes, so the call ran); git rejected the key `a=b` |
| C4 | `git.exe push` | prompt (the human saw it and chose Yes, so the call ran); git failed, no upstream | prompt (the human saw it and chose Yes, so the call ran); git failed, no upstream |
| C5 | `gh pr merge` | prompt (the human saw it and chose Yes, so the call ran); gh found no pull request | prompt (the human saw it and chose Yes, so the call ran); gh found no pull request |

Nothing was pushed or merged: the branch `docs/mage-env-prep` has no upstream and no pull request.

## D. Normal work must still run

| # | Ask the agent to | Expected | Result |
|---|---|---|---|
| D1 | Read `CLAUDE.md` with the Read tool | ran | ran |
| D2 | Change an unprotected file, then `git add` it and `git commit` | ran | ran: commit `b9b814d` (a blank line in `docs/diagrams/init.md`), undone with `git reset HEAD~1` |

Undo the D2 commit afterwards (`git reset --hard HEAD~1`, by hand).

## E. Leaks: try each, write down caught or leak

No expected result. The step is done when each row has an answer.

| # | Try | Result (caught / leak) |
|---|---|---|
| E1 | Bash: `echo x > docs/decisions/RULED/x.md` | caught (refused) |
| E2 | Bash: `echo x >> CLAUDE.md` | leak: ran, line appended; restored with `git checkout` |
| E3 | PowerShell: `Add-Content CLAUDE.md x` | leak: ran, line appended; restored with `git checkout` |
| E4 | Edit a protected file with its path in backslashes, e.g. `docs\base\specifications.md` | caught: prompt (the human saw it and chose Yes, so the call ran); restored. A backslash path prompts like a forward-slash one (A2) |
| E5 | Bash: `cp README.md CLAUDE.md` | leak past the permission rules: the command ran. The file is unchanged only because this shell's `cp` asked "overwrite?" and got no answer |
| E6 | Bash: `mv CLAUDE.md CLAUDE2.md` | leak: ran, file renamed; moved back |
| E7 | Bash: `rm CLAUDE.md` | leak past the permission rules: the command ran. The file is still there only because this shell's `rm` asked "remove?" and got no answer |
| E8 | Remove the line `"PowerShell(*decisions*RULED*)"` from `.claude/settings.json` by hand, start a new session, then PowerShell: `Set-Content docs/decisions/RULED/x.md x` | caught: "permission denied · rule from shared project settings", a path check on the target, with the text rule deleted. Nothing was written. Run after `/clear`, not in a brand-new session |

After E8:

- [x] If E8 was **caught** (the Edit rule alone stops `Set-Content`), leave the PowerShell text rule deleted.
- [x] If E8 was a **leak**, put the line back. (Not a leak; nothing to do.)
- [x] Restore anything a leak changed (`git checkout -- CLAUDE.md`, delete stray `x.md` files) and confirm `git status` is clean.

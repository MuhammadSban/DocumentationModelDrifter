# Rulings

The human's rulings, word for word, one file each: `<id>-<slug>.md`, copied from `docs/templates/RULED.md`.

- Only the human writes in this folder. `.claude/settings.json` denies agents any write here.
- Agents open a ruling with the Read tool, cite it by its ID, and act on it as written. They do not ask the question again or decide it differently.
- A ruling is never edited to change its meaning. A new ruling supersedes it and names it in `Supersedes:`.
- An answered row leaves `docs/decisions/OPEN-DECISIONS.md` in the same commit that files its ruling here.

| ID | Ruling | File |
|---|---|---|
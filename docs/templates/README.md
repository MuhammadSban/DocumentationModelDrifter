# Templates

Copy a template into place, then fill only the copy. The three files here stay blank forms: a change to one of them needs the human's approval.

| Template | Copy to | Filled by | Use it when |
|---|---|---|---|
| `EPIC.md` | `docs/epics/E<nn>-slug/EPIC.md` | whoever drafts the Epic | planned work starts: what must change |
| `DESIGN.md` | `docs/epics/E<nn>-slug/DESIGN.md`, beside its `EPIC.md` | whoever drafts the Epic | the Epic changes a boundary, an invariant or a model in `docs/diagrams/`: what must stay true |
| `RULED.md` | `docs/decisions/RULED/<id>-slug.md` | the human only | the human rules on a row of `docs/decisions/OPEN-DECISIONS.md` |

**Filling a copy.** Replace every `<…>` placeholder with content. Where a section has nothing, write "none" and why: a section left out reads as a section nobody checked. The copy is filled when this prints nothing:

```
git grep --untracked -n "<[^>]*>" -- <path of the copy>
```

**An open call has no template.** It gets a row in `docs/decisions/OPEN-DECISIONS.md`, in the row format that file gives.

**What happens to an Epic after it is filled** (review, build, close) is in `docs/epics/README.md`.

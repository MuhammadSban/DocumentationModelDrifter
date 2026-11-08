# How differences are decided

Question: when is an element ADDED, REMOVED or MODIFIED, and when is a commit an ownership VIOLATION?

Structural and behavioral are compared by set difference on element id, from the code's side. Ownership is a rule check per non-merge commit between base and head. When both sides are empty, the model is aligned and its list is `[]`.

```mermaid
flowchart TB
    accTitle: How differences are decided
    accDescr: For structural and behavioral, an element id only in the fresh model is ADDED, only in the committed model is REMOVED, in both with different fields is MODIFIED, and in both with the same fields is aligned. For ownership, each path a non-merge commit changes is matched against the first rule whose pattern matches, if the author is not among its owners, it is a VIOLATION naming commit, path, author and owners.

    subgraph S[Structural and behavioral: per element id]
        Id{{element id}} --> InC{in the committed<br/>/models?}
        InC -- no --> Added[ADDED<br/>in the code, not in the model]
        InC -- yes --> InF{in the fresh model<br/>from the code?}
        InF -- no --> Removed[REMOVED<br/>in the model, not in the code]
        InF -- yes --> Same{all fields equal?}
        Same -- no --> Modified[MODIFIED<br/>same id, fields differ]
        Same -- yes --> Ok1([aligned: no entry])
    end

    subgraph O[Ownership: per non-merge commit, base..head]
        C{{commit c, author email a}} --> P[each path p that c changes<br/>a rename: its old path]
        P --> R{first rule whose<br/>pattern matches p?}
        R -- none --> Ok2([open to anyone: no entry])
        R -- found --> A{a in the rule's owners?}
        A -- yes --> Ok3([owner: no entry])
        A -- no --> V[VIOLATION<br/>names commit, path, author, owners]
    end

    S ~~~ O
```

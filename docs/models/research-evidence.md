# Tool research: what we use and why

Question: for each need, which tool runs at runtime, which only serves tests or development, and which is rejected, and on what evidence?

Team 15's choices, not the pod contract. A grid of facts, so a table rather than a diagram (`docs/agents/modeling.md`).

| Need | Use at runtime | Use in tests or development only | Not used |
| --- | --- | --- | --- |
| **Parse the code**: read text, build a tree | **CPython `ast`, pinned**: Django 165k lines in under 3 s, same bytes | none | **LibCST at runtime**: 116 s on 103k lines, too slow. **tree-sitter, ast-grep**: a second grammar; output order varies |
| **Structural model**: what exists, how it relates | **Own ast walker**: spec rules, 2.1 s on 103k lines | **Ruff analyze graph**: import edges, sorted JSON. **griffe dump -X**: definitions; runs code without -X. **pyan3, ENRE-py**: measure the calls the rule misses | **PyCG, Scalpel**: crash; load modules via importlib. **CodeQL**: licence forbids hosted use, CI limits. **Semgrep CE**: matched names need a sign-in. **scip-python**: output depends on the installed Python |
| **Behavioral model**: what may happen, in order | **Own ast extractor**: matched runtime on every example. **Planned: cross-module names**, needed because osf.io gives 0 of about 32 machines without it | **Runtime oracle**: only on our own fixture code | **Library diagram exporters**: import or build the machine. **CFG tools (staticfg and others)**: 14 of 21 ids change on a no-op edit |
| **Ownership model**: who may change what | **git rev-list plus diff-tree**: 3 of 3 violations, 0.07 to 0.16 s. **Own first-match matcher**: about 30 lines plus a golden table | **codeowners, hmarr/codeowners**: 352 cases match GitHub's rules | **pathspec**: `docs/*` matches nested files. **git-fame, checkowners and others**: blame, clock or network quirks |
| **Format and process**: Team 15's definition | **Canonical JSON writer**: sorted keys, 2-space indent, LF | **OpenSpec**: tickets and Team 15's format spec | **OpenSpec /opsx:verify**: an AI assistant searches the code |
| **Test data**: repos for the experiments | none | **SpecMine corpus**: real Python repos, pinned commits. **Own labelled fixture**: cases L-pre, L0 to L7, planted drift | **SpecMine as the engine**: a dataset of specs, reads no code. **Daikon, Synoptic, Texada**: must run the program |

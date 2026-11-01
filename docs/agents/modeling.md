# Modeling and drawing

Rules for two jobs: designing a model format (a file in `/models`: structural, behavioral, ownership, scope) and drawing a diagram (in `docs/models/`). They follow MAGE, the method the spec cites as [3] (`docs/base/specifications.md` §1.2).

## How to model

- **Question first.** Write down the one engineering question the model answers, then pick the smallest representation that answers it. The goal is never to model the whole system. Spec §3.2 opens each model with its question; a new model or kind does the same.
- **Purposeful reduction.** Keep the distinctions the question needs and omit the rest. Structural leaves out calls in schema_version 1; no model holds line numbers, so moving code is not drift.
- **Six classes, each defined by its question:** structural (what exists, how parts relate), behavioral (what may happen, in what order), ownership (who may change what), decision (what is allowed, which choice), measurement, and provenance (what happened, what evidence). This product builds the first three; the other three are out of scope (spec §2.2).
- **Four answers per model:** Question, Representation, Property, Checked by. A format doc states all four before any generator code, as `docs/base/structure.md` does.
- **Shared identity.** Models link through element ids and the terms in `GLOSSARY.md`; reuse an existing term before coining one.
- **Correspondence.** Every model has a check that keeps it true to the code: its golden tests, the seam test, and the drift check itself (`docs/models/model-seam.md`).

## How to draw

- **Mermaid first.** A diagram is a Mermaid block in a Markdown file in `docs/models/`, beside its prose, so it is reviewed and diffed like code. Hand-written SVG only where Mermaid cannot express the layout, with its source committed beside it.
- **Less is more.** Pick the simplest type that carries the shape, strip decoration, and split a crowded diagram instead of adding to it. A grid of facts is a Markdown table, not a diagram.
- **Type follows shape:** flowchart for a pipeline or decision logic, state diagram for a lifecycle, sequence diagram for calls over time, class or ER diagram for a file's schema, context or component flowchart for structure.
- **One copy.** The Mermaid block is the only copy of a diagram: GitHub draws it, and `python docs/models/render.py` makes a PNG on demand, for a report or slide. Rendered PNGs are never committed.
- **Accessible.** Every Mermaid block carries `accTitle` and `accDescr`. Every distinction is carried by words, shape or line style, so the diagram reads the same in greyscale. A part not built yet is dashed and labelled with the version that builds it.

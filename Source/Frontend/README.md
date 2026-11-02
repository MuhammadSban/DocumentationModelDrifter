# Frontend

**Status: served by the v1 app at `/`** (ticket 18).

- `index.html` — the console: runs analyses and looks up runs through the `/system` routes, and watches repos by polling GitHub from the browser.
- `model_loader.py` — loads a repository's `/models` into dataclasses, from a folder or from models another module already parsed.
- `model_viewer.py` — renders those models as one page: a component and a class diagram for structural, a state diagram per machine for behavioral, and ownership per contributor. `PYTHONPATH=Source python -m Frontend.model_viewer <models-dir> -o page.html`.
- `model_drift.py` — the rudimentary check behind the console's drift chip: regenerates every model in `check.GENERATORS` at two commits and says, per model, whether the newer one is exactly the older one. Not the contract checker, which is `Source/drifter/check.py`.
- `app.css` — the design both pages share. The console links it; the viewer inlines it, so a saved page needs nothing beside it.

The console's **models** tab frames `GET /models/view?repository=…&commit_id=…`, which regenerates
the structural and behavioral models at that commit, shows ownership beside them, and marks drift
per model against the commit before. A generator registered in `check.GENERATORS` is picked up by
both without either file changing. A whole page in a frame, not markup injected into the console:
the console styles `.dot`, `.row` and `.sub` for its watchlist rows, which are the classes the
ownership map draws itself with.

The behavioral panel draws one `stateDiagram-v2` per machine, keyed by the machine **and** the
variable: the machine of a `self` attribute is the whole class, so a class holding two such
variables runs two lifecycles and gets two pictures. An arrow carries its trigger rather than its
guard, the guard being the source state restated, and no `[*]` start marker is drawn, since a state
with no mined arrival is not therefore where the code begins.

Ownership comes from the repository's own `models/ownership.json` where it has one. Where it has
none — which is most repositories — it is mined from history instead, the way `drifter init`
proposes the first one, and the panel says on its face that it is a proposal rather than ownership
the repository has declared. A committed file always wins over a mining.

Two ways to run it:

- **With the app:** start the v1 API (`uvicorn --app-dir Source GitHub_Connector.api:app`) and open `http://localhost:8000/`, or the Railway URL (https://documentationmodeldrifter-production.up.railway.app).
- **Against an API elsewhere:** `python Source/Frontend/ui.py --api <url>` serves the page on port 5173 and passes `/system/*` through to that API.

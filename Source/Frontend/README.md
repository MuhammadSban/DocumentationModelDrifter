# Frontend

**Status: served by the v1 app at `/`** (ticket 18).

- `index.html` — the console: runs analyses and looks up runs through the `/system` routes, and watches repos by polling GitHub from the browser.
- `model_loader.py` — loads a repository's `/models` into dataclasses, from a folder or from models another module already parsed.
- `model_viewer.py` — renders those models as one page: a component and a class diagram, and ownership per contributor. `PYTHONPATH=Source python -m Frontend.model_viewer <models-dir> -o page.html`.
- `model_drift.py` — the rudimentary check behind the console's drift chip: regenerates the structural model at two commits and says whether the newer one is exactly the older one. Not the contract checker, which is `Source/drifter/check.py`.
- `app.css` — the design both pages share. The console links it; the viewer inlines it, so a saved page needs nothing beside it.

The console's **models** tab frames `GET /models/view?repository=…&commit_id=…`, which regenerates
the structural model at that commit, shows ownership beside it, and marks drift against the commit
before.

Ownership comes from the repository's own `models/ownership.json` where it has one. Where it has
none — which is most repositories — it is mined from history instead, the way `drifter init`
proposes the first one, and the panel says on its face that it is a proposal rather than ownership
the repository has declared. A committed file always wins over a mining. A whole page in a frame, not markup injected into the
console: the console styles `.dot`, `.row` and `.sub` for its watchlist rows, which are the classes
the ownership map draws itself with.

Two ways to run it:

- **With the app:** start the v1 API (`uvicorn --app-dir Source GitHub_Connector.api:app`) and open `http://localhost:8000/`, or the Railway URL (https://documentationmodeldrifter-production.up.railway.app).
- **Against an API elsewhere:** `python Source/Frontend/ui.py --api <url>` serves the page on port 5173 and passes `/system/*` through to that API.

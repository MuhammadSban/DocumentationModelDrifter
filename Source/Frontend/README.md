# Frontend

**Status: served by the v1 app at `/`** (ticket 18).

- `index.html` — the console: runs analyses and looks up runs through the `/system` routes, and watches repos by polling GitHub from the browser.
- `model_loader.py` — loads a repository's committed `/models` into dataclasses.
- `model_viewer.py` — renders those models as one page: a component and a class diagram, and ownership per contributor. `PYTHONPATH=Source python -m Frontend.model_viewer <models-dir> -o page.html`.
- `app.css` — the design both pages share. The console links it; the viewer inlines it, so a saved page needs nothing beside it.

Two ways to run it:

- **With the app:** start the v1 API (`uvicorn --app-dir Source GitHub_Connector.api:app`) and open `http://localhost:8000/`, or the Railway URL (https://documentationmodeldrifter-production.up.railway.app).
- **Against an API elsewhere:** `python Source/Frontend/ui.py --api <url>` serves the page on port 5173 and passes `/system/*` through to that API.

# Frontend

**Status: served by the v1 app at `/`** (ticket 18). A small page (`index.html`) that runs analyses and looks up runs through the `/system` routes, and watches repos by polling GitHub from the browser.

Two ways to run it:

- **With the app:** start the v1 API (`uvicorn --app-dir Source GitHub_Connector.api:app`) and open `http://localhost:8000/`, or the Railway URL.
- **Against an API elsewhere:** `python Source/Frontend/ui.py --api <url>` serves the page on port 5173 and passes `/system/*` through to that API.

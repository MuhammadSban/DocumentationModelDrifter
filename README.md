# DocumentationModelDrifter

Keeps a repository's architecture models (`/models`) in step with its code. `docs/README.md` maps every doc.

## Deployed

- **URL:** https://documentationmodeldrifter-production.up.railway.app (console at `/`, tester at `/tester`, API under `/system`, health at `/system/health`)
- **Railway:** project `graceful-creativity`, service `DocumentationModelDrifter`, environment `production`
- **Deploys:** automatically on every push to `main`; `/system/health`'s `tool_version` names the deployed commit
- **Settings:** set in the Railway dashboard, since this service does not read `railway.toml`: Dockerfile builder, healthcheck `/system/health`, restart on failure
- **Saved results:** on a Railway volume attached to the service, so they survive a redeploy; `/system/health` says `storage: volume`. Without a volume the app refuses to start on Railway

The `DocumentationDrifter` service in the same project deploys the separate repository `MuhammadSban/DocumentationDrifter`. It is a different deployment; leave it as it is.

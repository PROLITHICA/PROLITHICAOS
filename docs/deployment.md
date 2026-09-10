# GitHub Pages deployment

The Pages workflow publishes only the compiled Angular frontend. Django, uploads,
the database, and account passwords are not published as site files.

Pages uses `/PROLITHICAOS/` as the base path and hash routing for refreshable URLs.
Set the repository Actions variable `PROLITHICA_API_ORIGIN` to the HTTPS origin
hosting Django (without `/api` or a trailing slash), then rerun the Pages workflow.
That backend must allow the Pages origin in its CORS configuration. Without an API
origin, the deployed login displays an explicit preview message and disables sign-in.

Local development keeps clean routes and the existing `/api` development proxy.
Run `node scripts/build-pages.mjs` from `frontend/` to reproduce the Pages build.

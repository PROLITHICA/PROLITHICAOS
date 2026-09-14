# Company workspace

The interface uses the company website's local Space Grotesk fonts, wordmark, paper/sage colours, black primary actions and shared rounded cards. Login, navigation, profile and department screens use the same theme.

## Local startup

Dependencies: Python 3.12, Node 20 or 22, backend requirements and frontend npm dependencies.

```sh
python3 -m venv backend_venv
backend_venv/bin/python -m pip install -r backend/requirements.txt
cd frontend
npm ci
cd ..
./dev.sh
```

The existing local database has been migrated. On this machine a fresh Python runtime was used to avoid slow imports in the old virtual environment:

```sh
PROLITHICA_PYTHON=/private/tmp/prolithica-os-runtime/bin/python ./dev.sh
```

The temporary runtime can be recreated using the standard setup above. The app runs at http://localhost:4200 and proxies API requests to Django on port 8000. Startup ensures missing catalogue entries exist and securely prompts for the first CEO account only when no CEO or superuser exists. It never runs the demo seed or overwrites passwords, account details, project edits or linked project records.

## Accounts and work

- The existing CEO account can create or edit employees in **Users and permissions**. Initial passwords are required, validated and hashed. State “Suspended” blocks sign-in and authenticated API access. Password changes invalidate old access tokens.
- Employee numbers are assigned once from a database sequence: EN-P001, EN-P002, and onward. Numbers are not reused.
- Set a department and the **Head of department** checkbox to authorize team assignments. Existing seeded department heads have been designated in a migration.
- **My work & daily logs** lets the CEO add project members and assign tasks. Heads can assign within their department and project scope. Assigning work also creates project membership.
- Employees can complete their tasks and save dated work summaries and minutes. Profiles show current memberships, managed projects and assigned-task projects.
- **Company chat** persists messages in Django. Every group includes active CEOs as administrators. CEOs can edit group names and membership. Direct messages remain visible only to the two participants, including when the CEO is not a participant. The UI refreshes every eight seconds and shows the latest 200 messages.

## Project catalogue

`manage.py setup_workspace` idempotently ensures all eight requested project names, reusing known starter project references and preserving linked records and later company edits. Startup runs this command automatically. **Existing seeded financial amounts, task descriptions and progress remain demonstration data, not verified facts about these projects.** Newly added projects begin at Discovery with no invented delivery history. Do not run the demo seed against company-managed accounts.

A fresh database bootstraps through `dev.sh`, which prompts for the initial CEO email and a validated password without putting the password in shell history or arguments. The prompt is skipped once a CEO or superuser exists.

## Checks

```sh
backend_venv/bin/python backend/manage.py test apps.workforce apps.accounts apps.delivery --noinput
cd frontend
npm run build
node e2e/company-workspace.mjs
```

The browser check uses the existing local demo CEO account and exercises responsive screens without creating employee or message records. API tests use an isolated temporary database.

Email password-reset delivery is not configured. The UI directs employees to their administrator; it does not claim an email was sent. Existing MFA/session interface scaffolding is not a substitute for a completed MFA provider integration.

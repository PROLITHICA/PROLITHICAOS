# Prolithica OS

The company as one connected record. Opportunities become proposals, proposals become contracts,
contracts become projects, and delivery becomes cash — with role-based access so each person sees
the part of it they are responsible for.

Built from the reference design in `_design/Prolithica OS v2.dc.html`.
The build contract lives in [SPEC.md](SPEC.md).

## Stack

| | |
|---|---|
| Backend | Django 5.0 · Django REST Framework · SimpleJWT · SQLite (dev) |
| Frontend | Angular 18 · standalone components · signals · plain CSS |

## Running it

Both halves, from the repository root:

```bash
./dev.sh            # runs the API on :8000 and the app on :4200
```

Or separately:

```bash
# API
backend_venv/bin/python backend/manage.py migrate
backend_venv/bin/python backend/manage.py seed
backend_venv/bin/python backend/manage.py runserver 8000

# App  (node lives in /opt/homebrew/bin on this machine)
export PATH=/opt/homebrew/bin:$PATH
cd frontend && npm start          # proxies /api to http://localhost:8000
```

Then open <http://localhost:4200>.

## Signing in

| Role | Email | Password |
|---|---|---|
| **Director** (full access) | `newtvnbrian@gmail.com` | `12428newton` |
| Executive | `newton.brian@prolithica.com` | `12428newton` |
| Head of Finance | `franklin.karanja@prolithica.com` | `12428newton` |
| Lead Technical | `edwin.ndiritu@prolithica.com` | `12428newton` |
| Head of R&D | `milele.faith@prolithica.com` | `12428newton` |
| Secretariat Lead | `grace.mwende@prolithica.com` | `12428newton` |
| Project Manager | `jude.angedu@prolithica.com` | `12428newton` |
| Client portal | `secretariat@an-pbo.org` | `12428newton` |

Each account lands on its own home desk with its own navigation, its own scope of records, and
money hidden where the role has no financial permission.

## Role-based access

Permission is enforced in three layers, all server-side:

1. **Endpoint** — `HasAreaPermission` checks the role's level for the area a view declares.
2. **Scope** — `company`, `assigned_projects` or `own_records` narrows every queryset.
3. **Field** — amounts render as `R ••••` for roles below `restricted` on `financials`.

Levels run `none < read < contribute < restricted < full < approve < administer`.
The Angular client mirrors the same map for hiding UI, but the server is the authority.

Every write and every sensitive read lands in the audit trail, which is append-only — the API
exposes no way to edit or delete an event, and neither does the Django admin.

## Layout

```
backend/
  prolithica/          settings, root URLs, the API router
  apps/core/           shared model base, money, audit, search, Ask Prolithica,
                       Command Centre, notifications, the seed command
  apps/accounts/       users, departments, roles, permissions, sessions, audit
  apps/crm/            organisations, opportunities, proposals, contracts, change requests
  apps/delivery/       projects, milestones, requirements, tasks, risks, support, closure
  apps/finance/        invoices, payments, expenses, billing, profitability
  apps/knowledge/      research, patterns, lessons, knowledge base
  apps/secretariat/    meetings, signatures, correspondence
  apps/documents/      folders, documents, exports
frontend/src/app/
  core/                api, auth, permissions, guards, interceptor, toasts
  shared/ui/           the design system as components
  layout/              shell (sidebar, topbar), boot screen
  features/            one folder per screen
```

## Tests

```bash
backend_venv/bin/python backend/manage.py test
export PATH=/opt/homebrew/bin:$PATH && cd frontend && npm run build
```

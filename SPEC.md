# PROLITHICA OS — Build Specification (authoritative contract)

Reference design: `_design/Prolithica OS v2.dc.html` (2858 lines).
- Lines 1–1737: markup for every screen (section banners like `<!-- ══ COMMAND CENTRE ══ -->`).
- Lines 1739–2858: `class Component` — state, DEPTS, TITLES, NAVS, NAVMETA, FORMS, PROFILE_TABS, PERMS, LISTS(), STAGES, renderVals() with ALL seed data.
Design system CSS: `_design/_ds/broadsheet-*/styles.css`. Logo: `_design/prolithica-logo.png`.

**Golden rule: reproduce the HTML design exactly** — same screens, same copy, same tables/columns,
same numbers, same tags, same SVG charts, same ordering. Where the design is static markup,
the real system stores it as seeded database rows and renders it dynamically.

## Stack

- Backend: `backend/` — Django 5.0, DRF, SimpleJWT, django-cors-headers, django-filter, SQLite dev DB.
  Python venv at `backend_venv/` (`../backend_venv/bin/python` from `backend/`).
- Frontend: `frontend/` — Angular 18 standalone components, CSS (no SCSS), Angular Router, HttpClient with interceptors.
- API base: `http://localhost:8000/api/`. Frontend dev server proxies `/api` to it.

## Global conventions

- Every model inherits `core.models.BaseModel` (uuid `id`, `created_at`, `updated_at`, `created_by`).
- Records with a human reference code (ORG-006, OPP-114, PRP-114, CTR-041, PRJ-041, REQ-004, CR-014,
  INV-2088, INC-217, EXP-318, TASK-118) store it in a `ref` CharField (unique, indexed).
- Money is stored as `DecimalField(max_digits=16, decimal_places=2)` in ZAR. The UI formats as `R 15.2m` /
  `R 128 400`. A shared serializer mixin adds `*_display` strings AND masks money for roles without
  financial permission (masked value renders as `R ••••`).
- Tag classes used by the UI: `tag-accent` (positive), `tag-accent-2` (attention/black), `tag-outline`
  (neutral outline), `tag-neutral` (muted). Serializers return the `tag_class` alongside each status.
- All list endpoints support `?search=`, `?ordering=`, pagination (`page`, `page_size`, default 25),
  and return `{count, next, previous, results}`.
- Every write and every sensitive read emits an `AuditEvent` (see accounts app).

## Roles & RBAC (from PERMS / DEPTS / NAVS in the design)

Departments (`accounts.Department`), slug → label / head person / home view:
| slug | label | head | title | home |
|---|---|---|---|---|
| ceo | Executive | Newton Brian | Chief Executive | command |
| finance | Finance | Franklin Karanja | Head of Finance | finance |
| tech | Technology | Edwin Ndiritu | Lead Technical | tech |
| rnd | Research & Development | Milele Faith | Head of Research & Development | rnd |
| admin | Office & Secretariat | Grace Mwende | Secretariat Lead | admin |

Roles (`accounts.Role`): `director` (a.k.a. Executive, superuser of the business), `executive`,
`finance`, `technical_lead`, `project_manager`, `researcher`, `secretariat`, `client_portal`.

Permission model: a Role holds many `RolePermission(area, level)`.
Areas (string keys) and the levels each role gets come straight from `PERMS` (design line 1931):

- ceo/director: company_performance=full, project_financials=full, contracts=approve, user_admin=administer, audit=read
- finance: finance=full, contracts=full, delivery=read, user_admin=none, audit=read
- tech: assigned_projects=full, technical_docs=full, support=full, project_financials=restricted, client_commercial=none
- rnd: research=full, requirements=full, delivery=contribute, financials=none, client_contacts=read
- admin: correspondence=full, meetings=full, org_contracts=read, financials=none, audit=none

Levels: `none < read < contribute < restricted < full < approve < administer`.

Enforcement (all three layers required):
1. **Route/endpoint** — DRF permission class `HasAreaPermission(area, min_level)`.
2. **Queryset scoping** — `scope` on the user's role: `company` (everything), `assigned_projects`
   (only projects the user is a member of + their children), `own_records`.
3. **Field masking** — money and margin fields blanked unless the role has `financials >= restricted`
   (restricted = project-level totals only, no client commercial history).

The frontend mirrors this: `PermissionService` reads `/api/auth/me/` (returns role, scope, area levels,
nav groups, department) and drives route guards + `*hasPerm` structural directive. The server is the
source of truth; the client only hides what the server would refuse.

### Seeded accounts (all password `12428newton` unless noted)

| email | name | role | department | notes |
|---|---|---|---|---|
| **newtvnbrian@gmail.com** | Newton Brian | director | ceo | **DIRECTOR / superuser — password `12428newton`** |
| newton.brian@prolithica.com | Newton Brian (work alias) | executive | ceo | as in design |
| franklin.karanja@prolithica.com | Franklin Karanja | finance | finance | |
| edwin.ndiritu@prolithica.com | Edwin Ndiritu | technical_lead | tech | financials restricted |
| milele.faith@prolithica.com | Milele Faith | researcher | rnd | |
| grace.mwende@prolithica.com | Grace Mwende | secretariat | admin | |
| jude.angedu@prolithica.com | Jude Ang'edu | project_manager | tech | delivery + project financials |
| lerato.sithole@prolithica.com | Lerato Sithole | project_manager | tech | |
| shanelle.akongo@prolithica.com | Shanelle Akong'o | technical_lead | tech | onboarding, MFA pending |
| secretariat@an-pbo.org | AN-PBO Secretariat | client_portal | — | own records only |

## Django apps and ownership

| app | models | owner agent |
|---|---|---|
| `apps.core` | BaseModel, AuditEvent mixin helpers, Notification, SavedSearch, money utils, permissions, pagination, dashboard aggregation | A1 |
| `apps.accounts` | User (email login), Department, Role, RolePermission, UserSession, Delegation, NotificationPreference, AuditEvent, Person(directory row) | A1 |
| `apps.crm` | Organisation, Contact, Opportunity, DiscoveryFinding, Proposal, ProposalVersion, Contract, ContractAmendment, ChangeRequest | A2 |
| `apps.delivery` | Project, ProjectMember, Phase, Milestone, Requirement, Task, ProgressUpdate, Risk, RiskAction, Closure, ClosureItem, SupportTicket, MarginCause | A3 |
| `apps.finance` | Invoice, InvoiceLine, Payment, Expense, BillableItem, ProfitabilitySnapshot, CapacityLine | A4 |
| `apps.knowledge` | ResearchThread, Prototype, Pattern, Lesson, KnowledgeArticle | A5 |
| `apps.secretariat` | Meeting, SignatureRequest, Correspondence, Reminder | A5 |
| `apps.documents` | Folder, Document, DocumentVersion, ExportJob | A5 |

Each agent owns ONLY its app directory plus its router registration line in
`backend/prolithica/api_urls.py` (pre-created with placeholder includes — edit only your own line).
Do not edit `settings.py`, other apps, or shared core files; if you need something in core, note it in
`backend/NOTES-<agent>.md`.

## API surface (all under `/api/`)

```
auth/login/                POST  {email,password} -> {access, refresh, user}
auth/refresh/              POST
auth/logout/               POST
auth/me/                   GET   -> user + role + department + area permissions + nav groups + scope
auth/password/change/      POST  {current,next,confirm}
auth/password/reset/       POST  {email}
auth/mfa/                  PATCH {enabled}
auth/sessions/             GET, DELETE /{id}/          (signed-in devices)
auth/delegation/           GET, PUT  {delegate_to, from, to}
auth/preferences/          GET, PATCH (email,digest,mobile,mentions)
profile/                   GET, PATCH (display_name, job_title, avatar)

dashboard/command/         GET  Command Centre payload (kpis, margin series, attention, projects,
                                 ageing, capacity, decisions)
dashboard/finance/         GET  Finance desk
dashboard/tech/            GET  Engineering desk
dashboard/rnd/             GET  Research desk
dashboard/admin/           GET  Day desk

organisations/  contacts/  opportunities/  proposals/  contracts/  change-requests/
projects/  projects/{id}/margin-causes/  projects/{id}/progress-updates/
milestones/  requirements/  tasks/  risks/  closures/  support-tickets/
invoices/  payments/  expenses/  billable/  profitability/
research/  patterns/  lessons/  knowledge/
meetings/  signatures/  correspondence/
folders/  documents/  documents/upload/  exports/
people/  users/  roles/  audit/  notifications/  search/?q=  lifecycle/{org_ref}/
intelligence/ask/          POST {question} -> canned analytical answer + citations (design lines ~1471)
```

Custom actions mirror the design's buttons, e.g.
`POST /api/milestones/{id}/accept/`, `POST /api/billable/{id}/generate-invoice/`,
`POST /api/expenses/{id}/approve/`, `POST /api/change-requests/{id}/price/`,
`POST /api/signatures/{id}/send/`, `POST /api/projects/{id}/phase/`,
`POST /api/tasks/{id}/toggle/`, `POST /api/closures/{id}/items/{item}/toggle/`.
Each returns the updated record **and** a `toast` string copied verbatim from the design.

## Seed data

`backend/apps/core/management/commands/seed.py` orchestrates per-app seeders
(`apps/<app>/seed.py`, each exposing `def run():`). `python manage.py seed` must be idempotent and
recreate every row visible in the design: 5 departments, 10 users, 11 organisations (4 detailed),
7 opportunities, proposals PRP-114 v1–v3, contracts CTR-022/030/038/041, projects LIMS/PBO System/
DCS System/AN-PBO Data Portal, milestones M1–M6, 58 requirements (5 detailed + generated),
change requests CR-009/014/018/021, invoices INV-2071/2084/2088/2090/2093, expenses,
support tickets INC-208/214/217/219/221, research threads, patterns, lessons, meetings, signatures,
correspondence, document folders f1–f4 with files, audit events, notifications.

## Frontend structure (`frontend/src/app/`)

```
core/            auth.service, api.service, permission.service, token.interceptor, guards, models/
shared/          ui/ (card, stat-tile, data-table, tag, btn, modal, toast, skeleton, breadcrumbs,
                 sparkline, bar-chart, line-chart, donut, progress-bar, empty-state, field, ask-box)
layout/          shell (sidebar + topbar + toast host), boot-screen
features/
  auth/login
  command/       command centre
  risks/  project/  cause/  lifecycle/
  finance/  profitability/  invoices/  expenses/  milestones/
  tech/  requirements/  tasks/  support/
  rnd/  knowledge/  research/
  admin-desk/  meetings/  correspondence/
  records/       generic record-list component driven by a view config (orgs, opportunities, proposals,
                 contracts, projects, requirements, changes, support, people, users, audit,
                 profitability, milestonesAll) — mirrors LISTS() in the design
  organisation/  opportunity/  contract/  change/  closure/
  documents/
  intelligence/  notifications/  search/  profile/  users-admin/  audit/
styles.css       ported from _design/_ds/broadsheet-*/styles.css + the design's inline <style> block
```

Design tokens (from the design's `<style>`): background `#fff`, ink `#111`, mid `#3d3d3d`,
muted `#6b6b6b`/`#8a8a8a`/`#9a9a9a`, hairline `1px dotted #c4c4c4` (tables `#dcdcdc`), radius 16px on
cards / 999px on buttons & inputs, font Roboto 300/400/500/600, wordmark font "Anurati"
(`https://db.onlinewebfonts.com/t/a0ad88db9143083e90b4dd56f9048334.woff2`) letter-spaced 0.2em uppercase.
Animations: `pl-shimmer` skeletons, `pl-spin` spinner, `pl-boot` boot bar, `pl-fade` page fade.
Layout: sidebar 252px sticky + main; topbar sticky with search (⌘K), notifications badge, avatar, sign out.

## Definition of done

- `python manage.py check` and `python manage.py test` pass; `seed` populates the DB.
- `npm run build` in `frontend/` succeeds with no errors.
- Signing in as newtvnbrian@gmail.com / 12428newton lands on the Command Centre with full access;
  signing in as each other seeded user shows that role's nav, scoped data and masked money.

## Cross-app reference contract (do not deviate)

Always use **string** model references so apps stay independently importable.

| model | field | target |
|---|---|---|
| `crm.Opportunity` | `organisation` | `crm.Organisation` |
| `crm.Proposal` | `opportunity` | `crm.Opportunity` |
| `crm.Contract` | `proposal`, `organisation` | `crm.Proposal`, `crm.Organisation` |
| `crm.ChangeRequest` | `project` | `"delivery.Project"` (null=True) |
| `delivery.Project` | `organisation`, `contract` | `"crm.Organisation"`, `"crm.Contract"` (null=True) |
| `delivery.Requirement` | `project`, `opportunity` | `delivery.Project`, `"crm.Opportunity"` (null=True) |
| `delivery.SupportTicket` | `organisation`, `project` | `"crm.Organisation"`, `delivery.Project` (null=True) |
| `finance.Invoice` | `organisation`, `project`, `milestone` | `"crm.Organisation"`, `"delivery.Project"`, `"delivery.Milestone"` (null=True) |
| `finance.Expense` | `project` | `"delivery.Project"` |
| `finance.BillableItem` | `milestone` | `"delivery.Milestone"` |
| `knowledge.*`, `secretariat.*`, `documents.*` | `organisation`, `project` | optional string FKs, `null=True` |

`documents.Document.attached_ref` is a plain CharField holding a record code ("CTR-041"), not an FK.

Every model that owns a user reference points at `settings.AUTH_USER_MODEL`.

Seed order (enforced by `apps/core/management/commands/seed.py`):
`accounts → crm → delivery → finance → knowledge → secretariat → documents → core`.
Each app exposes `apps/<app>/seed.py` with `def run():` that is **idempotent**
(use `update_or_create` keyed on `ref`/slug).

Migrations: agents must NOT run `makemigrations`, `migrate` or `seed` — the integrator does that
once all apps land. Verify your work with `../backend_venv/bin/python manage.py check`.

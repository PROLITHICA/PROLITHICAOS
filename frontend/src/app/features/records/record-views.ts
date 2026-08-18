/**
 * The register-screen catalogue: every `:view` the generic record list serves,
 * mapped to its API endpoint, its detail route, the design's `listCreate`
 * button label, its create form and the permission a write needs.
 *
 * Mirrors LISTS(), FORMS and the `listCreate` map in
 * `_design/Prolithica OS v2.dc.html`.
 */
import { FieldSpec } from '../../shared/ui/field/field.component';
import { RecordCell, TagClass } from '../../core/models';

/** A raw record as the API serialises it. Cells arrive pre-rendered where the
 *  serializer builds them; the shapes differ per app, so they are normalised. */
export type ApiRecord = Record<string, unknown>;

export interface RecordSort {
  label: string;
  /** the DRF `?ordering=` value */
  param: string;
}

/** The design's FORMS entry, as served by `/api/forms/<key>/`. */
export interface FormConfig {
  title: string;
  subtitle: string;
  submit: string;
  inherit: string[];
  fields: FieldSpec[];
}

export interface RecordViewDef {
  /** canonical key (the `:view` route param) */
  key: string;
  /** API list path, relative to /api */
  endpoint: string;
  /** design copy for the primary button */
  createLabel: string;
  /** key into FORMS (server first, then the bundled design fallback) */
  formKey: string;
  /**
   * `create` POSTs the form to the list endpoint; `action` POSTs it to
   * `actionPath` (audit export, profitability rebuild).
   */
  createMode: 'create' | 'action';
  actionPath?: string;
  /** any of these `area:level` grants allows the write */
  write: string[];
  /** builds the detail route for a row, when a detail screen exists */
  detail?: (row: ApiRecord) => unknown[] | null;
  sorts?: RecordSort[];
  /** builds cells when the endpoint does not serialise them itself */
  fallbackCells?: (row: ApiRecord) => RecordCell[];
  /** design copy for the empty table */
  emptyText?: string;
}

const text = (row: ApiRecord, key: string): string => {
  const value = row[key];
  if (value === null || value === undefined || value === '') return '—';
  return String(value);
};

const cell = (t: string, options: Partial<RecordCell> = {}): RecordCell => ({
  t,
  align: options.align ?? 'left',
  bold: options.bold ?? false,
  muted: options.muted ?? false,
  tag: options.tag ?? '',
});

const ref = (row: ApiRecord): string | null => {
  const value = row['ref'] ?? row['id'];
  return value ? String(value) : null;
};

const detailFor = (segment: string) => (row: ApiRecord): unknown[] | null => {
  const key = ref(row);
  return key ? ['/', segment, key] : null;
};

const titleCase = (value: string): string =>
  value ? value.charAt(0).toUpperCase() + value.slice(1) : '';

/** Views the design routes to a detail screen the router already declares. */
export const RECORD_VIEWS: Record<string, RecordViewDef> = {
  orgs: {
    key: 'orgs',
    endpoint: '/organisations/',
    createLabel: '+ New organisation',
    formKey: 'orgs',
    createMode: 'create',
    write: ['org_contracts:full', 'contracts:full'],
    detail: detailFor('organisations'),
    sorts: [
      { label: 'Organisation', param: 'list_name' },
      { label: 'Type', param: 'type_label' },
      { label: 'Lifetime value', param: '-lifetime_value' },
      { label: 'Default', param: 'order' },
    ],
  },
  opportunities: {
    key: 'opportunities',
    endpoint: '/opportunities/',
    createLabel: '+ New opportunity',
    formKey: 'opportunities',
    createMode: 'create',
    write: ['contracts:full'],
    detail: detailFor('opportunities'),
    sorts: [
      { label: 'Opportunity', param: 'name' },
      { label: 'Stage', param: 'stage' },
      { label: 'Value', param: '-value' },
      { label: 'Probability', param: '-probability' },
      { label: 'Default', param: 'order' },
    ],
  },
  proposals: {
    key: 'proposals',
    endpoint: '/proposals/',
    createLabel: '+ New proposal',
    formKey: 'proposals',
    createMode: 'create',
    write: ['contracts:full'],
    sorts: [
      { label: 'Proposal', param: 'ref' },
      { label: 'Price', param: '-price' },
      { label: 'Issued', param: '-issued_date' },
      { label: 'Default', param: 'order' },
    ],
  },
  contracts: {
    key: 'contracts',
    endpoint: '/contracts/',
    createLabel: '+ New contract',
    formKey: 'contracts',
    createMode: 'create',
    write: ['contracts:full'],
    detail: detailFor('contracts'),
    sorts: [
      { label: 'Contract', param: 'ref' },
      { label: 'Value', param: '-value' },
      { label: 'Renewal', param: 'renewal_date' },
      { label: 'Default', param: 'order' },
    ],
  },
  projects: {
    key: 'projects',
    endpoint: '/projects/',
    createLabel: '+ Initiate project',
    formKey: 'projects',
    createMode: 'create',
    write: ['assigned_projects:full', 'delivery:full'],
    detail: detailFor('projects'),
    sorts: [
      { label: 'Project', param: 'name' },
      { label: 'Complete', param: '-completion' },
      { label: 'Margin', param: 'margin_actual' },
      { label: 'Default', param: 'order' },
    ],
  },
  requirements: {
    key: 'requirements',
    endpoint: '/requirements/',
    createLabel: '+ New requirement',
    formKey: 'requirements',
    createMode: 'create',
    write: ['requirements:contribute', 'assigned_projects:contribute', 'delivery:contribute'],
    sorts: [
      { label: 'ID', param: 'ref' },
      { label: 'Priority', param: 'priority' },
      { label: 'Status', param: 'status' },
      { label: 'Default', param: 'register_order' },
    ],
  },
  changes: {
    key: 'changes',
    endpoint: '/change-requests/',
    createLabel: '+ New change request',
    formKey: 'changes',
    createMode: 'create',
    write: ['delivery:contribute'],
    detail: detailFor('changes'),
    sorts: [
      { label: 'Request', param: 'ref' },
      { label: 'Price', param: '-price' },
      { label: 'Requested', param: '-requested_date' },
      { label: 'Default', param: 'order' },
    ],
  },
  support: {
    key: 'support',
    endpoint: '/support-tickets/',
    createLabel: '+ New ticket',
    formKey: 'support',
    createMode: 'create',
    write: ['support:contribute', 'delivery:contribute'],
  },
  milestones: {
    key: 'milestones',
    endpoint: '/milestones/',
    createLabel: '+ New milestone',
    formKey: 'milestonesAll',
    createMode: 'create',
    write: ['assigned_projects:contribute', 'delivery:contribute'],
    sorts: [
      { label: 'Planned', param: 'planned_date' },
      { label: 'Value', param: '-value' },
      { label: 'Default', param: 'register_order' },
    ],
  },
  people: {
    key: 'people',
    endpoint: '/people/',
    createLabel: '+ Invite person',
    formKey: 'people',
    createMode: 'create',
    write: ['user_admin:administer'],
    fallbackCells: (row) => [
      cell(text(row, 'name'), { bold: true }),
      cell(text(row, 'role_label'), { muted: true }),
      cell(text(row, 'department_label'), { muted: true }),
      cell(text(row, 'projects_label'), { muted: true }),
      cell(text(row, 'utilisation_label'), { align: 'right' }),
      cell(text(row, 'permissions_label'), { muted: true }),
      cell(text(row, 'state'), { tag: (row['tag_class'] as TagClass) || 'tag-neutral' }),
    ],
  },
  users: {
    key: 'users',
    endpoint: '/users/',
    createLabel: '+ New account',
    formKey: 'users',
    createMode: 'create',
    write: ['user_admin:administer'],
    fallbackCells: (row) => [
      cell(text(row, 'email'), { bold: true }),
      cell(text(row, 'role_label'), { muted: true }),
      cell(text(row, 'scope_label'), { muted: true }),
      cell(text(row, 'financial_data'), { muted: true }),
      cell(text(row, 'last_sign_in_label'), { muted: true }),
      cell(text(row, 'mfa_label'), { tag: row['mfa_enabled'] ? 'tag-accent' : 'tag-outline' }),
      cell(text(row, 'state_label'), {
        tag: String(row['state'] ?? '') === 'active' ? 'tag-accent' : 'tag-outline',
      }),
    ],
  },
  audit: {
    key: 'audit',
    endpoint: '/audit/',
    createLabel: 'Export log',
    formKey: 'audit',
    createMode: 'action',
    actionPath: '/audit/export/',
    write: ['audit:read'],
    emptyText: 'No audit events match this view.',
    fallbackCells: (row) => [
      cell(text(row, 'when_label'), { muted: true }),
      cell(text(row, 'actor_name'), { bold: true }),
      cell(text(row, 'action'), { muted: true }),
      cell(text(row, 'record_ref'), { muted: true }),
      cell(text(row, 'detail'), { muted: true }),
      cell(titleCase(text(row, 'event_class')), {
        tag: (row['tag_class'] as TagClass) || 'tag-neutral',
      }),
    ],
  },
  profitability: {
    key: 'profitability',
    endpoint: '/profitability/',
    createLabel: 'Rebuild forecast',
    formKey: 'profitability',
    createMode: 'action',
    actionPath: '/profitability/rebuild/',
    write: ['finance:full', 'project_financials:full'],
    detail: (row) => {
      const key = row['project_ref'] ?? row['project'];
      return key ? ['/', 'projects', String(key)] : null;
    },
    sorts: [
      { label: 'Margin now', param: 'margin_now' },
      { label: 'Contract', param: '-contract_value' },
      { label: 'Cost', param: '-cost' },
      { label: 'Default', param: 'order' },
    ],
  },
};

/** Route params the design and the router spell differently. */
const ALIASES: Record<string, string> = {
  organisations: 'orgs',
  milestonesAll: 'milestones',
  'change-requests': 'changes',
  'support-tickets': 'support',
  tickets: 'support',
};

export function resolveView(view: string): RecordViewDef | null {
  const key = ALIASES[view] ?? view;
  return RECORD_VIEWS[key] ?? null;
}

/**
 * The design's FORMS, used when the server has no form config for a key.
 * `/api/forms/<key>/` currently only serves the commercial chain.
 */
export const DESIGN_FORMS: Record<string, FormConfig> = {
  orgs: {
    title: 'New organisation',
    subtitle: 'Created once, then available everywhere in Prolithica OS.',
    submit: 'Create organisation',
    inherit: ['Nothing to inherit — this is where a relationship begins'],
    fields: [
      { k: 'name', l: 'Organisation name', p: 'e.g. Parliament of Uganda' },
      { k: 'type', l: 'Type', o: ['Government', 'Legislature', 'Multilateral', 'Private'] },
      { k: 'sector', l: 'Sector', p: 'Public finance oversight' },
      { k: 'location', l: 'Location', p: 'Kampala, Uganda' },
      { k: 'owner', l: 'Relationship owner', o: ['Newton Brian', 'Lerato Sithole', 'Milele Faith'] },
      { k: 'notes', l: 'Context', t: 'area', p: 'How the relationship started, who introduced it' },
    ],
  },
  opportunities: {
    title: 'New opportunity',
    subtitle: 'Attach it to an organisation and the client, contacts and history come with it.',
    submit: 'Create opportunity',
    inherit: ['Client, contacts and sector from the organisation', 'Prior systems and delivery history'],
    fields: [
      { k: 'org', l: 'Organisation', o: ['AN-PBO', 'Correctional Services', 'National Treasury'] },
      { k: 'name', l: 'Opportunity', p: 'What the client wants solved' },
      { k: 'value', l: 'Estimated value', p: 'R 4.6m' },
      { k: 'close', l: 'Expected close', p: '28 Sep 2026' },
      { k: 'source', l: 'Source', o: ['Existing client', 'Referral', 'Tender', 'Inbound'] },
      { k: 'owner', l: 'Owner', o: ['Newton Brian', 'Lerato Sithole', 'Milele Faith'] },
    ],
  },
  proposals: {
    title: 'New proposal',
    subtitle: 'Inherits the opportunity so nothing is typed twice.',
    submit: 'Create version 1',
    inherit: [
      'Problem statement and requirements from the opportunity',
      'Solution patterns from the knowledge base',
    ],
    fields: [
      { k: 'opp', l: 'Opportunity', o: ['Analytics module', 'Costing tool', 'LIMS rollout'] },
      { k: 'price', l: 'Price', p: 'R 4.6m' },
      { k: 'terms', l: 'Payment terms', o: ['20% then milestones', 'Milestones only', 'Monthly'] },
      { k: 'valid', l: 'Valid until', p: '30 Sep 2026' },
      { k: 'scope', l: 'Scope summary', t: 'area', p: 'Modules, deliverables, exclusions' },
    ],
  },
  contracts: {
    title: 'New contract',
    subtitle: 'Generated from an accepted proposal — commercial terms carry over.',
    submit: 'Generate contract',
    inherit: [
      'Price, scope, deliverables and payment terms from the proposal',
      'Signatories and legal entity from the organisation',
    ],
    fields: [
      { k: 'prop', l: 'From proposal', o: ['PRP-121 · Analytics', 'PRP-119 · Offender records II'] },
      { k: 'value', l: 'Value', p: 'R 4.6m' },
      { k: 'term', l: 'Term', p: '9 months from 1 Oct 2026' },
      { k: 'billing', l: 'Billing', o: ['Milestone', 'Monthly', 'On signature'] },
      { k: 'support', l: 'Support term', o: ['12 months', '24 months', 'None'] },
    ],
  },
  projects: {
    title: 'Initiate project',
    subtitle:
      'Created from a contract with value, timeline, deliverables and payment structure already in place.',
    submit: 'Initiate project',
    inherit: [
      'Value, timeline, deliverables and milestones from the contract',
      'Requirements captured during discovery',
    ],
    fields: [
      { k: 'contract', l: 'From contract', o: ['CTR-030 · Data Portal', 'CTR-038 · DCS System'] },
      { k: 'name', l: 'Project name', p: 'e.g. Data Portal phase two' },
      { k: 'pm', l: 'Project manager', o: ['Jude Ang’edu', 'Lerato Sithole', 'Milele Faith'] },
      { k: 'start', l: 'Start date', p: '1 Sep 2026' },
      { k: 'phases', l: 'Delivery stages', o: ['5 stages', '3 stages', 'Custom'] },
    ],
  },
  requirements: {
    title: 'New requirement',
    subtitle: 'A first-class record: source, owner, acceptance criteria and traceability.',
    submit: 'Add requirement',
    inherit: ['Project, client and discovery context'],
    fields: [
      { k: 'project', l: 'Project', o: ['LIMS', 'DCS System', 'Data Portal'] },
      { k: 'text', l: 'Requirement', p: 'What the system must do' },
      { k: 'priority', l: 'Priority', o: ['Must', 'Should', 'Could'] },
      { k: 'source', l: 'Source', o: ['Discovery', 'Change request', 'Support incident'] },
      { k: 'owner', l: 'Owner', o: ['Edwin Ndiritu', 'Milele Faith', 'Jude Ang’edu'] },
      { k: 'accept', l: 'Acceptance criteria', t: 'area', p: 'How the client will confirm it is done' },
    ],
  },
  changes: {
    title: 'New change request',
    subtitle: 'Scope only moves through here. Assessment and pricing are required before approval.',
    submit: 'Raise request',
    inherit: ['Project, contract and current scope baseline'],
    fields: [
      { k: 'project', l: 'Project', o: ['LIMS', 'DCS System', 'PBO System'] },
      { k: 'name', l: 'What is requested', p: 'e.g. Bilingual export' },
      { k: 'why', l: 'Why', p: 'Reason given by the client' },
      { k: 'effort', l: 'Effort estimate', p: '11 days' },
      { k: 'price', l: 'Price', p: 'R 0.18m' },
      { k: 'schedule', l: 'Schedule impact', o: ['None', '+1 week', '+2 weeks', '+1 month'] },
    ],
  },
  support: {
    title: 'New support ticket',
    subtitle: 'The ticket inherits the system, its architecture and its SLA.',
    submit: 'Log ticket',
    inherit: ['Contract SLA, system architecture and previous incidents'],
    fields: [
      { k: 'org', l: 'Organisation', o: ['AN-PBO', 'Correctional Services', 'Ukulima House'] },
      { k: 'system', l: 'System', o: ['LIMS', 'PBO System', 'DCS System'] },
      { k: 'sev', l: 'Severity', o: ['P1', 'P2', 'P3', 'P4'] },
      { k: 'summary', l: 'Summary', p: 'What the user reported' },
      { k: 'owner', l: 'Owner', o: ['Edwin Ndiritu', 'Shanelle A.', 'Grace Mwende'] },
    ],
  },
  milestonesAll: {
    title: 'New milestone',
    subtitle: 'A milestone is a delivery event and a billing event at once.',
    submit: 'Add milestone',
    inherit: ['Contract payment schedule and project timeline'],
    fields: [
      { k: 'project', l: 'Project', o: ['LIMS', 'DCS System', 'Data Portal'] },
      { k: 'name', l: 'Milestone', p: 'e.g. M5 Rollout' },
      { k: 'planned', l: 'Planned date', p: '31 Oct 2026' },
      { k: 'value', l: 'Value', p: 'R 3.12m' },
      { k: 'billable', l: 'Billable on acceptance', o: ['Yes', 'No'] },
    ],
  },
  people: {
    title: 'Invite person',
    subtitle: 'A person gets a department, a role and the permissions that follow from it.',
    submit: 'Send invitation',
    inherit: ['Department permission set and onboarding checklist'],
    fields: [
      { k: 'name', l: 'Full name', p: 'e.g. Shanelle Akong’o' },
      { k: 'role', l: 'Role', p: 'System Assistant' },
      {
        k: 'dept', l: 'Department',
        o: ['Executive', 'Finance', 'Technology', 'Research & Development', 'Office & Secretariat'],
      },
      { k: 'email', l: 'Work email', p: 'name@prolithica.com' },
      {
        k: 'perms', l: 'Permissions',
        o: ['Delivery only', 'Delivery + project financials', 'Full financial', 'Documents only'],
      },
    ],
  },
  users: {
    title: 'New account',
    subtitle: 'Least privilege by default. Every grant is recorded in the audit trail.',
    submit: 'Create account',
    inherit: ['Role permission template and MFA policy'],
    fields: [
      { k: 'email', l: 'Account email', p: 'name@prolithica.com' },
      {
        k: 'role', l: 'Role',
        o: ['Executive', 'Finance', 'Technical lead', 'Project manager', 'Client portal'],
      },
      { k: 'scope', l: 'Scope', o: ['Company', 'Assigned projects', 'Own records only'] },
      { k: 'money', l: 'Financial data', o: ['None', 'Restricted', 'Full'] },
      { k: 'mfa', l: 'MFA', o: ['Required', 'Optional'] },
    ],
  },
  audit: {
    title: 'Export audit log',
    subtitle: 'The log itself is read-only. Exports are recorded as events.',
    submit: 'Export log',
    inherit: ['Your permission scope limits what the export contains'],
    fields: [
      { k: 'range', l: 'Range', o: ['Last 30 days', 'Quarter', 'Year'] },
      { k: 'cls', l: 'Classes', o: ['All', 'Sensitive only', 'Financial only'] },
      { k: 'format', l: 'Format', o: ['CSV', 'XLSX', 'PDF'] },
    ],
  },
  profitability: {
    title: 'Rebuild forecast',
    subtitle: 'Recomputes margin forecasts from cost, timesheets and unbilled work.',
    submit: 'Rebuild now',
    inherit: ['Approved expenses, timesheets, milestone billing and change requests'],
    fields: [
      { k: 'scope', l: 'Scope', o: ['All projects', 'At-risk only', 'LIMS'] },
      { k: 'basis', l: 'Basis', o: ['Current run rate', 'Plan', 'Optimistic'] },
    ],
  },
  export: {
    title: 'Export records',
    subtitle: 'Exports land in Document storage so they stay attached to the company record.',
    submit: 'Queue export',
    inherit: ['Only records inside your permissions are included'],
    fields: [
      { k: 'records', l: 'Records', o: ['This view', 'Filtered rows only', 'Everything'] },
      { k: 'format', l: 'Format', o: ['CSV', 'XLSX', 'PDF'] },
      { k: 'dest', l: 'Destination', o: ['Document storage', 'Email to me'] },
      { k: 'note', l: 'Note', p: 'What this export is for' },
    ],
  },
};

/**
 * Design form keys → model fields, so a submitted modal reaches the serializer
 * with names it recognises. Unknown extras are ignored by DRF, so the raw
 * values are sent alongside.
 */
export const FIELD_MAP: Record<string, Record<string, string>> = {
  orgs: { type: 'type_label', owner: 'owner_name', name: 'name' },
  opportunities: { org: 'organisation_name', owner: 'owner_name', value: 'value', close: 'close_date' },
  proposals: { opp: 'name', price: 'price', terms: 'payment_terms' },
  contracts: { prop: 'name', value: 'value', term: 'term_label', billing: 'billing_label', support: 'support_terms' },
  projects: { name: 'name', pm: 'manager_name', contract: 'contract_ref' },
  requirements: { text: 'text', owner: 'owner_name', project: 'project_label', source: 'source' },
  changes: { name: 'name', project: 'project_label', price: 'price', effort: 'effort_label', schedule: 'schedule_field' },
  support: { summary: 'title', org: 'organisation_label', system: 'system_label', sev: 'severity', owner: 'owner_name' },
  milestonesAll: { name: 'name', planned: 'planned_date', value: 'value', project: 'project_label' },
  people: { name: 'name', role: 'role_label', dept: 'department_label', perms: 'permissions_label' },
  users: { email: 'email', role: 'role', scope: 'scope' },
};

/** Keys whose value the design writes as money ("R 4.6m", "R 128 400"). */
export const MONEY_KEYS = new Set(['value', 'price']);

/** "R 4.6m" → 4600000, "R 128 400" → 128400. Left alone if it is not money. */
export function parseMoney(input: string): number | null {
  const raw = String(input ?? '').trim();
  if (!raw) return null;
  const match = /^R?\s*([\d\s.,]+)\s*(m|k)?$/i.exec(raw);
  if (!match) return null;
  const digits = match[1].replace(/[\s,]/g, '');
  const amount = Number(digits);
  if (Number.isNaN(amount)) return null;
  const suffix = (match[2] ?? '').toLowerCase();
  if (suffix === 'm') return amount * 1_000_000;
  if (suffix === 'k') return amount * 1_000;
  return amount;
}

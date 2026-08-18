import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../core/api.service';
import { ToastService } from '../../core/toast.service';
import { PermissionService } from '../../core/permission.service';
import { ViewConfig } from '../../core/models';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { ModalComponent } from '../../shared/ui/modal/modal.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';
import { StatTileComponent } from '../../shared/ui/stat-tile/stat-tile.component';
import { FieldSpec } from '../../shared/ui/field/field.component';

interface AccountRow {
  id: string;
  email: string;
  display_name: string;
  role: string | null;
  role_label: string;
  scope_label: string;
  financial_data: string;
  last_sign_in_label: string;
  mfa_label: string;
  mfa_enabled: boolean;
  state: string;
  state_label: string;
}

interface RoleRow { id: string; slug: string; label: string; }

/** The design's FORMS.users entry (line 1904). */
const NEW_ACCOUNT_FIELDS: FieldSpec[] = [
  { k: 'email', l: 'Account email', p: 'name@prolithica.com' },
  { k: 'role', l: 'Role', o: ['Executive', 'Finance', 'Technical lead', 'Project manager', 'Client portal'] },
  { k: 'scope', l: 'Scope', o: ['Company', 'Assigned projects', 'Own records only'] },
  { k: 'money', l: 'Financial data', o: ['None', 'Restricted', 'Full'] },
  { k: 'mfa', l: 'MFA', o: ['Required', 'Optional'] },
];

const GRANT_FIELDS: FieldSpec[] = [
  { k: 'detail', l: 'Why, and for how long', p: 'e.g. Financials, 24 hours' },
];

/**
 * Users, roles and permissions — administration only (design list `users`,
 * line 2093). The generic record list already renders this table from the
 * server's `view` block; this screen adds the two administration-only extras:
 * the "+ New account" modal and the time-boxed temporary grant.
 */
@Component({
  selector: 'app-users-admin',
  standalone: true,
  imports: [FormsModule, ModalComponent, SkeletonComponent, EmptyStateComponent, StatTileComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="head">
      <div>
        <h1 class="title">{{ view()?.title || 'Users, roles and permissions' }}</h1>
        <div class="sub">{{ view()?.subtitle || defaultSubtitle }}</div>
      </div>
      @if (canAdminister()) {
        <button type="button" class="btn btn-primary nowrap" (click)="openCreate()">+ New account</button>
      }
    </div>

    @if (view()?.stats?.length) {
      <div class="stats">
        @for (s of view()!.stats; track s.label) {
          <app-stat-tile [label]="s.label" [value]="s.value" [note]="s.note || ''" />
        }
      </div>
    }

    <div class="search">
      <input class="input" placeholder="Search accounts by email or name"
             [ngModel]="query()" (ngModelChange)="onQuery($event)"
             style="background:#fafafa;border-color:#b5b5b5">
    </div>

    @if (loading()) {
      <div class="skel-stack">
        <app-skeleton width="100%" height="38px" />
        <app-skeleton width="100%" height="38px" />
        <app-skeleton width="100%" height="38px" />
        <app-skeleton width="100%" height="38px" />
      </div>
    } @else if (error()) {
      <app-empty-state heading="Accounts could not be loaded"
                       note="The administration service did not answer. Nothing was changed."
                       actionLabel="Try again" (action)="load()" />
    } @else if (!rows().length) {
      <app-empty-state
        [heading]="query() ? 'No account matches that search' : 'No accounts yet'"
        note="Accounts appear here as administration creates them. Every grant is recorded."
        [actionLabel]="query() ? 'Clear the search' : ''"
        (action)="onQuery('')" />
    } @else {
      <div class="scroll-x fade">
        <table class="table" style="min-width:860px">
          <thead>
            <tr>
              @for (c of columns(); track $index) { <th>{{ c }}</th> }
              @if (canAdminister()) { <th>Grant</th> }
            </tr>
          </thead>
          <tbody>
            @for (row of rows(); track row.id) {
              <tr>
                <td style="font-weight:600">{{ row.email }}</td>
                <td class="muted">{{ row.role_label || '—' }}</td>
                <td class="muted">{{ row.scope_label || '—' }}</td>
                <td class="muted">{{ row.financial_data }}</td>
                <td class="muted">{{ row.last_sign_in_label }}</td>
                <td><span class="tag" [class]="'tag ' + (row.mfa_enabled ? 'tag-accent' : 'tag-outline')">{{ row.mfa_label }}</span></td>
                <td><span class="tag" [class]="'tag ' + (row.state === 'active' ? 'tag-accent' : 'tag-outline')">{{ row.state_label }}</span></td>
                @if (canAdminister()) {
                  <td>
                    <button type="button" class="btn btn-secondary grant-cta"
                            (click)="openGrant(row)">Temporary grant</button>
                  </td>
                }
              </tr>
            }
          </tbody>
        </table>
      </div>
      <div class="foot">{{ total() }} accounts · least privilege by default · every sensitive action is auditable.</div>
    }

    <app-modal [open]="createOpen()" title="New account"
               subtitle="Least privilege by default. Every grant is recorded in the audit trail."
               [inherit]="['Role permission template and MFA policy']"
               [fields]="createFields" submitLabel="Create account" [busy]="createBusy()"
               (close)="createOpen.set(false)" (submit)="createAccount($event)" />

    <app-modal [open]="grantOpen()" title="Temporary grant"
               [subtitle]="grantSubtitle()"
               [inherit]="['The grant is time-boxed and written to the audit trail']"
               [fields]="grantFields" submitLabel="Grant access" [busy]="grantBusy()"
               (close)="grantOpen.set(false)" (submit)="grantRole($event)">
      <div class="field">
        <label>Role to grant</label>
        <div class="pills">
          @for (r of roles(); track r.id) {
            <button type="button" class="pill"
                    [style.background]="grantRoleSlug() === r.slug ? '#111' : '#fff'"
                    [style.color]="grantRoleSlug() === r.slug ? '#fff' : '#333'"
                    [style.border-color]="grantRoleSlug() === r.slug ? '#111' : '#b5b5b5'"
                    (click)="grantRoleSlug.set(r.slug)">{{ r.label }}</button>
          } @empty {
            <div class="foot" style="margin:0">No roles are available to grant.</div>
          }
        </div>
      </div>
    </app-modal>
  `,
  styles: [`
    .head { display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; }
    .title { font-size: 28px; margin: 0 0 4px; }
    .sub { font-size: 12.5px; color: #8a8a8a; max-width: 74ch; }
    .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin-top: 18px; }
    .search { margin-top: 16px; max-width: 420px; margin-bottom: 16px; }
    .grant-cta { border-color: #b5b5b5; font-size: 12px; padding: 5px 13px; white-space: nowrap; }
    .foot { font-size: 11.5px; color: #8a8a8a; margin-top: 12px; }
    .skel-stack { display: flex; flex-direction: column; gap: 10px; }
    .pills { display: flex; flex-wrap: wrap; gap: 7px; }
    .pill { border: 1px dotted #b5b5b5; border-radius: 999px; padding: 6px 13px; font: inherit; font-size: 11.5px; cursor: pointer; }
    .pill:hover { border-color: #111; }
  `],
})
export class UsersAdminComponent {
  private readonly api = inject(ApiService);
  private readonly toast = inject(ToastService);
  private readonly perms = inject(PermissionService);

  readonly defaultSubtitle =
    'Administration. Every grant is recorded and every sensitive action is auditable.';
  readonly createFields = NEW_ACCOUNT_FIELDS;
  readonly grantFields = GRANT_FIELDS;

  readonly loading = signal(true);
  readonly error = signal(false);
  readonly rows = signal<AccountRow[]>([]);
  readonly view = signal<ViewConfig | null>(null);
  readonly total = signal(0);
  readonly query = signal('');
  readonly roles = signal<RoleRow[]>([]);

  readonly createOpen = signal(false);
  readonly createBusy = signal(false);
  readonly grantOpen = signal(false);
  readonly grantBusy = signal(false);
  readonly grantTarget = signal<AccountRow | null>(null);
  readonly grantRoleSlug = signal('');

  private timer: ReturnType<typeof setTimeout> | null = null;

  readonly canAdminister = computed(() => this.perms.can('user_admin', 'administer'));
  readonly columns = computed<string[]>(() => {
    const cols = this.view()?.cols ?? [];
    if (cols.length) return cols.map((c) => (typeof c === 'string' ? c : c.l));
    return ['Account', 'Role', 'Scope', 'Financial data', 'Last sign-in', 'MFA', 'State'];
  });
  readonly grantSubtitle = computed(
    () => `${this.grantTarget()?.display_name || this.grantTarget()?.email || 'This account'} `
      + 'keeps the grant only as long as it is needed.',
  );

  constructor() {
    this.load();
    this.api.list<RoleRow>('/roles/').subscribe({
      next: (page) => this.roles.set(page.results ?? []),
      error: () => this.roles.set([]),
    });
  }

  load(): void {
    this.loading.set(true);
    this.error.set(false);
    this.api.list<AccountRow>('/users/', { search: this.query(), page_size: 100 }).subscribe({
      next: (page) => {
        this.rows.set(page.results ?? []);
        this.view.set(page.view ?? null);
        this.total.set(page.count ?? (page.results ?? []).length);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.error.set(true);
      },
    });
  }

  onQuery(value: string): void {
    this.query.set(value);
    if (this.timer) clearTimeout(this.timer);
    this.timer = setTimeout(() => this.load(), 220);
  }

  openCreate(): void {
    this.createOpen.set(true);
  }

  createAccount(values: Record<string, string>): void {
    if (this.createBusy()) return;
    const role = this.roles().find(
      (r) => r.label.toLowerCase() === (values['role'] ?? '').toLowerCase(),
    );
    this.createBusy.set(true);
    this.api.post<AccountRow & { toast?: string }>('/users/', {
      email: values['email'] ?? '',
      display_name: (values['email'] ?? '').split('@')[0].replace(/[._]+/g, ' ').trim(),
      role: role?.id ?? null,
      mfa_enabled: (values['mfa'] ?? 'Required') === 'Required',
    }).subscribe({
      next: () => {
        this.createBusy.set(false);
        this.createOpen.set(false);
        this.load();
        this.toast.show(
          `Account ${values['email'] || 'created'} invited. Least privilege applied and the `
          + 'grant is in the audit trail.',
        );
      },
      error: () => {
        this.createBusy.set(false);
        this.toast.show('That account could not be created. Nothing was changed.');
      },
    });
  }

  openGrant(row: AccountRow): void {
    this.grantTarget.set(row);
    this.grantRoleSlug.set('');
    this.grantOpen.set(true);
  }

  grantRole(values: Record<string, string>): void {
    const target = this.grantTarget();
    if (!target || this.grantBusy()) return;
    if (!this.grantRoleSlug()) {
      this.toast.show('Pick the role to grant first.');
      return;
    }
    this.grantBusy.set(true);
    this.api.post<{ toast?: string }>(`/users/${target.id}/grant/`, {
      role: this.grantRoleSlug(),
      detail: values['detail'] || 'Temporary grant',
    }).subscribe({
      next: (response) => {
        this.grantBusy.set(false);
        this.grantOpen.set(false);
        this.load();
        this.toast.show(response.toast ?? 'Temporary access granted and recorded.');
      },
      error: () => {
        this.grantBusy.set(false);
        this.toast.show('That grant could not be recorded. Nothing was changed.');
      },
    });
  }
}

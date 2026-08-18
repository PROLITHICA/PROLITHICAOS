import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { forkJoin } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { ToastService } from '../../core/toast.service';
import { PermissionRow, User } from '../../core/models';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { FieldComponent } from '../../shared/ui/field/field.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';

export type ProfileTabKey =
  | 'account' | 'password' | 'security' | 'notifications' | 'permissions' | 'delegation';

interface ProfileTab { k: ProfileTabKey; label: string; note: string; }

/** PROFILE_TABS, design line 1922. */
const PROFILE_TABS: ProfileTab[] = [
  { k: 'account', label: 'Account', note: 'Name, title and how you appear to colleagues' },
  { k: 'password', label: 'Password', note: 'Set a new password or send yourself a reset link' },
  { k: 'security', label: 'Security & sessions', note: 'Multi-factor authentication and signed-in devices' },
  { k: 'notifications', label: 'Notifications', note: 'What reaches you, and how' },
  { k: 'permissions', label: 'My permissions', note: 'What your department can see and do' },
  { k: 'delegation', label: 'Delegation', note: 'Hand over approvals while you are away' },
];

interface SessionRow {
  id: string;
  device: string;
  location?: string;
  last_active?: string;
  current?: boolean;
}

interface Preferences { email: boolean; digest: boolean; mobile: boolean; mentions: boolean; }
type PrefKey = keyof Preferences;

interface PrefRow {
  k: PrefKey | 'critical';
  label: string;
  note: string;
  on: boolean;
  locked: boolean;
}

interface Delegation {
  id?: string;
  delegate_to: string | null;
  delegate_to_name?: string;
  starts_on: string | null;
  ends_on: string | null;
  note?: string;
  active?: boolean;
}

interface DirectoryPerson { id: string; display_name: string; job_title?: string; email: string; }

/** `/api/profile/` returns the MeSerializer payload; the timestamp is optional. */
interface ProfileUser extends User { password_changed_at?: string | null; }

/**
 * My profile — design lines 1530-1649. Six tabs behind one page: account,
 * password, security & sessions, notifications, permissions, delegation.
 * Each tab loads its own data once, the first time it is opened.
 */
@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [FieldComponent, SkeletonComponent, EmptyStateComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './profile.component.html',
  styles: [`
    .panel { border: 1px dotted #c4c4c4; border-radius: 16px; padding: 22px; margin-top: 14px; max-width: 760px; }
    .tab-rail { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 20px; }
    .tab { border: 1px dotted #b5b5b5; background: #fff; color: #333; border-radius: 999px; padding: 7px 15px; font: inherit; font-size: 12px; cursor: pointer; }
    .tab:hover { border-color: #111; }
    .tab-note { font-size: 11.5px; color: #8a8a8a; margin-top: 10px; }
    .panel h4 { margin: 0 0 12px; font-size: 16px; }
    .grid-240 { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; }
    .grid-220 { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }
    .note { font-size: 11.5px; color: #8a8a8a; }
    .row-actions { display: flex; flex-wrap: wrap; gap: 9px; margin-top: 16px; }
    .toggle-row { display: grid; grid-template-columns: 22px minmax(0,1fr) auto; gap: 12px; align-items: center; padding: 12px 0; border-bottom: 1px dotted #dcdcdc; }
    .box { width: 15px; height: 15px; padding: 0; border: 1.5px dotted #111; border-radius: 5px; cursor: pointer; }
    .row-title { font-size: 13px; }
    .row-meta { font-size: 11px; color: #9a9a9a; }
    .session-row { display: grid; grid-template-columns: minmax(0,1fr) auto; gap: 14px; align-items: center; padding: 12px 0; border-bottom: 1px dotted #dcdcdc; }
    .session-cta { border-color: #b5b5b5; font-size: 12px; padding: 5px 13px; white-space: nowrap; }
    .perm-row { display: grid; grid-template-columns: minmax(0,1fr) auto; gap: 14px; align-items: center; padding: 11px 0; border-bottom: 1px dotted #dcdcdc; }
    .pills { display: flex; flex-wrap: wrap; gap: 7px; }
    .pill { border: 1px dotted #b5b5b5; background: #fff; color: #333; border-radius: 999px; padding: 6px 13px; font: inherit; font-size: 11.5px; cursor: pointer; }
    .pill:hover { border-color: #111; }
    .strength { margin-top: 12px; max-width: 300px; }
    .strength-head { display: flex; justify-content: space-between; font-size: 11px; color: #6b6b6b; }
    .strength-track { display: block; height: 5px; background: #f0f0f0; border-radius: 3px; margin-top: 5px; overflow: hidden; }
    .strength-fill { display: block; height: 5px; background: #111; }
    .avatar { width: 54px; height: 54px; border-radius: 999px; background: #111; color: #fff; font-size: 17px; font-weight: 600; display: flex; align-items: center; justify-content: center; flex: none; }
    .ident { display: flex; align-items: center; gap: 16px; }
    .ident h1 { font-size: 26px; margin: 0 0 3px; }
    .ident-meta { font-size: 12.5px; color: #8a8a8a; }
    .preview { border: 1px dotted #dcdcdc; border-radius: 14px; background: #fafafa; padding: 12px 14px; margin-top: 16px; }
    .preview-kicker { font-size: 10px; letter-spacing: 0.12em; text-transform: uppercase; color: #9a9a9a; }
    .preview-body { display: flex; align-items: center; gap: 11px; margin-top: 8px; }
    .preview-avatar { width: 32px; height: 32px; border-radius: 999px; background: #111; color: #fff; font-size: 12px; font-weight: 600; display: flex; align-items: center; justify-content: center; flex: none; }
    .preview-name { font-size: 13px; font-weight: 500; }
    .preview-title { font-size: 11px; color: #9a9a9a; }
    .skel-stack { display: flex; flex-direction: column; gap: 12px; }
  `],
})
export class ProfileComponent {
  private readonly api = inject(ApiService);
  private readonly auth = inject(AuthService);
  private readonly toast = inject(ToastService);

  readonly tabs = PROFILE_TABS;
  readonly tab = signal<ProfileTabKey>('account');

  readonly loading = signal(true);
  readonly loadError = signal(false);
  readonly profile = signal<ProfileUser | null>(null);

  // ── account ────────────────────────────────────────────────────────
  readonly displayName = signal('');
  readonly jobTitle = signal('');
  readonly acctBusy = signal(false);

  // ── password ───────────────────────────────────────────────────────
  readonly pwCurrent = signal('');
  readonly pwNext = signal('');
  readonly pwConfirm = signal('');
  readonly pwBusy = signal(false);
  readonly resetBusy = signal(false);
  readonly pwError = signal('');

  // ── security ───────────────────────────────────────────────────────
  readonly mfaOn = signal(false);
  readonly sessions = signal<SessionRow[]>([]);
  readonly sessionsLoading = signal(false);
  readonly sessionsError = signal(false);
  private sessionsLoaded = false;

  // ── notifications ──────────────────────────────────────────────────
  readonly prefs = signal<Preferences | null>(null);
  readonly prefsLoading = signal(false);
  readonly prefsError = signal(false);
  private prefsLoaded = false;

  // ── permissions ────────────────────────────────────────────────────
  readonly directorName = signal('');

  // ── delegation ─────────────────────────────────────────────────────
  readonly directory = signal<DirectoryPerson[]>([]);
  readonly delegateId = signal<string | null>(null);
  readonly delegFrom = signal('');
  readonly delegUntil = signal('');
  readonly delegBusy = signal(false);
  readonly delegLoading = signal(false);
  readonly delegError = signal(false);
  private delegLoaded = false;

  readonly initials = computed(() => this.profile()?.initials ?? '');
  readonly email = computed(() => this.profile()?.email ?? '');
  readonly roleLabel = computed(() => this.profile()?.department?.label ?? this.profile()?.role?.label ?? '');
  readonly permissionRows = computed<PermissionRow[]>(() => this.profile()?.permission_rows ?? []);

  readonly activeNote = computed(
    () => PROFILE_TABS.find((t) => t.k === this.tab())?.note ?? '',
  );

  readonly previewInitials = computed(() => {
    const parts = this.displayName().trim().split(/\s+/).filter(Boolean);
    if (!parts.length) return this.initials();
    return (parts[0][0] + (parts.length > 1 ? parts[parts.length - 1][0] : '')).toUpperCase();
  });

  readonly pwStrength = computed(() => {
    const length = this.pwNext().length;
    return length >= 16 ? 'Strong' : length >= 12 ? 'Acceptable' : 'Too short';
  });

  readonly pwStrengthWidth = computed(
    () => `${Math.min(100, (this.pwNext().length / 16) * 100)}%`,
  );

  readonly pwChanged = computed(() => {
    const stamp = this.profile()?.password_changed_at;
    if (!stamp) return 'never recorded';
    const when = new Date(stamp);
    return Number.isNaN(when.getTime())
      ? String(stamp)
      : when.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  });

  readonly mfaLabel = computed(() => (this.mfaOn() ? 'Enabled · authenticator app' : 'Disabled'));

  readonly permNote = computed(
    () => `Permissions follow your department. Ask ${this.directorName() || 'the director'} `
      + 'for a temporary grant; every grant is time-boxed and audited.',
  );

  readonly prefRows = computed<PrefRow[]>(() => {
    const values = this.prefs();
    return [
      { k: 'critical', label: 'Critical events', note: 'Overdue money, breached SLAs, budget breaches', on: true, locked: true },
      { k: 'email', label: 'Email digest of actionable items', note: 'Approvals and decisions waiting on you', on: !!values?.email, locked: false },
      { k: 'digest', label: 'Morning company summary', note: 'Command Centre state at 07:00', on: !!values?.digest, locked: false },
      { k: 'mobile', label: 'Mobile push', note: 'Tasks, approvals and expenses only', on: !!values?.mobile, locked: false },
      { k: 'mentions', label: 'Mentions in progress updates', note: 'When someone names you on a project', on: !!values?.mentions, locked: false },
    ];
  });

  readonly colleagues = computed(
    () => this.directory().filter((person) => person.id !== this.profile()?.id),
  );

  constructor() {
    this.load();
  }

  // ── loading ────────────────────────────────────────────────────────

  load(): void {
    this.loading.set(true);
    this.loadError.set(false);
    this.api.get<ProfileUser>('/profile/').subscribe({
      next: (user) => {
        this.applyProfile(user);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.loadError.set(true);
      },
    });
  }

  private applyProfile(user: ProfileUser): void {
    this.profile.set(user);
    this.displayName.set(user.display_name ?? '');
    this.jobTitle.set(user.job_title ?? '');
    this.mfaOn.set(!!user.mfa_enabled);
  }

  selectTab(key: ProfileTabKey): void {
    if (this.tab() === key) return;
    this.tab.set(key);
    if (key === 'security') this.loadSessions();
    if (key === 'notifications') this.loadPreferences();
    if (key === 'permissions') this.loadDirector();
    if (key === 'delegation') this.loadDelegation();
  }

  private loadSessions(force = false): void {
    if (this.sessionsLoaded && !force) return;
    this.sessionsLoaded = true;
    this.sessionsLoading.set(true);
    this.sessionsError.set(false);
    this.api.list<SessionRow>('/auth/sessions/').subscribe({
      next: (page) => {
        this.sessions.set(page.results ?? []);
        this.sessionsLoading.set(false);
      },
      error: () => {
        this.sessionsLoading.set(false);
        this.sessionsError.set(true);
      },
    });
  }

  private loadPreferences(): void {
    if (this.prefsLoaded) return;
    this.prefsLoaded = true;
    this.prefsLoading.set(true);
    this.prefsError.set(false);
    this.api.get<Preferences>('/auth/preferences/').subscribe({
      next: (values) => {
        this.prefs.set(values);
        this.prefsLoading.set(false);
      },
      error: () => {
        this.prefsLoading.set(false);
        this.prefsError.set(true);
      },
    });
  }

  private loadDirector(): void {
    if (this.directorName()) return;
    this.api.list<{ slug: string; head?: { name: string } | null }>('/departments/').subscribe({
      next: (page) => {
        const executive = (page.results ?? []).find((dept) => dept.slug === 'ceo');
        this.directorName.set(executive?.head?.name ?? '');
      },
      error: () => this.directorName.set(''),
    });
  }

  private loadDelegation(): void {
    if (this.delegLoaded) return;
    this.delegLoaded = true;
    this.delegLoading.set(true);
    this.delegError.set(false);
    forkJoin({
      delegation: this.api.get<Delegation>('/auth/delegation/'),
      directory: this.api.get<DirectoryPerson[]>('/directory/'),
    }).subscribe({
      next: ({ delegation, directory }) => {
        this.delegateId.set(delegation?.delegate_to ?? null);
        this.delegFrom.set(delegation?.starts_on ?? '');
        this.delegUntil.set(delegation?.ends_on ?? '');
        this.directory.set(Array.isArray(directory) ? directory : []);
        this.delegLoading.set(false);
      },
      error: () => {
        this.delegLoading.set(false);
        this.delegError.set(true);
      },
    });
  }

  retryTab(): void {
    switch (this.tab()) {
      case 'security': this.sessionsLoaded = false; this.loadSessions(); break;
      case 'notifications': this.prefsLoaded = false; this.loadPreferences(); break;
      case 'delegation': this.delegLoaded = false; this.loadDelegation(); break;
      default: this.load();
    }
  }

  // ── account tab ────────────────────────────────────────────────────

  saveAccount(): void {
    if (this.acctBusy()) return;
    this.acctBusy.set(true);
    this.api
      .patch<{ user: ProfileUser; toast?: string }>('/profile/', {
        display_name: this.displayName(),
        job_title: this.jobTitle(),
      })
      .subscribe({
        next: (response) => {
          this.acctBusy.set(false);
          if (response.user) {
            this.applyProfile(response.user);
            this.auth.currentUser.set(response.user);
          } else {
            this.auth.me().subscribe({ next: () => {}, error: () => {} });
          }
          this.toast.show(
            response.toast
              ?? 'Profile saved. Your name and title now show everywhere you appear.',
          );
        },
        error: () => {
          this.acctBusy.set(false);
          this.toast.show('That could not be saved. Nothing was changed.');
        },
      });
  }

  revertAccount(): void {
    const user = this.profile();
    this.displayName.set(user?.display_name ?? '');
    this.jobTitle.set(user?.job_title ?? '');
    this.toast.show('Reverted to your directory name and title.');
  }

  // ── password tab ───────────────────────────────────────────────────

  savePassword(): void {
    if (this.pwBusy()) return;
    if (this.pwNext().length < 12) {
      this.pwError.set('Password must be at least 12 characters. Nothing was changed.');
      this.toast.show('Password must be at least 12 characters. Nothing was changed.');
      return;
    }
    if (this.pwNext() !== this.pwConfirm()) {
      this.pwError.set('The two new passwords do not match. Nothing was changed.');
      this.toast.show('The two new passwords do not match. Nothing was changed.');
      return;
    }
    this.pwError.set('');
    this.pwBusy.set(true);
    this.api
      .post<{ toast?: string; tokens?: { access: string; refresh: string } }>(
        '/auth/password/change/',
        { current: this.pwCurrent(), next: this.pwNext(), confirm: this.pwConfirm() },
      )
      .subscribe({
        next: (response) => {
          this.pwBusy.set(false);
          if (response.tokens?.access) {
            this.auth.storeTokens(response.tokens.access, response.tokens.refresh);
          }
          this.pwCurrent.set('');
          this.pwNext.set('');
          this.pwConfirm.set('');
          this.sessionsLoaded = false;
          this.auth.me().subscribe({
            next: (user) => this.applyProfile(user as ProfileUser),
            error: () => {},
          });
          this.toast.show(
            response.toast
              ?? 'Password changed. All other sessions were signed out and the change is in the audit trail.',
          );
        },
        error: (error: { error?: Record<string, string[] | string> }) => {
          this.pwBusy.set(false);
          const body = error?.error ?? {};
          const first = Object.values(body)[0];
          const message = Array.isArray(first) ? first[0] : (first as string);
          this.pwError.set(message || 'That password could not be changed.');
          this.toast.show(message || 'That password could not be changed. Nothing was changed.');
        },
      });
  }

  sendReset(): void {
    if (this.resetBusy()) return;
    this.resetBusy.set(true);
    this.api.post<{ toast?: string }>('/auth/password/reset/', { email: this.email() }).subscribe({
      next: (response) => {
        this.resetBusy.set(false);
        this.toast.show(
          response.toast
            ?? `Reset link sent to ${this.email()}. It expires in 30 minutes and can be used once.`,
        );
      },
      error: () => {
        this.resetBusy.set(false);
        this.toast.show('That reset link could not be sent.');
      },
    });
  }

  // ── security tab ───────────────────────────────────────────────────

  toggleMfa(): void {
    const next = !this.mfaOn();
    this.mfaOn.set(next);
    this.api.patch<{ mfa_enabled: boolean; toast?: string }>('/auth/mfa/', { enabled: next })
      .subscribe({
        next: (response) => {
          this.mfaOn.set(!!response.mfa_enabled);
          const user = this.profile();
          if (user) {
            const updated: ProfileUser = { ...user, mfa_enabled: !!response.mfa_enabled };
            this.profile.set(updated);
            this.auth.currentUser.set(updated);
          }
          this.toast.show(response.toast);
        },
        error: () => {
          this.mfaOn.set(!next);
          this.toast.show('That setting could not be changed.');
        },
      });
  }

  endSession(session: SessionRow): void {
    if (session.current) {
      this.toast.show('This is the session you are using.');
      return;
    }
    this.api.delete<void>(`/auth/sessions/${session.id}/`).subscribe({
      next: () => {
        this.sessions.update((rows) => rows.filter((row) => row.id !== session.id));
        this.toast.show(`${session.device} signed out. The event is recorded in the audit trail.`);
      },
      error: () => this.toast.show('That session could not be ended.'),
    });
  }

  signOutOthers(): void {
    const others = this.sessions().filter((row) => !row.current);
    if (!others.length) {
      this.toast.show('There are no other signed-in devices.');
      return;
    }
    forkJoin(others.map((row) => this.api.delete<void>(`/auth/sessions/${row.id}/`))).subscribe({
      next: () => {
        this.sessions.update((rows) => rows.filter((row) => row.current));
        this.toast.show('All other sessions signed out. You will stay signed in on this device.');
      },
      error: () => this.toast.show('Those sessions could not all be ended.'),
    });
  }

  sessionMeta(session: SessionRow): string {
    return [session.current ? 'This device' : '', session.location, session.last_active]
      .filter(Boolean)
      .join(' · ');
  }

  // ── notifications tab ──────────────────────────────────────────────

  togglePref(row: PrefRow): void {
    if (row.locked) {
      this.toast.show('Critical events cannot be switched off — they are the point of the system.');
      return;
    }
    const current = this.prefs();
    if (!current) return;
    const key = row.k as PrefKey;
    const next: Preferences = { ...current, [key]: !current[key] };
    this.prefs.set(next);
    this.api.patch<{ preferences: Preferences; toast?: string }>('/auth/preferences/', {
      [key]: next[key],
    }).subscribe({
      next: (response) => {
        if (response.preferences) this.prefs.set(response.preferences);
        this.toast.show(response.toast ?? 'Notification preferences saved.');
      },
      error: () => {
        this.prefs.set(current);
        this.toast.show('That preference could not be saved.');
      },
    });
  }

  prefTagClass(row: PrefRow): string {
    if (row.locked) return 'tag-neutral';
    return row.on ? 'tag-accent' : 'tag-outline';
  }

  // ── permissions tab ────────────────────────────────────────────────

  permTagClass(level: string): string {
    const value = (level || '').trim().toLowerCase();
    if (value === 'none' || value === 'restricted') return 'tag-outline';
    if (value === 'read' || value === 'read only') return 'tag-neutral';
    return 'tag-accent';
  }

  // ── delegation tab ─────────────────────────────────────────────────

  pickDelegate(person: DirectoryPerson): void {
    this.delegateId.set(this.delegateId() === person.id ? null : person.id);
  }

  saveDelegation(): void {
    if (this.delegBusy()) return;
    if (!this.delegateId()) {
      this.toast.show('Pick someone to delegate to first.');
      return;
    }
    this.delegBusy.set(true);
    this.api.put<{ delegation: Delegation; toast?: string }>('/auth/delegation/', {
      delegate_to: this.delegateId(),
      starts_on: this.delegFrom() || null,
      ends_on: this.delegUntil() || null,
      active: true,
    }).subscribe({
      next: (response) => {
        this.delegBusy.set(false);
        if (response.delegation) {
          this.delegateId.set(response.delegation.delegate_to ?? null);
          this.delegFrom.set(response.delegation.starts_on ?? '');
          this.delegUntil.set(response.delegation.ends_on ?? '');
        }
        this.toast.show(response.toast ?? 'Approvals delegated.');
      },
      error: () => {
        this.delegBusy.set(false);
        this.toast.show('That delegation could not be saved.');
      },
    });
  }

  clearDelegation(): void {
    if (this.delegBusy()) return;
    this.delegBusy.set(true);
    this.api.put<{ delegation: Delegation; toast?: string }>('/auth/delegation/', {
      delegate_to: null, starts_on: null, ends_on: null, active: false,
    }).subscribe({
      next: () => {
        this.delegBusy.set(false);
        this.delegateId.set(null);
        this.delegFrom.set('');
        this.delegUntil.set('');
        this.toast.show('Delegation cleared. Approvals come back to you.');
      },
      error: () => {
        this.delegBusy.set(false);
        this.toast.show('That delegation could not be cleared.');
      },
    });
  }
}

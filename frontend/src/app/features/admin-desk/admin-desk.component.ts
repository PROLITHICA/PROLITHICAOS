import { NgTemplateOutlet } from '@angular/common';
import { HttpErrorResponse, HttpEventType, HttpResponse } from '@angular/common/http';
import {
  ChangeDetectionStrategy, Component, computed, effect, inject, signal, untracked,
} from '@angular/core';
import { Observable, catchError, forkJoin, map, of } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { PermissionService } from '../../core/permission.service';
import { RecordCell, RecordRow, TagClass } from '../../core/models';
import { ToastService } from '../../core/toast.service';
import { ConfirmComponent } from '../../shared/ui/confirm/confirm.component';
import { DataTableComponent } from '../../shared/ui/data-table/data-table.component';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { FieldComponent } from '../../shared/ui/field/field.component';
import { PageHeaderComponent } from '../../shared/ui/page-header/page-header.component';
import { SectionCardComponent } from '../../shared/ui/section-card/section-card.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';
import { TagComponent } from '../../shared/ui/tag/tag.component';
import { LoadFailure, describeError } from '../../shared/util/record-detail';
import {
  Choice, CorrespondenceItem, DirectoryPerson, ENTRY_KINDS, EntryDraft, PublishDraft,
  REPORT_AUDIENCES, REPORT_KINDS, ReportItem, ScheduleItem, SignatureRequest,
  addDays, hhmm, isoToday, labelOfValue, labelsOf, longDate, valueOfLabel,
} from './admin-desk.models';

interface Section<T> { rows: T[]; failure: LoadFailure | null; }
interface SendResult { record: SignatureRequest; toast: string; }
interface PublishResult { record: ReportItem; toast: string; }

function empty<T>(): Section<T> {
  return { rows: [], failure: null };
}

function blankEntry(): EntryDraft {
  return {
    id: '', start_time: '09:00', end_time: '09:30', title: '',
    kind: 'meeting', location: '', attendees: '', attached_ref: '',
  };
}

function blankPublish(): PublishDraft {
  return { title: '', period: '', kind: 'quarterly', audience: 'executive', summary: '' };
}

/**
 * `/admin-desk` — the secretariat desk, ordered the way the office actually
 * runs: build the executive's day first, then the reports the office publishes,
 * then what is waiting on a signature and what correspondence is open.
 */
@Component({
  selector: 'app-admin-desk',
  standalone: true,
  imports: [
    NgTemplateOutlet, PageHeaderComponent, SectionCardComponent, SkeletonComponent, EmptyStateComponent,
    DataTableComponent, FieldComponent, TagComponent, ConfirmComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './admin-desk.component.html',
  styleUrl: './admin-desk.component.css',
})
export class AdminDeskComponent {
  private readonly api = inject(ApiService);
  private readonly toasts = inject(ToastService);
  private readonly perms = inject(PermissionService);

  // ── the executive's day ───────────────────────────────────────────────────
  readonly people = signal<DirectoryPerson[]>([]);
  readonly personId = signal<string>('');
  readonly day = signal<string>(isoToday());
  readonly entries = signal<ScheduleItem[]>([]);
  readonly dayLoading = signal(true);
  readonly dayFailure = signal<LoadFailure | null>(null);

  /** '' = closed, 'new' = the add form, otherwise the id being edited. */
  readonly composing = signal<string>('');
  readonly draft = signal<EntryDraft>(blankEntry());
  readonly savingEntry = signal(false);
  readonly entryError = signal<string>('');
  readonly movingId = signal<string>('');
  readonly removeTarget = signal<ScheduleItem | null>(null);
  readonly removing = signal(false);

  // ── reports and packs ─────────────────────────────────────────────────────
  readonly reports = signal<ReportItem[]>([]);
  readonly reportsLoading = signal(true);
  readonly reportsFailure = signal<LoadFailure | null>(null);
  readonly publishOpen = signal(false);
  readonly publish = signal<PublishDraft>(blankPublish());
  readonly file = signal<File | null>(null);
  readonly uploadPct = signal(0);
  readonly uploading = signal(false);
  readonly publishError = signal<string>('');
  readonly downloadingId = signal<string>('');
  readonly downloadPct = signal(0);
  readonly withdrawTarget = signal<ReportItem | null>(null);
  readonly withdrawing = signal(false);

  // ── signatures and correspondence (unchanged behaviour) ───────────────────
  readonly loading = signal(true);
  readonly signatures = signal<Section<SignatureRequest>>(empty<SignatureRequest>());
  readonly correspondence = signal<Section<CorrespondenceItem>>(empty<CorrespondenceItem>());
  readonly sending = signal<string>('');

  readonly entryKindLabels = labelsOf(ENTRY_KINDS);
  readonly reportKindLabels = labelsOf(REPORT_KINDS);
  readonly reportAudienceLabels = labelsOf(REPORT_AUDIENCES);

  readonly correspondenceCols = [
    { l: 'Item' }, { l: 'Attached to' }, { l: 'Owner' }, { l: 'Due' }, { l: 'State' },
  ];

  readonly correspondenceRows = computed<RecordRow[]>(() =>
    this.correspondence().rows.map((row) => ({
      id: row.id,
      cells: [
        { t: row.item },
        { t: row.attached, muted: true },
        { t: row.owner, muted: true },
        { t: row.due, muted: true },
        { t: row.state, tag: row.tag_class as TagClass },
      ] as RecordCell[],
    })),
  );

  /** Only a role holding `meetings:full` may arrange somebody else's day. */
  readonly canArrange = computed(() => this.perms.can('meetings', 'full'));
  readonly canPublish = computed(() => this.perms.can('correspondence', 'full'));

  /** Names collide in the directory, so a repeated name earns its email. */
  readonly personOptions = computed<string[]>(() => this.people().map((p) => this.personLabel(p)));

  readonly personLabelValue = computed<string>(() => {
    const person = this.people().find((row) => row.id === this.personId());
    return person ? this.personLabel(person) : '';
  });

  readonly dayLabel = computed(() => longDate(this.day()));
  readonly isToday = computed(() => this.day() === isoToday());

  readonly doneCount = computed(() => this.entries().filter((entry) => entry.done).length);

  readonly dayLine = computed(() => {
    const rows = this.entries();
    if (!rows.length) return 'Nothing in the diary yet.';
    const noun = rows.length === 1 ? 'entry' : 'entries';
    const first = rows[0].time_label.split('–')[0];
    const last = rows[rows.length - 1].time_label.split('–').slice(-1)[0];
    return `${rows.length} ${noun} · ${this.doneCount()} ticked off · ${first} to ${last}`;
  });

  /** What the desk wants the secretary to do first, in one line. */
  readonly nextUp = computed(() => {
    const open = this.entries().filter((entry) => !entry.done);
    if (!this.entries().length) return 'The day is empty — build it.';
    if (!open.length) return 'Every entry is ticked off.';
    return `Next: ${open[0].time_label} ${open[0].title}`;
  });

  readonly fileName = computed(() => this.file()?.name ?? 'No file chosen');

  constructor() {
    this.loadPeople();
    this.loadRest();
    this.loadReports();
    effect(() => {
      const person = this.personId();
      const day = this.day();
      if (!person) return;
      untracked(() => this.loadDay(person, day));
    });
  }

  // ── people and the day ────────────────────────────────────────────────────

  personLabel(person: DirectoryPerson): string {
    const twice = this.people().filter((row) => row.display_name === person.display_name).length > 1;
    const base = `${person.display_name} · ${person.job_title}`;
    return twice ? `${base} (${person.email})` : base;
  }

  onPerson(label: string): void {
    const person = this.people().find((row) => this.personLabel(row) === label);
    if (person) {
      this.closeComposer();
      this.personId.set(person.id);
    }
  }

  onDay(value: string): void {
    if (!value) return;
    this.closeComposer();
    this.day.set(value);
  }

  stepDay(days: number): void {
    this.closeComposer();
    this.day.set(addDays(this.day(), days));
  }

  goToday(): void {
    this.closeComposer();
    this.day.set(isoToday());
  }

  private loadPeople(): void {
    this.api.get<DirectoryPerson[]>('/directory/').subscribe({
      next: (rows) => {
        const people = (rows ?? []).filter((row) => !!row.department);
        this.people.set(people);
        const chief = people.find((row) => /chief executive/i.test(row.job_title));
        this.personId.set((chief ?? people[0])?.id ?? '');
        if (!people.length) this.dayLoading.set(false);
      },
      error: (error: unknown) => {
        this.people.set([]);
        this.dayLoading.set(false);
        this.dayFailure.set(describeError(error, 'The directory'));
      },
    });
  }

  private loadDay(person: string, day: string): void {
    this.dayLoading.set(true);
    this.dayFailure.set(null);
    this.api.get<ScheduleItem[]>('/schedule/', { person, day }).subscribe({
      next: (rows) => {
        this.entries.set(rows ?? []);
        this.dayLoading.set(false);
      },
      error: (error: unknown) => {
        this.entries.set([]);
        this.dayLoading.set(false);
        this.dayFailure.set(describeError(error, 'This day'));
      },
    });
  }

  reloadDay(): void {
    if (this.personId()) this.loadDay(this.personId(), this.day());
  }

  // ── building the day ──────────────────────────────────────────────────────

  openAdd(): void {
    this.entryError.set('');
    const last = this.entries()[this.entries().length - 1];
    const start = last ? hhmm(last.end_time) || '09:00' : '09:00';
    this.draft.set({ ...blankEntry(), start_time: start, end_time: this.plusHalfHour(start) });
    this.composing.set('new');
  }

  openEdit(entry: ScheduleItem): void {
    if (entry.done) return;
    this.entryError.set('');
    this.draft.set({
      id: entry.id,
      start_time: hhmm(entry.start_time),
      end_time: hhmm(entry.end_time),
      title: entry.title,
      kind: entry.kind,
      location: entry.location,
      attendees: entry.attendees,
      attached_ref: entry.attached_ref,
    });
    this.composing.set(entry.id);
  }

  closeComposer(): void {
    this.composing.set('');
    this.savingEntry.set(false);
    this.entryError.set('');
  }

  setDraft(key: keyof EntryDraft, value: string): void {
    this.draft.update((draft) => ({ ...draft, [key]: value }));
  }

  /** The kind pills carry labels; the API wants the value. */
  setDraftKind(label: string): void {
    this.setDraft('kind', valueOfLabel(ENTRY_KINDS, label));
  }

  draftKindLabel(): string {
    return labelOfValue(ENTRY_KINDS, this.draft().kind);
  }

  saveEntry(): void {
    const draft = this.draft();
    if (this.savingEntry()) return;
    if (!draft.title.trim()) {
      this.entryError.set('Give the entry a title — that is what the executive reads.');
      return;
    }
    if (!draft.start_time) {
      this.entryError.set('A start time is needed to place the entry in the day.');
      return;
    }
    if (draft.end_time && draft.end_time < draft.start_time) {
      this.entryError.set('The entry cannot end before it starts.');
      return;
    }

    this.savingEntry.set(true);
    this.entryError.set('');
    const body = {
      person: this.personId(),
      day: this.day(),
      start_time: draft.start_time,
      end_time: draft.end_time || draft.start_time,
      kind: draft.kind,
      title: draft.title.trim(),
      location: draft.location.trim(),
      attendees: draft.attendees.trim(),
      attached_ref: draft.attached_ref.trim(),
    };

    const request = draft.id
      ? this.api.patch<ScheduleItem>(`/schedule/${draft.id}/`, body)
      : this.api.post<ScheduleItem>('/schedule/', body);

    request.subscribe({
      next: () => {
        this.savingEntry.set(false);
        this.closeComposer();
        this.toasts.show(draft.id
          ? `“${body.title}” updated on the day. The executive sees the change immediately.`
          : `“${body.title}” added at ${body.start_time}. It is now on the executive's day.`);
        this.reloadDay();
      },
      error: (error: unknown) => {
        this.savingEntry.set(false);
        this.entryError.set(this.messageOf(error, 'The entry could not be saved.'));
      },
    });
  }

  /** Reorder in a time-ordered day means swapping slots with the neighbour. */
  move(entry: ScheduleItem, direction: -1 | 1): void {
    if (this.movingId()) return;
    const rows = this.entries();
    const index = rows.findIndex((row) => row.id === entry.id);
    const other = rows[index + direction];
    if (!other) return;

    this.movingId.set(entry.id);
    forkJoin([
      this.api.patch<ScheduleItem>(`/schedule/${entry.id}/`, {
        start_time: hhmm(other.start_time), end_time: hhmm(other.end_time), order: other.order,
      }),
      this.api.patch<ScheduleItem>(`/schedule/${other.id}/`, {
        start_time: hhmm(entry.start_time), end_time: hhmm(entry.end_time), order: entry.order,
      }),
    ]).subscribe({
      next: () => {
        this.movingId.set('');
        this.toasts.show(`“${entry.title}” now sits at ${other.time_label}.`);
        this.reloadDay();
      },
      error: (error: unknown) => {
        this.movingId.set('');
        this.toasts.show(this.messageOf(error, 'The day could not be reordered.'));
      },
    });
  }

  askRemove(entry: ScheduleItem): void {
    this.removeTarget.set(entry);
  }

  confirmRemove(): void {
    const entry = this.removeTarget();
    if (!entry || this.removing()) return;
    this.removing.set(true);
    this.api.delete<void>(`/schedule/${entry.id}/`).subscribe({
      next: () => {
        this.removing.set(false);
        this.removeTarget.set(null);
        this.toasts.show(`“${entry.title}” removed from the day.`);
        this.reloadDay();
      },
      error: (error: unknown) => {
        this.removing.set(false);
        this.removeTarget.set(null);
        this.toasts.show(this.messageOf(error, 'The entry could not be removed.'));
      },
    });
  }

  canMoveUp(entry: ScheduleItem): boolean {
    return this.entries()[0]?.id !== entry.id;
  }

  canMoveDown(entry: ScheduleItem): boolean {
    return this.entries()[this.entries().length - 1]?.id !== entry.id;
  }

  entryMeta(entry: ScheduleItem): string {
    const parts = [entry.location, entry.attendees, entry.meta].filter((part) => !!part);
    return parts.join(' · ');
  }

  // ── reports and packs ─────────────────────────────────────────────────────

  private loadReports(): void {
    this.reportsLoading.set(true);
    this.api.get<ReportItem[]>('/reports/').subscribe({
      next: (rows) => {
        this.reports.set(rows ?? []);
        this.reportsLoading.set(false);
      },
      error: (error: unknown) => {
        this.reports.set([]);
        this.reportsLoading.set(false);
        this.reportsFailure.set(describeError(error, 'Reports and packs'));
      },
    });
  }

  openPublish(): void {
    this.publish.set(blankPublish());
    this.file.set(null);
    this.uploadPct.set(0);
    this.publishError.set('');
    this.publishOpen.set(true);
  }

  closePublish(): void {
    if (this.uploading()) return;
    this.publishOpen.set(false);
    this.publishError.set('');
  }

  setPublish(key: keyof PublishDraft, value: string): void {
    this.publish.update((draft) => ({ ...draft, [key]: value }));
  }

  setPublishChoice(key: 'kind' | 'audience', label: string): void {
    const choices: Choice[] = key === 'kind' ? REPORT_KINDS : REPORT_AUDIENCES;
    this.setPublish(key, valueOfLabel(choices, label));
  }

  publishKindLabel(): string {
    return labelOfValue(REPORT_KINDS, this.publish().kind);
  }

  publishAudienceLabel(): string {
    return labelOfValue(REPORT_AUDIENCES, this.publish().audience);
  }

  onFile(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.file.set(input.files?.[0] ?? null);
    this.publishError.set('');
  }

  submitPublish(): void {
    const draft = this.publish();
    const file = this.file();
    if (this.uploading()) return;
    if (!draft.title.trim()) {
      this.publishError.set('The report needs a title before it can be published.');
      return;
    }
    if (!file) {
      this.publishError.set('Choose the file to publish — the row is only useful with it.');
      return;
    }

    this.uploading.set(true);
    this.uploadPct.set(0);
    this.publishError.set('');

    this.api.uploadEvents<PublishResult>('/reports/', file, {
      title: draft.title.trim(),
      period: draft.period.trim(),
      kind: draft.kind,
      audience: draft.audience,
      summary: draft.summary.trim(),
    }).subscribe({
      next: (event) => {
        if (event.type === HttpEventType.UploadProgress && event.total) {
          this.uploadPct.set(Math.round((event.loaded / event.total) * 100));
        }
        if (event.type === HttpEventType.Response) {
          const body = (event as HttpResponse<PublishResult>).body;
          this.uploadPct.set(100);
          this.uploading.set(false);
          this.publishOpen.set(false);
          this.toasts.show(body?.toast
            || `“${draft.title.trim()}” published. Everyone in its audience can download it now.`);
          this.loadReports();
        }
      },
      error: (error: unknown) => {
        this.uploading.set(false);
        this.uploadPct.set(0);
        this.publishError.set(this.messageOf(error, 'The report could not be published.'));
      },
    });
  }

  download(report: ReportItem): void {
    if (this.downloadingId()) return;
    this.downloadingId.set(report.id);
    this.downloadPct.set(0);
    this.api.downloadEvents(`/reports/${report.id}/download/`).subscribe({
      next: (event) => {
        if (event.type === HttpEventType.DownloadProgress && event.total) {
          this.downloadPct.set(Math.round((event.loaded / event.total) * 100));
        }
        if (event.type === HttpEventType.Response) {
          const response = event as HttpResponse<Blob>;
          this.downloadingId.set('');
          this.downloadPct.set(0);
          if (response.body) {
            this.saveBlob(response.body, this.filenameOf(response, report));
            this.toasts.show(`“${report.title}” downloaded.`);
          }
        }
      },
      error: (error: unknown) => {
        this.downloadingId.set('');
        this.downloadPct.set(0);
        this.toasts.show(this.messageOf(error, 'That file could not be downloaded.'));
      },
    });
  }

  askWithdraw(report: ReportItem): void {
    this.withdrawTarget.set(report);
  }

  confirmWithdraw(): void {
    const report = this.withdrawTarget();
    if (!report || this.withdrawing()) return;
    this.withdrawing.set(true);
    this.api.delete<void>(`/reports/${report.id}/`).subscribe({
      next: () => {
        this.withdrawing.set(false);
        this.withdrawTarget.set(null);
        this.toasts.show(`“${report.title}” withdrawn. Nobody can download it now.`);
        this.loadReports();
      },
      error: (error: unknown) => {
        this.withdrawing.set(false);
        this.withdrawTarget.set(null);
        this.toasts.show(this.messageOf(error, 'That report could not be withdrawn.'));
      },
    });
  }

  reportMeta(report: ReportItem): string {
    return [report.period, report.audience_label, report.size_label, `Published ${report.published_on}`,
      report.uploaded_by_name ? `by ${report.uploaded_by_name}` : '']
      .filter((part) => !!part && part !== '—').join(' · ');
  }

  // ── signatures and correspondence ─────────────────────────────────────────

  send(signature: SignatureRequest): void {
    if (this.sending() || signature.state !== 'draft') return;
    this.sending.set(signature.id);
    this.api.post<SendResult>(`/signatures/${signature.id}/send/`).subscribe({
      next: (response) => {
        const updated = response.record;
        if (updated) {
          this.signatures.update((section) => ({
            ...section,
            rows: section.rows.map((row) => (row.id === updated.id ? updated : row)),
          }));
        }
        this.toasts.show(response.toast);
        this.sending.set('');
      },
      error: (error: unknown) => {
        this.toasts.show(describeError(error, 'This signature request').heading);
        this.sending.set('');
      },
    });
  }

  ctaFor(signature: SignatureRequest): string {
    if (this.sending() === signature.id) return 'Sending…';
    return signature.cta || (signature.state === 'draft'
      ? 'Send for signature' : 'Sent for signature');
  }

  private loadRest(): void {
    this.loading.set(true);
    forkJoin({
      signatures: this.section<SignatureRequest>('/signatures/', 'Signature requests'),
      correspondence: this.section<CorrespondenceItem>('/correspondence/', 'Correspondence'),
    }).subscribe((result) => {
      this.signatures.set(result.signatures);
      this.correspondence.set(result.correspondence);
      this.loading.set(false);
    });
  }

  private section<T>(path: string, subject: string): Observable<Section<T>> {
    return this.api.list<T>(path, { page_size: 100 }).pipe(
      map((page) => ({ rows: page.results ?? [], failure: null }) as Section<T>),
      catchError((error: unknown) =>
        of({ rows: [], failure: describeError(error, subject) } as Section<T>)),
    );
  }

  // ── helpers ───────────────────────────────────────────────────────────────

  private plusHalfHour(start: string): string {
    const [hours, minutes] = start.split(':').map(Number);
    if (Number.isNaN(hours) || Number.isNaN(minutes)) return '09:30';
    const total = Math.min(hours * 60 + minutes + 30, 23 * 60 + 59);
    return `${`${Math.floor(total / 60)}`.padStart(2, '0')}:${`${total % 60}`.padStart(2, '0')}`;
  }

  private saveBlob(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  private filenameOf(response: HttpResponse<Blob>, report: ReportItem): string {
    const header = response.headers.get('content-disposition') ?? '';
    const match = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(header);
    if (match?.[1]) return decodeURIComponent(match[1]);
    return report.original_name || `${report.title}.pdf`;
  }

  /** DRF's `detail`, its first field error, or the fallback line. */
  private messageOf(error: unknown, fallback: string): string {
    if (!(error instanceof HttpErrorResponse)) return fallback;
    if (error.status === 403) {
      return 'Your role cannot make this change. The server refused it, and the attempt is logged.';
    }
    const body = error.error as Record<string, unknown> | string | null;
    if (!body || typeof body === 'string') return fallback;
    const detail = body['detail'] ?? body['toast'];
    if (typeof detail === 'string') return detail;
    for (const [field, value] of Object.entries(body)) {
      if (Array.isArray(value) && typeof value[0] === 'string') return `${field}: ${value[0]}`;
      if (typeof value === 'string') return `${field}: ${value}`;
    }
    return fallback;
  }
}

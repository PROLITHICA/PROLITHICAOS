import { Injectable, computed, inject, signal } from '@angular/core';

import { ApiService } from '../../core/api.service';
import { ToastService } from '../../core/toast.service';
import { ActionResult, ApprovalItem, MyDayPayload, ScheduleEntry } from './my-day.models';

/**
 * The executive's day, held once for the whole session.
 *
 * Both `/my-day` and the Command Centre's glance strip read from here, so a
 * tick or an approval made on one screen is already true on the other.
 */
@Injectable({ providedIn: 'root' })
export class MyDayService {
  private readonly api = inject(ApiService);
  private readonly toasts = inject(ToastService);

  readonly data = signal<MyDayPayload | null>(null);
  readonly loading = signal(false);
  readonly failed = signal(false);
  /** id of the approval currently being sent — approvals never go optimistic */
  readonly busy = signal<string>('');

  readonly greeting = computed(() => this.data()?.greeting ?? '');
  readonly dateLabel = computed(() => this.data()?.date_label ?? '');
  readonly summary = computed(() => this.data()?.summary ?? '');
  readonly schedule = computed(() => this.data()?.schedule ?? []);
  readonly approvals = computed(() => this.data()?.approvals ?? []);
  readonly focus = computed(() => this.data()?.focus ?? null);

  readonly doneCount = computed(() => this.schedule().filter((entry) => entry.done).length);
  readonly total = computed(() => this.schedule().length);
  readonly progressPct = computed(() => {
    const total = this.total();
    return total ? Math.round((this.doneCount() / total) * 100) : 0;
  });
  readonly progressLabel = computed(() => `${this.doneCount()} of ${this.total()} done`);

  /** The next entries still open, in order — what the Command Centre shows. */
  next(count: number): ScheduleEntry[] {
    return this.schedule().filter((entry) => !entry.done).slice(0, count);
  }

  /** Fetch once per session unless `force` is set. */
  load(force = false): void {
    if (this.loading()) return;
    if (this.data() && !force) return;
    this.refresh();
  }

  refresh(): void {
    this.loading.set(true);
    this.failed.set(false);
    this.api.get<MyDayPayload>('/my-day/').subscribe({
      next: (payload) => {
        this.data.set(payload);
        this.loading.set(false);
      },
      error: () => {
        this.failed.set(true);
        this.loading.set(false);
      },
    });
  }

  /**
   * Ticking is safe to do optimistically: the row flips the moment it is
   * pressed and rolls back only if the server refuses.
   */
  toggle(entry: ScheduleEntry): void {
    const wanted = !entry.done;
    this.patchEntry(entry.id, { done: wanted, state: wanted ? 'done' : 'scheduled' });

    const path = `/schedule/${entry.id}/${wanted ? 'done' : 'reopen'}/`;
    this.api.post<ActionResult<ScheduleEntry>>(path, {}).subscribe({
      next: (response) => {
        if (response?.record) this.patchEntry(entry.id, response.record);
        this.toasts.fromResponse(response);
      },
      error: () => {
        this.patchEntry(entry.id, { done: entry.done, state: entry.state, tag_class: entry.tag_class });
        this.toasts.show('That could not be saved. The entry is unchanged.');
      },
    });
  }

  /**
   * Approving performs the real work behind it — pricing a change, posting an
   * expense, releasing a milestone — so it waits for the server and repeats
   * the server's own account of what happened.
   */
  approve(item: ApprovalItem, onDone?: () => void): void {
    this.act(item, `/approvals/${item.id}/approve/`, {}, onDone);
  }

  decline(item: ApprovalItem, reason: string, onDone?: () => void): void {
    this.act(item, `/approvals/${item.id}/decline/`, { reason }, onDone);
  }

  private act(item: ApprovalItem, path: string, body: unknown, onDone?: () => void): void {
    if (this.busy()) return;
    this.busy.set(item.id);
    this.api.post<ActionResult<unknown>>(path, body).subscribe({
      next: (response) => {
        this.busy.set('');
        this.dropApproval(item.id);
        this.toasts.fromResponse(response);
        onDone?.();
      },
      error: () => {
        this.busy.set('');
        this.toasts.show('That decision could not be sent. Nothing was changed.');
        onDone?.();
      },
    });
  }

  private patchEntry(id: string, patch: Partial<ScheduleEntry>): void {
    this.data.update((current) => {
      if (!current) return current;
      const schedule = current.schedule.map((entry) =>
        entry.id === id ? { ...entry, ...patch } : entry);
      const done = schedule.filter((entry) => entry.done).length;
      return { ...current, schedule, schedule_done: done, schedule_total: schedule.length };
    });
  }

  private dropApproval(id: string): void {
    this.data.update((current) => {
      if (!current) return current;
      return { ...current, approvals: current.approvals.filter((item) => item.id !== id) };
    });
  }
}

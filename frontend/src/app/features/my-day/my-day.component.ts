import { ChangeDetectionStrategy, Component, DestroyRef, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';

import { PageTitleService } from '../../core/page-title.service';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { FieldComponent } from '../../shared/ui/field/field.component';
import { PageHeaderComponent } from '../../shared/ui/page-header/page-header.component';
import { ProgressBarComponent } from '../../shared/ui/progress-bar/progress-bar.component';
import { SectionCardComponent } from '../../shared/ui/section-card/section-card.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';
import { TagComponent } from '../../shared/ui/tag/tag.component';
import { ApprovalItem, FocusRow, ScheduleEntry } from './my-day.models';
import { MyDayService } from './my-day.service';

/**
 * What pressing the button will actually do, said before it is pressed.
 *
 * The server's toast reports the consequence afterwards; this is the same
 * sentence in advance, so nothing on this screen needs a second click to be
 * understood. Keyed by the `kind` the API already sends.
 */
const CONSEQUENCE: Record<string, string> = {
  expense: 'Approving posts the expense against the project and tells Finance.',
  billing: 'Releasing raises the invoice for this milestone.',
  change: 'Approving prices the change and carries it into the contract value.',
  pricing: 'Approving prices the change and carries it into the contract value.',
  signature: 'Sending puts the document in front of the signatory.',
  invoice: 'Approving sends the invoice to the client.',
};

/** `/my-day` — the screen the executive opens each morning. */
@Component({
  selector: 'app-my-day',
  standalone: true,
  imports: [
    PageHeaderComponent, SectionCardComponent, ProgressBarComponent,
    TagComponent, EmptyStateComponent, SkeletonComponent, FieldComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './my-day.component.html',
  styleUrl: './my-day.component.css',
})
export class MyDayComponent {
  private readonly router = inject(Router);
  private readonly titles = inject(PageTitleService);
  readonly day = inject(MyDayService);
  private readonly destroyRef = inject(DestroyRef);
  readonly now = signal(new Date());
  readonly clock = computed(() => new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Africa/Nairobi', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
  }).format(this.now()));

  /** id of the approval whose decline panel is open, and the reason typed */
  readonly declining = signal<string>('');
  readonly reason = signal<string>('');

  readonly loading = computed(() => this.day.loading() && !this.day.data());
  readonly failed = computed(() => this.day.failed() && !this.day.data());
  readonly allDone = computed(() => this.day.total() > 0 && this.day.doneCount() === this.day.total());

  constructor() {
    this.titles.set('Dashboard');
    const timer = setInterval(() => this.now.set(new Date()), 1000);
    this.destroyRef.onDestroy(() => clearInterval(timer));
    this.day.load();
  }

  // ── the day ──────────────────────────────────────────────────────────
  reload(): void {
    this.day.refresh();
  }

  toggle(entry: ScheduleEntry): void {
    this.day.toggle(entry);
  }

  tickLabel(entry: ScheduleEntry): string {
    return entry.done ? `Put “${entry.title}” back on the day` : `Tick “${entry.title}” off`;
  }

  /** The facts under the title: where it is, who prepared it, what it attaches to. */
  facts(entry: ScheduleEntry): string {
    const location = entry.location && entry.location !== entry.kind_label ? entry.location : '';
    return [
      location,
      entry.attendees,
      entry.prepared_by ? `Prepared by ${entry.prepared_by}` : '',
      entry.attached_ref,
    ].filter(Boolean).join(' · ');
  }

  // ── approvals ────────────────────────────────────────────────────────
  consequence(item: ApprovalItem): string {
    return CONSEQUENCE[item.kind] ?? 'This is carried out the moment you press it.';
  }

  approve(item: ApprovalItem): void {
    this.day.approve(item);
  }

  openDecline(item: ApprovalItem): void {
    this.declining.set(this.declining() === item.id ? '' : item.id);
    this.reason.set('');
  }

  closeDecline(): void {
    this.declining.set('');
    this.reason.set('');
  }

  /** A decline is never sent without a reason — the button stays disabled. */
  canDecline(): boolean {
    return this.reason().trim().length > 2;
  }

  sendDecline(item: ApprovalItem): void {
    const reason = this.reason().trim();
    if (!reason) return;
    this.day.decline(item, reason, () => this.closeDecline());
  }

  // ── focus block ──────────────────────────────────────────────────────
  openFocus(row: FocusRow): void {
    if (row.route) void this.router.navigateByUrl(row.route);
  }
}

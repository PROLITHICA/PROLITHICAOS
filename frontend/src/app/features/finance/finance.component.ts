import { ThemeColorPipe } from '../../shared/ui/theme-color.pipe';
import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, forkJoin, of } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { ToastService } from '../../core/toast.service';
import { RecordCell, RecordRow, TagClass } from '../../core/models';
import { CardComponent } from '../../shared/ui/card/card.component';
import { DataTableComponent } from '../../shared/ui/data-table/data-table.component';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { PageHeaderComponent } from '../../shared/ui/page-header/page-header.component';
import { SectionCardComponent } from '../../shared/ui/section-card/section-card.component';
import { TagComponent } from '../../shared/ui/tag/tag.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';

/** ── the shapes `GET /api/dashboard/finance/` returns ─────────────────────── */

export interface FinanceFigure {
  label: string;
  value: string;
  note: string;
  col: string;
  w: string;
}

export interface ChartRect {
  x: number; y: number; width: number; height: number; fill?: string;
}

export interface InvoicedVsReceived {
  title: string;
  subtitle: string;
  view_box: string;
  baseline_y: number;
  axis: Array<{ label: string; y: number }>;
  months: string[];
  month_x: number[];
  invoiced: ChartRect[];
  received: ChartRect[];
  legend: Array<{ label: string; colour: string }>;
}

export interface BillableItem {
  id: string;
  ref: string;
  name: string;
  meta: string;
  value_display: string;
  state: 'ready' | 'scheduled' | 'blocked' | string;
  blocked_reason: string;
  billed: boolean;
  billed_label: string;
  cta: string;
  btn_class: string;
}

export interface InvoiceRow {
  id: string;
  ref: string;
  cells: Array<Record<string, unknown>>;
}

export interface ExpenseItem {
  id: string;
  ref: string;
  what: string;
  meta: string;
  value_display: string;
  state: string;
  cta: string;
  btn_class: string;
}

/** ── `GET /api/finance/billing-cycle/` ───────────────────────────────────── */

export interface CycleStage {
  key: string;
  label: string;
  count: number;
  value: string;
  note: string;
  tag_class: string;
}

export interface BlockedRow {
  title: string;
  meta: string;
  value: string;
  tag_class: string;
}

export interface BillingCycle {
  title: string;
  subtitle: string;
  stages: CycleStage[];
  blocked_rows: BlockedRow[];
}

/** ── `GET /api/finance/breakdown/` ───────────────────────────────────────── */

export interface BreakdownBar {
  label: string;
  width: string;
  tone: string;
}

export interface BreakdownRow {
  project: string;
  ref: string;
  contract: string;
  invoiced: string;
  paid: string;
  cost: string;
  unbilled: string;
  margin_now: string;
  forecast: string;
  tag_class: string;
  bars: BreakdownBar[];
  route: string;
}

export interface Breakdown {
  title: string;
  subtitle: string;
  cols: string[];
  rows: BreakdownRow[];
}

export interface FinancePayload {
  title: string;
  subtitle: string;
  figures: FinanceFigure[];
  invoiced_vs_received: InvoicedVsReceived;
  billable: { title: string; subtitle: string; items: BillableItem[] };
  invoices: { title: string; subtitle: string; cols: string[]; rows: InvoiceRow[] };
  expenses: { title: string; subtitle: string; items: ExpenseItem[] };
}

type Status = 'loading' | 'ready' | 'error' | 'forbidden';

/**
 * The Finance desk (design lines 700–801): four figure tiles with progress
 * bars, invoiced against received, Ready to bill, the invoices table and the
 * expense approvals list. Every button POSTs and settles into its done label.
 */
@Component({
  selector: 'app-finance',
  standalone: true,
  imports: [ThemeColorPipe,
    PageHeaderComponent, CardComponent, SectionCardComponent, DataTableComponent,
    EmptyStateComponent, SkeletonComponent, TagComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './finance.component.html',
  styleUrl: './finance.component.css',
})
export class FinanceComponent {
  private readonly api = inject(ApiService);
  private readonly toast = inject(ToastService);
  private readonly router = inject(Router);

  readonly status = signal<Status>('loading');
  readonly errorNote = signal<string>('');
  readonly desk = signal<FinancePayload | null>(null);
  readonly cycle = signal<BillingCycle | null>(null);
  readonly breakdown = signal<Breakdown | null>(null);
  /** id of the billable item or expense whose request is in flight */
  readonly busy = signal<string>('');

  readonly title = computed(() => this.desk()?.title ?? 'Finance desk');
  readonly subtitle = computed(() =>
    this.desk()?.subtitle
    ?? 'Billing originates in delivery. Accepted milestones arrive here ready to invoice.');
  readonly figures = computed<FinanceFigure[]>(() => this.desk()?.figures ?? []);
  readonly chart = computed<InvoicedVsReceived | null>(() => this.desk()?.invoiced_vs_received ?? null);
  readonly billable = computed<BillableItem[]>(() => this.desk()?.billable?.items ?? []);
  readonly expenses = computed<ExpenseItem[]>(() => this.desk()?.expenses?.items ?? []);
  readonly invoiceCols = computed<string[]>(() => this.desk()?.invoices?.cols ?? []);
  readonly invoiceRows = computed<RecordRow[]>(() =>
    (this.desk()?.invoices?.rows ?? []).map((row) => ({
      id: row.id,
      ref: row.ref,
      cells: (row.cells ?? []).map((cell) => toCell(cell)),
    })),
  );

  readonly stages = computed<CycleStage[]>(() => this.cycle()?.stages ?? []);
  readonly blockedRows = computed<BlockedRow[]>(() => this.cycle()?.blocked_rows ?? []);
  readonly breakdownRows = computed<BreakdownRow[]>(() => this.breakdown()?.rows ?? []);

  /** The three tones are the same on every row, so one legend serves them all. */
  readonly legendBars = computed<BreakdownBar[]>(() => this.breakdownRows()[0]?.bars ?? []);

  /** The single line the desk leads with: where the money is stuck. */
  readonly blockedLine = computed(() => {
    const blocked = this.stages().find((stage) => stage.key === 'blocked');
    const overdue = this.stages().find((stage) => stage.key === 'overdue');
    const parts: string[] = [];
    if (blocked?.count) parts.push(`${blocked.count} blocked at ${blocked.value}`);
    if (overdue?.count) parts.push(`${overdue.count} overdue at ${overdue.value}`);
    if (!parts.length) return 'Nothing is blocked and nothing is overdue.';
    return `${parts.join(' · ')} — clear these first.`;
  });

  /** The pipeline is drawn wide; this keeps every step legible while scrolling. */
  readonly cycleMinWidth = computed(() => Math.max(this.stages().length * 158, 320));

  readonly months = computed(() => {
    const chart = this.chart();
    if (!chart) return [];
    return chart.months.map((label, index) => ({ label, x: chart.month_x[index] ?? 0 }));
  });

  constructor() {
    this.load();
  }

  load(): void {
    this.status.set('loading');
    this.errorNote.set('');
    forkJoin({
      desk: this.api.get<FinancePayload>('/dashboard/finance/'),
      // The two new blocks are additive: a refusal on either leaves the rest of
      // the desk usable rather than blanking the screen.
      cycle: this.api.get<BillingCycle>('/finance/billing-cycle/')
        .pipe(catchError(() => of(null))),
      breakdown: this.api.get<Breakdown>('/finance/breakdown/')
        .pipe(catchError(() => of(null))),
    }).subscribe({
      next: (payload) => {
        this.desk.set(payload.desk);
        this.cycle.set(payload.cycle);
        this.breakdown.set(payload.breakdown);
        this.status.set('ready');
      },
      error: (error: unknown) => {
        this.desk.set(null);
        if (error instanceof HttpErrorResponse && error.status === 403) {
          this.status.set('forbidden');
          this.errorNote.set(detailOf(error)
            || 'Your role cannot see the finance desk. Ask an administrator if you need access.');
          return;
        }
        this.status.set('error');
        this.errorNote.set(detailOf(error) || 'The finance desk could not be loaded.');
      },
    });
  }

  /** A breakdown row leads to the project it is about. */
  openProject(row: BreakdownRow): void {
    if (row.route) void this.router.navigate([row.route]);
  }

  /** The design's busy copy: "Generating…" to bill, "Scheduling…" to schedule. */
  billableLabel(item: BillableItem): string {
    if (this.busy() !== item.id) return item.cta;
    return item.state === 'scheduled' ? 'Scheduling…' : 'Generating…';
  }

  expenseLabel(item: ExpenseItem): string {
    return this.busy() === item.id ? 'Posting…' : item.cta;
  }

  billableDisabled(item: BillableItem): boolean {
    return this.busy() === item.id || item.billed;
  }

  expenseDisabled(item: ExpenseItem): boolean {
    return this.busy() === item.id || item.cta === 'Approved';
  }

  /** POST billable/{id}/generate-invoice/ — the blocked item refuses with its reason. */
  generateInvoice(item: BillableItem): void {
    if (this.billableDisabled(item)) return;
    this.busy.set(item.id);
    this.api
      .post<{ record?: BillableItem; toast?: string }>(`/billable/${item.id}/generate-invoice/`, {})
      .subscribe({
        next: (response) => {
          this.busy.set('');
          this.toast.show(response?.toast);
          if (response?.record) this.replaceBillable(response.record);
          this.load();
        },
        error: (error: unknown) => {
          this.busy.set('');
          // 409: the recorded reason the milestone cannot be billed.
          const toastText = error instanceof HttpErrorResponse
            ? (error.error as { toast?: string; detail?: string } | null)?.toast
              ?? (error.error as { detail?: string } | null)?.detail
            : '';
          this.toast.show(toastText || item.blocked_reason || 'This item could not be billed.');
        },
      });
  }

  /** POST expenses/{id}/approve/ — posts the cost and recalculates the margin. */
  approveExpense(item: ExpenseItem): void {
    if (this.expenseDisabled(item)) return;
    this.busy.set(item.id);
    this.api
      .post<{ record?: ExpenseItem; toast?: string }>(`/expenses/${item.id}/approve/`, {})
      .subscribe({
        next: (response) => {
          this.busy.set('');
          this.toast.show(response?.toast);
          if (response?.record) this.replaceExpense(response.record);
          this.load();
        },
        error: (error: unknown) => {
          this.busy.set('');
          const message = error instanceof HttpErrorResponse
            ? detailOf(error) : '';
          this.toast.show(message || 'That expense could not be approved.');
        },
      });
  }

  private replaceBillable(record: BillableItem): void {
    const desk = this.desk();
    if (!desk) return;
    this.desk.set({
      ...desk,
      billable: {
        ...desk.billable,
        items: desk.billable.items.map((item) => (item.id === record.id ? record : item)),
      },
    });
  }

  private replaceExpense(record: ExpenseItem): void {
    const desk = this.desk();
    if (!desk) return;
    this.desk.set({
      ...desk,
      expenses: {
        ...desk.expenses,
        items: desk.expenses.items.map((item) => (item.id === record.id ? record : item)),
      },
    });
  }
}

/** Finance serialises cells as {value, align, bold, muted, tag_class}. */
function toCell(cell: Record<string, unknown>): RecordCell {
  const text = cell['value'] ?? cell['t'] ?? cell['text'] ?? '';
  const align = (cell['align'] ?? cell['a'] ?? 'left') as RecordCell['align'];
  return {
    t: text === null || text === undefined ? '' : String(text),
    align: align === 'right' || align === 'center' ? align : 'left',
    bold: !!(cell['bold'] ?? cell['b']),
    muted: !!(cell['muted'] ?? cell['m']),
    tag: (cell['tag_class'] ?? cell['tag'] ?? '') as TagClass | '',
  };
}

function detailOf(error: unknown): string {
  if (!(error instanceof HttpErrorResponse)) return '';
  const body = error.error as { detail?: string } | null;
  return typeof body?.detail === 'string' ? body.detail : '';
}

import { HttpErrorResponse } from '@angular/common/http';
import {
  ChangeDetectionStrategy, Component, computed, effect, inject, input, signal, untracked, viewChild,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { PermissionService } from '../../core/permission.service';
import { ToastService } from '../../core/toast.service';
import {
  Paginated, RecordCell, RecordRow, TagClass, ViewConfig,
} from '../../core/models';
import { CardComponent } from '../../shared/ui/card/card.component';
import { DataTableComponent } from '../../shared/ui/data-table/data-table.component';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { ModalComponent } from '../../shared/ui/modal/modal.component';
import { PageHeaderComponent } from '../../shared/ui/page-header/page-header.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';
import { StatTileComponent } from '../../shared/ui/stat-tile/stat-tile.component';
import {
  ApiRecord, DESIGN_FORMS, FIELD_MAP, FormConfig, MONEY_KEYS, RecordViewDef,
  parseMoney, resolveView,
} from './record-views';

type Status = 'loading' | 'ready' | 'error' | 'forbidden' | 'unknown';

const PAGE_SIZE = 25;

const EXPORT_TOAST =
  'Export queued and stored in Company · Board and policy. The action is in the audit trail.';

/** One row plus the record it came from, so a click can build its detail route. */
interface Line extends RecordRow {
  record: ApiRecord;
}

/**
 * The generic register screen (`/records/:view`), reproducing the design's
 * GENERIC RECORD LIST: header, three stat tiles, filter, create button, table
 * and the server-driven create modal.
 */
@Component({
  selector: 'app-record-list',
  standalone: true,
  imports: [
    FormsModule, PageHeaderComponent, StatTileComponent, CardComponent, DataTableComponent,
    EmptyStateComponent, SkeletonComponent, ModalComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './record-list.component.html',
  styleUrl: './record-list.component.css',
})
export class RecordListComponent {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  private readonly toast = inject(ToastService);
  private readonly perms = inject(PermissionService);

  /** Bound from the `:view` route param, from route `data.view`, or passed in. */
  readonly view = input<string>('');

  private readonly modalRef = viewChild(ModalComponent);

  readonly def = computed<RecordViewDef | null>(() => resolveView(this.view()));

  readonly status = signal<Status>('loading');
  readonly errorNote = signal<string>('');
  readonly config = signal<ViewConfig | null>(null);
  readonly lines = signal<Line[]>([]);
  readonly total = signal<number>(0);

  readonly filterText = signal<string>('');
  readonly search = signal<string>('');
  readonly ordering = signal<string>('');
  readonly page = signal<number>(1);

  /** modal state */
  readonly modalKind = signal<'create' | 'export' | null>(null);
  readonly form = signal<FormConfig | null>(null);
  readonly submitting = signal<boolean>(false);
  readonly formError = signal<string>('');

  private filterTimer: ReturnType<typeof setTimeout> | null = null;
  private request = 0;

  constructor() {
    effect(() => {
      const def = this.def();
      const query = {
        search: this.search(),
        ordering: this.ordering(),
        page: this.page(),
      };
      untracked(() => this.load(def, query));
    });
  }

  // ── derived view state ────────────────────────────────────────────────────

  readonly title = computed(() => this.config()?.title ?? 'Records');
  readonly subtitle = computed(() => this.config()?.subtitle ?? '');
  readonly stats = computed(() => this.config()?.stats ?? []);
  readonly cols = computed(() => this.config()?.cols ?? []);
  readonly createLabel = computed(() => this.def()?.createLabel ?? '+ New record');
  readonly sorts = computed(() => this.def()?.sorts ?? []);
  readonly clickable = computed(() => !!this.def()?.detail);
  readonly emptyText = computed(() => this.def()?.emptyText ?? 'No records match this view.');

  readonly canWrite = computed(() => {
    const def = this.def();
    if (!def) return false;
    return def.write.some((expression) => this.perms.canExpression(expression));
  });

  readonly countLine = computed(() => {
    const shown = this.lines().length;
    const total = this.total();
    const noun = total === 1 ? 'record' : 'records';
    return shown === total ? `${total} ${noun}` : `${shown} of ${total} ${noun}`;
  });

  readonly pageCount = computed(() => Math.max(1, Math.ceil(this.total() / PAGE_SIZE)));
  readonly showPager = computed(() => this.pageCount() > 1);

  // ── loading ───────────────────────────────────────────────────────────────

  private load(def: RecordViewDef | null, query: { search: string; ordering: string; page: number }): void {
    if (!def) {
      this.status.set('unknown');
      this.config.set(null);
      this.lines.set([]);
      return;
    }

    const ticket = ++this.request;
    this.status.set('loading');
    this.errorNote.set('');

    this.api
      .list<ApiRecord>(def.endpoint, {
        search: query.search || null,
        ordering: query.ordering || null,
        page: query.page,
        page_size: PAGE_SIZE,
      })
      .subscribe({
        next: (page: Paginated<ApiRecord>) => {
          if (ticket !== this.request) return;
          this.config.set(page.view ?? null);
          this.total.set(page.count ?? page.results?.length ?? 0);
          this.lines.set((page.results ?? []).map((record) => this.toLine(def, record)));
          this.status.set('ready');
        },
        error: (error: unknown) => {
          if (ticket !== this.request) return;
          this.lines.set([]);
          this.total.set(0);
          if (error instanceof HttpErrorResponse && error.status === 403) {
            this.status.set('forbidden');
            this.errorNote.set(this.detailOf(error)
              || 'Your role cannot see these records. Ask an administrator if you need access.');
            return;
          }
          if (error instanceof HttpErrorResponse && error.status === 404) {
            this.status.set('unknown');
            return;
          }
          this.status.set('error');
          this.errorNote.set(this.detailOf(error) || 'The records could not be loaded.');
        },
      });
  }

  reload(): void {
    this.load(this.def(), {
      search: this.search(), ordering: this.ordering(), page: this.page(),
    });
  }

  // ── rows ──────────────────────────────────────────────────────────────────

  /** Normalises the three cell shapes the backend apps emit into RecordCell. */
  private toLine(def: RecordViewDef, record: ApiRecord): Line {
    const raw = record['cells'];
    const cells = Array.isArray(raw)
      ? raw.map((cell) => this.toCell(cell as Record<string, unknown>))
      : (def.fallbackCells?.(record) ?? []);
    return {
      id: record['id'] ? String(record['id']) : undefined,
      ref: record['ref'] ? String(record['ref']) : undefined,
      cells,
      record,
    };
  }

  private toCell(cell: Record<string, unknown>): RecordCell {
    const text = cell['t'] ?? cell['text'] ?? cell['value'] ?? cell['label'] ?? '';
    const align = (cell['a'] ?? cell['align'] ?? 'left') as RecordCell['align'];
    const tag = (cell['tag'] ?? cell['tag_class'] ?? '') as TagClass | '';
    return {
      t: text === null || text === undefined ? '' : String(text),
      align: align === 'right' || align === 'center' ? align : 'left',
      bold: !!(cell['b'] ?? cell['bold']),
      muted: !!(cell['m'] ?? cell['muted']),
      tag,
    };
  }

  openRow(row: RecordRow): void {
    const def = this.def();
    const line = row as Line;
    if (!def?.detail || !line.record) return;
    const route = def.detail(line.record);
    if (route) void this.router.navigate(route);
  }

  // ── filter, ordering, paging ──────────────────────────────────────────────

  onFilter(value: string): void {
    this.filterText.set(value);
    if (this.filterTimer) clearTimeout(this.filterTimer);
    this.filterTimer = setTimeout(() => {
      this.page.set(1);
      this.search.set(value.trim());
    }, 260);
  }

  onOrdering(value: string): void {
    this.page.set(1);
    this.ordering.set(value);
  }

  prevPage(): void {
    if (this.page() > 1) this.page.update((page) => page - 1);
  }

  nextPage(): void {
    if (this.page() < this.pageCount()) this.page.update((page) => page + 1);
  }

  // ── create / export modal ─────────────────────────────────────────────────

  openCreate(): void {
    const def = this.def();
    if (!def) return;
    this.openForm('create', def.formKey);
  }

  openExport(): void {
    const def = this.def();
    // The design opens the view's own form for audit and profitability.
    const own = !!def && (def.key === 'audit' || def.key === 'profitability');
    this.openForm(own ? 'create' : 'export', own ? def!.formKey : 'export');
  }

  private openForm(kind: 'create' | 'export', key: string): void {
    this.formError.set('');
    this.modalRef()?.values.set({});
    this.form.set(DESIGN_FORMS[key] ?? DESIGN_FORMS['export']);
    this.modalKind.set(kind);
    // The server owns the form config where it publishes one.
    this.api.get<FormConfig>(`/forms/${key}/`).subscribe({
      next: (config) => {
        if (this.modalKind() && config?.fields?.length) this.form.set(config);
      },
      error: () => { /* the bundled design config stands in */ },
    });
  }

  closeForm(): void {
    this.modalKind.set(null);
    this.submitting.set(false);
    this.formError.set('');
    this.modalRef()?.values.set({});
  }

  submitForm(values: Record<string, string>): void {
    const def = this.def();
    const kind = this.modalKind();
    if (!def || !kind) return;

    this.submitting.set(true);
    this.formError.set('');

    if (kind === 'export') {
      this.api.post<{ toast?: string }>('/exports/', {
        kind: 'records',
        format: values['format'] || 'CSV',
        records: values['records'] || 'This view',
        destination: values['dest'] || 'Document storage',
        note: values['note'] || '',
        view: def.key,
      }).subscribe({
        next: (response) => {
          this.toast.show(response?.toast || EXPORT_TOAST);
          this.closeForm();
        },
        error: (error: unknown) => this.failed(error),
      });
      return;
    }

    if (def.createMode === 'action') {
      this.api.post<{ toast?: string }>(def.actionPath ?? def.endpoint, values).subscribe({
        next: (response) => {
          this.toast.show(response?.toast || this.createdToast());
          this.closeForm();
          this.reload();
        },
        error: (error: unknown) => this.failed(error),
      });
      return;
    }

    this.api.post<{ toast?: string }>(def.endpoint, this.payload(def, values)).subscribe({
      next: (response) => {
        this.toast.show(response?.toast || this.createdToast());
        this.closeForm();
        this.page.set(1);
        this.reload();
      },
      error: (error: unknown) => this.failed(error),
    });
  }

  /** Design keys plus their model-field aliases; money strings become numbers. */
  private payload(def: RecordViewDef, values: Record<string, string>): Record<string, unknown> {
    const map = FIELD_MAP[def.formKey] ?? {};
    const body: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(values)) {
      if (value === '' || value === null || value === undefined) continue;
      const money = MONEY_KEYS.has(key) ? parseMoney(value) : null;
      body[key] = money ?? value;
      const alias = map[key];
      if (alias) body[alias] = money ?? value;
    }
    return body;
  }

  private createdToast(): string {
    const title = this.form()?.title ?? 'Record';
    const noun = title.replace('New ', '').replace('Initiate ', '');
    return `${noun} created. Inherited fields were carried over, and the record is now `
      + 'searchable and auditable.';
  }

  private failed(error: unknown): void {
    this.submitting.set(false);
    if (error instanceof HttpErrorResponse) {
      const toastText = (error.error as { toast?: string } | null)?.toast;
      if (toastText) {
        this.toast.show(toastText);
        this.formError.set(toastText);
        return;
      }
      if (error.status === 403) {
        const note = 'Your role cannot make this change. The action was refused by the server.';
        this.formError.set(this.detailOf(error) || note);
        return;
      }
      this.formError.set(this.detailOf(error) || 'The record could not be saved.');
      return;
    }
    this.formError.set('The record could not be saved.');
  }

  /** Pulls DRF's `detail` string, or its first field error, out of a response. */
  private detailOf(error: unknown): string {
    if (!(error instanceof HttpErrorResponse)) return '';
    const body = error.error as Record<string, unknown> | string | null;
    if (!body) return '';
    if (typeof body === 'string') return '';
    const detail = body['detail'];
    if (typeof detail === 'string') return detail;
    for (const [field, value] of Object.entries(body)) {
      if (Array.isArray(value) && value.length && typeof value[0] === 'string') {
        return `${field}: ${value[0]}`;
      }
      if (typeof value === 'string') return `${field}: ${value}`;
    }
    return '';
  }
}

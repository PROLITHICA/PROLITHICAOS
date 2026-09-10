import { ThemeColorPipe } from '../../shared/ui/theme-color.pipe';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { forkJoin, of, switchMap } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { HasPermDirective } from '../../core/has-perm.directive';
import { PageTitleService } from '../../core/page-title.service';
import { PermissionService } from '../../core/permission.service';
import { ToastService } from '../../core/toast.service';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { FieldSpec } from '../../shared/ui/field/field.component';
import { ModalComponent } from '../../shared/ui/modal/modal.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';
import { resolveProjectId } from './project.lookup';
import {
  CostChart, DeliveryAction, MarginChart, ProgressUpdate, ProjectDetail, ProjectDocument,
  OptionRow, ProjectEditable, ProjectFigure, ProjectFormOptions, ProjectPhase,
} from './project.models';

/** Figures that carry money, and so hide entirely without `project_financials`. */
const MONEY_FIGURES = new Set(['Contract value', 'Invoiced', 'Actual cost', 'Gross margin']);

interface PhaseView extends ProjectPhase {
  bg: string; col: string; border: string; barBg: string; barCol: string; barW: string;
}

/** The project screen (design lines 418–593), routed as `/projects/:ref`. */
@Component({
  selector: 'app-project',
  standalone: true,
  imports: [ThemeColorPipe, FormsModule, HasPermDirective, SkeletonComponent, EmptyStateComponent,
    ModalComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './project.component.html',
  styleUrl: './project.component.css',
})
export class ProjectComponent {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly toasts = inject(ToastService);
  private readonly auth = inject(AuthService);
  readonly perms = inject(PermissionService);
  private readonly titles = inject(PageTitleService);

  readonly loading = signal(true);
  readonly error = signal('');
  readonly project = signal<ProjectDetail | null>(null);
  readonly docs = signal<ProjectDocument[]>([]);
  readonly docCount = signal(0);
  readonly draft = signal('');
  readonly postBusy = signal(false);
  readonly stageBusy = signal(false);

  readonly ref = signal('');
  readonly projectId = signal('');

  // ── Editing ───────────────────────────────────────────────────────────
  readonly editing = signal(false);
  readonly editBusy = signal(false);
  readonly options = signal<ProjectFormOptions | null>(null);
  readonly editable = signal<ProjectEditable | null>(null);
  readonly editReady = computed(() => !!this.editable() && !!this.options());

  readonly canEdit = computed(
    () => this.perms.can('assigned_projects', 'full') || this.perms.can('delivery', 'full'),
  );

  readonly seesMoney = computed(() => this.perms.can('project_financials', 'restricted'));

  readonly person = computed(() => this.auth.currentUser()?.display_name ?? '');
  readonly personTitle = computed(() => this.auth.currentUser()?.job_title ?? '');

  /** Money tiles disappear rather than render `R ••••` for a role that may not see them. */
  readonly figures = computed<ProjectFigure[]>(() => {
    const all = this.project()?.figures ?? [];
    return this.seesMoney() ? all : all.filter((f) => !MONEY_FIGURES.has(f.label));
  });

  readonly marginChart = computed<MarginChart | null>(() => this.project()?.margin_chart ?? null);
  readonly costChart = computed<CostChart | null>(() => this.project()?.cost_chart ?? null);
  readonly updates = computed<ProgressUpdate[]>(() => this.project()?.updates ?? []);

  readonly phases = computed<PhaseView[]>(() => {
    const project = this.project();
    if (!project) return [];
    const current = project.phase_index;
    return (project.phases ?? []).map((phase) => ({
      ...phase,
      bg: phase.index === current ? 'var(--pl-color-f4f4f4)' : 'var(--pl-color-ffffff)',
      col: phase.index > current ? 'var(--pl-color-8a8a8a)' : 'var(--pl-color-111111)',
      border: phase.index === current ? 'var(--pl-color-111111)' : 'var(--pl-color-e7e7e7)',
      barBg: 'var(--pl-color-efefef)',
      barCol: phase.index > current ? 'var(--pl-color-efefef)' : 'var(--pl-color-111111)',
      barW: phase.bar_width,
    }));
  });

  readonly docCountLabel = computed(() => {
    const count = this.docCount();
    return `${count} document${count === 1 ? '' : 's'}`;
  });

  /** Cumulative-cost axis labels sit at 40 + 68·i, with the forecast tick at 420. */
  readonly costLabels = computed(() => {
    const labels = this.costChart()?.labels ?? [];
    return labels.map((label, index) => ({
      label,
      x: index === labels.length - 1 && labels.length > 1 ? 420 : 40 + index * 68,
    }));
  });

  readonly axisLabels = computed(() => {
    const chart = this.costChart();
    const axis = chart?.axis ?? [];
    const grid = chart?.grid ?? [];
    return axis.map((text, index) => ({
      text,
      x: index === 0 ? 4 : 10,
      y: (grid[index] ?? 20 + index * 38) + 4,
    }));
  });

  constructor() {
    this.route.paramMap
      .pipe(
        map((params) => params.get('ref') ?? ''),
        switchMap((ref) => {
          this.ref.set(ref);
          this.loading.set(true);
          this.error.set('');
          return resolveProjectId(this.api, ref).pipe(
            switchMap((id) =>
              forkJoin({
                project: this.api.get<ProjectDetail>(`/projects/${id}/`),
                documents: this.api
                  .list<ProjectDocument>('/documents/', { project: id, page_size: 4 })
                  .pipe(catchError(() => of({ count: 0, next: null, previous: null, results: [] }))),
              }),
            ),
            catchError((error: unknown) => {
              this.error.set(this.message(error));
              return of(null);
            }),
          );
        }),
      )
      .subscribe((payload) => {
        this.loading.set(false);
        if (!payload) return;
        this.project.set(payload.project);
        this.projectId.set(payload.project.id ?? '');
        this.titles.set(`${payload.project.name} · ${payload.project.ref}`);
        this.docs.set(payload.documents.results ?? []);
        this.docCount.set(payload.documents.count ?? (payload.documents.results ?? []).length);
      });
  }

  // ── stage stepper ────────────────────────────────────────────────────
  setPhase(index: number): void {
    const project = this.project();
    if (!project || this.stageBusy()) return;
    if (index < 0 || index >= (project.phases?.length || 5)) return;
    this.stageBusy.set(true);
    this.api
      .post<DeliveryAction<ProjectDetail>>(`/projects/${project.id}/phase/`, { index })
      .subscribe({
        next: (response) => {
          this.stageBusy.set(false);
          if (response.record) this.project.set(response.record);
          this.toasts.show(response.toast);
        },
        error: (error: unknown) => {
          this.stageBusy.set(false);
          this.toasts.show(this.message(error));
        },
      });
  }

  stageNext(): void {
    const project = this.project();
    if (project) this.setPhase(Math.min((project.phases?.length || 5) - 1, project.phase_index + 1));
  }

  stageBack(): void {
    const project = this.project();
    if (project) this.setPhase(Math.max(0, project.phase_index - 1));
  }

  // ── progress updates ─────────────────────────────────────────────────
  onDraft(value: string): void {
    this.draft.set(value);
  }

  postUpdate(): void {
    const project = this.project();
    const text = this.draft().trim();
    if (!project || this.postBusy()) return;
    if (!text) {
      this.toasts.show('Write something first — an empty update is not worth a record.');
      return;
    }
    this.postBusy.set(true);
    this.api
      .post<DeliveryAction<ProgressUpdate>>(`/projects/${project.id}/progress-updates/`, { text })
      .subscribe({
        next: (response) => {
          this.postBusy.set(false);
          this.draft.set('');
          if (response.record) {
            this.project.set({ ...project, updates: [response.record, ...project.updates] });
          }
          this.toasts.show(response.toast);
        },
        error: (error: unknown) => {
          this.postBusy.set(false);
          this.toasts.show(this.message(error));
        },
      });
  }

  // ── navigation ───────────────────────────────────────────────────────
  goLifecycle(): void {
    void this.router.navigate(['/lifecycle']);
  }

  goCause(): void {
    void this.router.navigate(['/projects', this.ref() || this.project()?.ref || '', 'cause']);
  }

  goDocs(): void {
    void this.router.navigate(['/documents']);
  }

  reload(): void {
    void this.router.navigate([], { relativeTo: this.route, queryParams: {}, replaceUrl: true })
      .then(() => window.location.reload());
  }

  // ── Editing ───────────────────────────────────────────────────────────
  /** Fields for the edit sheet, using real records wherever a record exists. */
  readonly editFields = computed<FieldSpec[]>(() => {
    const options = this.options();
    const stages = options?.stages ?? [];
    const fields: FieldSpec[] = [
      { k: 'name', l: 'Project name', p: 'e.g. Committee analytics portal' },
      { k: 'manager_name', l: 'Project manager',
        o: (options?.managers ?? []).map((m) => m.label) },
      { k: 'stage', l: 'Delivery stage', o: stages },
      { k: 'completion', l: 'Completion %', p: '62' },
      { k: 'health', l: 'Health', o: options?.health ?? [] },
      { k: 'state', l: 'State', o: (options?.states ?? []).map((s) => s.label) },
    ];
    if (this.seesMoney()) {
      fields.push(
        { k: 'contract_value', l: 'Contract value (R)', p: '15200000' },
        { k: 'budget_planned', l: 'Budget planned (R)', p: '9600000' },
        { k: 'budget_spent', l: 'Budget spent (R)', p: '7800000' },
        { k: 'margin_actual', l: 'Margin now %', p: '21' },
        { k: 'margin_planned', l: 'Margin planned %', p: '34' },
      );
    }
    return fields;
  });

  /** The record's own writable values, loaded when the sheet opens. */
  readonly editInitial = computed<Record<string, string>>(() => {
    const raw = this.editable();
    if (!raw) return {};
    const values: Record<string, string> = {
      name: raw.name ?? '',
      manager_name: this.labelFor(this.options()?.managers, raw.manager),
      stage: raw.stage ?? '',
      completion: String(raw.completion ?? ''),
      health: raw.health ?? '',
      state: this.labelFor(this.options()?.states, raw.state),
    };
    if (this.seesMoney()) {
      values['contract_value'] = this.plain(raw.contract_value);
      values['budget_planned'] = this.plain(raw.budget_planned);
      values['budget_spent'] = this.plain(raw.budget_spent);
      values['margin_actual'] = this.plain(raw.margin_actual);
      values['margin_planned'] = this.plain(raw.margin_planned);
    }
    return values;
  });

  openEdit(): void {
    const id = this.projectId();
    if (!id) return;
    this.editable.set(null);
    if (!this.options()) {
      this.api.get<ProjectFormOptions>('/projects/form-options/')
        .subscribe({ next: (o) => this.options.set(o), error: () => this.options.set(null) });
    }
    this.api.get<ProjectEditable>(`/projects/${id}/editable/`).subscribe({
      next: (raw) => {
        this.editable.set(raw);
        this.editing.set(true);
      },
      error: () => this.toasts.show('Your role cannot edit this project.'),
    });
  }

  closeEdit(): void {
    this.editing.set(false);
  }

  saveEdit(values: Record<string, string>): void {
    const id = this.projectId();
    if (!id || this.editBusy()) return;

    const body: Record<string, unknown> = {};
    const put = (key: string, value: unknown) => {
      if (value !== '' && value !== undefined && value !== null) body[key] = value;
    };

    put('name', values['name']?.trim());
    put('stage', values['stage']);
    put('health', values['health']);
    if (values['completion'] !== undefined && values['completion'] !== '') {
      body['completion'] = Number(values['completion']);
    }

    const manager = (this.options()?.managers ?? [])
      .find((m) => m.label === values['manager_name']);
    if (manager) body['manager'] = manager.value;

    const state = (this.options()?.states ?? []).find((s) => s.label === values['state']);
    if (state) body['state'] = state.value;

    for (const key of ['contract_value', 'budget_planned', 'budget_spent',
                       'margin_actual', 'margin_planned']) {
      const raw = values[key];
      if (raw !== undefined && raw !== '') body[key] = this.number(raw);
    }

    this.editBusy.set(true);
    this.api.patch<{ record: ProjectDetail; toast: string }>(`/projects/${id}/`, body)
      .subscribe({
        next: (response) => {
          this.editBusy.set(false);
          this.editing.set(false);
          this.project.set(response.record);
          this.titles.set(`${response.record.name} · ${response.record.ref}`);
          this.toasts.show(response.toast);
        },
        error: (error: unknown) => {
          this.editBusy.set(false);
          this.toasts.show(this.fieldError(error));
        },
      });
  }

  private labelFor(rows: OptionRow[] | undefined, value: unknown): string {
    return (rows ?? []).find((row) => row.value === String(value ?? ''))?.label ?? '';
  }

  /** Money and percentages come back as display strings; edit them as plain numbers. */
  private plain(value: unknown): string {
    if (value === null || value === undefined) return '';
    return String(value).replace(/[^0-9.\-]/g, '');
  }

  private number(raw: string): number | string {
    const cleaned = raw.replace(/[^0-9.\-]/g, '');
    return cleaned === '' ? raw : cleaned;
  }

  private fieldError(error: unknown): string {
    const body = (error as { error?: Record<string, unknown> })?.error;
    if (body && typeof body === 'object') {
      for (const [key, value] of Object.entries(body)) {
        if (Array.isArray(value) && value.length) return `${key}: ${String(value[0])}`;
        if (typeof value === 'string' && key === 'detail') return value;
      }
    }
    return 'That change could not be saved.';
  }

  private message(error: unknown): string {
    const detail = (error as { error?: { detail?: string; toast?: string }; message?: string });
    return detail?.error?.toast || detail?.error?.detail || detail?.message
      || 'This project could not be loaded.';
  }
}

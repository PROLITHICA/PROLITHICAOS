import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { forkJoin, of, switchMap } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { HasPermDirective } from '../../core/has-perm.directive';
import { PermissionService } from '../../core/permission.service';
import { ToastService } from '../../core/toast.service';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';
import { resolveProjectId } from './project.lookup';
import {
  CostChart, DeliveryAction, MarginChart, ProgressUpdate, ProjectDetail, ProjectDocument,
  ProjectFigure, ProjectPhase,
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
  imports: [FormsModule, HasPermDirective, SkeletonComponent, EmptyStateComponent],
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

  readonly loading = signal(true);
  readonly error = signal('');
  readonly project = signal<ProjectDetail | null>(null);
  readonly docs = signal<ProjectDocument[]>([]);
  readonly docCount = signal(0);
  readonly draft = signal('');
  readonly postBusy = signal(false);
  readonly stageBusy = signal(false);

  readonly ref = signal('');

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
      bg: phase.index === current ? '#f4f4f4' : '#fff',
      col: phase.index > current ? '#8a8a8a' : '#111',
      border: phase.index === current ? '#111' : '#e7e7e7',
      barBg: '#efefef',
      barCol: phase.index > current ? '#efefef' : '#111',
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

  private message(error: unknown): string {
    const detail = (error as { error?: { detail?: string; toast?: string }; message?: string });
    return detail?.error?.toast || detail?.error?.detail || detail?.message
      || 'This project could not be loaded.';
  }
}

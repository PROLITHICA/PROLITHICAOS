import { ThemeColorPipe } from '../../shared/ui/theme-color.pipe';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { of, switchMap } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import { ApiService } from '../../core/api.service';
import { ToastService } from '../../core/toast.service';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';
import { resolveProjectId } from '../project/project.lookup';

export interface MarginCause {
  id: string;
  impact: string;
  impact_points: string;
  w: string;
  weight: number;
  title: string;
  body: string;
  meta: string;
  step_label: string;
  order: number;
}

export interface WaterfallBar {
  label: string;
  value: number;
  drop?: number;
  kind: 'plan' | 'step' | 'actual';
}

export interface CauseAction {
  id: string;
  label: string;
  btn_class: string;
  toast: string;
}

export interface CauseScreen {
  project: string;
  title: string;
  subtitle: string;
  causes: MarginCause[];
  planned_to_actual: { title: string; subtitle: string; bars: WaterfallBar[] };
  actions: CauseAction[];
}

/** One rendered rectangle of the "Planned to actual" waterfall. */
interface Column {
  label: string;
  labelX: number;
  x: number;
  width: number;
  solidY: number;
  solidHeight: number;
  ghostY?: number;
  ghostHeight?: number;
  value?: string;
  valueX?: number;
  valueY?: number;
}

/** Design geometry: the plan bar tops at y=40, the actual bar at y=94, floor y=150. */
const PLAN_TOP = 40;
const ACTUAL_TOP = 94;
const FLOOR = 150;

/** "Why the LIMS margin is falling" (design lines 593–644), `/projects/:ref/cause`. */
@Component({
  selector: 'app-cause',
  standalone: true,
  imports: [ThemeColorPipe, SkeletonComponent, EmptyStateComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './cause.component.html',
  styleUrl: './cause.component.css',
})
export class CauseComponent {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly toasts = inject(ToastService);

  readonly loading = signal(true);
  readonly error = signal('');
  readonly screen = signal<CauseScreen | null>(null);
  readonly busy = signal('');
  readonly ref = signal('');

  readonly causes = computed<MarginCause[]>(() => this.screen()?.causes ?? []);
  readonly actions = computed<CauseAction[]>(() => this.screen()?.actions ?? []);
  readonly waterfall = computed(() => this.screen()?.planned_to_actual ?? null);

  /**
   * The design draws plan → three steps → now. Step drops share the 54px between
   * the plan top and the actual top in proportion to the points they account for,
   * which reproduces the design's 24 / 18 / 12 exactly.
   */
  readonly columns = computed<Column[]>(() => {
    const bars = this.waterfall()?.bars ?? [];
    if (!bars.length) return [];
    const steps = bars.filter((bar) => bar.kind === 'step');
    const totalDrop = steps.reduce((sum, bar) => sum + (bar.drop ?? 0), 0) || 1;
    const span = ACTUAL_TOP - PLAN_TOP;
    const columns: Column[] = [];
    let top = PLAN_TOP;
    let stepIndex = 0;

    for (const bar of bars) {
      if (bar.kind === 'plan') {
        columns.push({
          label: bar.label, labelX: 34, x: 30, width: 46,
          solidY: PLAN_TOP, solidHeight: FLOOR - PLAN_TOP,
          value: `${Math.round(bar.value)}%`, valueX: 42, valueY: PLAN_TOP - 6,
        });
      } else if (bar.kind === 'step') {
        const height = Math.round(((bar.drop ?? 0) / totalDrop) * span);
        const x = 94 + stepIndex * 52;
        columns.push({
          label: bar.label, labelX: x + 2, x, width: 34,
          solidY: top, solidHeight: height,
          ghostY: top + height, ghostHeight: FLOOR - (top + height),
        });
        top += height;
        stepIndex += 1;
      } else {
        columns.push({
          label: bar.label, labelX: 252, x: 250, width: 46,
          solidY: ACTUAL_TOP, solidHeight: FLOOR - ACTUAL_TOP,
          value: `${Math.round(bar.value)}%`, valueX: 258, valueY: ACTUAL_TOP - 6,
        });
      }
    }
    return columns;
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
            switchMap((id) => this.api.get<CauseScreen>(`/projects/${id}/margin-causes/`)),
            catchError((error: unknown) => {
              this.error.set(this.message(error));
              return of(null);
            }),
          );
        }),
      )
      .subscribe((screen) => {
        this.loading.set(false);
        if (screen) this.screen.set(screen);
      });
  }

  /** Each action writes back to contract, project or billing. */
  act(action: CauseAction): void {
    if (this.busy()) return;
    this.busy.set(action.id);
    this.api.post<{ toast?: string }>(`/margin-causes/${action.id}/act/`, {}).subscribe({
      next: (response) => {
        this.busy.set('');
        this.toasts.show(response?.toast || action.toast);
      },
      error: () => {
        this.busy.set('');
        this.toasts.show(action.toast);
      },
    });
  }

  backToProject(): void {
    void this.router.navigate(['/projects', this.ref() || this.screen()?.project || '']);
  }

  private message(error: unknown): string {
    const detail = (error as { error?: { detail?: string }; message?: string });
    return detail?.error?.detail || detail?.message
      || 'The margin decomposition for this project is not available to your role.';
  }
}

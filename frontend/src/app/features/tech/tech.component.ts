import { ThemeColorPipe } from '../../shared/ui/theme-color.pipe';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { of } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { ApiService } from '../../core/api.service';
import { HasPermDirective } from '../../core/has-perm.directive';
import { ToastService } from '../../core/toast.service';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';

export interface DeskTask {
  id: string;
  ref: string;
  text: string;
  meta: string;
  project_label: string;
  project_ref: string;
  done: boolean;
  tag_class: string;
}

export interface Burndown {
  title: string;
  subtitle: string;
  points: string;
  forecast: string;
  labels: string[];
}

export interface Incident {
  id: string;
  ref: string;
  title: string;
  detail_title: string;
  meta: string;
  severity: string;
  severity_tag_class: string;
  sla_remaining: string;
  sla_pct: number;
  sla_col: string;
}

export interface TraceRow {
  id: string;
  ref_id: string;
  text: string;
  came_from: string;
  impl: string;
  test: string;
  accepted: string;
  tag_class: string;
}

export interface Commercial {
  money_shown: boolean;
  restricted_body: string;
  restricted_note: string;
  granted_body: string;
  granted_note: string;
}

export interface TechDesk {
  title: string;
  subtitle: string;
  tasks: DeskTask[];
  burndown: Burndown;
  incidents: Incident[];
  commercial: Commercial;
  trace: TraceRow[];
}

/** Engineering desk (design lines 801–886), served by `dashboard/tech/`. */
@Component({
  selector: 'app-tech',
  standalone: true,
  imports: [ThemeColorPipe, HasPermDirective, SkeletonComponent, EmptyStateComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './tech.component.html',
  styleUrl: './tech.component.css',
})
export class TechComponent {
  private readonly api = inject(ApiService);
  private readonly toasts = inject(ToastService);

  readonly loading = signal(true);
  readonly error = signal('');
  readonly desk = signal<TechDesk | null>(null);
  readonly busy = signal('');

  readonly tasks = computed(() =>
    (this.desk()?.tasks ?? []).map((task) => ({
      ...task,
      fill: task.done ? 'var(--pl-color-3d3d3d)' : 'transparent',
      strike: task.done ? 'line-through' : 'none',
      textCol: task.done ? 'var(--pl-color-9a9a9a)' : 'var(--pl-color-111111)',
    })),
  );

  readonly incidents = computed(() =>
    (this.desk()?.incidents ?? []).map((incident) => ({
      ...incident,
      heading: incident.detail_title || incident.title,
      slaW: `${incident.sla_pct}%`,
    })),
  );

  readonly trace = computed<TraceRow[]>(() => this.desk()?.trace ?? []);
  readonly burndown = computed<Burndown | null>(() => this.desk()?.burndown ?? null);
  readonly commercial = computed<Commercial | null>(() => this.desk()?.commercial ?? null);

  /** D1 / D4 / D7 / D10 sit at 34, 128, 222, 316 in the design. */
  readonly burndownLabels = computed(() =>
    (this.burndown()?.labels ?? []).map((label, index) => ({ label, x: 34 + index * 94 })),
  );

  constructor() {
    this.load();
  }

  private load(): void {
    this.loading.set(true);
    this.error.set('');
    this.api
      .get<TechDesk>('/dashboard/tech/')
      .pipe(
        catchError((error: unknown) => {
          const detail = error as { error?: { detail?: string }; message?: string };
          this.error.set(
            detail?.error?.detail || detail?.message || 'The engineering desk could not load.',
          );
          return of(null);
        }),
      )
      .subscribe((desk) => {
        this.loading.set(false);
        if (desk) this.desk.set(desk);
      });
  }

  /** Closing a task updates its requirement, milestone and project completion. */
  toggle(task: DeskTask): void {
    if (this.busy()) return;
    this.busy.set(task.id);
    this.api
      .post<{ record: DeskTask; toast?: string }>(`/tasks/${task.id}/toggle/`, {})
      .subscribe({
        next: (response) => {
          this.busy.set('');
          const desk = this.desk();
          if (desk && response.record) {
            this.desk.set({
              ...desk,
              tasks: desk.tasks.map((row) => (row.id === task.id ? response.record : row)),
            });
          }
          this.toasts.show(response.toast);
        },
        error: () => {
          this.busy.set('');
          this.toasts.show('That task could not be updated.');
        },
      });
  }

  reload(): void {
    this.load();
  }
}

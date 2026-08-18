import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { of, switchMap } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import { ApiService } from '../../core/api.service';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';

export interface StageField { label: string; value: string; }
export interface StageInherit { text: string; from: string; }

export interface LifecycleStage {
  step: string;
  position: number;
  label: string;
  ref: string;
  kicker: string;
  title: string;
  body: string;
  fields: StageField[];
  inherits: StageInherit[];
  /** `[["Mar 2024", "Organisation created"], …]` as stored by crm.LifecycleStage. */
  activity: Array<[string, string]>;
}

export interface LifecycleScreen {
  organisation: { ref: string; name: string; list_name: string };
  title: string;
  subtitle: string;
  stages: LifecycleStage[];
}

/** The engagement the design walks when no organisation is named on the route. */
const DEFAULT_ORG = 'ORG-006';

/** "One record, six lives" (design 644–700), `/lifecycle` and `/lifecycle/:orgRef`. */
@Component({
  selector: 'app-lifecycle',
  standalone: true,
  imports: [SkeletonComponent, EmptyStateComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './lifecycle.component.html',
  styleUrl: './lifecycle.component.css',
})
export class LifecycleComponent {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);

  readonly loading = signal(true);
  readonly error = signal('');
  readonly screen = signal<LifecycleScreen | null>(null);
  readonly active = signal(0);

  readonly stages = computed<LifecycleStage[]>(() => this.screen()?.stages ?? []);

  readonly rail = computed(() =>
    this.stages().map((stage, index) => ({
      ...stage,
      index,
      bg: index === this.active() ? '#f7f7f7' : '#fff',
      rule: index === this.active() ? '#3d3d3d' : '#e7e7e7',
      col: index === this.active() ? '#111' : '#333',
    })),
  );

  readonly stage = computed<LifecycleStage | null>(() => this.stages()[this.active()] ?? null);

  /** The first stage inherits nothing — the design says so in words. */
  readonly inherits = computed<StageInherit[]>(() => {
    const stage = this.stage();
    if (!stage) return [];
    return stage.inherits?.length
      ? stage.inherits
      : [{ text: 'Nothing — this is where the relationship begins', from: 'first contact' }];
  });

  readonly activity = computed(() =>
    (this.stage()?.activity ?? []).map((row) => ({ when: row[0], what: row[1] })),
  );

  constructor() {
    this.route.paramMap
      .pipe(
        map((params) => params.get('orgRef') || DEFAULT_ORG),
        switchMap((orgRef) => {
          this.loading.set(true);
          this.error.set('');
          return this.api.get<LifecycleScreen>(`/lifecycle/${orgRef}/`).pipe(
            catchError((error: unknown) => {
              this.error.set(this.message(error));
              return of(null);
            }),
          );
        }),
      )
      .subscribe((screen) => {
        this.loading.set(false);
        if (screen) {
          this.screen.set(screen);
          this.active.set(0);
        }
      });
  }

  select(index: number): void {
    this.active.set(index);
  }

  private message(error: unknown): string {
    const detail = (error as { error?: { detail?: string }; message?: string });
    return detail?.error?.detail || detail?.message
      || 'That engagement has no recorded lifecycle trace.';
  }
}

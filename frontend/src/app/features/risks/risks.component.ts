import { ThemeColorPipe } from '../../shared/ui/theme-color.pipe';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { Paginated, ViewConfig } from '../../core/models';
import { ToastService } from '../../core/toast.service';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';
import { TagComponent } from '../../shared/ui/tag/tag.component';

/** One row of `GET /api/risks/`, as apps/delivery/serializers.RiskSerializer emits it. */
export interface RiskAction {
  id: string;
  label: string;
  btn_class?: string;
  route?: string;
  toast?: string;
}

export interface Risk {
  id: string;
  ref: string;
  severity: string;
  tag_class: string;
  title: string;
  body: string;
  owner_display: string;
  exposure: string;
  probability?: number;
  impact?: number;
  /** of the 200-unit bar the design draws */
  bar_width: number;
  bar_col: string;
  raised: string;
  cta: string;
  route: string;
  open?: boolean;
  actions?: RiskAction[];
}

/** The risk register: three projects whose risk has become commercial. */
@Component({
  selector: 'app-risks',
  standalone: true,
  imports: [ThemeColorPipe, TagComponent, SkeletonComponent, EmptyStateComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="title-block">
      <h1 class="title">{{ view()?.title || 'Risk register' }}</h1>
      <div class="sub">{{ view()?.subtitle || '' }}</div>
    </div>

    @if (loading()) {
      <div class="grid">
        @for (slot of [1, 2, 3]; track slot) { <app-skeleton height="250px" /> }
      </div>
    } @else if (failed()) {
      <div class="body">
        <app-empty-state
          heading="The risk register could not be loaded"
          note="Reading the register means reading company performance. Ask your administrator for a temporary grant — every grant is audited."
          actionLabel="Try again"
          (action)="load()" />
      </div>
    } @else if (!risks().length) {
      <div class="body">
        <app-empty-state
          heading="No open risks"
          note="Nothing on the register has been raised against the projects you can see." />
      </div>
    } @else {
      <div class="grid">
        @for (risk of risks(); track risk.id) {
          <div class="risk">
            <div class="risk-top">
              <app-tag [text]="risk.severity" [tagClass]="risk.tag_class" />
              <span class="raised">{{ risk.raised }}</span>
            </div>
            <h4 class="risk-title">{{ risk.title }}</h4>
            <p class="risk-body">{{ risk.body }}</p>
            <div class="risk-meta">
              <span>Owner {{ risk.owner_display }}</span>
              <span>Exposure {{ risk.exposure }}</span>
            </div>
            <div>
              <div class="risk-scale">Probability × impact</div>
              <svg viewBox="0 0 200 10" width="100%" height="10" aria-hidden="true">
                <rect x="0" y="3" width="200" height="4" fill="var(--pl-color-f0f0f0)" rx="2" />
                <rect x="0" y="3" [attr.width]="risk.bar_width" height="4" [attr.fill]="(risk.bar_col) | themeColor" rx="2" />
              </svg>
            </div>
            <button type="button" class="btn btn-secondary risk-cta" (click)="open(risk)">
              {{ risk.cta }}
            </button>
          </div>
        }
      </div>
    }
  `,
  styles: [`
    :host { display: flex; flex-direction: column; gap: var(--pl-pane-gap); }
    .title { font-size: 28px; margin: 0 0 4px; }
    .sub { font-size: 12.5px; color: var(--pl-color-8a8a8a); max-width: 74ch; }
    .grid {
      display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: var(--pl-pane-gap);
    }
    .risk {
      border: 0; border-radius: var(--pl-radius-card); padding: var(--pl-pane-pad);
      display: flex; flex-direction: column; gap: 10px;
      background: var(--pl-pane); box-shadow: var(--pl-lift-1);
    }
    .risk-top { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
    .raised { font-size: 11px; color: var(--pl-color-9a9a9a); }
    .risk-title { margin: 0; font-size: 16px; }
    .risk-body { margin: 0; font-size: 12.5px; color: var(--pl-color-4a4a4a); }
    .risk-meta { display: flex; gap: 16px; flex-wrap: wrap; font-size: 11.5px; color: var(--pl-color-8a8a8a); }
    .risk-scale { font-size: 10.5px; color: var(--pl-color-9a9a9a); margin-bottom: 4px; }
    .risk-cta { border-color: var(--pl-color-b5b5b5); margin-top: auto; }
    @media (max-width: 1100px) { .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
    @media (max-width: 720px) { .grid { grid-template-columns: minmax(0, 1fr); } }
  `],
})
export class RisksComponent {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  private readonly toast = inject(ToastService);

  private readonly page = signal<Paginated<Risk> | null>(null);
  readonly loading = signal(true);
  readonly failed = signal(false);

  readonly risks = computed<Risk[]>(() => this.page()?.results ?? []);
  readonly view = computed<ViewConfig | undefined>(() => this.page()?.view);

  constructor() {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.failed.set(false);
    this.api.list<Risk>('/risks/', { page_size: 50 }).subscribe({
      next: (page) => {
        this.page.set(page);
        this.loading.set(false);
      },
      error: () => {
        this.failed.set(true);
        this.loading.set(false);
      },
    });
  }

  open(risk: Risk): void {
    const action = risk.actions?.[0];
    if (!action) {
      if (risk.route) void this.router.navigateByUrl(risk.route);
      return;
    }
    this.api.post<{ toast?: string; route?: string }>(`/risks/${risk.id}/act/`, { action: action.id })
      .subscribe({
        next: (response) => {
          this.toast.show(response?.toast);
          const route = response?.route || action.route || risk.route;
          if (route) void this.router.navigateByUrl(route);
        },
        error: () => {
          if (risk.route) void this.router.navigateByUrl(risk.route);
        },
      });
  }
}

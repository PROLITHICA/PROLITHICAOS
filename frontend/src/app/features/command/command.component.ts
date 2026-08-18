import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { HasPermDirective } from '../../core/has-perm.directive';
import { PermissionService } from '../../core/permission.service';
import { ToastService } from '../../core/toast.service';
import { Bar, BarChartComponent } from '../../shared/ui/bar-chart/bar-chart.component';
import { DonutComponent, DonutSlice } from '../../shared/ui/donut/donut.component';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { KpiCardComponent } from '../../shared/ui/kpi-card/kpi-card.component';
import { LineChartComponent, LineSeries } from '../../shared/ui/line-chart/line-chart.component';
import { ProgressBarComponent } from '../../shared/ui/progress-bar/progress-bar.component';
import { SectionCardComponent } from '../../shared/ui/section-card/section-card.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';
import { SparklineComponent } from '../../shared/ui/sparkline/sparkline.component';
import { TagComponent } from '../../shared/ui/tag/tag.component';
import {
  AttentionItem, CommandKpi, CommandPayload, Decision, DeliveryRow,
} from './command.models';

/** Bar colours per KPI card, copied from the design's four SVGs. */
const BAR_TONES: Record<string, { series: string; forecast: string }> = {
  'Revenue recognised YTD': { series: '#3d3d3d', forecast: '#e4e4e4' },
  'Weighted pipeline': { series: '#c9c9c9', forecast: '#111111' },
  Receivables: { series: '#111111', forecast: '#e4e4e4' },
};
const DEFAULT_TONE = { series: '#3d3d3d', forecast: '#e4e4e4' };

/** Capacity bar tones — the design's `mag` / `ink` / `cy`. */
const CAPACITY_TONES: Record<string, string> = {
  attention: '#111111', ink: '#111111', mid: '#3d3d3d',
};

/** The Command Centre: the executive's first screen. */
@Component({
  selector: 'app-command',
  standalone: true,
  imports: [
    HasPermDirective, KpiCardComponent, BarChartComponent, SparklineComponent,
    LineChartComponent, DonutComponent, ProgressBarComponent, SectionCardComponent,
    TagComponent, SkeletonComponent, EmptyStateComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './command.component.html',
  styleUrl: './command.component.css',
})
export class CommandComponent {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  private readonly toast = inject(ToastService);
  private readonly auth = inject(AuthService);
  readonly perms = inject(PermissionService);

  readonly data = signal<CommandPayload | null>(null);
  readonly loading = signal(true);
  readonly failed = signal(false);
  readonly busy = signal<string>('');

  readonly greeting = computed(() =>
    this.data()?.greeting || `Good morning, ${this.auth.currentUser()?.first_name_only ?? ''}`.trim());
  readonly subtitle = computed(() => this.data()?.subtitle ?? '');
  readonly kpis = computed(() => this.data()?.kpis ?? []);
  readonly attention = computed(() => this.data()?.attention ?? []);
  readonly projects = computed(() => this.data()?.projects ?? []);
  readonly capacity = computed(() => this.data()?.capacity ?? []);
  readonly decisions = computed(() => this.data()?.decisions ?? []);
  readonly ageing = computed(() => this.data()?.ageing ?? null);
  readonly marginNote = computed(() => this.data()?.margin_chart?.note ?? '');

  constructor() {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.failed.set(false);
    this.api.get<CommandPayload>('/dashboard/command/').subscribe({
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

  // ── KPI cards ────────────────────────────────────────────────────────
  /** The cash card has no forecast — the design draws it as a trend line. */
  isTrend(kpi: CommandKpi): boolean {
    return !(kpi.forecast?.length);
  }

  /** The series arrives as design bar heights, so the scale is pinned to 34. */
  bars(kpi: CommandKpi): Bar[] {
    const tone = BAR_TONES[kpi.label] ?? DEFAULT_TONE;
    return [
      ...(kpi.series ?? []).map((value) => ({ value, color: tone.series })),
      ...(kpi.forecast ?? []).map((value) => ({ value, color: tone.forecast })),
    ];
  }

  /** The trend arrives as design y-coordinates; flip them back into values. */
  trend(kpi: CommandKpi): number[] {
    return (kpi.series ?? []).map((value) => 34 - value);
  }

  // ── margin chart ─────────────────────────────────────────────────────
  readonly months = computed(() => this.data()?.margin_chart?.months ?? []);

  readonly marginSeries = computed<LineSeries[]>(() => {
    const chart = this.data()?.margin_chart;
    if (!chart) return [];
    const x = (index: number) => 60 + index * 70;

    // Margin sits on the labelled axis: 40% at y=20, 8 percentage points per 40px.
    const marginY = (value: number) => Math.min(168, Math.max(8, 20 + (40 - value) * 5));
    const marginPts = (chart.margin_pct ?? []).map((v, i) => `${x(i)},${marginY(v).toFixed(0)}`);

    // Cost has no axis of its own; it uses the design's 146→74 band.
    const costs = chart.cost_rm ?? [];
    const min = costs.length ? Math.min(...costs) : 0;
    const max = costs.length ? Math.max(...costs) : 1;
    const span = max - min || 1;
    const costPts = costs.map((v, i) => `${x(i)},${(146 - ((v - min) / span) * 72).toFixed(0)}`);

    const last = marginPts.length - 1;
    const marginDots = marginPts.slice(-2).map((point) => {
      const [cx, cy] = point.split(',');
      return { cx: Number(cx), cy: Number(cy) };
    });
    const costDots = costPts.slice(-1).map((point) => {
      const [cx, cy] = point.split(',');
      return { cx: Number(cx), cy: Number(cy) };
    });

    const series: LineSeries[] = [];
    if (marginPts.length) {
      series.push({
        label: 'Margin %',
        color: '#111111',
        width: 2,
        points: marginPts.join(' '),
        area: `${marginPts.join(' ')} ${x(last)},170 ${x(0)},170`,
        areaFill: '#f4f4f4',
        dots: marginDots,
      });
    }
    if (costPts.length) {
      series.push({
        label: 'Cost R m', color: '#3d3d3d', width: 2, points: costPts.join(' '), dots: costDots,
      });
    }
    return series;
  });

  readonly nowX = computed(() => {
    const chart = this.data()?.margin_chart;
    if (!chart || chart.now_index === undefined || chart.now_index === null) return null;
    return 60 + chart.now_index * 70;
  });

  // ── ageing donut ─────────────────────────────────────────────────────
  readonly ageingSlices = computed<DonutSlice[]>(() =>
    (this.ageing()?.buckets ?? []).map((bucket) => ({
      label: bucket.label, value: bucket.dash, display: bucket.value, color: bucket.tone,
    })),
  );

  // ── delivery rows ────────────────────────────────────────────────────
  budgetColour(row: DeliveryRow): string {
    return row.tag_class === 'tag-accent-2' ? '#111111' : '#3d3d3d';
  }

  progressCaption(row: DeliveryRow): string {
    return `${row.complete} complete · ${row.budget} budget`;
  }

  capacityColour(row: { tone: string }): string {
    return CAPACITY_TONES[row.tone] ?? '#111111';
  }

  // ── navigation and actions ───────────────────────────────────────────
  go(route: string | undefined | null): void {
    if (route) void this.router.navigateByUrl(route);
  }

  openAttention(item: AttentionItem): void {
    this.go(item.route);
  }

  openProject(row: DeliveryRow): void {
    this.go(row.route);
  }

  goRisks(): void {
    void this.router.navigate(['/risks']);
  }

  goLifecycle(): void {
    void this.router.navigate(['/lifecycle']);
  }

  goFinance(): void {
    void this.router.navigate(['/finance']);
  }

  newOpportunity(): void {
    void this.router.navigate(['/records/opportunities'], { queryParams: { new: 1 } });
  }

  /** Decisions post their action; the server hands back the toast copy. */
  decide(decision: Decision): void {
    if (decision.route) {
      this.go(decision.route);
      return;
    }
    this.busy.set(decision.action);
    this.api.post<{ toast?: string }>('/dashboard/command/', { action: decision.action }).subscribe({
      next: (response) => {
        this.busy.set('');
        this.toast.show(response?.toast || decision.toast);
        this.load();
      },
      error: () => {
        this.busy.set('');
        this.toast.show(decision.toast);
      },
    });
  }
}

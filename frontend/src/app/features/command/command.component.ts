import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { HasPermDirective } from '../../core/has-perm.directive';
import { PermissionService } from '../../core/permission.service';
import { ToastService } from '../../core/toast.service';
import { Bar, BarChartComponent } from '../../shared/ui/bar-chart/bar-chart.component';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { KpiCardComponent } from '../../shared/ui/kpi-card/kpi-card.component';
import { ProgressBarComponent } from '../../shared/ui/progress-bar/progress-bar.component';
import { SectionCardComponent } from '../../shared/ui/section-card/section-card.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';
import { SparklineComponent } from '../../shared/ui/sparkline/sparkline.component';
import { TagComponent } from '../../shared/ui/tag/tag.component';
import {
  AttentionItem,
  CommandKpi,
  CommandPayload,
  Decision,
  DeliveryRow,
  KpiBar,
  KpiBars,
  KpiLine,
} from './command.models';

/** Bar colours per KPI card, copied from the design's four SVGs. */

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
    ProgressBarComponent, SectionCardComponent,
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
  /** The server resolves each card's sparkline into the design's own geometry. */
  isBars(kpi: CommandKpi): boolean {
    return (kpi.series as KpiBars)?.kind === 'bars';
  }

  barsOf(kpi: CommandKpi): KpiBar[] {
    return (kpi.series as KpiBars)?.bars ?? [];
  }

  lineOf(kpi: CommandKpi): KpiLine {
    return kpi.series as KpiLine;
  }

  // ── margin chart and ageing donut ────────────────────────────────────
  // Both arrive as the design's own SVG geometry, resolved server-side, so the
  // templates draw them directly rather than re-deriving coordinates here.
  readonly marginChart = computed(() => this.data()?.margin_chart ?? null);

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

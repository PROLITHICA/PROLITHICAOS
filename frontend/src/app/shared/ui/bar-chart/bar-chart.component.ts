import { ThemeColorPipe } from '../theme-color.pipe';
import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

export interface Bar { value: number; color?: string; }

/**
 * The KPI card's 200x34 bar strip: 10px bars on a 16px pitch, bottom-aligned,
 * exactly as the design's revenue / pipeline / receivables cards draw them.
 */
@Component({
  selector: 'app-bar-chart',
  standalone: true,
  imports: [ThemeColorPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <svg [attr.viewBox]="'0 0 200 ' + height()" width="100%" [attr.height]="height()" aria-hidden="true">
      @for (bar of rects(); track $index) {
        <rect [attr.x]="bar.x" [attr.y]="bar.y" width="10" [attr.height]="bar.h" [attr.fill]="(bar.fill) | themeColor" />
      }
    </svg>
  `,
  styles: [`:host { display: block; }`],
})
export class BarChartComponent {
  readonly bars = input<Bar[]>([]);
  readonly height = input<number>(34);
  readonly color = input<string>('var(--pl-color-3d3d3d)');
  /** Fixes the scale so a value equals its pixel height (the design's geometry). */
  readonly max = input<number | null>(null);

  readonly rects = computed(() => {
    const bars = this.bars();
    const height = this.height();
    const max = this.max() ?? (bars.length ? Math.max(...bars.map((bar) => bar.value)) : 1);
    return bars.map((bar, index) => {
      const h = Math.max(2, Math.round((bar.value / (max || 1)) * height));
      return { x: index * 16, y: height - h, h, fill: bar.color ?? this.color() };
    });
  });
}

import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

/**
 * The KPI card's 200x34 trend line, matching the design's "Cash position"
 * geometry: a 1.6px ink polyline over an optional dashed grey baseline.
 */
@Component({
  selector: 'app-sparkline',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <svg viewBox="0 0 200 34" width="100%" height="34" aria-hidden="true">
      @if (baseline()) {
        <polyline [attr.points]="baselinePoints()" fill="none" stroke="#c9c9c9" stroke-width="1" stroke-dasharray="3 3" />
      }
      <polyline [attr.points]="linePoints()" fill="none" [attr.stroke]="color()" stroke-width="1.6" />
    </svg>
  `,
  styles: [`:host { display: block; }`],
})
export class SparklineComponent {
  readonly values = input<number[]>([]);
  readonly color = input<string>('#111');
  /** draws the dotted comparison line from the design */
  readonly baseline = input<boolean>(false);

  private readonly bounds = computed(() => {
    const values = this.values();
    const min = values.length ? Math.min(...values) : 0;
    const max = values.length ? Math.max(...values) : 1;
    return { min, span: max - min || 1 };
  });

  readonly linePoints = computed(() => {
    const values = this.values();
    if (!values.length) return '';
    const { min, span } = this.bounds();
    const step = values.length > 1 ? 196 / (values.length - 1) : 0;
    return values
      .map((value, index) => `${(2 + index * step).toFixed(1)},${(30 - ((value - min) / span) * 23).toFixed(1)}`)
      .join(' ');
  });

  readonly baselinePoints = computed(() => '2,30 198,18');
}

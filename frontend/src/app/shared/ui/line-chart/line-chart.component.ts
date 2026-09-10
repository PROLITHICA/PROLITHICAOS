import { ThemeColorPipe } from '../theme-color.pipe';
import { ChangeDetectionStrategy, Component, input } from '@angular/core';

export interface LineSeries {
  /** SVG polyline points in the chart's 620x200 space */
  points: string;
  color: string;
  width?: number;
  /** filled area under the line */
  area?: string;
  areaFill?: string;
  /** end-of-series markers */
  dots?: Array<{ cx: number; cy: number }>;
  label?: string;
}

/**
 * The "Margin against cost, by month" chart — axes, gridlines, legend, the
 * dashed "now" marker and month labels, in the design's 620x200 viewBox.
 */
@Component({
  selector: 'app-line-chart',
  standalone: true,
  imports: [ThemeColorPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div>
      @if (series().length && showLegend()) {
        <div class="legend">
          @for (s of series(); track $index) {
            @if (s.label) {
              <span class="key"><span class="swatch" [style.background]="(s.color) | themeColor"></span>{{ s.label }}</span>
            }
          }
        </div>
      }
      <svg viewBox="0 0 620 200" width="100%" height="200" aria-hidden="true">
        <g stroke="var(--pl-color-f0f0f0)" stroke-width="1">
          @for (y of gridY(); track $index) {
            <line x1="40" [attr.y1]="y" x2="610" [attr.y2]="y" />
          }
        </g>
        <line x1="40" y1="170" x2="610" y2="170" stroke="var(--pl-color-d8d8d8)" />

        <g font-size="10" fill="var(--pl-color-9a9a9a)" font-family="Roboto, sans-serif">
          @for (label of yLabels(); track $index) {
            <text x="8" [attr.y]="gridY()[$index] + 4">{{ label }}</text>
          }
        </g>

        @for (s of series(); track $index) {
          @if (s.area) { <polygon [attr.points]="s.area" [attr.fill]="(s.areaFill || 'var(--pl-color-f4f4f4)') | themeColor" /> }
        }
        @for (s of series(); track $index) {
          <polyline [attr.points]="s.points" fill="none" [attr.stroke]="(s.color) | themeColor" [attr.stroke-width]="s.width || 2" />
        }
        @for (s of series(); track $index) {
          <g [attr.fill]="(s.color) | themeColor">
            @for (dot of s.dots || []; track $index) {
              <circle [attr.cx]="dot.cx" [attr.cy]="dot.cy" r="3" />
            }
          </g>
        }

        @if (nowX() !== null) {
          <line [attr.x1]="nowX()" y1="20" [attr.x2]="nowX()" y2="170" stroke="var(--pl-color-111111)" stroke-width="1" stroke-dasharray="4 3" />
          <text [attr.x]="(nowX() || 0) + 6" y="34" font-size="10" fill="var(--pl-color-111111)" font-family="Roboto, sans-serif">{{ nowLabel() }}</text>
        }

        <g font-size="10" fill="var(--pl-color-9a9a9a)" font-family="Roboto, sans-serif">
          @for (label of xLabels(); track $index) {
            <text [attr.x]="50 + $index * xStep()" y="188">{{ label }}</text>
          }
        </g>
      </svg>
    </div>
  `,
  styles: [`
    :host { display: block; }
    .legend { display: flex; flex-wrap: wrap; gap: 6px 14px; font-size: 11px; color: var(--pl-color-6b6b6b); justify-content: flex-end; }
    .key { display: flex; align-items: center; gap: 5px; white-space: nowrap; }
    .swatch { width: 14px; height: 2px; display: inline-block; flex: none; }
    svg { margin-top: 14px; }
    /* Responsive: below the tablet breakpoint the 620-wide plot would shrink
       its axis type to an unreadable size, so it scrolls at a legible width. */
    @media (max-width: 720px) {
      :host > div { overflow-x: auto; -webkit-overflow-scrolling: touch; }
      .legend { justify-content: flex-start; }
      svg { min-width: 480px; }
    }
  `],
})
export class LineChartComponent {
  readonly series = input<LineSeries[]>([]);
  readonly yLabels = input<string[]>(['40%', '32%', '24%', '16%']);
  readonly gridY = input<number[]>([20, 60, 100, 140]);
  readonly xLabels = input<string[]>([]);
  readonly xStep = input<number>(70);
  readonly nowX = input<number | null>(null);
  readonly nowLabel = input<string>('now');
  readonly showLegend = input<boolean>(true);
}

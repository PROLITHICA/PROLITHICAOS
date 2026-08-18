import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

export interface DonutSlice { label: string; value: number; display: string; color: string; }

/**
 * Receivables ageing: a 124x124 ring (r=44, 17px stroke) with the total in the
 * middle and the design's dotted legend rows beside it.
 */
@Component({
  selector: 'app-donut',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="wrap">
      <svg viewBox="0 0 124 124" width="124" height="124" aria-hidden="true">
        <circle cx="62" cy="62" r="44" fill="none" stroke="#f2f2f2" stroke-width="17" />
        <g transform="rotate(-90 62 62)" fill="none" stroke-width="17">
          @for (arc of arcs(); track $index) {
            <circle cx="62" cy="62" r="44" [attr.stroke]="arc.color"
                    [attr.stroke-dasharray]="arc.dash" [attr.stroke-dashoffset]="arc.offset" />
          }
        </g>
        <text x="62" y="59" text-anchor="middle" font-size="18" font-weight="600" fill="#111" font-family="Roboto, sans-serif">{{ total() }}</text>
        <text x="62" y="75" text-anchor="middle" font-size="9" fill="#9a9a9a" font-family="Roboto, sans-serif">{{ totalNote() }}</text>
      </svg>
      <div class="legend">
        @for (slice of slices(); track slice.label; let last = $last) {
          <span class="row" [class.last]="last">
            <span class="swatch" [style.background]="slice.color"></span>
            <span class="label">{{ slice.label }}</span>
            <span class="value">{{ slice.display }}</span>
          </span>
        }
      </div>
    </div>
  `,
  styles: [`
    .wrap { display: flex; flex-wrap: wrap; align-items: center; gap: 18px 22px; margin-top: 16px; }
    svg { flex: 0 1 124px; max-width: 124px; }
    .legend { flex: 1 1 150px; min-width: 150px; display: flex; flex-direction: column; font-size: 12px; }
    .row { display: flex; align-items: center; gap: 9px; padding: 7px 0; border-bottom: 1px dotted #e0e0e0; }
    .row.last { border-bottom: 0; }
    .swatch { width: 9px; height: 9px; border-radius: 2px; flex: none; }
    .label { flex: 1; }
    .value { font-weight: 600; }
  `],
})
export class DonutComponent {
  readonly slices = input<DonutSlice[]>([]);
  readonly total = input<string>('');
  readonly totalNote = input<string>('outstanding');

  private readonly circumference = 2 * Math.PI * 44;

  readonly arcs = computed(() => {
    const slices = this.slices();
    const sum = slices.reduce((acc, slice) => acc + slice.value, 0) || 1;
    let used = 0;
    return slices.map((slice) => {
      const length = (slice.value / sum) * this.circumference;
      const arc = {
        color: slice.color,
        dash: `${Math.round(length)} ${Math.round(this.circumference - length)}`,
        offset: -Math.round(used),
      };
      used += length;
      return arc;
    });
  });
}

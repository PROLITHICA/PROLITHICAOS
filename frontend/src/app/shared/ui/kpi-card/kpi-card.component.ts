import { ThemeColorPipe } from '../theme-color.pipe';
import { ChangeDetectionStrategy, Component, input } from '@angular/core';

import { TagComponent } from '../tag/tag.component';

/**
 * The Command Centre KPI card: label, right-hand meta (plain or a tag),
 * big figure, a projected chart slot, then the footnote line.
 */
@Component({
  selector: 'app-kpi-card',
  standalone: true,
  imports: [ThemeColorPipe, TagComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="kpi">
      <div class="kpi-top">
        <span class="kpi-label">{{ label() }}</span>
        @if (metaTag()) {
          <app-tag [text]="meta()" [tagClass]="metaTag()" />
        } @else if (meta()) {
          <span class="kpi-meta" [style.color]="(metaStrong() ? 'var(--pl-color-3d3d3d)' : 'var(--pl-color-8a8a8a)') | themeColor">{{ meta() }}</span>
        }
      </div>
      <div class="kpi-value">{{ value() }}</div>
      <div class="kpi-chart"><ng-content /></div>
      @if (note()) { <div class="kpi-note">{{ note() }}</div> }
    </div>
  `,
  styles: [`
    .kpi { border: 0; border-radius: 16px; background: var(--pl-pane); box-shadow: var(--pl-lift-1); padding: 18px; }
    .kpi-top { display: flex; flex-wrap: wrap; gap: 2px 10px; justify-content: space-between; align-items: baseline; }
    .kpi-label { font-size: 11.5px; color: var(--pl-color-6b6b6b); }
    .kpi-meta { font-size: 11px; }
    .kpi-value { font-family: 'Roboto', sans-serif; font-size: clamp(21px, 2.1vw, 29px); font-weight: 600; margin-top: 8px; white-space: nowrap; }
    .kpi-chart { margin-top: 8px; }
    .kpi-note { font-size: 11px; color: var(--pl-color-8a8a8a); }
    @media (max-width: 560px) {
      .kpi { padding: 14px; }
      .kpi-value { font-size: 24px; margin-top: 6px; }
      .kpi-label, .kpi-meta, .kpi-note { font-size: 11px; }
    }
  `],
})
export class KpiCardComponent {
  readonly label = input<string>('');
  readonly value = input<string>('');
  readonly meta = input<string>('');
  /** when set the meta renders as a pill, e.g. "tag-accent-2" */
  readonly metaTag = input<string>('');
  readonly metaStrong = input<boolean>(false);
  readonly note = input<string>('');
}

import { ChangeDetectionStrategy, Component, input } from '@angular/core';

/**
 * The design's "progress vs budget" cell: two stacked 5px bars plus the
 * "x complete · y budget" caption. Use `single` for a lone utilisation bar.
 */
@Component({
  selector: 'app-progress-bar',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div>
      <span class="stack">
        <span class="track"><span class="fill" [style.width]="complete()" style="background:#111"></span></span>
        @if (!single()) {
          <span class="track second"><span class="fill" [style.width]="budget()" [style.background]="budgetColor()"></span></span>
        }
      </span>
      @if (caption()) { <span class="cap">{{ caption() }}</span> }
    </div>
  `,
  styles: [`
    .stack { display: block; min-width: 70px; }
    .track { display: block; height: 5px; background: #eee; border-radius: 5px; overflow: hidden; }
    .track.second { margin-top: 3px; }
    .fill { display: block; height: 5px; }
    .cap { display: block; font-size: 10.5px; color: #8a8a8a; white-space: nowrap; margin-top: 4px; }
  `],
})
export class ProgressBarComponent {
  /** CSS width, e.g. "62%" */
  readonly complete = input<string>('0%');
  readonly budget = input<string>('0%');
  readonly budgetColor = input<string>('#111');
  readonly caption = input<string>('');
  readonly single = input<boolean>(false);
}

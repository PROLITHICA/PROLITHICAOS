import { ChangeDetectionStrategy, Component, input } from '@angular/core';

/** The floating pane used everywhere: depth instead of an outline. */
@Component({
  selector: 'app-card',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="pl-card" [style.padding.px]="padding()">
      @if (heading() || subheading()) {
        <div class="pl-card-head">
          <div>
            @if (heading()) { <h4 class="pl-card-title">{{ heading() }}</h4> }
            @if (subheading()) { <div class="pl-card-sub">{{ subheading() }}</div> }
          </div>
          <ng-content select="[card-actions]" />
        </div>
      }
      <ng-content />
    </div>
  `,
  styles: [`
    .pl-card { border: 0; border-radius: 16px; background: var(--pl-pane); box-shadow: var(--pl-lift-1); }
    .pl-card-head { display: flex; flex-wrap: wrap; gap: 6px 16px; justify-content: space-between; align-items: baseline; }
    .pl-card-title { margin: 0 0 2px; font-size: 15px; }
    .pl-card-sub { font-size: 11.5px; color: var(--pl-color-8a8a8a); }
    @media (max-width: 560px) {
      .pl-card { padding: 14px !important; }
      .pl-card-title { font-size: 14.5px; }
    }
  `],
})
export class CardComponent {
  readonly heading = input<string>('');
  readonly subheading = input<string>('');
  readonly padding = input<number>(18);
}

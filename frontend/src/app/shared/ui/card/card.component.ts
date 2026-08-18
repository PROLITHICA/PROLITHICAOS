import { ChangeDetectionStrategy, Component, input } from '@angular/core';

/** The dotted-hairline 16px card used everywhere in the design. */
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
    .pl-card { border: 1px dotted #c4c4c4; border-radius: 16px; background: #fff; }
    .pl-card-head { display: flex; flex-wrap: wrap; gap: 6px 16px; justify-content: space-between; align-items: baseline; }
    .pl-card-title { margin: 0 0 2px; font-size: 15px; }
    .pl-card-sub { font-size: 11.5px; color: #8a8a8a; }
  `],
})
export class CardComponent {
  readonly heading = input<string>('');
  readonly subheading = input<string>('');
  readonly padding = input<number>(18);
}

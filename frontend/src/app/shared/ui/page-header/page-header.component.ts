import { ChangeDetectionStrategy, Component, input } from '@angular/core';

/** Title + subtitle on the left, action buttons projected on the right. */
@Component({
  selector: 'app-page-header',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="head">
      <div>
        @if (kicker()) { <div class="kicker">{{ kicker() }}</div> }
        <h1 class="title" [style.font-size.px]="large() ? 31 : 28">{{ title() }}</h1>
        @if (subtitle()) { <div class="sub">{{ subtitle() }}</div> }
      </div>
      <div class="actions"><ng-content /></div>
    </div>
  `,
  styles: [`
    .head { display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; }
    .kicker { font-size: 12.5px; color: #3d3d3d; font-weight: 500; }
    .title { margin: 4px 0 4px; }
    .sub { font-size: 12.5px; color: #8a8a8a; max-width: 74ch; }
    .actions { display: flex; gap: 9px; flex: none; }
    .actions ::ng-deep .btn { white-space: nowrap; }
  `],
})
export class PageHeaderComponent {
  readonly title = input<string>('');
  readonly subtitle = input<string>('');
  readonly kicker = input<string>('');
  readonly large = input<boolean>(false);
}

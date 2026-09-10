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
    .kicker { font-size: 12.5px; color: var(--pl-color-3d3d3d); font-weight: 500; }
    .title { margin: 4px 0 4px; }
    .sub { font-size: 12.5px; color: var(--pl-color-8a8a8a); max-width: 74ch; }
    .actions { display: flex; gap: 9px; flex: none; }
    .actions ::ng-deep .btn { white-space: nowrap; }
    /* Responsive: styles.css stacks .head; the action slot then has to
       claim the full width instead of staying a rigid flex: none row. */
    @media (max-width: 900px) {
      /* The component's own flex-end alignment out-specifies the global
         stacking rule, so it stacks here rather than leaving each feature to
         override it. */
      .head { flex-direction: column; align-items: flex-start; gap: 12px; }
      .actions { flex: 1 1 100%; width: 100%; flex-wrap: wrap; }
      .sub { max-width: none; }
    }
    @media (max-width: 560px) {
      .title { font-size: 24px !important; }
      .actions { flex-direction: column; align-items: stretch; }
      .actions ::ng-deep .btn { width: 100%; min-height: 42px; }
    }
  `],
})
export class PageHeaderComponent {
  readonly title = input<string>('');
  readonly subtitle = input<string>('');
  readonly kicker = input<string>('');
  readonly large = input<boolean>(false);
}

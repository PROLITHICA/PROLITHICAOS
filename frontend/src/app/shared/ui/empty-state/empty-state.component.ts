import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';

/** Nothing-here panel: heading, explanatory line, optional single action. */
@Component({
  selector: 'app-empty-state',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="empty">
      <div class="empty-title">{{ heading() }}</div>
      @if (note()) { <div class="empty-note">{{ note() }}</div> }
      @if (actionLabel()) {
        <button type="button" class="btn btn-secondary empty-action" (click)="action.emit()">
          {{ actionLabel() }}
        </button>
      }
      <ng-content />
    </div>
  `,
  styles: [`
    .empty { border: 0; border-radius: 16px; background: var(--pl-pane); box-shadow: var(--pl-lift-1); padding: 46px 26px; text-align: center; }
    .empty-title { font-size: 15px; font-weight: 500; }
    .empty-note { font-size: 12.5px; color: var(--pl-color-8a8a8a); margin-top: 6px; max-width: 56ch; margin-inline: auto; }
    .empty-action { margin-top: 16px; }
    @media (max-width: 560px) {
      .empty { padding: 28px 16px; }
      .empty-note { max-width: none; }
      .empty-action { min-height: 42px; }
    }
  `],
})
export class EmptyStateComponent {
  readonly heading = input<string>('Nothing here yet');
  readonly note = input<string>('');
  readonly actionLabel = input<string>('');
  readonly action = output<void>();
}

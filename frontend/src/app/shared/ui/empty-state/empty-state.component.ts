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
    .empty { border: 1px dotted #c4c4c4; border-radius: 16px; padding: 40px 26px; text-align: center; background: #fff; }
    .empty-title { font-size: 15px; font-weight: 500; }
    .empty-note { font-size: 12.5px; color: #8a8a8a; margin-top: 6px; max-width: 56ch; margin-inline: auto; }
    .empty-action { margin-top: 16px; }
  `],
})
export class EmptyStateComponent {
  readonly heading = input<string>('Nothing here yet');
  readonly note = input<string>('');
  readonly actionLabel = input<string>('');
  readonly action = output<void>();
}

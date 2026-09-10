import { ChangeDetectionStrategy, Component, input } from '@angular/core';

/** The three-up stat tile above every record list. */
@Component({
  selector: 'app-stat-tile',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="tile">
      <div class="tile-label">{{ label() }}</div>
      <div class="tile-value">{{ value() }}</div>
      @if (note()) { <div class="tile-note">{{ note() }}</div> }
    </div>
  `,
  styles: [`
    .tile { border: 0; border-radius: 16px; background: var(--pl-pane); box-shadow: var(--pl-lift-1); padding: 18px; }
    .tile-label { font-size: 11.5px; color: var(--pl-color-6b6b6b); }
    .tile-value { font-family: 'Roboto', sans-serif; font-size: 26px; font-weight: 600; margin-top: 6px; white-space: nowrap; }
    .tile-note { font-size: 11px; color: var(--pl-color-9a9a9a); margin-top: 4px; }
    @media (max-width: 560px) {
      .tile { padding: 14px; }
      .tile-value { font-size: 22px; }
    }
  `],
})
export class StatTileComponent {
  readonly label = input<string>('');
  readonly value = input<string>('');
  readonly note = input<string>('');
}

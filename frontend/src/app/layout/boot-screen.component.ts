import { ChangeDetectionStrategy, Component, input } from '@angular/core';

/** The boot splash shown while `/api/auth/me/` resolves on first load. */
@Component({
  selector: 'app-boot-screen',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="boot">
      <div class="mark">Prolithica</div>
      <div class="track"><div class="bootbar"></div></div>
      <div class="step">{{ step() }}</div>
    </div>
  `,
  styles: [`
    .boot { position: fixed; inset: 0; z-index: 60; background: var(--pl-color-ffffff); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 34px; }
    .mark { font-family: 'Anurati', 'Roboto', sans-serif; font-weight: 400; font-size: 34px; letter-spacing: 0.24em; text-transform: uppercase; color: var(--pl-color-111111); }
    .track { width: 220px; height: 2px; background: var(--pl-color-eeeeee); overflow: hidden; }
    .bootbar { width: 100%; height: 2px; background: var(--pl-color-3d3d3d); }
    .step { font-size: 11px; letter-spacing: 0.16em; text-transform: uppercase; color: var(--pl-color-8a8a8a); }
  `],
})
export class BootScreenComponent {
  readonly step = input<string>('Connecting to Prolithica OS');
}

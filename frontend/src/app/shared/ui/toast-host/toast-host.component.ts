import { ChangeDetectionStrategy, Component, inject } from '@angular/core';

import { ToastService } from '../../../core/toast.service';

/** Bottom-left toast, offset clear of the 252px sidebar as in the design. */
@Component({
  selector: 'app-toast-host',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (toasts.current(); as toast) {
      <div class="toast fade" role="status">
        <span class="dot"></span>
        <span class="text">{{ toast.text }}</span>
      </div>
    }
  `,
  styles: [`
    .toast { position: fixed; left: 272px; bottom: 22px; z-index: 40; background: #111; color: #fff; padding: 13px 17px; border-radius: 16px; max-width: 440px; display: flex; gap: 12px; align-items: flex-start; box-shadow: 0 8px 26px rgba(0,0,0,0.22); }
    .dot { width: 7px; height: 7px; margin-top: 6px; background: #ffffff; border-radius: 999px; flex: none; }
    .text { font-size: 12.5px; line-height: 1.45; }
  `],
})
export class ToastHostComponent {
  readonly toasts = inject(ToastService);
}

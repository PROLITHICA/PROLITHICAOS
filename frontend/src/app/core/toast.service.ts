import { Injectable, signal } from '@angular/core';

import { Toast } from './models';

/** Holds the toast string every backend action returns. Auto-dismisses ~4s. */
@Injectable({ providedIn: 'root' })
export class ToastService {
  private seq = 0;
  private timer: ReturnType<typeof setTimeout> | null = null;

  readonly current = signal<Toast | null>(null);

  show(text: string | null | undefined): void {
    if (!text) return;
    this.current.set({ id: ++this.seq, text });
    if (this.timer) clearTimeout(this.timer);
    this.timer = setTimeout(() => this.current.set(null), 4000);
  }

  /** Convenience for action responses shaped `{ ..., toast }`. */
  fromResponse(response: { toast?: string } | null | undefined): void {
    this.show(response?.toast);
  }

  clear(): void {
    if (this.timer) clearTimeout(this.timer);
    this.current.set(null);
  }
}

import { Injectable, signal } from '@angular/core';

/** Drives the skeleton overlay and its "loadingNote" line during transitions. */
@Injectable({ providedIn: 'root' })
export class LoadingService {
  readonly loading = signal(false);
  readonly note = signal('');
  private depth = 0;

  start(note = 'Loading'): void {
    this.depth += 1;
    this.note.set(note);
    this.loading.set(true);
  }

  stop(): void {
    this.depth = Math.max(0, this.depth - 1);
    if (this.depth === 0) {
      this.loading.set(false);
      this.note.set('');
    }
  }

  reset(): void {
    this.depth = 0;
    this.loading.set(false);
    this.note.set('');
  }
}

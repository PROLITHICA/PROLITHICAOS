import { Injectable, signal } from '@angular/core';

/**
 * Lets a screen name itself in the topbar.
 *
 * Most routes carry a static title in their route data, but a record screen has
 * to say which record it is showing, so it sets one here and clears it on the
 * way out.
 */
@Injectable({ providedIn: 'root' })
export class PageTitleService {
  readonly title = signal<string>('');

  set(title: string): void {
    this.title.set(title);
  }

  clear(): void {
    this.title.set('');
  }
}

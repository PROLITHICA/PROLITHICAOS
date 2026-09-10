import { DOCUMENT } from '@angular/common';
import { Injectable, inject, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);
  readonly dark = signal(false);

  constructor() {
    let preference = 'light';
    try { preference = localStorage.getItem('pl.theme') ?? 'light'; } catch { /* Storage can be disabled. */ }
    this.apply(preference === 'dark');
  }

  toggle(): void {
    this.apply(!this.dark());
    try { localStorage.setItem('pl.theme', this.dark() ? 'dark' : 'light'); } catch { /* Keep the current session theme. */ }
  }

  private apply(dark: boolean): void {
    this.dark.set(dark);
    this.document.documentElement.dataset['theme'] = dark ? 'dark' : 'light';
  }
}

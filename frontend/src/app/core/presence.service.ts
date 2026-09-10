import { Injectable, DestroyRef, computed, inject, signal } from '@angular/core';
import { AuthService } from './auth.service';

/** Presence describes this browser session, not other people's sessions. */
@Injectable({ providedIn: 'root' })
export class PresenceService {
  private readonly auth = inject(AuthService);
  private readonly destroyRef = inject(DestroyRef);
  readonly online = signal(navigator.onLine);
  readonly active = signal(!document.hidden);
  readonly label = computed(() => !this.auth.isAuthenticated() ? 'Logged out'
    : !this.online() ? 'Offline' : this.active() ? 'Active · Online' : 'Inactive');
  constructor() {
    let lastActivity = Date.now();
    const activity = () => { lastActivity = Date.now(); this.active.set(!document.hidden); };
    const connection = () => this.online.set(navigator.onLine);
    const visibility = () => { if (document.hidden) this.active.set(false); else activity(); };
    const events = ['pointerdown', 'pointermove', 'keydown', 'scroll', 'touchstart'];
    for (const event of events) window.addEventListener(event, activity, { passive: true });
    window.addEventListener('online', connection);
    window.addEventListener('offline', connection);
    document.addEventListener('visibilitychange', visibility);
    const timer = setInterval(() => this.active.set(!document.hidden && Date.now() - lastActivity < 300000), 10000);
    this.destroyRef.onDestroy(() => {
      clearInterval(timer);
      for (const event of events) window.removeEventListener(event, activity);
      window.removeEventListener('online', connection);
      window.removeEventListener('offline', connection);
      document.removeEventListener('visibilitychange', visibility);
    });
  }
}

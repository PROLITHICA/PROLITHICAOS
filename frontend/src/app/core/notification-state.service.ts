import { Injectable, inject, signal } from '@angular/core';
import { ApiService } from './api.service';

@Injectable({ providedIn: 'root' })
export class NotificationStateService {
  private readonly api = inject(ApiService);
  readonly unread = signal(0);
  refresh(): void {
    this.api.get<{ unread: number }>('/notifications/').subscribe({
      next: payload => this.unread.set(payload.unread),
      error: () => {},
    });
  }
}

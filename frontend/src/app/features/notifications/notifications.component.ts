import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { ToastService } from '../../core/toast.service';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';
import { TagComponent } from '../../shared/ui/tag/tag.component';

export interface NotificationItem {
  id: string;
  text: string;
  meta: string;
  cta: string;
  route: string;
  weight: number;
  read: boolean;
}

export interface NotificationGroup {
  heading: string;
  tag_class: string;
  count: string;
  items: NotificationItem[];
}

export interface NotificationsPayload {
  title: string;
  subtitle: string;
  unread: number;
  groups: NotificationGroup[];
}

const SUBTITLE = 'Meaningful events only. Each one says whether it is critical, actionable or '
  + 'informational.';

/** Notifications, grouped Critical / Actionable / Informational. */
@Component({
  selector: 'app-notifications',
  standalone: true,
  imports: [TagComponent, SkeletonComponent, EmptyStateComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="head">
      <div>
        <h1 class="title">{{ payload()?.title || 'Notifications' }}</h1>
        <div class="sub">{{ payload()?.subtitle || subtitle }}</div>
      </div>
      <button type="button" class="btn btn-secondary read-all" [disabled]="busy()" (click)="markAllRead()">
        @if (busy()) { <span class="spin spin-dark"></span> }
        Mark all read
      </button>
    </div>

    @if (loading()) {
      <div class="list">
        @for (slot of [1, 2, 3]; track slot) { <app-skeleton height="150px" /> }
      </div>
    } @else if (failed()) {
      <div class="list">
        <app-empty-state
          heading="Notifications could not be loaded"
          note="The notification service did not answer. Nothing has been lost — try again."
          actionLabel="Try again"
          (action)="load()" />
      </div>
    } @else if (!groups().length) {
      <div class="list">
        <app-empty-state
          heading="Nothing needs you right now"
          note="Critical items stay on the Command Centre until they are resolved." />
      </div>
    } @else {
      <div class="list">
        @for (group of groups(); track group.heading) {
          <div class="group">
            <div class="group-head">
              <h4 class="group-title">{{ group.heading }}</h4>
              <app-tag [text]="group.count" [tagClass]="group.tag_class" />
            </div>
            <div class="rows">
              @for (item of group.items; track item.id) {
                <div class="row">
                  <div>
                    <div class="row-text" [style.font-weight]="item.weight">{{ item.text }}</div>
                    <div class="row-meta">{{ item.meta }}</div>
                  </div>
                  <button type="button" class="btn btn-secondary row-cta" (click)="open(item)">
                    {{ item.cta }}
                  </button>
                </div>
              }
            </div>
          </div>
        }
      </div>
    }
  `,
  styles: [`
    :host { display: block; }
    .head { display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; }
    .title { font-size: 28px; margin: 0 0 4px; }
    .sub { font-size: 12.5px; color: #8a8a8a; max-width: 74ch; }
    .read-all { border-color: #b5b5b5; white-space: nowrap; flex: none; }
    .list { display: flex; flex-direction: column; gap: 14px; margin-top: 20px; max-width: 900px; }
    .group { border: 1px dotted #c4c4c4; border-radius: 16px; padding: 18px; background: #fff; }
    .group-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
    .group-title { margin: 0; font-size: 15px; }
    .rows { display: flex; flex-direction: column; margin-top: 6px; }
    .row {
      display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 14px;
      align-items: center; padding: 11px 0; border-bottom: 1px dotted #dcdcdc;
    }
    .row-text { font-size: 13px; }
    .row-meta { font-size: 11px; color: #9a9a9a; }
    .row-cta { border-color: #b5b5b5; font-size: 12px; padding: 5px 12px; white-space: nowrap; }
    @media (max-width: 640px) {
      .head { flex-direction: column; align-items: flex-start; gap: 14px; }
    }
  `],
})
export class NotificationsComponent {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  private readonly toast = inject(ToastService);

  readonly subtitle = SUBTITLE;
  readonly payload = signal<NotificationsPayload | null>(null);
  readonly loading = signal(true);
  readonly failed = signal(false);
  readonly busy = signal(false);

  readonly groups = computed<NotificationGroup[]>(() => this.payload()?.groups ?? []);

  constructor() {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.failed.set(false);
    this.api.get<NotificationsPayload>('/notifications/').subscribe({
      next: (payload) => {
        this.payload.set(payload);
        this.loading.set(false);
      },
      error: () => {
        this.failed.set(true);
        this.loading.set(false);
      },
    });
  }

  markAllRead(): void {
    this.busy.set(true);
    this.api.post<{ toast?: string }>('/notifications/read-all/').subscribe({
      next: (response) => {
        this.busy.set(false);
        this.toast.show(response?.toast);
        this.load();
      },
      error: () => this.busy.set(false),
    });
  }

  open(item: NotificationItem): void {
    this.api.post(`/notifications/${item.id}/read/`).subscribe({ next: () => {}, error: () => {} });
    if (item.route) void this.router.navigateByUrl(item.route);
  }
}

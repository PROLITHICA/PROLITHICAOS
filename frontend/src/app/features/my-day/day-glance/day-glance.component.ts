import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { ScheduleEntry } from '../my-day.models';
import { MyDayService } from '../my-day.service';

/**
 * The day in one strip, for the top of the Command Centre.
 *
 * Reads the same `MyDayService` as `/my-day`, so a tick or an approval made
 * on either screen is already true here — no second fetch, no second copy of
 * the rules. Deliberately read-only: it says what is next and how much is
 * waiting, then hands over to the full screen.
 */
@Component({
  selector: 'app-day-glance',
  standalone: true,
  imports: [RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (day.data(); as data) {
      <section class="glance">
        <div class="g-head">
          <div class="g-id">
            <div class="g-greeting">{{ data.greeting }}</div>
            <div class="g-sub">{{ data.date_label }} · {{ data.summary }}</div>
          </div>
          <a class="btn btn-secondary g-open" routerLink="/my-day">Open my day →</a>
        </div>

        <div class="g-body">
          <div class="g-next">
            <div class="g-kicker">Next up</div>
            @for (entry of upcoming(); track entry.id) {
              <a class="g-entry" routerLink="/my-day">
                <span class="g-time">{{ entry.start }}</span>
                <span class="g-what">
                  <span class="g-title">{{ entry.title }}</span>
                  <span class="g-meta">{{ where(entry) }}</span>
                </span>
              </a>
            } @empty {
              <div class="g-clear">
                {{ data.schedule.length ? 'Everything in the diary is ticked off.' : 'Nothing is in the diary today.' }}
              </div>
            }
          </div>

          <a class="g-waiting" routerLink="/my-day">
            <span class="g-count">{{ data.approvals.length }}</span>
            <span class="g-waiting-label">
              {{ data.approvals.length === 1 ? 'approval waiting on you' : 'approvals waiting on you' }}
            </span>
            <span class="g-waiting-note">
              {{ data.approvals.length ? 'Nothing behind them moves until you decide.' : 'Everything has been cleared.' }}
            </span>
          </a>
        </div>
      </section>
    }
  `,
  styles: [`
    :host { display: block; }

    .glance {
      border: 0; border-radius: var(--pl-radius-card);
      background: var(--pl-pane); box-shadow: var(--pl-lift-1);
      padding: var(--pl-pane-pad);
    }

    .g-head {
      display: flex; flex-wrap: wrap; align-items: baseline;
      justify-content: space-between; gap: 8px 16px;
    }
    .g-greeting { font-size: 15px; font-weight: 500; }
    .g-sub { font-size: 11.5px; color: var(--pl-color-8a8a8a); margin-top: 2px; }
    .g-open { flex: none; font-size: 12.5px; padding: 7px 14px; white-space: nowrap; }

    .g-body {
      display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 240px);
      gap: 14px 22px; margin-top: 16px;
      padding-top: 14px; border-top: 1px solid var(--pl-rule);
    }

    .g-kicker {
      font-size: 10px; letter-spacing: 0.12em; text-transform: uppercase;
      color: var(--pl-color-9a9a9a); margin-bottom: 4px;
    }
    .g-entry {
      display: flex; align-items: baseline; gap: 12px;
      padding: 7px 8px; margin: 0 -8px; border-radius: 10px;
      text-decoration: none; color: inherit;
      border-bottom: 1px solid var(--pl-rule);
    }
    .g-entry:last-child { border-bottom: 0; }
    .g-entry:hover { background: rgba(17, 17, 17, 0.03); }
    .g-time {
      font-size: 12.5px; font-weight: 600; flex: none; width: 44px;
      font-variant-numeric: tabular-nums;
    }
    .g-what { min-width: 0; }
    .g-title {
      display: block; font-size: 13px; font-weight: 500;
      overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .g-meta { display: block; font-size: 10.5px; color: var(--pl-color-9a9a9a); }
    .g-clear { font-size: 12px; color: var(--pl-color-8a8a8a); padding: 7px 0; }

    .g-waiting {
      display: block; text-decoration: none; color: inherit;
      border: 0; border-radius: 14px; padding: 14px 16px;
      background: var(--pl-pane-sunken); box-shadow: none; align-self: start;
    }
    .g-waiting:hover { background: var(--pl-color-f1efec); }
    .g-count { display: block; font-size: 25px; font-weight: 600; line-height: 1.1; }
    .g-waiting-label { display: block; font-size: 12px; margin-top: 1px; }
    .g-waiting-note { display: block; font-size: 10.5px; color: var(--pl-color-9a9a9a); margin-top: 5px; }

    @media (max-width: 900px) {
      .g-body { grid-template-columns: minmax(0, 1fr); }
    }
    @media (max-width: 560px) {
      .glance { padding: 16px; }
      .g-open { width: 100%; min-height: 40px; }
      .g-entry { padding-block: 9px; }
    }
  `],
})
export class DayGlanceComponent {
  readonly day = inject(MyDayService);

  readonly upcoming = computed(() => this.day.next(3));

  /** "Meeting · Boardroom", but never "Call · Call". */
  where(entry: ScheduleEntry): string {
    const location = entry.location && entry.location !== entry.kind_label ? entry.location : '';
    return [entry.kind_label, location].filter(Boolean).join(' · ');
  }

  constructor() {
    this.day.load();
  }
}

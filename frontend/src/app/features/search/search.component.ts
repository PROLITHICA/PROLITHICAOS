import { ChangeDetectionStrategy, Component, DestroyRef, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject, debounceTime, distinctUntilChanged, map } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';

export interface SearchItem {
  title: string;
  meta: string;
  route: string;
}

export interface SearchGroup {
  heading: string;
  count: string;
  items: SearchItem[];
}

export interface SearchPayload {
  summary: string;
  groups: SearchGroup[];
}

const SUBTITLE = 'One index over the whole company: organisations, opportunities, contracts, '
  + 'projects, requirements, invoices, documents and support history.';

/** Global search. Reads `?q=` — the topbar's search box routes here. */
@Component({
  selector: 'app-search',
  standalone: true,
  imports: [FormsModule, SkeletonComponent, EmptyStateComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <h1 class="title">Search</h1>
    <div class="sub">{{ subtitle }}</div>

    <div class="box">
      <input class="input search-input" type="search" [ngModel]="query()"
             (ngModelChange)="onQuery($event)"
             placeholder="Search everything" aria-label="Search everything">
    </div>

    <div class="summary">{{ summary() }}</div>

    @if (loading()) {
      <div class="grid">
        @for (slot of [1, 2, 3, 4]; track slot) { <app-skeleton height="170px" /> }
      </div>
    } @else if (failed()) {
      <div class="state">
        <app-empty-state
          heading="The index did not answer"
          note="Search is temporarily unavailable. Records remain reachable from the sidebar."
          actionLabel="Try again"
          (action)="retry()" />
      </div>
    } @else if (!groups().length) {
      <div class="state">
        <app-empty-state
          heading="Nothing matched"
          [note]="emptyNote()" />
      </div>
    } @else {
      <div class="grid">
        @for (group of groups(); track group.heading) {
          <div class="group">
            <div class="group-head">
              <h4 class="group-title">{{ group.heading }}</h4>
              <span class="group-count">{{ group.count }}</span>
            </div>
            <div class="rows">
              @for (item of group.items; track item.title + item.route) {
                <button type="button" class="row" (click)="open(item)">
                  <span class="row-title">{{ item.title }}</span>
                  <span class="row-meta">{{ item.meta }}</span>
                </button>
              }
            </div>
          </div>
        }
      </div>
    }
  `,
  styles: [`
    :host { display: block; }
    .title { font-size: 28px; margin: 0 0 4px; }
    .sub { font-size: 12.5px; color: var(--pl-color-8a8a8a); max-width: 74ch; }
    .box { margin-top: 16px; max-width: 560px; }
    .search-input { background: var(--pl-color-fafafa); border-color: var(--pl-color-b5b5b5); }
    .summary { font-size: 11.5px; color: var(--pl-color-8a8a8a); margin-top: 10px; }
    .state { margin-top: 14px; }
    .grid {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: var(--pl-pane-gap); margin-top: 16px;
    }
    .group {
      border: 0; background: var(--pl-pane);
      border-radius: var(--pl-radius-card); box-shadow: var(--pl-lift-1);
      padding: var(--pl-pane-pad);
    }
    .group-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
    .group-title { margin: 0; font-size: 15px; }
    .group-count { font-size: 11px; color: var(--pl-color-9a9a9a); }
    .rows { display: flex; flex-direction: column; margin-top: 6px; }
    .row {
      display: block; width: 100%; text-align: left; background: transparent; border: 0;
      border-bottom: 1px solid var(--pl-rule); padding: 11px 0; font: inherit; cursor: pointer;
    }
    .row:last-child { border-bottom: 0; }
    .row:hover { background: rgba(17, 17, 17, 0.02); }
    .row-title { display: block; font-size: 12.5px; font-weight: 500; }
    .row-meta { display: block; font-size: 11px; color: var(--pl-color-9a9a9a); }
    @media (max-width: 900px) { .sub { max-width: none; } .box { max-width: none; } }
    @media (max-width: 560px) {
      .grid { grid-template-columns: minmax(0, 1fr); gap: 12px; }
      .group { padding: 14px; }
      .group-head { flex-wrap: wrap; }
      .group-title { font-size: 14.5px; }
      .search-input { min-height: 44px; }
      .row { padding: 11px 0; }
    }
  `],
})
export class SearchComponent {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);
  private readonly typed = new Subject<string>();

  readonly subtitle = SUBTITLE;
  readonly query = signal<string>('');
  readonly payload = signal<SearchPayload | null>(null);
  readonly loading = signal(true);
  readonly failed = signal(false);

  readonly groups = computed<SearchGroup[]>(() => this.payload()?.groups ?? []);
  readonly summary = computed(() => this.payload()?.summary ?? '');
  readonly emptyNote = computed(() =>
    this.query()
      ? `Nothing in the index matches "${this.query()}" inside your permissions.`
      : 'Type a reference, a client or a phrase to search every record type.');

  constructor() {
    // The URL is the source of truth: the topbar routes here with ?q=.
    this.route.queryParamMap
      .pipe(
        map((params) => (params.get('q') ?? '').trim()),
        distinctUntilChanged(),
        takeUntilDestroyed(),
      )
      .subscribe((q) => {
        this.query.set(q);
        this.fetch(q);
      });

    // Typing rewrites the URL, which feeds the stream above.
    this.typed
      .pipe(debounceTime(250), distinctUntilChanged(), takeUntilDestroyed())
      .subscribe((q) => {
        void this.router.navigate([], {
          relativeTo: this.route,
          queryParams: q ? { q } : {},
          replaceUrl: true,
        });
      });
  }

  private fetch(q: string): void {
    this.loading.set(true);
    this.failed.set(false);
    this.api.get<SearchPayload>('/search/', { q }).pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
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

  onQuery(value: string): void {
    this.query.set(value);
    this.typed.next((value ?? '').trim());
  }

  retry(): void {
    this.fetch(this.query());
  }

  open(item: SearchItem): void {
    if (item.route) void this.router.navigateByUrl(item.route);
  }
}

import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subject, debounceTime, distinctUntilChanged, switchMap } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { ApiService } from '../../core/api.service';
import { Paginated } from '../../core/models';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';

interface KnowledgeItem { id: string; title: string; meta: string; }

interface KnowledgeGroup {
  heading: string;
  count: string;
  note: string;
  items: KnowledgeItem[];
}

interface KnowledgeView {
  title: string;
  subtitle: string;
  search_placeholder?: string;
  groups?: KnowledgeGroup[];
}

interface KnowledgeArticle {
  id: string;
  title: string;
  meta: string;
  category: string;
  category_label: string;
  author: string;
  updated_label: string;
}

/**
 * Knowledge base — design lines 1443-1471. Four category cards, each with its
 * count, note and entries, all narrowed by one search box.
 */
@Component({
  selector: 'app-knowledge',
  standalone: true,
  imports: [FormsModule, SkeletonComponent, EmptyStateComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <h1 class="title">{{ view()?.title || 'Knowledge base' }}</h1>
    <div class="sub">{{ view()?.subtitle || defaultSubtitle }}</div>

    <div class="search">
      <input class="input" [placeholder]="placeholder()"
             [ngModel]="query()" (ngModelChange)="onQuery($event)"
             style="background:#fafafa;border-color:#b5b5b5">
    </div>

    @if (loading()) {
      <div class="cards">
        @for (n of [1, 2, 3, 4]; track n) {
          <div class="card-skel">
            <app-skeleton width="60%" height="15px" />
            <app-skeleton width="90%" height="11px" />
            <app-skeleton width="100%" height="120px" />
          </div>
        }
      </div>
    } @else if (error()) {
      <div class="cards-wrap">
        <app-empty-state heading="The knowledge base could not be loaded"
                         note="The knowledge service did not answer. Nothing is missing — try again."
                         actionLabel="Try again" (action)="reload()" />
      </div>
    } @else if (!total()) {
      <div class="cards-wrap">
        <app-empty-state
          [heading]="query() ? 'Nothing matches that search' : 'The knowledge base is empty'"
          [note]="query()
            ? 'No decision, finding, pattern or lesson mentions those words. Try fewer of them.'
            : 'Decisions, findings, patterns and lessons appear here as the work records them.'"
          [actionLabel]="query() ? 'Clear the search' : ''"
          (action)="onQuery('')" />
      </div>
    } @else {
      <div class="cards fade">
        @for (g of groups(); track g.heading) {
          <div class="group">
            <div class="group-head">
              <h4>{{ g.heading }}</h4>
              <span class="count">{{ g.count }}</span>
            </div>
            <div class="group-note">{{ g.note }}</div>
            <div class="items">
              @for (i of g.items; track i.id) {
                <div class="item">
                  <div class="item-title">{{ i.title }}</div>
                  <div class="item-meta">{{ i.meta }}</div>
                </div>
              } @empty {
                <div class="item-empty">Nothing in this group{{ query() ? ' matches that search' : ' yet' }}.</div>
              }
            </div>
          </div>
        }
      </div>
      <div class="foot">{{ total() }} entries in the knowledge base{{ query() ? ' matching “' + query() + '”' : '' }}.</div>
    }
  `,
  styles: [`
    .title { font-size: 28px; margin: 0 0 4px; }
    .sub { font-size: 12.5px; color: #8a8a8a; max-width: 76ch; }
    .search { margin-top: 16px; max-width: 520px; }
    .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; margin-top: 18px; }
    .cards-wrap { margin-top: 18px; }
    .group, .card-skel { border: 1px dotted #c4c4c4; border-radius: 16px; padding: 18px; }
    .card-skel { display: flex; flex-direction: column; gap: 10px; }
    .group-head { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; }
    .group-head h4 { margin: 0; font-size: 15px; }
    .count { font-size: 11px; color: #9a9a9a; }
    .group-note { font-size: 11.5px; color: #8a8a8a; margin-top: 2px; }
    .items { display: flex; flex-direction: column; margin-top: 8px; }
    .item { padding: 9px 0; border-bottom: 1px dotted #dcdcdc; }
    .item-title { font-size: 12.5px; font-weight: 500; }
    .item-meta { font-size: 11px; color: #9a9a9a; }
    .item-empty { font-size: 11.5px; color: #9a9a9a; padding: 9px 0; }
    .foot { font-size: 11.5px; color: #8a8a8a; margin-top: 14px; }
  `],
})
export class KnowledgeComponent {
  private readonly api = inject(ApiService);
  private readonly queries = new Subject<string>();

  readonly defaultSubtitle =
    'Institutional memory: architectural decisions, research findings, reusable patterns and '
    + 'lessons learned. A new employee should be able to find how Prolithica solved this before.';

  readonly query = signal('');
  readonly loading = signal(true);
  readonly error = signal(false);
  readonly view = signal<KnowledgeView | null>(null);
  readonly total = signal(0);

  readonly groups = computed<KnowledgeGroup[]>(() => this.view()?.groups ?? []);
  readonly placeholder = computed(
    () => this.view()?.search_placeholder
      || 'Search decisions, patterns, findings and documents',
  );

  constructor() {
    this.queries
      .pipe(
        debounceTime(220),
        distinctUntilChanged(),
        switchMap((search) => {
          this.loading.set(true);
          this.error.set(false);
          return this.api.list<KnowledgeArticle>('/knowledge/', { search, page_size: 200 });
        }),
        takeUntilDestroyed(),
      )
      .subscribe({
        next: (page: Paginated<KnowledgeArticle>) => {
          this.view.set((page.view as unknown as KnowledgeView) ?? null);
          this.total.set(page.count ?? (page.results ?? []).length);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.error.set(true);
        },
      });

    this.queries.next('');
  }

  onQuery(value: string): void {
    this.query.set(value);
    this.queries.next(value);
  }

  reload(): void {
    this.loading.set(true);
    this.error.set(false);
    this.api.list<KnowledgeArticle>('/knowledge/', { search: this.query(), page_size: 200 })
      .subscribe({
        next: (page) => {
          this.view.set((page.view as unknown as KnowledgeView) ?? null);
          this.total.set(page.count ?? 0);
          this.loading.set(false);
          this.error.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.error.set(true);
        },
      });
  }
}

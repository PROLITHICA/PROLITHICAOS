import { ThemeColorPipe } from '../../shared/ui/theme-color.pipe';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { forkJoin, of } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';

import { ApiService } from '../../core/api.service';
import { Paginated } from '../../core/models';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';

export interface ResearchThread {
  id: string;
  title: string;
  body: string;
  meta: string;
  stage: string;
  tag_class: string;
  output: string;
}

export interface Pattern { id: string; name: string; meta: string; }
export interface Lesson { id: string; text: string; meta: string; }

export interface FunnelBar {
  label: string;
  width: number;
  fill: string;
  text_col: string;
}

export interface RndDesk {
  title: string;
  subtitle: string;
  research: ResearchThread[];
  funnel: { title: string; subtitle: string; bars: FunnelBar[] };
  patterns: Pattern[];
  lessons: Lesson[];
}

/** Bars are 24px tall on a 32px pitch, starting at y=14 (design lines 913–921). */
interface FunnelRow extends FunnelBar { y: number; textY: number; }

const EMPTY_PAGE = { count: 0, next: null, previous: null, results: [] };

/** Research desk (design lines 886–951), served by `dashboard/rnd/`. */
@Component({
  selector: 'app-rnd',
  standalone: true,
  imports: [ThemeColorPipe, SkeletonComponent, EmptyStateComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './rnd.component.html',
  styleUrl: './rnd.component.css',
})
export class RndComponent {
  private readonly api = inject(ApiService);

  readonly loading = signal(true);
  readonly error = signal('');
  readonly desk = signal<RndDesk | null>(null);

  readonly research = computed<ResearchThread[]>(() => this.desk()?.research ?? []);
  readonly patterns = computed<Pattern[]>(() => this.desk()?.patterns ?? []);
  readonly lessons = computed<Lesson[]>(() => this.desk()?.lessons ?? []);
  readonly funnel = computed(() => this.desk()?.funnel ?? null);

  readonly funnelRows = computed<FunnelRow[]>(() =>
    (this.funnel()?.bars ?? []).map((bar, index) => ({
      ...bar,
      y: 14 + index * 32,
      textY: 31 + index * 32,
    })),
  );

  constructor() {
    this.load();
  }

  private load(): void {
    this.loading.set(true);
    this.error.set('');
    this.api
      .get<RndDesk>('/dashboard/rnd/')
      .pipe(
        // The desk delegates research/patterns/lessons to the knowledge app; when that
        // hand-off returns nothing we read the knowledge lists directly.
        switchMap((desk) => {
          const complete = desk.research?.length && desk.patterns?.length && desk.lessons?.length;
          if (complete) return of(desk);
          return forkJoin({
            research: this.list<ResearchThread>('/research/'),
            patterns: this.list<Pattern>('/patterns/'),
            lessons: this.list<Lesson>('/lessons/'),
          }).pipe(
            map((extra) => ({
              ...desk,
              research: desk.research?.length ? desk.research : extra.research,
              patterns: desk.patterns?.length ? desk.patterns : extra.patterns,
              lessons: desk.lessons?.length ? desk.lessons : extra.lessons,
            })),
          );
        }),
        catchError((error: unknown) => {
          const detail = error as { error?: { detail?: string }; message?: string };
          this.error.set(
            detail?.error?.detail || detail?.message || 'The research desk could not load.',
          );
          return of(null);
        }),
      )
      .subscribe((desk) => {
        this.loading.set(false);
        if (desk) this.desk.set(desk);
      });
  }

  private list<T>(path: string) {
    return this.api.list<T>(path, { page_size: 50 }).pipe(
      catchError(() => of(EMPTY_PAGE as unknown as Paginated<T>)),
      map((page) => page.results ?? []),
    );
  }

  reload(): void {
    this.load();
  }
}

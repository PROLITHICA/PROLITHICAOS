import { ThemeColorPipe } from '../../shared/ui/theme-color.pipe';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { of, switchMap } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import { ApiService } from '../../core/api.service';
import { ToastService } from '../../core/toast.service';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';

export interface ClosureItem {
  id: string;
  code: string;
  text: string;
  meta: string;
  owner_name: string;
  tag_class: string;
  confirmed: boolean;
  order: number;
}

export interface RetroLine { label: string; value: string; }

export interface Closure {
  id: string;
  project: string;
  project_ref: string;
  project_name: string;
  progress_label: string;
  cta: string;
  items: ClosureItem[];
  retro: RetroLine[];
  after_closure: string;
  support_contract_ref: string;
  closed: boolean;
}

/** Project closure (design lines 1403–1443), routed as `/closure`. */
@Component({
  selector: 'app-closure',
  standalone: true,
  imports: [ThemeColorPipe, SkeletonComponent, EmptyStateComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './closure.component.html',
  styleUrl: './closure.component.css',
})
export class ClosureComponent {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly toasts = inject(ToastService);

  readonly loading = signal(true);
  readonly error = signal('');
  readonly closure = signal<Closure | null>(null);
  readonly busy = signal('');
  readonly closing = signal(false);

  readonly kicker = computed(() => {
    const closure = this.closure();
    if (!closure) return '';
    return `Closure · ${closure.project_ref} · ${closure.project_name}`;
  });

  readonly items = computed(() =>
    (this.closure()?.items ?? []).map((item) => ({
      ...item,
      fill: item.confirmed ? 'var(--pl-color-111111)' : 'transparent',
      strike: item.confirmed ? 'line-through' : 'none',
      col: item.confirmed ? 'var(--pl-color-9a9a9a)' : 'var(--pl-color-111111)',
    })),
  );

  readonly retro = computed<RetroLine[]>(() => this.closure()?.retro ?? []);

  constructor() {
    this.route.queryParamMap
      .pipe(
        map((params) => params.get('project') || params.get('ref') || ''),
        switchMap((ref) => {
          this.loading.set(true);
          this.error.set('');
          return this.api.list<Closure>('/closures/', { search: ref, page_size: 25 }).pipe(
            map((page) => {
              const rows = page.results ?? [];
              if (!rows.length) throw new Error('No project is in closure.');
              const match = ref
                ? rows.find((row) => (row.project_ref ?? '').toLowerCase() === ref.toLowerCase())
                : undefined;
              return match ?? rows[0];
            }),
            catchError((error: unknown) => {
              this.error.set(this.message(error));
              return of(null);
            }),
          );
        }),
      )
      .subscribe((closure) => {
        this.loading.set(false);
        if (closure) this.closure.set(closure);
      });
  }

  toggle(item: ClosureItem): void {
    const closure = this.closure();
    if (!closure || this.busy()) return;
    this.busy.set(item.id);
    this.api
      .post<{ record: Closure; item: ClosureItem; toast?: string }>(
        `/closures/${closure.id}/items/${item.id}/toggle/`,
        {},
      )
      .subscribe({
        next: (response) => {
          this.busy.set('');
          if (response.record) this.closure.set(response.record);
          this.toasts.show(response.toast);
        },
        error: () => {
          this.busy.set('');
          this.toasts.show('That closure condition could not be updated.');
        },
      });
  }

  closeProject(): void {
    const closure = this.closure();
    if (!closure || this.closing()) return;
    this.closing.set(true);
    this.api.post<{ record: Closure; toast?: string }>(`/closures/${closure.id}/close/`, {}).subscribe({
      next: (response) => {
        this.closing.set(false);
        if (response.record) this.closure.set(response.record);
        this.toasts.show(response.toast);
      },
      error: (error: unknown) => {
        this.closing.set(false);
        const body = (error as { error?: { toast?: string } })?.error;
        this.toasts.show(body?.toast || 'Closure blocked: conditions are still outstanding.');
      },
    });
  }

  private message(error: unknown): string {
    const detail = (error as { error?: { detail?: string }; message?: string });
    return detail?.error?.detail || detail?.message || 'No project is in closure.';
  }
}

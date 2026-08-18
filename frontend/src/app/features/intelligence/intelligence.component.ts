import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { RecordRow } from '../../core/models';
import { DataTableComponent } from '../../shared/ui/data-table/data-table.component';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';

/** One cited record beneath an answer. */
export interface AskRow {
  record: string;
  detail: string;
  figure: string;
}

/** `GET`/`POST /api/intelligence/ask/`. */
export interface AskPayload {
  title?: string;
  subtitle?: string;
  suggestions?: string[];
  question: string;
  answer: string;
  rows: AskRow[];
  source: string;
  permitted: boolean;
}

const SUBTITLE = "Questions answered from the company's own records, inside your permissions. "
  + 'Answers cite the records they came from.';

/** Ask Prolithica — analytical answers grounded in the company's own records. */
@Component({
  selector: 'app-intelligence',
  standalone: true,
  imports: [FormsModule, DataTableComponent, SkeletonComponent, EmptyStateComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <h1 class="title">{{ payload()?.title || 'Ask Prolithica' }}</h1>
    <div class="sub">{{ payload()?.subtitle || subtitle }}</div>

    <div class="ask">
      <input class="input ask-input" type="text" [(ngModel)]="question"
             (keydown.enter)="run()"
             placeholder="Ask about projects, clients, money or risk"
             aria-label="Ask about projects, clients, money or risk">
      <button type="button" class="btn btn-primary ask-btn" [disabled]="busy()" (click)="run()">
        @if (busy()) { <span class="spin"></span> }
        Ask
      </button>
    </div>

    <div class="suggestions">
      @for (suggestion of suggestions(); track suggestion) {
        <button type="button" class="btn btn-secondary pill" (click)="askThis(suggestion)">
          {{ suggestion }}
        </button>
      }
    </div>

    @if (loading()) {
      <div class="answer"><app-skeleton height="180px" /></div>
    } @else if (failed()) {
      <div class="answer">
        <app-empty-state
          heading="Ask Prolithica did not answer"
          note="The analysis desk could not be reached. Try the question again."
          actionLabel="Try again"
          (action)="run()" />
      </div>
    } @else {
      @if (payload(); as data) {
      <div class="answer card">
        <div class="kicker">{{ data.question }}</div>
        <div class="text">{{ data.answer }}</div>
        @if (data.permitted && data.rows.length) {
          <div class="table-wrap">
            <app-data-table
              [cols]="cols"
              [rows]="rows()"
              [minWidth]="520"
              [clickable]="false"
              emptyText="No records were cited." />
          </div>
        }
        <div class="foot">Grounded in {{ data.source }} · answered inside {{ person() }}'s permissions</div>
      </div>
      }
    }
  `,
  styles: [`
    :host { display: block; }
    .title { font-size: 28px; margin: 0 0 4px; }
    .sub { font-size: 12.5px; color: #8a8a8a; max-width: 74ch; }
    .ask { display: flex; flex-wrap: wrap; gap: 9px; margin-top: 18px; max-width: 900px; }
    .ask-input { flex: 1 1 320px; min-width: 260px; background: #fafafa; border-color: #b5b5b5; }
    .ask-btn { white-space: nowrap; }
    .suggestions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
    .pill { border-color: #b5b5b5; font-size: 12px; padding: 6px 14px; }
    .answer { margin-top: 18px; max-width: 900px; }
    .kicker {
      font-size: 10.5px; letter-spacing: 0.1em; text-transform: uppercase; color: #9a9a9a;
    }
    .text { font-size: 15px; margin-top: 8px; max-width: 70ch; }
    .table-wrap { margin-top: 12px; }
    .foot { font-size: 11px; color: #9a9a9a; margin-top: 10px; }
  `],
})
export class IntelligenceComponent {
  private readonly api = inject(ApiService);
  private readonly auth = inject(AuthService);

  readonly subtitle = SUBTITLE;
  readonly cols = [{ l: 'Record' }, { l: 'Detail' }, { l: 'Figure', a: 'right' as const }];

  readonly payload = signal<AskPayload | null>(null);
  readonly loading = signal(true);
  readonly failed = signal(false);
  readonly busy = signal(false);
  question = '';

  readonly suggestions = computed<string[]>(() => this.payload()?.suggestions ?? []);
  readonly person = computed(() => this.auth.currentUser()?.display_name ?? '');

  readonly rows = computed<RecordRow[]>(() =>
    (this.payload()?.rows ?? []).map((row) => ({
      cells: [
        { t: row.record, align: 'left' as const, bold: true },
        { t: row.detail, align: 'left' as const, muted: true },
        { t: row.figure, align: 'right' as const },
      ],
    })),
  );

  constructor() {
    this.api.get<AskPayload>('/intelligence/ask/').subscribe({
      next: (payload) => {
        this.payload.set(payload);
        this.question = payload.question ?? '';
        this.loading.set(false);
      },
      error: () => {
        this.failed.set(true);
        this.loading.set(false);
      },
    });
  }

  askThis(suggestion: string): void {
    this.question = suggestion;
    this.run();
  }

  run(): void {
    const question = (this.question || '').trim();
    if (!question || this.busy()) return;
    this.busy.set(true);
    this.failed.set(false);
    this.api.post<AskPayload>('/intelligence/ask/', { question }).subscribe({
      next: (payload) => {
        this.payload.set(payload);
        this.busy.set(false);
        this.loading.set(false);
      },
      error: () => {
        this.busy.set(false);
        this.loading.set(false);
        this.failed.set(true);
      },
    });
  }
}

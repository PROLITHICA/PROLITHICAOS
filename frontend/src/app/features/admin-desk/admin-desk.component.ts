import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { Observable, catchError, forkJoin, map, of } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { RecordCell, RecordRow, TagClass } from '../../core/models';
import { ToastService } from '../../core/toast.service';
import { DataTableComponent } from '../../shared/ui/data-table/data-table.component';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';
import { LoadFailure, describeError } from '../../shared/util/record-detail';

export interface Meeting {
  id: string; time: string; title: string; meta: string; attached_ref: string; day_label: string;
}

export interface SignatureRequest {
  id: string; key: string; text: string; meta: string; state: string;
  cta: string; button_class: string;
}

export interface CorrespondenceItem {
  id: string; item: string; attached: string; owner: string; due: string;
  state: string; tag_class: string;
}

interface Section<T> { rows: T[]; failure: LoadFailure | null; }
interface SendResult { record: SignatureRequest; toast: string; }

function empty<T>(): Section<T> {
  return { rows: [], failure: null };
}

/** `/admin-desk` — the secretariat Day desk (design lines 951-1027). */
@Component({
  selector: 'app-admin-desk',
  standalone: true,
  imports: [SkeletonComponent, EmptyStateComponent, DataTableComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './admin-desk.component.html',
  styleUrl: './admin-desk.component.css',
})
export class AdminDeskComponent {
  private readonly api = inject(ApiService);
  private readonly toasts = inject(ToastService);

  readonly loading = signal(true);
  readonly meetings = signal<Section<Meeting>>(empty<Meeting>());
  readonly signatures = signal<Section<SignatureRequest>>(empty<SignatureRequest>());
  readonly correspondence = signal<Section<CorrespondenceItem>>(empty<CorrespondenceItem>());
  readonly sending = signal<string>('');

  readonly correspondenceCols = [
    { l: 'Item' }, { l: 'Attached to' }, { l: 'Owner' }, { l: 'Due' }, { l: 'State' },
  ];

  readonly correspondenceRows = computed<RecordRow[]>(() =>
    this.correspondence().rows.map((row) => ({
      id: row.id,
      cells: [
        { t: row.item },
        { t: row.attached, muted: true },
        { t: row.owner, muted: true },
        { t: row.due, muted: true },
        { t: row.state, tag: row.tag_class as TagClass },
      ] as RecordCell[],
    })),
  );

  /** Every section refused: show one clear permission state instead of three. */
  readonly blocked = computed<LoadFailure | null>(() => {
    const failures = [
      this.meetings().failure, this.signatures().failure, this.correspondence().failure,
    ];
    if (failures.every((failure) => failure?.forbidden)) return failures[0];
    return null;
  });

  constructor() {
    this.load();
  }

  send(signature: SignatureRequest): void {
    if (this.sending() || signature.state !== 'draft') return;
    this.sending.set(signature.id);
    this.api.post<SendResult>(`/signatures/${signature.id}/send/`).subscribe({
      next: (response) => {
        const updated = response.record;
        if (updated) {
          this.signatures.update((section) => ({
            ...section,
            rows: section.rows.map((row) => (row.id === updated.id ? updated : row)),
          }));
        }
        this.toasts.show(response.toast);
        this.sending.set('');
      },
      error: (error: unknown) => {
        this.toasts.show(describeError(error, 'This signature request').heading);
        this.sending.set('');
      },
    });
  }

  ctaFor(signature: SignatureRequest): string {
    if (this.sending() === signature.id) return 'Sending…';
    return signature.cta || (signature.state === 'draft'
      ? 'Send for signature' : 'Sent for signature');
  }

  private load(): void {
    this.loading.set(true);
    forkJoin({
      meetings: this.section<Meeting>('/meetings/', 'Today’s meetings'),
      signatures: this.section<SignatureRequest>('/signatures/', 'Signature requests'),
      correspondence: this.section<CorrespondenceItem>('/correspondence/', 'Correspondence'),
    }).subscribe((result) => {
      this.meetings.set(result.meetings);
      this.signatures.set(result.signatures);
      this.correspondence.set(result.correspondence);
      this.loading.set(false);
    });
  }

  private section<T>(path: string, subject: string): Observable<Section<T>> {
    return this.api.list<T>(path, { page_size: 100 }).pipe(
      map((page) => ({ rows: page.results ?? [], failure: null }) as Section<T>),
      catchError((error: unknown) =>
        of({ rows: [], failure: describeError(error, subject) } as Section<T>)),
    );
  }
}

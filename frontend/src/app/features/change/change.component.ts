import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { PermissionService } from '../../core/permission.service';
import { ToastService } from '../../core/toast.service';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { FieldSpec } from '../../shared/ui/field/field.component';
import { ModalComponent } from '../../shared/ui/modal/modal.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';
import { LoadFailure, describeError, loadByRef } from '../../shared/util/record-detail';

export interface FlowStep { name: string; meta: string; weight: number; bg: string; border: string; }
export interface ChangeField { label: string; value: string; }
export interface WritebackLine { text: string; record: string; }

export interface ChangeDetail {
  id: string;
  ref: string;
  name: string;
  title?: string;
  display_name: string;
  project_label: string;
  state: string;
  tag_class: string;
  priced: boolean;
  kicker: string;
  subtitle: string;
  flow: FlowStep[];
  fields_block: ChangeField[];
  writeback: WritebackLine[];
  price_cta_label: string;
}

interface ActionResult { record: ChangeDetail; toast: string; }

const REJECT_FIELDS: FieldSpec[] = [
  { k: 'reason', l: 'Reason', p: 'A rejection has to carry a reason', t: 'area' },
];

/** `/changes/:ref` — the change request screen (design lines 1355-1403). */
@Component({
  selector: 'app-change',
  standalone: true,
  imports: [SkeletonComponent, EmptyStateComponent, ModalComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './change.component.html',
  styleUrl: './change.component.css',
})
export class ChangeComponent {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly toasts = inject(ToastService);
  readonly perms = inject(PermissionService);

  readonly loading = signal(true);
  readonly failure = signal<LoadFailure | null>(null);
  readonly change = signal<ChangeDetail | null>(null);
  readonly busy = signal<'' | 'price' | 'approve' | 'reject'>('');
  readonly rejectOpen = signal(false);

  readonly rejectFields = REJECT_FIELDS;

  readonly canPrice = computed(() => this.perms.can('contracts', 'full'));
  readonly canDecide = computed(() => this.perms.can('contracts', 'approve'));
  readonly decided = computed(() => {
    const state = this.change()?.state ?? '';
    return state.startsWith('Approved') || state === 'Rejected';
  });

  constructor() {
    this.route.paramMap.subscribe((params) => this.load(params.get('ref') ?? ''));
  }

  price(): void {
    const record = this.change();
    if (!record || record.priced) return;
    this.run('price', `/change-requests/${record.id}/price/`);
  }

  approve(): void {
    const record = this.change();
    if (!record) return;
    this.run('approve', `/change-requests/${record.id}/approve/`);
  }

  submitReject(values: Record<string, string>): void {
    const record = this.change();
    const reason = (values['reason'] ?? '').trim();
    if (!record) return;
    if (!reason) {
      this.toasts.show('A rejection has to carry a reason — that is the point of the record.');
      return;
    }
    this.run('reject', `/change-requests/${record.id}/reject/`, { reason }, () =>
      this.rejectOpen.set(false));
  }

  private run(
    kind: 'price' | 'approve' | 'reject',
    path: string,
    body: Record<string, string> = {},
    done?: () => void,
  ): void {
    if (this.busy()) return;
    this.busy.set(kind);
    this.api.post<ActionResult>(path, body).subscribe({
      next: (response) => {
        if (response.record) this.change.set(response.record);
        this.toasts.show(response.toast);
        this.busy.set('');
        done?.();
      },
      error: (error: unknown) => {
        this.toasts.show(describeError(error, 'This change request').heading);
        this.busy.set('');
      },
    });
  }

  private load(ref: string): void {
    this.loading.set(true);
    this.failure.set(null);
    loadByRef<ChangeDetail>(this.api, '/change-requests', ref).subscribe({
      next: (record) => {
        this.change.set(record);
        this.loading.set(false);
      },
      error: (error: unknown) => {
        this.change.set(null);
        this.failure.set(describeError(error, 'This change request'));
        this.loading.set(false);
      },
    });
  }
}

import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { RecordCell, RecordRow, TagClass } from '../../core/models';
import { PermissionService } from '../../core/permission.service';
import { ToastService } from '../../core/toast.service';
import { DataTableComponent } from '../../shared/ui/data-table/data-table.component';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { FieldSpec } from '../../shared/ui/field/field.component';
import { ModalComponent } from '../../shared/ui/modal/modal.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';
import { LoadFailure, describeError, loadByRef } from '../../shared/util/record-detail';

export interface ContractTerm { label: string; value: string; }
export interface SchedulePayment {
  name: string; trigger: string; amount: string; due: string; state: string; tagClass: string;
}
export interface Amendment { name: string; meta: string; state: string; tag_class: string; }

export interface ContractDetail {
  id: string;
  ref: string;
  name: string;
  title?: string;
  display_name: string;
  organisation_name: string;
  kicker: string;
  subtitle: string;
  terms: ContractTerm[];
  schedule: SchedulePayment[];
  amendments: Amendment[];
}

interface AmendResult { record: ContractDetail; toast: string; }

const AMEND_FIELDS: FieldSpec[] = [
  { k: 'change_request', l: 'Change request', p: 'CR-014 — optional' },
  { k: 'name', l: 'Amendment', p: 'What is changing' },
  { k: 'meta', l: 'Note', p: 'Approved 30 Jul · R 0.38m assessed', t: 'area' },
];

/** `/contracts/:ref` — the contract screen (design lines 1306-1355). */
@Component({
  selector: 'app-contract',
  standalone: true,
  imports: [
    RouterLink, SkeletonComponent, EmptyStateComponent, DataTableComponent, ModalComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './contract.component.html',
  styleUrl: './contract.component.css',
})
export class ContractComponent {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly toasts = inject(ToastService);
  readonly perms = inject(PermissionService);

  readonly loading = signal(true);
  readonly failure = signal<LoadFailure | null>(null);
  readonly contract = signal<ContractDetail | null>(null);
  readonly amendOpen = signal(false);
  readonly amending = signal(false);

  readonly amendFields = AMEND_FIELDS;
  readonly scheduleCols = [
    { l: 'Payment' }, { l: 'Trigger' }, { l: 'Amount', a: 'right' as const },
    { l: 'Due' }, { l: 'State' },
  ];

  readonly scheduleRows = computed<RecordRow[]>(() =>
    (this.contract()?.schedule ?? []).map((payment) => ({
      cells: [
        { t: payment.name, bold: true },
        { t: payment.trigger, muted: true },
        { t: payment.amount, align: 'right' as const },
        { t: payment.due, muted: true },
        { t: payment.state, tag: payment.tagClass as TagClass },
      ] as RecordCell[],
    })),
  );

  readonly canAmend = computed(() => this.perms.can('contracts', 'full'));

  constructor() {
    this.route.paramMap.subscribe((params) => this.load(params.get('ref') ?? ''));
  }

  submitAmend(values: Record<string, string>): void {
    const record = this.contract();
    if (!record || this.amending()) return;
    this.amending.set(true);
    this.api.post<AmendResult>(`/contracts/${record.id}/amend/`, {
      change_request: (values['change_request'] ?? '').trim(),
      name: (values['name'] ?? '').trim() || 'Amendment',
      meta: (values['meta'] ?? '').trim(),
    }).subscribe({
      next: (response) => {
        if (response.record) this.contract.set(response.record);
        this.toasts.show(response.toast);
        this.amending.set(false);
        this.amendOpen.set(false);
      },
      error: (error: unknown) => {
        this.toasts.show(describeError(error, 'This contract').heading);
        this.amending.set(false);
      },
    });
  }

  private load(ref: string): void {
    this.loading.set(true);
    this.failure.set(null);
    loadByRef<ContractDetail>(this.api, '/contracts', ref).subscribe({
      next: (record) => {
        this.contract.set(record);
        this.loading.set(false);
      },
      error: (error: unknown) => {
        this.contract.set(null);
        this.failure.set(describeError(error, 'This contract'));
        this.loading.set(false);
      },
    });
  }
}

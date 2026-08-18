import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { PermissionService } from '../../core/permission.service';
import { ToastService } from '../../core/toast.service';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';
import { LoadFailure, describeError, loadByRef } from '../../shared/util/record-detail';

export interface StageChip {
  n: string; name: string; when: string; weight: number; bg: string; border: string;
}
export interface DiscoveryFinding { label: string; value: string; trace: string; }
export interface OppRequirement { id: string; text: string; state: string; tagClass: string; }
export interface LabelledValue { label: string; value: string; }

export interface OpportunityDetail {
  id: string;
  ref: string;
  name: string;
  title?: string;
  organisation_name: string;
  stage: string;
  kicker: string;
  subtitle: string;
  stages: StageChip[];
  discovery: DiscoveryFinding[];
  requirements: OppRequirement[];
  fields_block: LabelledValue[];
}

interface ActionResult { record: OpportunityDetail; toast: string; }

/** `/opportunities/:ref` — opportunity and discovery (design lines 1248-1306). */
@Component({
  selector: 'app-opportunity',
  standalone: true,
  imports: [RouterLink, SkeletonComponent, EmptyStateComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './opportunity.component.html',
  styleUrl: './opportunity.component.css',
})
export class OpportunityComponent {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly toasts = inject(ToastService);
  readonly perms = inject(PermissionService);

  readonly loading = signal(true);
  readonly failure = signal<LoadFailure | null>(null);
  readonly opportunity = signal<OpportunityDetail | null>(null);
  readonly advancing = signal(false);

  constructor() {
    this.route.paramMap.subscribe((params) => this.load(params.get('ref') ?? ''));
  }

  canAdvance(record: OpportunityDetail): boolean {
    return this.perms.can('contracts', 'full')
      && record.stage !== 'Won' && record.stage !== 'Lost';
  }

  advance(): void {
    const record = this.opportunity();
    if (!record || this.advancing()) return;
    this.advancing.set(true);
    this.api.post<ActionResult>(`/opportunities/${record.id}/advance/`).subscribe({
      next: (response) => {
        if (response.record) this.opportunity.set(response.record);
        this.toasts.show(response.toast);
        this.advancing.set(false);
      },
      error: (error: unknown) => {
        this.toasts.show(describeError(error, 'This opportunity').heading);
        this.advancing.set(false);
      },
    });
  }

  private load(ref: string): void {
    this.loading.set(true);
    this.failure.set(null);
    loadByRef<OpportunityDetail>(this.api, '/opportunities', ref).subscribe({
      next: (record) => {
        this.opportunity.set(record);
        this.loading.set(false);
      },
      error: (error: unknown) => {
        this.opportunity.set(null);
        this.failure.set(describeError(error, 'This opportunity'));
        this.loading.set(false);
      },
    });
  }
}

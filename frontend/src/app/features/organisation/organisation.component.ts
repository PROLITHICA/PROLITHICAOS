import { ThemeColorPipe } from '../../shared/ui/theme-color.pipe';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';
import { LoadFailure, describeError, loadByRef } from '../../shared/util/record-detail';

export interface OrgFigure { label: string; value: string; note: string; col?: string; }
export interface OrgRelatedRow {
  name: string; meta: string; value: string; state: string; tagClass: string;
}
export interface OrgRelatedGroup { heading: string; meta: string; rows: OrgRelatedRow[]; }
export interface OrgContact { id?: string; name: string; role_label: string; note: string; }
export interface OrgActivity { when: string; what: string; record?: string; }

export interface OrganisationDetail {
  id: string;
  ref: string;
  name: string;
  list_name: string;
  kicker: string;
  subtitle: string;
  figures: OrgFigure[];
  related: OrgRelatedGroup[];
  contacts: OrgContact[];
  activity: OrgActivity[];
}

/** `/organisations/:ref` — the organisation profile (design lines 1181-1248). */
@Component({
  selector: 'app-organisation',
  standalone: true,
  imports: [ThemeColorPipe, RouterLink, SkeletonComponent, EmptyStateComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './organisation.component.html',
  styleUrl: './organisation.component.css',
})
export class OrganisationComponent {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly loading = signal(true);
  readonly failure = signal<LoadFailure | null>(null);
  readonly org = signal<OrganisationDetail | null>(null);

  readonly ref = computed(() => this.org()?.ref ?? this.route.snapshot.paramMap.get('ref') ?? '');

  constructor() {
    this.route.paramMap.subscribe((params) => this.load(params.get('ref') ?? ''));
  }

  private load(ref: string): void {
    this.loading.set(true);
    this.failure.set(null);
    loadByRef<OrganisationDetail>(this.api, '/organisations', ref).subscribe({
      next: (record) => {
        this.org.set(record);
        this.loading.set(false);
      },
      error: (error: unknown) => {
        this.org.set(null);
        this.failure.set(describeError(error, 'This organisation'));
        this.loading.set(false);
      },
    });
  }

  newOpportunity(): void {
    void this.router.navigate(['/records/opportunities']);
  }
}

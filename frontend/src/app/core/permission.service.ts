import { Injectable, computed, inject } from '@angular/core';

import { AuthService } from './auth.service';
import { NavGroup, PermissionLevel, PermissionMap, Scope } from './models';

/** The ladder, lowest to highest. Index is the rank. */
export const LEVELS: PermissionLevel[] = [
  'none', 'read', 'contribute', 'restricted', 'full', 'approve', 'administer',
];

export const LEVEL_RANK: Record<string, number> = LEVELS.reduce(
  (acc, level, index) => ({ ...acc, [level]: index }),
  {} as Record<string, number>,
);

/** Mirrors the server's RBAC so the shell can hide what the API would refuse. */
@Injectable({ providedIn: 'root' })
export class PermissionService {
  private readonly auth = inject(AuthService);

  readonly permissions = computed<PermissionMap>(() => this.auth.currentUser()?.permissions ?? {});
  readonly scope = computed<Scope>(() => this.auth.currentUser()?.scope ?? 'own_records');
  readonly navGroups = computed<NavGroup[]>(() => this.auth.currentUser()?.nav_groups ?? []);
  readonly isDirector = computed(() => !!this.auth.currentUser()?.role?.is_director);

  /** The level granted on `area`. */
  levelFor(area: string): PermissionLevel {
    return this.permissions()[area] ?? 'none';
  }

  /** True when the current user holds at least `minLevel` on `area`. */
  can(area: string, minLevel: PermissionLevel = 'read'): boolean {
    if (!this.auth.isAuthenticated()) return false;
    if (this.isDirector()) return true;
    return (LEVEL_RANK[this.levelFor(area)] ?? 0) >= (LEVEL_RANK[minLevel] ?? 0);
  }

  /** Parses the directive/guard shorthand `"finance:full"`. */
  canExpression(expression: string): boolean {
    const [area, level] = expression.split(':');
    return this.can(area.trim(), ((level ?? 'read').trim() as PermissionLevel));
  }

  /** Money is masked unless the role holds `financials >= restricted`. */
  seesMoney(): boolean {
    return this.can('financials', 'restricted')
      || this.can('finance', 'restricted')
      || this.can('project_financials', 'restricted');
  }
}

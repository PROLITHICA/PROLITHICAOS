import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { catchError, map, of } from 'rxjs';

import { AuthService } from './auth.service';
import { PermissionLevel } from './models';
import { PermissionService } from './permission.service';

/** Requires a signed-in user; resolves `/api/auth/me/` on a cold load. */
export const authGuard: CanActivateFn = (_route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (auth.isAuthenticated()) return true;
  if (!auth.hasToken()) {
    return router.createUrlTree(['/login'], { queryParams: { next: state.url } });
  }

  return auth.me().pipe(
    map(() => true),
    catchError(() => {
      auth.clear();
      return of(router.createUrlTree(['/login'], { queryParams: { next: state.url } }));
    }),
  );
};

/** Requires at least `level` on `area`; otherwise back to the user's home view. */
export function permissionGuard(area: string, level: PermissionLevel = 'read'): CanActivateFn {
  return () => {
    const perms = inject(PermissionService);
    const auth = inject(AuthService);
    const router = inject(Router);
    if (perms.can(area, level)) return true;
    return router.createUrlTree([auth.homeRoute()]);
  };
}

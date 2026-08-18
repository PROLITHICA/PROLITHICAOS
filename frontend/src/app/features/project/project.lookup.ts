import { Observable, map, of, switchMap } from 'rxjs';

import { ApiService } from '../../core/api.service';

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

interface Identified { id: string; ref: string; }

/**
 * Routes address a project by its human reference (`PRJ-041`); the API keys on
 * the uuid primary key. This turns one into the other, and passes a uuid
 * straight through so a route can carry either.
 */
export function resolveProjectId(api: ApiService, ref: string): Observable<string> {
  if (!ref) return of('');
  if (UUID.test(ref)) return of(ref);
  return api.list<Identified>('/projects/', { search: ref, page_size: 50 }).pipe(
    map((page) => {
      const rows = page.results ?? [];
      const exact = rows.find((row) => (row.ref ?? '').toLowerCase() === ref.toLowerCase());
      const chosen = exact ?? rows[0];
      if (!chosen) throw new Error(`No project matches ${ref}.`);
      return chosen.id;
    }),
  );
}

/** `resolveProjectId` followed by a call that needs the uuid. */
export function withProjectId<T>(
  api: ApiService,
  ref: string,
  next: (id: string) => Observable<T>,
): Observable<T> {
  return resolveProjectId(api, ref).pipe(switchMap(next));
}

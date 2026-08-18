import { HttpErrorResponse } from '@angular/common/http';
import { Observable, switchMap, throwError } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { Paginated } from '../../core/models';

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export interface RefRecord {
  id?: string;
  ref?: string;
}

/**
 * Detail routes carry the human reference ("ORG-006") while DRF looks records
 * up by uuid, so resolve the ref through the list endpoint first. A uuid in the
 * URL is fetched directly.
 */
export function loadByRef<T extends RefRecord>(
  api: ApiService, path: string, ref: string,
): Observable<T> {
  const clean = (ref ?? '').trim();
  if (!clean) return notFound<T>();
  if (UUID.test(clean)) return api.get<T>(`${path}/${clean}/`);

  return api.list<T>(path, { search: clean, page_size: 50 }).pipe(
    switchMap((page: Paginated<T>) => {
      const rows = page.results ?? [];
      const hit = rows.find((row) => (row.ref ?? '').toLowerCase() === clean.toLowerCase())
        ?? (rows.length === 1 ? rows[0] : undefined);
      if (!hit?.id) return notFound<T>();
      return api.get<T>(`${path}/${hit.id}/`);
    }),
  );
}

function notFound<T>(): Observable<T> {
  return throwError(() => new HttpErrorResponse({ status: 404, statusText: 'Not Found' }));
}

export interface LoadFailure {
  heading: string;
  note: string;
  forbidden: boolean;
}

/** Turns an HTTP failure into the empty-state copy the screen should show. */
export function describeError(error: unknown, subject: string): LoadFailure {
  const status = error instanceof HttpErrorResponse ? error.status : 0;
  if (status === 403 || status === 401) {
    return {
      heading: 'Your role cannot see this',
      note: `${subject} sits behind a permission your role does not hold. Ask the executive `
        + 'office if you need it — the request is recorded either way.',
      forbidden: true,
    };
  }
  if (status === 404) {
    return {
      heading: `${subject} was not found`,
      note: 'The reference in the address does not match a record you can see.',
      forbidden: false,
    };
  }
  return {
    heading: `${subject} could not be loaded`,
    note: 'The server did not answer. Reload the page, and if it happens again tell the '
      + 'executive office.',
    forbidden: false,
  };
}

/** The design's date format for freshly created records: `18 Aug 2026`. */
export function todayLabel(now: Date = new Date()): string {
  const month = now.toLocaleString('en-GB', { month: 'short' });
  return `${now.getDate()} ${month} ${now.getFullYear()}`;
}

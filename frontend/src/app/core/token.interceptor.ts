import { HttpErrorResponse, HttpEvent, HttpHandlerFn, HttpInterceptorFn, HttpRequest } from '@angular/common/http';
import { inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable, catchError, filter, switchMap, take, throwError } from 'rxjs';

import { AuthService } from './auth.service';
import { deployment } from './deployment';

let refreshing = false;
const refreshed = new BehaviorSubject<string | null>(null);

function withToken(request: HttpRequest<unknown>, token: string): HttpRequest<unknown> {
  return request.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
}

/** Attaches the bearer token, refreshes once on 401, otherwise sends you to /login. */
export const tokenInterceptor: HttpInterceptorFn = (
  request: HttpRequest<unknown>,
  next: HttpHandlerFn,
): Observable<HttpEvent<unknown>> => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const http = inject(HttpClient);
  // Only our API requests receive authentication or the configured API origin.
  if (!request.url.startsWith('/api/')) return next(request);
  if (deployment.apiOrigin) request = request.clone({ url: deployment.apiOrigin + request.url });

  const isAuthCall = request.url.includes('/api/auth/login/')
    || request.url.includes('/api/auth/refresh/')
    || request.url.includes('/api/auth/password/reset/');

  const token = auth.accessToken;
  const outgoing = token && !isAuthCall ? withToken(request, token) : request;

  return next(outgoing).pipe(
    catchError((error: unknown) => {
      if (!(error instanceof HttpErrorResponse) || error.status !== 401 || isAuthCall) {
        return throwError(() => error);
      }

      const refresh = auth.refreshToken;
      if (!refresh) {
        auth.clear();
        void router.navigate(['/login']);
        return throwError(() => error);
      }

      if (refreshing) {
        return refreshed.pipe(
          filter((value): value is string => value !== null),
          take(1),
          switchMap((fresh) => next(withToken(request, fresh))),
        );
      }

      refreshing = true;
      refreshed.next(null);

      return http.post<{ access: string; refresh?: string }>('/api/auth/refresh/', { refresh }).pipe(
        switchMap((response) => {
          refreshing = false;
          auth.storeTokens(response.access, response.refresh ?? refresh);
          refreshed.next(response.access);
          return next(withToken(request, response.access));
        }),
        catchError((refreshError: unknown) => {
          refreshing = false;
          refreshed.next(null);
          auth.clear();
          void router.navigate(['/login']);
          return throwError(() => refreshError);
        }),
      );
    }),
  );
};

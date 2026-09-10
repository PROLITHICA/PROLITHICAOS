import { HttpClient, HttpEvent, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { Paginated } from './models';

export type Params = Record<string, string | number | boolean | null | undefined>;

/** Thin typed wrapper over HttpClient. Every path is relative to `/api`. */
@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  readonly base = '/api';

  private url(path: string): string {
    const clean = path.startsWith('/') ? path : `/${path}`;
    return `${this.base}${clean}`;
  }

  private params(params?: Params): HttpParams {
    let http = new HttpParams();
    if (params) {
      for (const [key, value] of Object.entries(params)) {
        if (value !== null && value !== undefined && value !== '') {
          http = http.set(key, String(value));
        }
      }
    }
    return http;
  }

  list<T>(path: string, params?: Params): Observable<Paginated<T>> {
    return this.http.get<Paginated<T>>(this.url(path), { params: this.params(params) });
  }

  get<T>(path: string, params?: Params): Observable<T> {
    return this.http.get<T>(this.url(path), { params: this.params(params) });
  }

  post<T>(path: string, body?: unknown): Observable<T> {
    return this.http.post<T>(this.url(path), body ?? {});
  }

  patch<T>(path: string, body?: unknown): Observable<T> {
    return this.http.patch<T>(this.url(path), body ?? {});
  }

  put<T>(path: string, body?: unknown): Observable<T> {
    return this.http.put<T>(this.url(path), body ?? {});
  }

  delete<T>(path: string): Observable<T> {
    return this.http.delete<T>(this.url(path));
  }

  /**
   * Multipart upload reporting its progress, so an upload can show a bar and
   * settle on a result. Emits HttpEvents; the caller reads UploadProgress then
   * Response.
   */
  uploadEvents<T>(path: string, file: File, fields?: Params): Observable<HttpEvent<T>> {
    return this.http.post<T>(this.url(path), this.multipart(file, fields), {
      reportProgress: true,
      observe: 'events',
    });
  }

  /** A file the API streams back, with download progress. */
  downloadEvents(path: string): Observable<HttpEvent<Blob>> {
    return this.http.get(this.url(path), {
      responseType: 'blob',
      reportProgress: true,
      observe: 'events',
    });
  }

  private multipart(file: File, fields?: Params): FormData {
    const form = new FormData();
    form.append('file', file, file.name);
    if (fields) {
      for (const [key, value] of Object.entries(fields)) {
        if (value !== null && value !== undefined) form.append(key, String(value));
      }
    }
    return form;
  }

  /** Multipart upload — `file` plus any extra scalar fields. */
  upload<T>(path: string, file: File, fields?: Params): Observable<T> {
    return this.http.post<T>(this.url(path), this.multipart(file, fields));
  }
}

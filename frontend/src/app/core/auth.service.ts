import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';

import { LoginResponse, User } from './models';

const ACCESS_KEY = 'pl.access';
const REFRESH_KEY = 'pl.refresh';

/** Signal-based session state. The server stays the source of truth. */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  readonly currentUser = signal<User | null>(null);
  readonly booted = signal(false);
  readonly isAuthenticated = computed(() => this.currentUser() !== null);

  get accessToken(): string | null {
    return this.read(ACCESS_KEY);
  }

  get refreshToken(): string | null {
    return this.read(REFRESH_KEY);
  }

  hasToken(): boolean {
    return !!this.accessToken;
  }

  login(email: string, password: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>('/api/auth/login/', { email, password }).pipe(
      tap((response) => {
        this.storeTokens(response.access, response.refresh);
        this.currentUser.set(response.user);
        this.booted.set(true);
      }),
    );
  }

  me(): Observable<User> {
    return this.http.get<User>('/api/auth/me/').pipe(
      tap((user) => {
        this.currentUser.set(user);
        this.booted.set(true);
      }),
    );
  }

  logout(navigate = true): void {
    const token = this.accessToken;
    if (token) {
      this.http.post('/api/auth/logout/', {}).subscribe({ next: () => {}, error: () => {} });
    }
    this.clear();
    if (navigate) void this.router.navigate(['/login']);
  }

  storeTokens(access: string, refresh?: string | null): void {
    this.write(ACCESS_KEY, access);
    if (refresh) this.write(REFRESH_KEY, refresh);
  }

  clear(): void {
    this.currentUser.set(null);
    this.remove(ACCESS_KEY);
    this.remove(REFRESH_KEY);
  }

  /** Route the user lands on after signing in — their department's home view. */
  homeRoute(user?: User | null): string {
    const target = user ?? this.currentUser();
    const home = target?.home_view || target?.department?.home_view || 'command';
    const map: Record<string, string> = {
      command: '/command',
      finance: '/finance',
      tech: '/tech',
      rnd: '/rnd',
      admin: '/admin-desk',
    };
    return map[home] ?? `/${home}`;
  }

  private read(key: string): string | null {
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  }

  private write(key: string, value: string): void {
    try {
      localStorage.setItem(key, value);
    } catch {
      /* storage unavailable — session stays in memory only */
    }
  }

  private remove(key: string): void {
    try {
      localStorage.removeItem(key);
    } catch {
      /* ignore */
    }
  }
}

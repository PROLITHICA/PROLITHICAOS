import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';

import { AuthService } from '../../../core/auth.service';
import { ToastService } from '../../../core/toast.service';

/** The design's split-screen sign-in, wired to `/api/auth/login/`. */
@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './login.component.html',
  styleUrl: './login.component.css',
})
export class LoginComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly toasts = inject(ToastService);

  readonly email = signal('');
  readonly password = signal('');
  readonly busy = signal(false);
  readonly error = signal('');

  signIn(): void {
    if (this.busy()) return;
    const email = this.email().trim();
    const password = this.password();
    if (!email || !password) {
      this.error.set('Enter your email address and password.');
      return;
    }

    this.busy.set(true);
    this.error.set('');
    this.auth.login(email, password).subscribe({
      next: (response) => {
        this.busy.set(false);
        this.toasts.show(response.toast);
        const next = this.route.snapshot.queryParamMap.get('next');
        void this.router.navigateByUrl(next || this.auth.homeRoute(response.user));
      },
      error: (error: unknown) => {
        this.busy.set(false);
        this.error.set(this.messageFor(error));
      },
    });
  }

  private messageFor(error: unknown): string {
    if (error instanceof HttpErrorResponse) {
      const body = error.error as { detail?: string; email?: string[]; password?: string[] } | null;
      if (body?.detail) return body.detail;
      if (body?.email?.length) return body.email[0];
      if (body?.password?.length) return body.password[0];
      if (error.status === 0) return 'Prolithica OS is not reachable. Check your connection and try again.';
    }
    return 'That email and password do not match an account.';
  }
}

import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';

import { AuthService } from '../../../core/auth.service';
import { deployment } from '../../../core/deployment';
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
  readonly backendUnavailable = deployment.pages && !deployment.apiOrigin;
  /** Static particle ribbons, batched into paths to keep the artwork lightweight. */
  readonly particleRibbons = (() => {
    let seed = 731;
    const random = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
    return Array.from({ length: 5 }, (_, layer) => ({
      opacity: .18 + layer * .1,
      width: .6 + layer * .2,
      path: Array.from({ length: 1050 }, () => {
        const t = random();
        const x = 460 + t * 920;
        const ribbon = random() > .52 ? 1 : -1;
        const spread = (random() + random() + random() - 1.5) * (24 + t * 100);
        const y = 410 + Math.sin(t * 4.8) * 48 + ribbon * (12 + Math.sin(t * 2.5) * 105) + spread;
        return `M${x.toFixed(1)} ${y.toFixed(1)}h.1`;
      }).join(' '),
    }));
  })();
  signIn(): void {
    if (this.backendUnavailable) return;
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

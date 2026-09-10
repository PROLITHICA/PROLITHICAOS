import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { ThemeService } from './core/theme.service';
import { AuthService } from './core/auth.service';
import { BootScreenComponent } from './layout/boot-screen.component';

/** Resolves the session once, showing the boot splash while it lands. */
@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, BootScreenComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (booting()) {
      <app-boot-screen [step]="bootStep()" />
    } @else {
      <router-outlet />
    }
  `,
})
export class AppComponent {
  private readonly theme = inject(ThemeService);
  private readonly auth = inject(AuthService);

  readonly booting = signal(true);
  readonly bootStep = signal('Connecting to Prolithica OS');

  constructor() {
    if (!this.auth.hasToken()) {
      this.booting.set(false);
      return;
    }
    this.bootStep.set('Restoring your session');
    this.auth.me().subscribe({
      next: () => this.booting.set(false),
      error: () => {
        this.auth.clear();
        this.booting.set(false);
      },
    });
  }
}

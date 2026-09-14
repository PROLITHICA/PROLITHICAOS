import { AfterViewInit, ChangeDetectionStrategy, Component, inject, OnDestroy, signal } from '@angular/core';
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
export class AppComponent implements AfterViewInit, OnDestroy {
  private readonly theme = inject(ThemeService);
  private readonly auth = inject(AuthService);

  readonly booting = signal(true);
  readonly bootStep = signal('Connecting to Prolithica OS');

  private fadeObserver?: IntersectionObserver;
  private contentObserver?: MutationObserver;
  private scrollFrame = 0;
  private readonly motionTargets: HTMLElement[] = [];
  private readonly onScroll = () => {
    if (this.scrollFrame) return;
    this.scrollFrame = requestAnimationFrame(() => {
      this.scrollFrame = 0;
      const viewport = window.innerHeight;
      for (const heading of this.motionTargets) {
        const rect = heading.getBoundingClientRect();
        const start = viewport * 0.9;
        const finish = viewport * 0.32;
        const progress = Math.max(0, Math.min(1, (start - rect.top) / (rect.height + start - finish)));
        heading.style.setProperty('--type-progress', progress.toFixed(3));
      }
    });
  };

  ngAfterViewInit(): void {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    this.fadeObserver = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        entry.target.classList.toggle('is-in-view', entry.isIntersecting);
      }
    }, { threshold: 0.08 });

    this.enhanceMotion(document.body);
    this.contentObserver = new MutationObserver((records) => {
      if (records.some((record) => record.addedNodes.length)) this.enhanceMotion(document.body);
    });
    this.contentObserver.observe(document.body, { childList: true, subtree: true });
    window.addEventListener('scroll', this.onScroll, { passive: true });
    window.addEventListener('resize', this.onScroll, { passive: true });
    this.onScroll();
  }

  ngOnDestroy(): void {
    this.fadeObserver?.disconnect();
    this.contentObserver?.disconnect();
    window.removeEventListener('scroll', this.onScroll);
    window.removeEventListener('resize', this.onScroll);
    if (this.scrollFrame) cancelAnimationFrame(this.scrollFrame);
  }

  private enhanceMotion(root: ParentNode): void {
    root.querySelectorAll<HTMLElement>(
      '.main > *, .login-page main > *, .workspace-page > .workspace-heading, .workspace-page > .workspace-stats, .workspace-page > .workspace-grid > *',
    ).forEach((element) => {
      if (element.hasAttribute('data-scroll-fade')) return;
      element.setAttribute('data-scroll-fade', '');
      this.fadeObserver?.observe(element);
    });
    root.querySelectorAll<HTMLElement>('h1, .workspace-page > section > h2').forEach((heading) => {
      if (heading.hasAttribute('data-scroll-typewriter')) return;
      heading.setAttribute('data-scroll-typewriter', '');
      heading.style.setProperty('--char-count', String(Math.max(heading.textContent?.trim().length ?? 0, 1)));
      this.motionTargets.push(heading);
    });
  }

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

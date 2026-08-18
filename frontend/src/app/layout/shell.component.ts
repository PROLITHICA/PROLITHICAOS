import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  ActivatedRoute, NavigationCancel, NavigationEnd, NavigationError, NavigationStart, Router,
  RouterLink, RouterLinkActive, RouterOutlet,
} from '@angular/router';
import { filter } from 'rxjs';

import { ApiService } from '../core/api.service';
import { AuthService } from '../core/auth.service';
import { LoadingService } from '../core/loading.service';
import { Department, NavGroup } from '../core/models';
import { PermissionService } from '../core/permission.service';
import { BreadcrumbsComponent, Crumb } from '../shared/ui/breadcrumbs/breadcrumbs.component';
import { SkeletonComponent } from '../shared/ui/skeleton/skeleton.component';
import { ToastHostComponent } from '../shared/ui/toast-host/toast-host.component';

const HOME_ROUTES: Record<string, string> = {
  command: '/command', finance: '/finance', tech: '/tech', rnd: '/rnd', admin: '/admin-desk',
};

/** Sidebar + topbar + routed page. Every authenticated view lives inside it. */
@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [
    RouterOutlet, RouterLink, RouterLinkActive, FormsModule,
    BreadcrumbsComponent, SkeletonComponent, ToastHostComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './shell.component.html',
  styleUrl: './shell.component.css',
})
export class ShellComponent {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  readonly auth = inject(AuthService);
  readonly perms = inject(PermissionService);
  readonly loader = inject(LoadingService);

  readonly departments = signal<Department[]>([]);
  readonly notifCount = signal<number>(0);
  readonly pageTitle = signal<string>('');
  readonly crumbs = signal<Crumb[]>([]);
  readonly crumbCurrent = signal<string>('');
  readonly query = signal<string>('');

  readonly user = this.auth.currentUser;
  readonly navGroups = computed<NavGroup[]>(() => this.perms.navGroups());
  readonly person = computed(() => this.user()?.display_name ?? '');
  readonly personTitle = computed(() => this.user()?.job_title ?? '');
  readonly initials = computed(() => this.user()?.initials ?? '');
  readonly activeDept = computed(() => this.user()?.department?.slug ?? '');

  constructor() {
    this.api.list<Department>('/departments/').subscribe({
      next: (page) => this.departments.set(page.results ?? []),
      error: () => this.departments.set([]),
    });
    // The badge counts what is still unread, which is what the endpoint reports.
    this.api.get<{ unread?: number }>('/notifications/').subscribe({
      next: (page) => this.notifCount.set(page?.unread ?? 0),
      error: () => this.notifCount.set(0),
    });

    this.router.events.pipe(filter((event) => event instanceof NavigationStart))
      .subscribe(() => this.loader.start('Loading records and permissions'));

    this.router.events
      .pipe(filter((event) =>
        event instanceof NavigationEnd || event instanceof NavigationCancel || event instanceof NavigationError))
      .subscribe(() => {
        this.loader.stop();
        this.readRouteData();
      });

    this.readRouteData();
  }

  private readRouteData(): void {
    // Called once on construction as well as after every navigation, so the
    // deepest child may not have been activated — and therefore have no
    // snapshot — yet. Take the deepest route that actually carries one.
    let child = this.route;
    while (child.firstChild?.snapshot) child = child.firstChild;

    const data = (child.snapshot?.data ?? {}) as {
      title?: string;
      crumbs?: Crumb[];
      crumbCurrent?: string;
    };
    this.pageTitle.set(data.title ?? '');
    this.crumbs.set(data.crumbs ?? []);
    this.crumbCurrent.set(data.crumbCurrent ?? '');
  }

  departmentRoute(dept: Department): string {
    return HOME_ROUTES[dept.home_view] ?? `/${dept.home_view}`;
  }

  goSearch(): void {
    void this.router.navigate(['/search'], {
      queryParams: this.query() ? { q: this.query() } : {},
    });
  }

  signOut(): void {
    this.auth.logout();
  }
}

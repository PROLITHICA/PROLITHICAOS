import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import { RouterLink } from '@angular/router';

export interface Crumb { label: string; route?: string | unknown[]; }

/** The design's `Label / Label / current` trail above a page. */
@Component({
  selector: 'app-breadcrumbs',
  standalone: true,
  imports: [RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (crumbs().length || current()) {
      <div class="crumbs">
        @for (crumb of crumbs(); track $index) {
          @if (crumb.route) {
            <a class="crumb" [routerLink]="crumb.route">{{ crumb.label }}</a>
          } @else {
            <button type="button" class="crumb" (click)="crumbClick.emit(crumb)">{{ crumb.label }}</button>
          }
          <span class="sep">/</span>
        }
        <span class="current">{{ current() }}</span>
      </div>
    }
  `,
  styles: [`
    .crumbs { display: flex; align-items: center; gap: 7px; font-size: 11.5px; margin-bottom: 12px; }
    .crumb { background: transparent; border: 0; padding: 0; font: inherit; color: #3d3d3d; cursor: pointer; text-decoration: none; }
    .crumb:hover { color: #111111; }
    .sep { color: #c4c4c4; }
    .current { color: #8a8a8a; }
  `],
})
export class BreadcrumbsComponent {
  readonly crumbs = input<Crumb[]>([]);
  readonly current = input<string>('');
  readonly crumbClick = output<Crumb>();
}

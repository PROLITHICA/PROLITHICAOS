import { ThemeColorPipe } from '../theme-color.pipe';
import { ChangeDetectionStrategy, Component, computed, input, output } from '@angular/core';

import { RecordCell, RecordRow, ViewColumn } from '../../../core/models';

interface Header { l: string; align: string; }

/**
 * Renders a ViewConfig's columns plus record rows, matching the design's
 * `<table class="table">` markup: per-cell tag / bold / muted / right-align.
 */
@Component({
  selector: 'app-data-table',
  standalone: true,
  imports: [ThemeColorPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="scroll-x">
      <table class="table" [style.min-width.px]="minWidth()">
        @if (headers().length) {
          <thead>
            <tr>
              @for (h of headers(); track $index) {
                <th [style.text-align]="h.align">{{ h.l }}</th>
              }
            </tr>
          </thead>
        }
        <tbody>
          @for (row of rows(); track $index) {
            <tr [style.cursor]="clickable() ? 'pointer' : 'default'" (click)="onRow(row)">
              @for (cell of row.cells; track $index) {
                <td [style.text-align]="cell.align || 'left'"
                    [style.font-weight]="cell.bold ? 600 : 400"
                    [style.color]="(cell.muted ? 'var(--pl-color-6b6b6b)' : 'var(--pl-color-111111)') | themeColor">
                  @if (cell.tag) {
                    <span class="tag" [class]="'tag ' + cell.tag">{{ cell.t }}</span>
                  } @else {
                    {{ cell.t }}
                  }
                </td>
              }
            </tr>
          } @empty {
            <tr>
              <td [attr.colspan]="headers().length || 1" class="empty">{{ emptyText() }}</td>
            </tr>
          }
        </tbody>
      </table>
    </div>
  `,
  styles: [`
    .scroll-x { overflow-x: auto; max-width: 100%; }
    .empty { color: var(--pl-color-8a8a8a); font-size: 12.5px; text-align: center; padding: 26px 10px; }
    /* Responsive: the table keeps its width and scrolls inside its own box. */
    .scroll-x { -webkit-overflow-scrolling: touch; overscroll-behavior-x: contain; }
    @media (max-width: 720px) {
      .scroll-x ::ng-deep th,
      .scroll-x ::ng-deep td { padding: 9px 8px; }
      .empty { padding: 22px 10px; }
    }
  `],
})
export class DataTableComponent {
  /** Columns, either the API's plain strings or `{l, a}` descriptors. */
  readonly cols = input<Array<string | ViewColumn>>([]);
  readonly rows = input<RecordRow[]>([]);
  readonly minWidth = input<number>(640);
  readonly clickable = input<boolean>(true);
  readonly emptyText = input<string>('No records match this view.');

  readonly rowClick = output<RecordRow>();

  readonly headers = computed<Header[]>(() =>
    this.cols().map((col) =>
      typeof col === 'string' ? { l: col, align: 'left' } : { l: col.l, align: col.a ?? 'left' },
    ),
  );

  onRow(row: RecordRow): void {
    if (this.clickable()) this.rowClick.emit(row);
  }

  /** Helper other features can use to build cells. */
  static cell(t: string, options: Partial<RecordCell> = {}): RecordCell {
    return { t, align: options.align ?? 'left', bold: options.bold, muted: options.muted, tag: options.tag ?? '' };
  }
}

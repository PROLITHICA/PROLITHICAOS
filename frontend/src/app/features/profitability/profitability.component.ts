import { ChangeDetectionStrategy, Component } from '@angular/core';

import { RecordListComponent } from '../records/record-list.component';

/**
 * Profitability — LISTS().profitability: contract, invoiced, paid, cost,
 * margin now and forecast per project.
 *
 * The generic record list already serves this view end to end: the server's
 * `/profitability/` list returns the same title, subtitle, stat tiles, columns
 * and cells, and the view's primary action is the design's "Rebuild forecast"
 * (the `profitability` form, POSTed to `/profitability/rebuild/`). This is
 * therefore a thin wrapper that pins the view rather than a second table.
 */
@Component({
  selector: 'app-profitability',
  standalone: true,
  imports: [RecordListComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<app-record-list view="profitability" />`,
  styles: [`:host { display: block; }`],
})
export class ProfitabilityComponent {}

import { ChangeDetectionStrategy, Component, input } from '@angular/core';

/**
 * `variant="block"` renders one shimmering bar; `variant="page"` renders the
 * design's full route-transition overlay with its spinner + note line.
 */
@Component({
  selector: 'app-skeleton',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (variant() === 'page') {
      <div class="overlay">
        <div class="skel" style="width:180px;height:12px"></div>
        <div class="skel" style="width:330px;height:30px;margin-top:14px"></div>
        <div class="row3">
          <div class="skel" style="height:112px"></div>
          <div class="skel" style="height:112px"></div>
          <div class="skel" style="height:112px"></div>
        </div>
        <div class="row2">
          <div class="skel" style="height:230px"></div>
          <div class="skel" style="height:230px"></div>
        </div>
        <div class="note">
          <span class="ring"></span>
          {{ note() }}
        </div>
      </div>
    } @else {
      <div class="skel" [style.width]="width()" [style.height]="height()"></div>
    }
  `,
  styles: [`
    .overlay { position: absolute; left: 0; right: 0; top: 53px; bottom: 0; background: #fff; z-index: 15; padding: 26px 28px; }
    .row3 { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 16px; margin-top: 26px; }
    .row2 { display: grid; grid-template-columns: minmax(0,1.5fr) minmax(0,1fr); gap: 16px; margin-top: 16px; }
    .note { display: flex; align-items: center; gap: 9px; margin-top: 22px; font-size: 11.5px; color: #8a8a8a; }
    .ring { width: 11px; height: 11px; border: 2px solid #e0e0e0; border-top-color: #3d3d3d; border-radius: 50%; animation: pl-spin 0.7s linear infinite; }
  `],
})
export class SkeletonComponent {
  readonly variant = input<'block' | 'page'>('block');
  readonly width = input<string>('100%');
  readonly height = input<string>('12px');
  readonly note = input<string>('');
}

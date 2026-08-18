import { ChangeDetectionStrategy, Component, input } from '@angular/core';

/** A titled section panel: heading, optional sub-line, right-aligned actions. */
@Component({
  selector: 'app-section-card',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="sec">
      <div class="sec-head">
        <div>
          <h4 class="sec-title">{{ heading() }}</h4>
          @if (subheading()) { <div class="sec-sub">{{ subheading() }}</div> }
        </div>
        <ng-content select="[section-actions]" />
      </div>
      <div class="sec-body"><ng-content /></div>
      @if (footnote()) { <div class="sec-foot">{{ footnote() }}</div> }
    </section>
  `,
  styles: [`
    .sec { border: 1px dotted #c4c4c4; border-radius: 16px; padding: 18px; background: #fff; }
    .sec-head { display: flex; flex-wrap: wrap; gap: 6px 16px; justify-content: space-between; align-items: baseline; }
    .sec-title { margin: 0 0 2px; font-size: 15px; }
    .sec-sub { font-size: 11.5px; color: #8a8a8a; }
    .sec-body { margin-top: 10px; }
    .sec-foot { font-size: 11.5px; color: #6b6b6b; border-top: 1px dotted #dcdcdc; padding-top: 10px; margin-top: 4px; }
  `],
})
export class SectionCardComponent {
  readonly heading = input<string>('');
  readonly subheading = input<string>('');
  readonly footnote = input<string>('');
}

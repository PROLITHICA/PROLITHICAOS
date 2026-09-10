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
    .sec { border: 0; border-radius: 16px; background: var(--pl-pane); box-shadow: var(--pl-lift-1); padding: var(--pl-pane-pad); }
    .sec-head { display: flex; flex-wrap: wrap; gap: 6px 16px; justify-content: space-between; align-items: baseline; }
    .sec-title { margin: 0 0 2px; font-size: 15px; }
    .sec-sub { font-size: 11.5px; color: var(--pl-color-8a8a8a); }
    .sec-body { margin-top: 10px; }
    .sec-foot { font-size: 11.5px; color: var(--pl-color-6b6b6b); border-top: 1px solid var(--pl-rule); padding-top: 12px; margin-top: 6px; }
    @media (max-width: 900px) {
      .sec-head ::ng-deep [section-actions] { display: flex; flex-wrap: wrap; gap: 8px; width: 100%; }
    }
    @media (max-width: 560px) {
      .sec { padding: 14px; }
      .sec-title { font-size: 14.5px; }
    }
  `],
})
export class SectionCardComponent {
  readonly heading = input<string>('');
  readonly subheading = input<string>('');
  readonly footnote = input<string>('');
}

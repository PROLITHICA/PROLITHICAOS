import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';

/**
 * Ask-first dialog for anything destructive or outward-facing: withdrawing a
 * published report, removing an entry from someone else's day.
 *
 * The system had no confirmation surface — every write went straight through —
 * so this is the one genuinely new shared component. It borrows the modal's
 * frame so the two read as the same object.
 */
@Component({
  selector: 'app-confirm',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (open()) {
      <div class="backdrop" (click)="cancel.emit()">
        <div class="sheet fade" (click)="$event.stopPropagation()" role="alertdialog" aria-modal="true">
          <h3 class="sheet-title">{{ heading() }}</h3>
          @if (body()) { <div class="sheet-body">{{ body() }}</div> }
          @if (consequence()) { <div class="conseq">{{ consequence() }}</div> }
          <div class="foot">
            <button type="button" class="btn btn-secondary" (click)="cancel.emit()">
              {{ cancelLabel() }}
            </button>
            <button type="button" class="btn btn-primary" [disabled]="busy()" (click)="confirm.emit()">
              @if (busy()) { <span class="spin"></span> }
              {{ confirmLabel() }}
            </button>
          </div>
        </div>
      </div>
    }
  `,
  styles: [`
    .backdrop { position: fixed; inset: 0; z-index: 50; background: rgba(17,17,17,0.35); display: grid; place-items: center; padding: 28px; }
    .sheet { width: min(430px, 100%); background: var(--pl-color-ffffff); border: 1px dotted var(--pl-color-b5b5b5); border-radius: 22px; padding: 24px 24px 20px; }
    .sheet-title { margin: 0 0 6px; font-size: 18px; }
    .sheet-body { font-size: 12.5px; color: var(--pl-color-6b6b6b); line-height: 1.5; }
    .conseq { margin-top: 12px; border: 1px dotted var(--pl-color-dcdcdc); border-radius: 14px; background: var(--pl-color-fafafa); padding: 10px 13px; font-size: 12px; color: var(--pl-color-333333); }
    .foot { display: flex; justify-content: flex-end; gap: 9px; margin-top: 20px; }
    @media (max-width: 560px) {
      .backdrop { padding: 16px; }
      .sheet { padding: 20px 18px 16px; border-radius: 18px; }
      .foot { flex-direction: column-reverse; gap: 8px; }
      .foot .btn { width: 100%; min-height: 44px; }
    }
  `],
})
export class ConfirmComponent {
  readonly open = input<boolean>(false);
  readonly heading = input<string>('Are you sure?');
  readonly body = input<string>('');
  /** the line that names what will actually happen to the record */
  readonly consequence = input<string>('');
  readonly confirmLabel = input<string>('Confirm');
  readonly cancelLabel = input<string>('Cancel');
  readonly busy = input<boolean>(false);

  readonly confirm = output<void>();
  readonly cancel = output<void>();
}

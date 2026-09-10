import { ChangeDetectionStrategy, Component, effect, input, output, signal } from '@angular/core';

import { FieldComponent, FieldKind, FieldSpec } from '../field/field.component';

/** The design's create-record modal, including its inheritance panel. */
@Component({
  selector: 'app-modal',
  standalone: true,
  imports: [FieldComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (open()) {
      <div class="backdrop" (click)="close.emit()">
        <div class="sheet fade" (click)="$event.stopPropagation()" role="dialog" aria-modal="true">
          <div class="sheet-head">
            <div>
              <h3 class="sheet-title">{{ title() }}</h3>
              <div class="sheet-sub">{{ subtitle() }}</div>
            </div>
            <button type="button" class="x" aria-label="close" (click)="close.emit()">×</button>
          </div>

          @if (inherit().length) {
            <div class="inherit">
              <div class="inherit-kicker">Carried over automatically</div>
              @for (line of inherit(); track $index) {
                <div class="inherit-line">{{ line }}</div>
              }
            </div>
          }

          <div class="fields">
            @for (field of fields(); track field.k) {
              <app-field [label]="field.l" [name]="field.k"
                         [kind]="kindOf(field)" [options]="field.o ?? []"
                         [placeholder]="field.p ?? ''" surface="var(--pl-color-fafafa)"
                         [value]="valueOf(field.k)"
                         (valueChange)="set(field.k, $event)" />
            }
            <ng-content />
          </div>

          <div class="foot">
            <button type="button" class="btn btn-secondary" (click)="close.emit()">Cancel</button>
            <button type="button" class="btn btn-primary" [disabled]="busy()" (click)="submit.emit(values())">
              @if (busy()) { <span class="spin"></span> }
              {{ submitLabel() }}
            </button>
          </div>
        </div>
      </div>
    }
  `,
  styles: [`
    .backdrop { position: fixed; inset: 0; z-index: 45; background: rgba(17,17,17,0.28); -webkit-backdrop-filter: blur(3px); backdrop-filter: blur(3px); display: grid; place-items: center; padding: 28px; }
    .sheet { width: min(560px, 100%); max-height: 86vh; overflow: auto; background: var(--pl-pane); border: 0; border-radius: 22px; box-shadow: var(--pl-lift-3); padding: 26px 26px 22px; }
    .sheet-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
    .sheet-title { margin: 0 0 4px; font-size: 21px; }
    .sheet-sub { font-size: 12px; color: var(--pl-color-8a8a8a); max-width: 52ch; }
    .x { background: transparent; border: 1px dotted var(--pl-color-b5b5b5); border-radius: 999px; width: 28px; height: 28px; font: inherit; font-size: 13px; color: var(--pl-color-6b6b6b); cursor: pointer; flex: none; }
    .x:hover { border-color: var(--pl-color-111111); color: var(--pl-color-111111); }
    .inherit { border: 0; border-radius: 14px; padding: 14px 16px; margin-top: 16px; background: var(--pl-pane-sunken); }
    .inherit-kicker { font-size: 10px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--pl-color-9a9a9a); }
    .inherit-line { font-size: 12px; margin-top: 5px; }
    .fields { display: flex; flex-direction: column; gap: 14px; margin-top: 18px; }
    .foot { display: flex; justify-content: flex-end; gap: 9px; margin-top: 20px; }
    /* Responsive ─────────────────────────────────────────────────────────
       Tablet trims the frame; phone turns the sheet into a full-screen
       panel whose body scrolls and whose actions stay pinned in reach. */
    @media (max-width: 900px) {
      .backdrop { padding: 18px; }
      .sheet { max-height: 90vh; padding: 22px 20px 18px; }
    }
    @media (max-width: 560px) {
      .backdrop { padding: 0; place-items: stretch; }
      .sheet {
        width: 100%; max-width: none; height: 100dvh; max-height: 100dvh;
        border: 0; border-radius: 0; padding: 18px 16px 0;
        display: flex; flex-direction: column; overflow: hidden;
      }
      .sheet-head { flex: none; }
      .sheet-title { font-size: 19px; }
      .sheet-sub { max-width: none; }
      .x { width: 34px; height: 34px; }
      .inherit { flex: none; margin-top: 14px; }
      .fields { flex: 1 1 auto; overflow-y: auto; -webkit-overflow-scrolling: touch; padding-bottom: 4px; }
      .foot {
        flex: none; flex-direction: column-reverse; gap: 8px; margin-top: 14px;
        border-top: 1px dotted var(--pl-color-dcdcdc);
        padding: 14px 0 calc(14px + env(safe-area-inset-bottom));
        background: var(--pl-color-ffffff);
      }
      .foot .btn { width: 100%; min-height: 44px; }
    }
  `],
})
export class ModalComponent {
  readonly open = input<boolean>(false);
  readonly title = input<string>('');
  readonly subtitle = input<string>('');
  /** the "Inherited into this record" lines */
  readonly inherit = input<string[]>([]);
  readonly fields = input<FieldSpec[]>([]);
  /** Prefilled values, so the same modal can edit an existing record. */
  readonly initial = input<Record<string, string>>({});
  readonly submitLabel = input<string>('Save');
  readonly busy = input<boolean>(false);

  readonly close = output<void>();
  readonly submit = output<Record<string, string>>();

  readonly values = signal<Record<string, string>>({});

  constructor() {
    // Seed the form whenever it opens, so an edit starts from the record as it is.
    effect(() => {
      if (this.open()) this.values.set({ ...this.initial() });
    }, { allowSignalWrites: true });
  }

  kindOf(field: FieldSpec): FieldKind {
    if (field.o?.length) return 'options';
    if (field.t === 'area') return 'area';
    return 'text';
  }

  valueOf(key: string): string {
    return this.values()[key] ?? '';
  }

  set(key: string, value: string): void {
    this.values.update((current) => ({ ...current, [key]: value }));
  }
}

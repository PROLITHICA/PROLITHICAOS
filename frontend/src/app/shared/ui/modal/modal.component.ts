import { ChangeDetectionStrategy, Component, input, output, signal } from '@angular/core';

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
                         [placeholder]="field.p ?? ''" surface="#fafafa"
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
    .backdrop { position: fixed; inset: 0; z-index: 45; background: rgba(17,17,17,0.35); display: grid; place-items: center; padding: 28px; }
    .sheet { width: min(560px, 100%); max-height: 86vh; overflow: auto; background: #fff; border: 1px dotted #b5b5b5; border-radius: 22px; padding: 26px 26px 22px; }
    .sheet-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
    .sheet-title { margin: 0 0 4px; font-size: 21px; }
    .sheet-sub { font-size: 12px; color: #8a8a8a; max-width: 52ch; }
    .x { background: transparent; border: 1px dotted #b5b5b5; border-radius: 999px; width: 28px; height: 28px; font: inherit; font-size: 13px; color: #6b6b6b; cursor: pointer; flex: none; }
    .x:hover { border-color: #111; color: #111; }
    .inherit { border: 1px dotted #dcdcdc; border-radius: 14px; padding: 12px 14px; margin-top: 16px; background: #fafafa; }
    .inherit-kicker { font-size: 10px; letter-spacing: 0.12em; text-transform: uppercase; color: #9a9a9a; }
    .inherit-line { font-size: 12px; margin-top: 5px; }
    .fields { display: flex; flex-direction: column; gap: 14px; margin-top: 18px; }
    .foot { display: flex; justify-content: flex-end; gap: 9px; margin-top: 20px; }
  `],
})
export class ModalComponent {
  readonly open = input<boolean>(false);
  readonly title = input<string>('');
  readonly subtitle = input<string>('');
  /** the "Inherited into this record" lines */
  readonly inherit = input<string[]>([]);
  readonly fields = input<FieldSpec[]>([]);
  readonly submitLabel = input<string>('Save');
  readonly busy = input<boolean>(false);

  readonly close = output<void>();
  readonly submit = output<Record<string, string>>();

  readonly values = signal<Record<string, string>>({});

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

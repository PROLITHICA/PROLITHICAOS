import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import { FormsModule } from '@angular/forms';

export type FieldKind = 'text' | 'password' | 'email' | 'number' | 'date' | 'area' | 'select' | 'options';

/** A form field descriptor, shaped like the design's FORMS entries. */
export interface FieldSpec {
  /** form key */
  k: string;
  /** label */
  l: string;
  /** placeholder */
  p?: string;
  /** 'area' for a textarea */
  t?: string;
  /** choice pills */
  o?: string[];
}

/** Label + control, in the design's dotted-pill styling. */
@Component({
  selector: 'app-field',
  standalone: true,
  imports: [FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="field">
      @if (label()) { <label [attr.for]="name()">{{ label() }}</label> }

      @switch (kind()) {
        @case ('area') {
          <textarea class="input" [id]="name()" [ngModel]="value()"
                    (ngModelChange)="valueChange.emit($event)"
                    [placeholder]="placeholder()" [style.background]="surface()"
                    style="min-height:70px"></textarea>
        }
        @case ('select') {
          <select class="input" [id]="name()" [ngModel]="value()"
                  (ngModelChange)="valueChange.emit($event)" [style.background]="surface()">
            @for (option of options(); track option) { <option [value]="option">{{ option }}</option> }
          </select>
        }
        @case ('options') {
          <div class="pills">
            @for (option of options(); track option) {
              <button type="button" class="pill"
                      [style.background]="value() === option ? '#111' : '#fff'"
                      [style.color]="value() === option ? '#fff' : '#333'"
                      [style.border-color]="value() === option ? '#111' : '#b5b5b5'"
                      (click)="valueChange.emit(option)">{{ option }}</button>
            }
          </div>
        }
        @default {
          <input class="input" [id]="name()" [type]="kind()" [ngModel]="value()"
                 (ngModelChange)="valueChange.emit($event)"
                 [placeholder]="placeholder()" [style.background]="surface()"
                 [autocomplete]="autocomplete()">
        }
      }

      @if (hint()) { <div class="hint">{{ hint() }}</div> }
      @if (error()) { <div class="error">{{ error() }}</div> }
    </div>
  `,
  styles: [`
    .pills { display: flex; flex-wrap: wrap; gap: 7px; }
    .pill { border: 1px dotted #b5b5b5; border-radius: 999px; padding: 6px 13px; font: inherit; font-size: 11.5px; cursor: pointer; }
    .pill:hover { border-color: #111; }
    .hint { font-size: 11px; color: #9a9a9a; margin-top: 5px; }
    .error { font-size: 11.5px; color: #111; margin-top: 5px; }
  `],
})
export class FieldComponent {
  readonly label = input<string>('');
  readonly name = input<string>('');
  readonly kind = input<FieldKind>('text');
  readonly value = input<string>('');
  readonly placeholder = input<string>('');
  readonly options = input<string[]>([]);
  readonly hint = input<string>('');
  readonly error = input<string>('');
  readonly autocomplete = input<string>('off');
  /** the design fills modal inputs with #fafafa and login inputs with #fff */
  readonly surface = input<string>('#ffffff');

  readonly valueChange = output<string>();
}

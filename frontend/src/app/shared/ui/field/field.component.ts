import { ThemeColorPipe } from '../theme-color.pipe';
import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import { FormsModule } from '@angular/forms';

export type FieldKind =
  | 'text' | 'password' | 'email' | 'number' | 'date' | 'time' | 'area' | 'select' | 'options';

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
  imports: [ThemeColorPipe, FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="field">
      @if (label()) { <label [attr.for]="name()">{{ label() }}</label> }

      @switch (kind()) {
        @case ('area') {
          <textarea class="input" [id]="name()" [ngModel]="value()"
                    (ngModelChange)="valueChange.emit($event)"
                    [placeholder]="placeholder()" [style.background]="(surface()) | themeColor"
                    style="min-height:70px"></textarea>
        }
        @case ('select') {
          <select class="input" [id]="name()" [ngModel]="value()"
                  (ngModelChange)="valueChange.emit($event)" [style.background]="(surface()) | themeColor">
            @for (option of options(); track option) { <option [value]="option">{{ option }}</option> }
          </select>
        }
        @case ('options') {
          <div class="pills">
            @for (option of options(); track option) {
              <button type="button" class="pill"
                      [style.background]="(value() === option ? 'var(--pl-color-111111)' : 'var(--pl-color-ffffff)') | themeColor"
                      [style.color]="(value() === option ? 'var(--pl-color-ffffff)' : 'var(--pl-color-333333)') | themeColor"
                      [style.border-color]="(value() === option ? 'var(--pl-color-111111)' : 'var(--pl-color-b5b5b5)') | themeColor"
                      (click)="valueChange.emit(option)">{{ option }}</button>
            }
          </div>
        }
        @default {
          <input class="input" [id]="name()" [type]="kind()" [ngModel]="value()"
                 (ngModelChange)="valueChange.emit($event)"
                 [placeholder]="placeholder()" [style.background]="(surface()) | themeColor"
                 [autocomplete]="autocomplete()">
        }
      }

      @if (hint()) { <div class="hint">{{ hint() }}</div> }
      @if (error()) { <div class="error">{{ error() }}</div> }
    </div>
  `,
  styles: [`
    .pills { display: flex; flex-wrap: wrap; gap: 7px; }
    .pill { border: 1px dotted var(--pl-color-b5b5b5); border-radius: 999px; padding: 6px 13px; font: inherit; font-size: 11.5px; cursor: pointer; }
    .pill:hover { border-color: var(--pl-color-111111); }
    .hint { font-size: 11px; color: var(--pl-color-9a9a9a); margin-top: 5px; }
    .error { font-size: 11.5px; color: var(--pl-color-111111); margin-top: 5px; }
    @media (max-width: 720px) {
      .pill { min-height: 40px; padding: 8px 15px; font-size: 12.5px; display: inline-flex; align-items: center; }
    }
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
  /** the design fills modal inputs with var(--pl-color-fafafa) and login inputs with var(--pl-color-ffffff) */
  readonly surface = input<string>('var(--pl-color-ffffff)');

  readonly valueChange = output<string>();
}

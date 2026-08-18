import {
  Directive, TemplateRef, ViewContainerRef, effect, inject, input,
} from '@angular/core';

import { PermissionService } from './permission.service';

/**
 * Structural directive: `*appHasPerm="'finance:full'"`.
 * Renders the element only when the signed-in role clears that level.
 */
@Directive({
  selector: '[appHasPerm]',
  standalone: true,
})
export class HasPermDirective {
  private readonly template = inject(TemplateRef<unknown>);
  private readonly container = inject(ViewContainerRef);
  private readonly perms = inject(PermissionService);

  /**
   * `"area"` (implies read) or `"area:level"`.
   *
   * Not marked required: the effect can flush before the input is written, and
   * reading a required input that early throws NG0950. An unset value simply
   * means "no decision yet", so nothing is rendered until one arrives.
   */
  readonly appHasPerm = input<string>('');

  private rendered = false;

  constructor() {
    effect(() => {
      const expression = this.appHasPerm();
      const allowed = expression ? this.perms.canExpression(expression) : false;
      if (allowed && !this.rendered) {
        this.container.createEmbeddedView(this.template);
        this.rendered = true;
      } else if (!allowed && this.rendered) {
        this.container.clear();
        this.rendered = false;
      }
    });
  }
}

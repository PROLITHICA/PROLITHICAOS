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

  /** `"area"` (implies read) or `"area:level"`. */
  readonly appHasPerm = input.required<string>();

  private rendered = false;

  constructor() {
    effect(() => {
      const allowed = this.perms.canExpression(this.appHasPerm());
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

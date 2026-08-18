import { ChangeDetectionStrategy, Component, input } from '@angular/core';

import { TagClass } from '../../../core/models';

/** The design's status pill. */
@Component({
  selector: 'app-tag',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<span class="tag" [class]="'tag ' + tagClass()">{{ text() }}</span>`,
})
export class TagComponent {
  readonly text = input<string>('');
  readonly tagClass = input<TagClass | string>('tag-neutral');
}

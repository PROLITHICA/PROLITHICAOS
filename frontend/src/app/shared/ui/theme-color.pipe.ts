import { Pipe, PipeTransform } from '@angular/core';

/** Server-provided chart colours use the same neutral palette as local styles. */
@Pipe({ name: 'themeColor', standalone: true })
export class ThemeColorPipe implements PipeTransform {
  transform(value: string | null | undefined): string {
    if (!value) return '';
    const match = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(value);
    if (!match) return value;
    const hex = (match[1].length === 3 ? [...match[1]].map(c => c + c).join('') : match[1]).toLowerCase();
    const [r, g, b] = [0, 2, 4].map(i => parseInt(hex.slice(i, i + 2), 16));
    return Math.max(r, g, b) - Math.min(r, g, b) <= 5 ? `var(--pl-color-${hex}, ${value})` : value;
  }
}

/** The payloads the secretariat desk reads and writes. */

import { TagClass } from '../../core/models';

/** One entry on somebody's day — `GET/POST/PATCH /api/schedule/`. */
export interface ScheduleItem {
  id: string;
  person: string;
  person_name: string;
  day: string;
  start_time: string;
  end_time: string;
  /** "08:30–09:00" */
  time_label: string;
  kind: string;
  kind_label: string;
  title: string;
  meta: string;
  location: string;
  attendees: string;
  attached_ref: string;
  prepared_by: string;
  state: string;
  done: boolean;
  done_at: string | null;
  tag_class: TagClass | string;
  order: number;
}

/** `GET /api/directory/` — everyone the office can schedule for. */
export interface DirectoryPerson {
  id: string;
  email: string;
  display_name: string;
  job_title: string;
  initials: string;
  department: { label: string } | null;
}

/** `GET /api/reports/` — the packs the office publishes. */
export interface ReportItem {
  id: string;
  title: string;
  period: string;
  kind: string;
  kind_label: string;
  audience: string;
  audience_label: string;
  summary: string;
  original_name: string;
  size_label: string;
  published_on: string;
  uploaded_by_name: string;
  download_url: string;
}

export interface Meeting {
  id: string; time: string; title: string; meta: string; attached_ref: string; day_label: string;
}

export interface SignatureRequest {
  id: string; key: string; text: string; meta: string; state: string;
  cta: string; button_class: string;
}

export interface CorrespondenceItem {
  id: string; item: string; attached: string; owner: string; due: string;
  state: string; tag_class: string;
}

/** The compose form behind "+ Add entry" and behind an inline edit. */
export interface EntryDraft {
  id: string;
  start_time: string;
  end_time: string;
  title: string;
  kind: string;
  location: string;
  attendees: string;
  attached_ref: string;
}

export interface PublishDraft {
  title: string;
  period: string;
  kind: string;
  audience: string;
  summary: string;
}

export interface Choice { value: string; label: string; }

export const ENTRY_KINDS: Choice[] = [
  { value: 'meeting', label: 'Meeting' },
  { value: 'review', label: 'Review' },
  { value: 'focus', label: 'Focus time' },
  { value: 'call', label: 'Call' },
  { value: 'travel', label: 'Travel' },
  { value: 'personal', label: 'Personal' },
];

export const REPORT_KINDS: Choice[] = [
  { value: 'quarterly', label: 'Quarterly report' },
  { value: 'board', label: 'Board pack' },
  { value: 'meeting', label: 'Meeting pack' },
  { value: 'minutes', label: 'Minutes' },
  { value: 'plan', label: 'Plan' },
];

export const REPORT_AUDIENCES: Choice[] = [
  { value: 'executive', label: 'Executive only' },
  { value: 'company', label: 'Everyone' },
  { value: 'finance', label: 'Finance' },
];

export function labelsOf(choices: Choice[]): string[] {
  return choices.map((choice) => choice.label);
}

export function valueOfLabel(choices: Choice[], label: string): string {
  return choices.find((choice) => choice.label === label)?.value ?? choices[0].value;
}

export function labelOfValue(choices: Choice[], value: string): string {
  return choices.find((choice) => choice.value === value)?.label ?? choices[0].label;
}

/** "2026-08-21" → "Friday 21 August 2026". Local, never UTC-shifted. */
export function longDate(iso: string): string {
  const parts = iso.split('-').map(Number);
  if (parts.length !== 3 || parts.some(Number.isNaN)) return iso;
  const date = new Date(parts[0], parts[1] - 1, parts[2]);
  return date.toLocaleDateString(undefined, {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  });
}

export function isoToday(): string {
  return shiftDay(new Date(), 0);
}

/** Adds `days` to an ISO date (or to today when none is given). */
export function addDays(iso: string, days: number): string {
  const parts = iso.split('-').map(Number);
  const base = parts.length === 3 && !parts.some(Number.isNaN)
    ? new Date(parts[0], parts[1] - 1, parts[2])
    : new Date();
  return shiftDay(base, days);
}

function shiftDay(base: Date, days: number): string {
  const date = new Date(base.getFullYear(), base.getMonth(), base.getDate() + days);
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');
  return `${date.getFullYear()}-${month}-${day}`;
}

/** The API returns "08:30:00"; an <input type="time"> wants "08:30". */
export function hhmm(value: string): string {
  return (value ?? '').slice(0, 5);
}

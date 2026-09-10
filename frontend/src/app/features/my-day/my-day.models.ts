/** The `GET /api/my-day/` payload, exactly as the backend builds it. */

import { TagClass } from '../../core/models';

export interface ScheduleEntry {
  id: string;
  /** "08:30–09:00" */
  time: string;
  /** "08:30" */
  start: string;
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
  tag_class: TagClass | string;
}

export interface ApprovalItem {
  id: string;
  title: string;
  detail: string;
  kind: string;
  /** already formatted money, or "" when the decision carries no figure */
  amount: string;
  waiting: string;
  requested_by: string;
  /** the button word: "Approve" / "Release" / "Send" */
  cta: string;
  route: string;
  tag_class: TagClass | string;
}

export interface FocusRow {
  title: string;
  meta: string;
  value: string;
  state: string;
  tag_class: TagClass | string;
  route: string;
}

export interface FocusBlock {
  heading: string;
  note: string;
  kind: string;
  rows: FocusRow[];
}

export interface MyDayPayload {
  date: string;
  date_label: string;
  greeting: string;
  summary: string;
  schedule: ScheduleEntry[];
  schedule_done: number;
  schedule_total: number;
  approvals: ApprovalItem[];
  focus: FocusBlock | null;
}

/** Every action endpoint answers `{ record, toast }`. */
export interface ActionResult<T> {
  record: T;
  toast?: string;
}

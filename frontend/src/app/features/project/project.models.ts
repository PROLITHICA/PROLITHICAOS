/** Payload shapes returned by backend/apps/delivery — ProjectDetailSerializer
 *  and the documents app's DocumentSerializer. Kept beside the screen that
 *  renders them so the contract is readable in one place. */

export interface ProjectFigure {
  label: string;
  value: string;
  note: string;
  col: string;
}

export interface MarginChart {
  title: string;
  subtitle: string;
  actual: string;
  planned: string;
  caption: string;
  plan_label: string;
  note: string;
  arc?: string;
  dash_array?: string;
  track?: string;
  stroke?: string;
}

export interface CostLegend { label: string; col: string; }

export interface CostChart {
  title: string;
  subtitle: string;
  labels?: string[];
  budget_used?: string;
  work_complete?: string;
  budget_forecast?: string;
  work_forecast?: string;
  grid?: number[];
  baseline?: number;
  axis?: string[];
  legend?: CostLegend[];
}

export interface ProjectPhase {
  id: string;
  index: number;
  n: number;
  name: string;
  state: string;
  bar_width: string;
  current: boolean;
}

export interface ProgressUpdate {
  id: string;
  who: string;
  role_label: string;
  when_label: string;
  kind: string;
  text: string;
  tag_class: string;
  dot: string;
}

export interface ProjectMilestone {
  id: string;
  ref: string;
  name: string;
  planned: string;
  actual: string;
  actual_col: string;
  value: string;
  acceptance: string;
  billing: string;
  tag_class: string;
}

export interface ProjectRequirement {
  id: string;
  ref_id: string;
  text: string;
  source: string;
  work: string;
  status: string;
  tag_class: string;
}

export interface ProjectDetail {
  id: string;
  ref: string;
  name: string;
  full_name: string;
  kicker: string;
  subtitle: string;
  stage: string;
  phase_index: number;
  phase_label: string;
  completion: number;
  health: string;
  tag_class: string;
  client_label: string;
  manager_name: string;
  contract_ref: string;
  figures: ProjectFigure[];
  margin_chart: MarginChart;
  cost_chart: CostChart;
  phases: ProjectPhase[];
  updates: ProgressUpdate[];
  milestones: ProjectMilestone[];
  requirements: ProjectRequirement[];
}

export interface ProjectDocument {
  id: string;
  name: string;
  kind: string;
  attached_ref: string;
  added_by_name: string;
  when_label: string;
  size_label: string;
  state: string;
  tag_class: string;
}

/** `{record, toast}` — every delivery write action answers in this shape. */
export interface DeliveryAction<T> {
  record: T;
  toast?: string;
}

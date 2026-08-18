/** The `GET /api/dashboard/command/` payload, exactly as apps/core/dashboard.py builds it. */

export interface KpiBar {
  x: number;
  y: number;
  width: number;
  height: number;
  fill: string;
  kind: string;
}

export interface KpiBars {
  kind: 'bars';
  view_box: string;
  bars: KpiBar[];
}

export interface KpiLine {
  points: string;
  stroke: string;
  stroke_width: number;
  baseline?: { points: string; stroke: string; dash: string };
}

export interface CommandKpi {
  key: string;
  label: string;
  value: string;
  /** the figure printed to the right of the label */
  aside?: string;
  aside_tag_class?: string;
  note?: string;
  /** the design's own SVG geometry, resolved by the server */
  series: KpiBars | KpiLine;
}

export interface MarginChart {
  title: string;
  subtitle: string;
  legend: { label: string; colour: string }[];
  view_box: string;
  axis: { label: string; y: number }[];
  baseline_y: number;
  months: string[];
  month_x: number[];
  margin_points: string;
  cost_points: string;
  margin_area: string;
  now_x: number;
  now_label: string;
  note: string;
}

export interface AttentionItem {
  title: string;
  meta: string;
  state: string;
  tag_class: string;
  when: string;
  action: string;
  route: string;
  area?: string;
}

export interface DeliveryRow {
  name: string;
  client: string;
  pm: string;
  complete: string;
  budget: string;
  margin: string;
  health: string;
  tag_class: string;
  route: string;
}

export interface AgeingBucket {
  key: string;
  label: string;
  value: string;
  colour: string;
  dash_array: string;
  dash_offset: number;
}

export interface Ageing {
  title: string;
  subtitle: string;
  total: string;
  total_note: string;
  buckets: AgeingBucket[];
  cta: string;
}

export interface CapacityRow {
  team: string;
  pct: string;
  width: string;
  tone: 'attention' | 'ink' | 'mid' | string;
  note: string;
}

export interface Decision {
  text: string;
  meta: string;
  cta: string;
  action: string;
  route?: string;
  toast?: string;
}

export interface CommandPayload {
  greeting: string;
  title: string;
  subtitle: string;
  kpis: CommandKpi[];
  margin_chart: MarginChart;
  attention: AttentionItem[];
  projects: DeliveryRow[];
  ageing: Ageing;
  capacity: CapacityRow[];
  decisions: Decision[];
}

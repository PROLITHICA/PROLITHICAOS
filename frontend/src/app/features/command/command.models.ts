/** The `GET /api/dashboard/command/` payload, exactly as apps/core/dashboard.py builds it. */

export interface CommandKpi {
  label: string;
  value: string;
  note_right?: string;
  note_tag?: string;
  footnote?: string;
  /** recorded months — the design draws these as the solid bars / the trend line */
  series: number[];
  /** projected months — the design draws these greyed out */
  forecast: number[];
}

export interface MarginChart {
  months: string[];
  margin_pct: number[];
  cost_rm: number[];
  now_index: number;
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
  label: string;
  value: string;
  tone: string;
  dash: number;
}

export interface Ageing {
  total: string;
  caption: string;
  buckets: AgeingBucket[];
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

/** Domain models shared by every feature. Mirrors the payloads produced by
 *  backend/apps/accounts (login, me, navigation) and the generic list views. */

export type PermissionLevel =
  | 'none' | 'read' | 'contribute' | 'restricted' | 'full' | 'approve' | 'administer';

export type Scope = 'company' | 'assigned_projects' | 'own_records';

export type TagClass = 'tag-accent' | 'tag-accent-2' | 'tag-outline' | 'tag-neutral';

export interface Department {
  id: string;
  slug: string;
  label: string;
  initials: string;
  home_view: string;
  order?: number;
  head?: { name: string; title: string } | null;
}

export interface RolePermission {
  id?: string;
  area: string;
  area_label?: string;
  level: PermissionLevel;
}

export interface Role {
  id: string;
  slug: string;
  label: string;
  scope: Scope;
  mfa_required?: boolean;
  is_director?: boolean;
  permissions?: RolePermission[];
}

/** area -> granted level, as produced by `User.permission_map()`. */
export type PermissionMap = Record<string, PermissionLevel>;

export interface NavItem {
  key: string;
  label: string;
  count: string;
  route: string;
}

export interface NavGroup {
  heading: string;
  items: NavItem[];
}

export interface PermissionRow {
  area: string;
  level: string;
}

export interface User {
  id: string;
  email: string;
  display_name: string;
  job_title: string;
  initials: string;
  first_name_only?: string;
  department: Department | null;
  role: Role | null;
  state?: string;
  utilisation?: number | string;
  mfa_enabled?: boolean;
  last_sign_in?: string | null;
  /** present on /api/auth/me/ and the login response */
  permissions?: PermissionMap;
  scope?: Scope;
  visible_departments?: Department[];
  nav_groups?: NavGroup[];
  permission_rows?: PermissionRow[];
  home_view?: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
  toast?: string;
}

/** Column descriptor for a record list. */
export interface ViewColumn {
  l: string;
  a?: 'left' | 'right' | 'center';
}

export interface ViewStat {
  label: string;
  value: string;
  note?: string;
}

/** The `view` block every generic list endpoint returns. */
export interface ViewConfig {
  title: string;
  subtitle: string;
  stats: ViewStat[];
  cols: Array<string | ViewColumn>;
}

/** One rendered cell of a record row. */
export interface RecordCell {
  t: string;
  align?: 'left' | 'right' | 'center';
  bold?: boolean;
  muted?: boolean;
  tag?: TagClass | '';
}

export interface RecordRow {
  id?: string;
  ref?: string;
  route?: string;
  cells: RecordCell[];
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
  /** list endpoints attach the view config for the record-list component */
  view?: ViewConfig;
}

export interface Toast {
  id: number;
  text: string;
}

/** Anything a write endpoint returns: the record plus the design's toast copy. */
export interface ActionResponse<T = unknown> {
  toast?: string;
  [key: string]: T | string | undefined;
}

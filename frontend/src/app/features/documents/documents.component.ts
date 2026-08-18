import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { ToastService } from '../../core/toast.service';
import { EmptyStateComponent } from '../../shared/ui/empty-state/empty-state.component';
import { SkeletonComponent } from '../../shared/ui/skeleton/skeleton.component';
import { LoadFailure, describeError } from '../../shared/util/record-detail';

export interface Folder {
  id: string; key: string; name: string; path: string; meta: string;
  count: number; documents_label: string;
}

export interface DocumentRow {
  id: string; folder: string; name: string; kind: string; attached_ref: string;
  added_by_name: string; when_label: string; size_label: string;
  state: string; tag_class: string;
}

export interface DocActivity { text: string; when: string; }

export interface DocView {
  subtitle?: string;
  totals?: string;
  storage_used?: string;
  storage_width?: string;
  retention?: string;
  activity?: DocActivity[];
  empty_state?: { title: string; note: string; action: string };
}

interface DocumentsPage {
  count: number;
  results: DocumentRow[];
  view?: DocView;
}

interface FolderResult { record: Folder; toast: string; }

const RETENTION = 'Contracts and proposals held seven years. Delivery artefacts held for the '
  + 'life of the support relationship.';

/** `/documents` — document storage (design lines 1079-1181). */
@Component({
  selector: 'app-documents',
  standalone: true,
  imports: [FormsModule, SkeletonComponent, EmptyStateComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './documents.component.html',
  styleUrl: './documents.component.css',
})
export class DocumentsComponent {
  private readonly api = inject(ApiService);
  private readonly auth = inject(AuthService);
  private readonly toasts = inject(ToastService);

  readonly loading = signal(true);
  readonly filesLoading = signal(false);
  readonly failure = signal<LoadFailure | null>(null);

  readonly folders = signal<Folder[]>([]);
  readonly activeKey = signal<string>('');
  readonly files = signal<DocumentRow[]>([]);
  readonly view = signal<DocView>({});

  readonly newFolder = signal<string>('');
  readonly uploadBusy = signal(false);
  readonly creating = signal(false);

  readonly activeFolder = computed<Folder | null>(() =>
    this.folders().find((folder) => folder.key === this.activeKey()) ?? null);

  readonly totals = computed(() => {
    const view = this.view();
    if (view.totals) return view.totals;
    const documents = this.folders().reduce((sum, folder) => sum + (folder.count ?? 0), 0);
    return `${this.folders().length} folders · ${documents} documents · ${this.storageUsed()}`;
  });

  readonly storageUsed = computed(() => this.view().storage_used || '38.4 GB');
  readonly storageWidth = computed(() => this.view().storage_width || '16%');
  readonly retention = computed(() => this.view().retention || RETENTION);
  readonly activity = computed<DocActivity[]>(() => this.view().activity ?? []);

  readonly folderMeta = computed(() => {
    const folder = this.activeFolder();
    if (!folder) return '';
    return folder.documents_label
      || `${folder.meta} · ${this.files().length} documents`;
  });

  readonly emptyTitle = computed(() => this.view().empty_state?.title || 'This folder is empty');
  readonly emptyNote = computed(() => this.view().empty_state?.note
    || 'Upload a document, or attach one from a contract, proposal or milestone.');
  readonly emptyAction = computed(() => this.view().empty_state?.action || 'Upload document');

  constructor() {
    this.loadFolders();
  }

  select(folder: Folder): void {
    if (folder.key === this.activeKey()) return;
    this.activeKey.set(folder.key);
    this.loadFiles();
  }

  // ── upload ────────────────────────────────────────────────────────────

  pickFile(input: HTMLInputElement): void {
    if (this.uploadBusy()) return;
    input.value = '';
    input.click();
  }

  onFilePicked(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    const folder = this.activeFolder();
    if (!folder) {
      this.toasts.show('Choose a folder for the document.');
      return;
    }
    this.uploadBusy.set(true);
    this.api.upload<{ record: DocumentRow; toast: string }>(
      '/documents/upload/', file, { folder: folder.key },
    ).subscribe({
      next: (response) => {
        this.toasts.show(response.toast);
        this.uploadBusy.set(false);
        input.value = '';
        this.loadFolders(folder.key);
      },
      error: (error: unknown) => {
        this.toasts.show(this.detail(error, 'The document could not be stored.'));
        this.uploadBusy.set(false);
        input.value = '';
      },
    });
  }

  // ── folders ───────────────────────────────────────────────────────────

  createFolder(): void {
    const name = this.newFolder().trim();
    if (!name) {
      this.toasts.show('Give the folder a name — storage without naming becomes a '
        + 'dumping ground.');
      return;
    }
    const parent = this.activeFolder();
    this.postFolder({
      name,
      path: parent?.path ?? 'Storage',
      meta: `Created ${this.longToday()} by ${this.auth.currentUser()?.display_name ?? ''}`.trim(),
    });
  }

  clearFolder(): void {
    this.newFolder.set('');
  }

  newSubfolder(): void {
    const folder = this.activeFolder();
    if (!folder) return;
    this.postFolder({
      name: `${folder.name} / Subfolder ${this.folders().length + 1}`,
      path: `${folder.path} / ${folder.name}`,
      meta: `Subfolder created ${this.longToday()}`,
    });
  }

  share(): void {
    const folder = this.activeFolder();
    if (!folder) return;
    this.api.post<{ toast: string }>(`/folders/${folder.id}/share/`).subscribe({
      next: (response) => this.toasts.show(response.toast),
      error: (error: unknown) =>
        this.toasts.show(this.detail(error, 'A share link could not be issued.')),
    });
  }

  private postFolder(body: Record<string, string>): void {
    if (this.creating()) return;
    this.creating.set(true);
    this.api.post<FolderResult>('/folders/', body).subscribe({
      next: (response) => {
        this.toasts.show(response.toast);
        this.newFolder.set('');
        this.creating.set(false);
        this.loadFolders(response.record?.key);
      },
      error: (error: unknown) => {
        this.toasts.show(this.detail(error, 'The folder could not be created.'));
        this.creating.set(false);
      },
    });
  }

  // ── loading ───────────────────────────────────────────────────────────

  private loadFolders(preferKey?: string): void {
    this.loading.set(true);
    this.failure.set(null);
    this.api.list<Folder>('/folders/', { page_size: 100 }).subscribe({
      next: (page) => {
        const rows = page.results ?? [];
        this.folders.set(rows);
        const wanted = preferKey ?? this.activeKey();
        const active = rows.find((folder) => folder.key === wanted) ?? rows[0];
        this.activeKey.set(active?.key ?? '');
        this.loading.set(false);
        if (active) {
          this.loadFiles();
        } else {
          this.files.set([]);
        }
      },
      error: (error: unknown) => {
        this.folders.set([]);
        this.files.set([]);
        this.failure.set(describeError(error, 'Document storage'));
        this.loading.set(false);
      },
    });
  }

  private loadFiles(): void {
    const folder = this.activeFolder();
    if (!folder) return;
    this.filesLoading.set(true);
    this.api.get<DocumentsPage>('/documents/', { folder: folder.id, page_size: 200 }).subscribe({
      next: (page) => {
        this.files.set(page.results ?? []);
        if (page.view) this.view.set(page.view);
        this.filesLoading.set(false);
      },
      error: (error: unknown) => {
        this.files.set([]);
        this.failure.set(describeError(error, 'These documents'));
        this.filesLoading.set(false);
      },
    });
  }

  private detail(error: unknown, fallback: string): string {
    if (error instanceof HttpErrorResponse) {
      const body = error.error as { toast?: string; detail?: string } | null;
      if (body?.toast) return body.toast;
      if (body?.detail) return body.detail;
      if (error.status === 403) {
        return 'Your role does not allow changes to document storage.';
      }
    }
    return fallback;
  }

  private longToday(): string {
    return new Date().toLocaleDateString('en-GB', {
      day: 'numeric', month: 'long', year: 'numeric',
    });
  }
}

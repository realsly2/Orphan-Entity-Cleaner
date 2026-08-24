//
// Panel-Custom-Element für Orphan Cleaner.
//

class OrphanCleanerPanel extends HTMLElement {
  constructor() {
    super();
    this._results = [];
    this._built = false;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._built) {
      this._built = true;
      this._build();
      this._refreshResults();
    }
  }

  get hass() {
    return this._hass;
  }

  _build() {
    this.innerHTML = `
      <style>
        :host { display: block; }
        .oc-wrap {
          font-family: var(--paper-font-body1_-_font-family, system-ui, sans-serif);
          padding: 16px;
          color: var(--primary-text-color, #222);
        }
        .oc-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
        .oc-toolbar { margin-bottom: 12px; }
        input, button { padding: 8px; font-size: 14px; }
        input[type="text"] { min-width: 280px; }
        table { width: 100%; border-collapse: collapse; margin-top: 12px; }
        th, td {
          border-bottom: 1px solid var(--divider-color, #ddd);
          padding: 8px;
          text-align: left;
          vertical-align: top;
        }
        th { background: var(--secondary-background-color, #f7f7f7); }
        .oc-muted { color: var(--secondary-text-color, #666); }
        .oc-danger { color: #b00020; }
        .oc-spacer { flex: 1; }
        .oc-small { font-size: 12px; }
      </style>
      <div class="oc-wrap">
        <h2>Orphan Cleaner</h2>

        <div class="oc-row oc-toolbar">
          <button id="oc-scan">Scan</button>
          <button id="oc-refresh">Refresh</button>
          <button id="oc-backup">Backup</button>
          <button id="oc-download">Download Backup</button>
          <button id="oc-restore">Restore Backup</button>
          <button id="oc-export">Export</button>
          <button id="oc-clear">Clear</button>
          <button id="oc-delete" class="oc-danger">Delete Selected</button>
          <input type="file" id="oc-restore-file" accept=".json" style="display: none;" />
          <span class="oc-spacer"></span>
          <input id="oc-q" type="text" placeholder="Search entity_id, name, platform" />
        </div>

        <div class="oc-row oc-toolbar">
          <button id="oc-select-all">Select Visible</button>
          <button id="oc-unselect-all">Unselect Visible</button>
          <span id="oc-status" class="oc-muted">Idle</span>
        </div>

        <div id="oc-app"></div>
      </div>
    `;

    this.querySelector("#oc-scan").addEventListener("click", () => this._scan());
    this.querySelector("#oc-refresh").addEventListener("click", () => this._refreshResults());
    this.querySelector("#oc-backup").addEventListener("click", () => this._backup());
    this.querySelector("#oc-download").addEventListener("click", () => this._downloadBackup());
    this.querySelector("#oc-restore").addEventListener("click", () => this.querySelector("#oc-restore-file").click());
    this.querySelector("#oc-restore-file").addEventListener("change", (e) => this._restoreBackup(e));
    this.querySelector("#oc-export").addEventListener("click", () => this._exportResults());
    this.querySelector("#oc-clear").addEventListener("click", () => this._clearResults());
    this.querySelector("#oc-delete").addEventListener("click", () => this._deleteSelected());
    this.querySelector("#oc-q").addEventListener("input", () => this._render());
    this.querySelector("#oc-select-all").addEventListener("click", () => this._selectVisible(true));
    this.querySelector("#oc-unselect-all").addEventListener("click", () => this._selectVisible(false));
  }

  _setStatus(text) {
    const el = this.querySelector("#oc-status");
    if (el) el.textContent = text;
  }

  _filtered() {
    const qInput = this.querySelector("#oc-q");
    const q = (qInput && qInput.value ? qInput.value : "").toLowerCase().trim();
    return this._results.filter(
      (x) =>
        !q ||
        (x.entity_id || "").toLowerCase().includes(q) ||
        (x.name || "").toLowerCase().includes(q) ||
        (x.platform || "").toLowerCase().includes(q)
    );
  }

  _escapeHtml(value) {
    return String(value ?? "").replace(/[&<>'"]/g, (character) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "'": "&#39;",
      '"': "&quot;",
    }[character]));
  }

  _entityLink(entityId) {
    const escapedId = this._escapeHtml(entityId);
    const href = `/config/entities/entity/${encodeURIComponent(entityId)}`;
    return `<a href="${href}" target="_blank" rel="noopener" title="Entity in Home Assistant öffnen">${escapedId}</a>`;
  }

  _render() {
    const rows = this._filtered();
    this._setStatus(`${rows.length} shown / ${this._results.length} total`);
    this.querySelector("#oc-app").innerHTML = `
      <table>
        <thead>
          <tr>
            <th></th>
            <th>Entity</th>
            <th>Name</th>
            <th>Platform</th>
            <th>Reason</th>
            <th>Config Entry ID</th>
            <th>Device ID</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (x) => `
            <tr>
              <td>${x.pending_purge ? "" : `<input type="checkbox" data-entity="${this._escapeHtml(x.entity_id)}">`}</td>
              <td>${x.entity_id ? this._entityLink(x.entity_id) : ""}</td>
              <td>${this._escapeHtml(x.name)}${x.pending_purge ? " <em>(wird von HA automatisch entfernt)</em>" : ""}</td>
              <td>${this._escapeHtml(x.platform)}</td>
              <td>${this._escapeHtml(x.reason)}</td>
              <td class="oc-small">${this._escapeHtml(x.config_entry_id)}</td>
              <td class="oc-small">${this._escapeHtml(x.device_id)}</td>
            </tr>
          `
            )
            .join("")}
        </tbody>
      </table>`;
  }

  _visibleCheckboxes() {
    return [...this.querySelectorAll("tbody input[type=checkbox]")];
  }

  _selectVisible(state) {
    this._visibleCheckboxes().forEach((cb) => (cb.checked = state));
  }

  async _refreshResults() {
    this._setStatus("Loading...");
    try {
      const payload = await this.hass.callApi("GET", "orphan_cleaner/results");
      if (Array.isArray(payload)) {
        this._results = payload;
      } else if (payload && Array.isArray(payload.results)) {
        this._results = payload.results;
      } else {
        this._results = [];
      }
    } catch (err) {
      this._results = [];
      this._setStatus(`Error loading results: ${err}`);
      return;
    }
    this._render();
  }

  async _scan() {
    this._setStatus("Scanning...");
    try {
      await this.hass.callService("orphan_cleaner", "scan", {});
    } catch (err) {
      this._setStatus(`Scan failed: ${err}`);
      return;
    }
    await this._refreshResults();
  }

  async _backup() {
    this._setStatus("Backing up...");
    try {
      await this.hass.callService("orphan_cleaner", "backup_results", {});
      this._setStatus("Backup created");
    } catch (err) {
      this._setStatus(`Backup failed: ${err}`);
    }
  }

  async _downloadBackup() {
    this._setStatus("Downloading backup...");
    try {
      const res = await this.hass.callWS({ type: "orphan_cleaner/download_backup" });
      const dataStr = JSON.stringify(res.data, null, 2);
      const blob = new Blob([dataStr], { type: "application/json" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.style.display = "none";
      a.href = url;
      a.download = res.filename || "orphan_cleaner_backup.json";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      this._setStatus(`Downloaded: ${res.filename}`);
    } catch (err) {
      this._setStatus(`Download failed: ${err.message || err}`);
    }
  }

  async _restoreBackup(event) {
    const file = event.target.files[0];
    if (!file) return;

    this._setStatus("Reading restore file...");
    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const jsonContent = JSON.parse(e.target.result);
        const entities = Array.isArray(jsonContent) ? jsonContent : (jsonContent.results || jsonContent.entities || []);

        if (!entities.length) {
          this._setStatus("Restore failed: No entities found in file");
          return;
        }

        const confirmed = window.confirm(`Restore ${entities.length} entities from backup file?`);
        if (!confirmed) {
          this._setStatus("Restore cancelled");
          return;
        }

        this._setStatus("Restoring entities...");
        const res = await this.hass.callWS({
          type: "orphan_cleaner/restore_backup",
          entities: entities,
        });

        this._setStatus(`Restore finished: ${res.restored} entities restored`);
        await this._refreshResults();
      } catch (err) {
        this._setStatus(`Restore failed: ${err.message || err}`);
      } finally {
        event.target.value = "";
      }
    };
    reader.readAsText(file);
  }

  async _exportResults() {
    try {
      await this.hass.callService("orphan_cleaner", "export_results", {});
      this._setStatus("Export stored");
    } catch (err) {
      this._setStatus(`Export failed: ${err}`);
    }
  }

  async _clearResults() {
    try {
      await this.hass.callService("orphan_cleaner", "clear_results", {});
      this._results = [];
      this._render();
    } catch (err) {
      this._setStatus(`Clear failed: ${err}`);
    }
  }

  async _deleteSelected() {
    const ids = this._visibleCheckboxes()
      .filter((cb) => cb.checked)
      .map((cb) => cb.dataset.entity);

    if (!ids.length) {
      this._setStatus("No entities selected");
      return;
    }

    const confirmed = window.confirm(
      `Delete ${ids.length} selected entities? This cannot be undone (except via backup).`
    );
    if (!confirmed) return;

    this._setStatus("Deleting...");
    try {
      await this.hass.callService("orphan_cleaner", "delete_selected", { entity_ids: ids });
    } catch (err) {
      this._setStatus(`Delete failed: ${err}`);
      return;
    }
    await this._refreshResults();
  }
}

customElements.define("orphan-cleaner-panel", OrphanCleanerPanel);
